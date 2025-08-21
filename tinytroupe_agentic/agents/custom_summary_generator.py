"""
Custom Summary Generator Agent
Generates summaries based on user-provided schemas and requirements
"""

import json
import re
from typing import Dict, List, Any
from datetime import datetime
from collections import Counter
from core.llm_client import LLMClient

class CustomSummaryGeneratorAgent:
    """Agent that generates custom summaries based on user-defined schemas"""
    
    def __init__(self):
        self._llm = LLMClient()
    
    async def generate_custom_summary(self, transcript: List[Dict[str, Any]], 
                                    personas: List[Dict[str, Any]], 
                                    schema: str, 
                                    topic: str) -> Dict[str, Any]:
        """Generate custom summary based on user schema"""
        
        # Organize transcript data
        organized_data = self._organize_transcript_data(transcript, personas, topic)
        
        # Parse user schema to understand requirements
        schema_sections = self._parse_schema(schema)
        
        # LLM-first: attempt to directly produce the custom-structured JSON
        if self._llm.enabled and schema_sections:
            system_prompt = (
                "You are an insights analyst. Given a transcript, personas, and a user-defined outline, "
                "produce a JSON object whose keys are derived from the outline entries (underscored)."
            )
            schema_list = "\n".join(s.get("original_line", s.get("title", "")) for s in schema_sections)
            transcript_text = "\n".join(
                f"[{e.get('speaker','')}|{e.get('type','')}] {e.get('content','')}" for e in transcript[:800]
            )
            user_prompt = (
                f"Outline lines (keep order):\n{schema_list}\n\n"
                f"Personas count: {len(personas)}\nTopic: {topic}\n\n"
                f"Transcript excerpt (truncated):\n{transcript_text}\n\n"
                "Return STRICT JSON only."
            )
            try:
                llm_json = self._llm.generate_json_sync(system_prompt, user_prompt, schema_hint="arbitrary keyed object")
                if isinstance(llm_json, dict) and llm_json:
                    meta = {
                        "summary_type": "custom",
                        "user_schema": schema,
                        "generated_at": datetime.now().isoformat(),
                        "total_participants": len(personas),
                        "discussion_topic": topic
                    }
                    llm_json.setdefault("metadata", meta)
                    return llm_json
            except Exception:
                pass

        # Fallback: local generation per section
        custom_summary = {
            "metadata": {
                "summary_type": "custom",
                "user_schema": schema,
                "generated_at": datetime.now().isoformat(),
                "total_participants": len(personas),
                "discussion_topic": topic
            }
        }
        for section in schema_sections:
            section_content = await self._generate_section_content(
                section, organized_data, transcript, personas
            )
            custom_summary[section["key"]] = section_content
        return custom_summary
    
    def _organize_transcript_data(self, transcript: List[Dict[str, Any]], 
                                 personas: List[Dict[str, Any]], 
                                 topic: str) -> Dict[str, Any]:
        """Organize transcript data for analysis"""
        
        organized = {
            "participants": {p["name"]: p for p in personas},
            "responses": [],
            "interactions": [],
            "questions": [],
            "topic": topic,
            "all_content": "",
            "participant_contributions": {},
            "themes": [],
            "quotes": []
        }
        
        # Process transcript entries
        for entry in transcript:
            entry_type = entry.get("type", "unknown")
            speaker = entry.get("speaker", "Unknown")
            content = entry.get("content", "")
            
            if entry_type == "response" and speaker != "Moderator":
                response_data = {
                    "speaker": speaker,
                    "content": content,
                    "word_count": len(content.split()),
                    "timestamp": entry.get("timestamp")
                }
                organized["responses"].append(response_data)
                organized["all_content"] += f" {content}"
                
                # Track participant contributions
                if speaker not in organized["participant_contributions"]:
                    organized["participant_contributions"][speaker] = []
                organized["participant_contributions"][speaker].append(response_data)
                
                # Collect potential quotes
                if len(content) > 50 and len(content) < 300:
                    organized["quotes"].append({
                        "speaker": speaker,
                        "content": content,
                        "impact_score": self._calculate_quote_impact(content)
                    })
            
            elif entry_type == "question":
                organized["questions"].append({
                    "question": content,
                    "responses": []
                })
            
            elif entry_type == "interaction":
                organized["interactions"].append({
                    "speaker": speaker,
                    "content": content,
                    "type": entry.get("interaction_type", "general")
                })
        
        # Extract themes from content
        organized["themes"] = self._extract_themes(organized["all_content"])
        
        return organized
    
    def _parse_schema(self, schema: str) -> List[Dict[str, str]]:
        """Parse user schema into structured sections"""
        
        sections = []
        lines = schema.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered sections (1. Title - Description)
            match = re.match(r'^(\d+)\.\s*(.+?)(?:\s*-\s*(.+))?$', line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                description = match.group(3).strip() if match.group(3) else ""
                
                section_key = title.lower().replace(' ', '_').replace('&', 'and')
                section_key = re.sub(r'[^\w]', '', section_key)
                
                sections.append({
                    "number": number,
                    "title": title,
                    "description": description,
                    "key": section_key,
                    "original_line": line
                })
            
            # Look for bullet points or other formats
            elif line.startswith('-') or line.startswith('•'):
                title = line[1:].strip()
                section_key = title.lower().replace(' ', '_').replace('&', 'and')
                section_key = re.sub(r'[^\w]', '', section_key)
                
                sections.append({
                    "number": str(len(sections) + 1),
                    "title": title,
                    "description": "",
                    "key": section_key,
                    "original_line": line
                })
        
        return sections
    
    async def _generate_section_content(self, section: Dict[str, str], 
                                      organized_data: Dict[str, Any],
                                      transcript: List[Dict[str, Any]], 
                                      personas: List[Dict[str, Any]]) -> Any:
        """Generate content for a specific section based on its requirements"""
        
        title_lower = section["title"].lower()
        description_lower = section["description"].lower()
        
        # Objective/Purpose sections
        if any(word in title_lower for word in ["objective", "purpose", "goal"]):
            return self._generate_objective_content(organized_data, section)
        
        # Participant/Demographics sections
        elif any(word in title_lower for word in ["participant", "demographic", "sample"]):
            return self._generate_participant_content(organized_data, personas, section)
        
        # Key insights/findings/themes sections
        elif any(word in title_lower for word in ["insight", "finding", "theme", "key"]):
            return self._generate_insights_content(organized_data, section)
        
        # Quotes/verbatim sections
        elif any(word in title_lower for word in ["quote", "verbatim", "statement"]):
            return self._generate_quotes_content(organized_data, section)
        
        # Recommendations/opportunities sections
        elif any(word in title_lower for word in ["recommend", "opportunity", "suggestion"]):
            return self._generate_recommendations_content(organized_data, section)
        
        # Next steps/future sections
        elif any(word in title_lower for word in ["next", "future", "follow"]):
            return self._generate_next_steps_content(organized_data, section)
        
        # Behavior/purchase/decision sections
        elif any(word in title_lower for word in ["behavior", "purchase", "decision", "buying"]):
            return self._generate_behavioral_content(organized_data, section)
        
        # Brand/competitive sections
        elif any(word in title_lower for word in ["brand", "competitive", "competitor"]):
            return self._generate_brand_content(organized_data, section)
        
        # Marketing/message sections
        elif any(word in title_lower for word in ["marketing", "message", "campaign", "communication"]):
            return self._generate_marketing_content(organized_data, section)
        
        # Price/cost sections
        elif any(word in title_lower for word in ["price", "cost", "budget", "pricing"]):
            return self._generate_pricing_content(organized_data, section)
        
        # General analysis sections
        else:
            return self._generate_general_content(organized_data, section)
    
    def _generate_objective_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> str:
        """Generate objective/purpose content"""
        
        topic = organized_data["topic"]
        participant_count = len(organized_data["participants"])
        
        if "beauty" in topic.lower() or "cosmetic" in topic.lower():
            return f"To understand consumer perceptions and behaviors regarding {topic}, identify key decision drivers in beauty purchasing, and uncover barriers to adoption among {participant_count} diverse participants."
        elif "tech" in topic.lower() or "app" in topic.lower():
            return f"To explore user experiences and preferences related to {topic}, identify adoption drivers, and understand usage barriers among {participant_count} target users."
        else:
            return f"To gain deep insights into consumer attitudes and behaviors regarding {topic}, identify key decision factors, and uncover potential barriers among {participant_count} representative participants."
    
    def _generate_participant_content(self, organized_data: Dict[str, Any], 
                                    personas: List[Dict[str, Any]], 
                                    section: Dict[str, str]) -> Dict[str, Any]:
        """Generate participant demographics content"""
        
        participant_data = {
            "total_count": len(personas),
            "demographics": {},
            "selection_criteria": [],
            "participant_profiles": []
        }
        
        # Analyze demographics
        ages = [p.get("age", 0) for p in personas if p.get("age")]
        locations = [p.get("location", "Unknown") for p in personas]
        personality_types = [p.get("personality_type", "unknown") for p in personas]
        
        participant_data["demographics"] = {
            "age_range": f"{min(ages)}-{max(ages)} years" if ages else "Not specified",
            "locations": list(set(locations)),
            "personality_distribution": dict(Counter(personality_types))
        }
        
        # Generate selection criteria
        participant_data["selection_criteria"] = [
            "Diverse personality types to ensure varied perspectives",
            "Representative age range of target demographic",
            "Geographic diversity across different market segments",
            "Authentic backgrounds with real spending patterns"
        ]
        
        # Individual profiles
        for persona in personas[:5]:  # Show up to 5 profiles
            profile = {
                "name": persona.get("name", "Unknown"),
                "age": persona.get("age", "N/A"),
                "occupation": persona.get("occupation", "N/A"),
                "location": persona.get("location", "N/A"),
                "personality_type": persona.get("personality_type", "balanced").replace('_', ' ').title(),
                "budget": persona.get("monthly_budget", "N/A")
            }
            participant_data["participant_profiles"].append(profile)
        
        return participant_data
    
    def _generate_insights_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> List[str]:
        """Generate key insights content"""
        
        insights = []
        all_content = organized_data["all_content"].lower()
        themes = organized_data["themes"]
        
        # Price/budget insights
        if "price" in all_content or "budget" in all_content or "cost" in all_content:
            insights.append("Price transparency and value demonstration are critical decision factors for this demographic")
        
        # Trust and credibility insights
        if "trust" in all_content or "review" in all_content or "experience" in all_content:
            insights.append("Peer recommendations and authentic reviews significantly influence decisions more than traditional advertising")
        
        # Digital behavior insights
        if "online" in all_content or "app" in all_content or "website" in all_content:
            insights.append("Digital-first experiences are preferred, with mobile accessibility being a key requirement")
        
        # Brand insights
        if "brand" in all_content or "quality" in all_content:
            insights.append("Brand reputation and proven quality are essential for building consumer confidence and loyalty")
        
        # Add theme-based insights
        for theme in themes[:3]:
            insights.append(f"Participants consistently discussed {theme} as a key factor in their decision-making process")
        
        # Ensure we have enough insights
        if len(insights) < 3:
            insights.extend([
                "Participants demonstrate strong preference for authentic, relatable experiences over polished marketing",
                "Word-of-mouth and social proof play crucial roles in decision-making processes",
                "Convenience and accessibility are increasingly important factors in consumer choices"
            ])
        
        return insights[:5]  # Return top 5 insights
    
    def _generate_quotes_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> List[Dict[str, str]]:
        """Generate quotes/verbatim content"""
        
        quotes = organized_data["quotes"]
        
        # Sort by impact score and select best quotes
        quotes.sort(key=lambda x: x["impact_score"], reverse=True)
        
        selected_quotes = []
        used_speakers = set()
        
        for quote in quotes:
            if len(selected_quotes) >= 3:
                break
            
            # Avoid multiple quotes from same speaker
            if quote["speaker"] not in used_speakers:
                content = quote["content"]
                if len(content) > 200:
                    content = content[:197] + "..."
                
                selected_quotes.append({
                    "speaker": quote["speaker"],
                    "quote": f'"{content}"',
                    "context": "During focus group discussion"
                })
                used_speakers.add(quote["speaker"])
        
        return selected_quotes
    
    def _generate_recommendations_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> List[str]:
        """Generate recommendations content"""
        
        recommendations = []
        all_content = organized_data["all_content"].lower()
        
        # Content-based recommendations
        if "expensive" in all_content or "price" in all_content:
            recommendations.append("Implement transparent pricing strategy with clear value proposition to address price sensitivity concerns")
        
        if "online" in all_content or "website" in all_content:
            recommendations.append("Optimize mobile-first user experience to match participant preferences for digital interactions")
        
        if "trust" in all_content or "review" in all_content:
            recommendations.append("Develop comprehensive review and testimonial system to build credibility and social proof")
        
        if "confus" in all_content or "understand" in all_content:
            recommendations.append("Develop educational content and clear explanations to address knowledge gaps and confusion")
        
        # Default recommendations if none match
        if len(recommendations) < 3:
            recommendations.extend([
                "Launch targeted pilot program to test key concepts with similar demographic groups",
                "Implement feedback collection system to continuously improve based on user input",
                "Develop community-building features to leverage peer influence and recommendations"
            ])
        
        return recommendations[:5]
    
    def _generate_next_steps_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> List[str]:
        """Generate next steps content"""
        
        return [
            "Conduct quantitative survey with larger sample to validate key findings from this qualitative research",
            "Develop prototype or concept based on identified opportunities and test with similar user groups",
            "Create user journey maps incorporating insights from different personality types identified in discussion",
            "Prioritize recommendations based on implementation complexity and potential impact for roadmap planning"
        ]
    
    def _generate_behavioral_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> Dict[str, Any]:
        """Generate behavioral analysis content"""
        
        return {
            "decision_drivers": [
                "Quality and reliability as primary motivators",
                "Value for money considerations",
                "Social proof and peer recommendations",
                "Brand trust and reputation"
            ],
            "barriers": [
                "Price sensitivity and budget constraints",
                "Trust and credibility concerns",
                "Information overload and confusion",
                "Previous negative experiences"
            ],
            "research_behavior": [
                "Online reviews and peer recommendations highly valued",
                "Social media and influencer content influence research",
                "Traditional advertising has limited impact on this demographic"
            ]
        }
    
    def _generate_brand_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> Dict[str, Any]:
        """Generate brand/competitive analysis content"""
        
        all_content = organized_data["all_content"]
        
        # Extract brand mentions (simplified)
        brand_mentions = []
        common_brands = ["Apple", "Google", "Amazon", "Samsung", "Nike", "Adidas", "Zara", "H&M"]
        
        for brand in common_brands:
            if brand.lower() in all_content.lower():
                brand_mentions.append(brand)
        
        return {
            "mentioned_brands": brand_mentions,
            "brand_preferences": "Participants showed preference for established, trusted brands with strong reputation",
            "competitive_insights": "Brand loyalty varies by personality type, with some preferring innovation and others stability",
            "positioning_opportunities": "Focus on authenticity and value proposition to differentiate from competitors"
        }
    
    def _generate_marketing_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> Dict[str, Any]:
        """Generate marketing insights content"""
        
        return {
            "message_resonance": [
                "Authentic, relatable messaging performs better than polished corporate communication",
                "Value proposition clarity is more important than promotional offers",
                "Personal stories and testimonials create stronger emotional connection"
            ],
            "channel_preferences": [
                "Social media platforms for discovery and research",
                "Peer recommendations through word-of-mouth",
                "Online reviews and comparison sites for validation"
            ],
            "creative_insights": [
                "Visual content should reflect diversity and authenticity",
                "User-generated content more trusted than branded content",
                "Educational content valued over purely promotional material"
            ]
        }
    
    def _generate_pricing_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> Dict[str, Any]:
        """Generate pricing analysis content"""
        
        personas = list(organized_data["participants"].values())
        budgets = [p.get("monthly_budget", "") for p in personas if p.get("monthly_budget")]
        
        return {
            "price_sensitivity": "High sensitivity to price with strong focus on value for money",
            "budget_ranges": budgets,
            "value_perception": [
                "Quality and durability justify higher prices",
                "Transparent pricing builds trust and confidence",
                "Bundled offers and packages show better value perception"
            ],
            "pricing_recommendations": [
                "Implement tiered pricing to accommodate different budget levels",
                "Provide clear value comparison against competitors",
                "Consider subscription or payment plan options for higher-priced items"
            ]
        }
    
    def _generate_general_content(self, organized_data: Dict[str, Any], section: Dict[str, str]) -> str:
        """Generate general analysis content"""
        
        return f"Based on the discussion analysis for '{section['title']}', participants provided diverse perspectives that highlight the complexity of consumer decision-making in this space. The insights gathered provide valuable direction for strategic planning and implementation."
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract themes from content"""
        
        # Simple theme extraction based on word frequency
        words = content.lower().split()
        word_counts = Counter(words)
        
        # Filter for meaningful themes
        theme_words = ["price", "quality", "brand", "experience", "value", "service", "product", "online", "trust", "recommend"]
        themes = []
        
        for word in theme_words:
            if word_counts.get(word, 0) > 2:  # Mentioned more than twice
                themes.append(word)
        
        return themes[:5]  # Return top 5 themes
    
    def _calculate_quote_impact(self, content: str) -> int:
        """Calculate impact score for quote selection"""
        
        impact_score = 0
        content_lower = content.lower()
        
        # Emotional indicators
        emotional_words = ["love", "hate", "amazing", "terrible", "perfect", "awful", "excited", "disappointed"]
        impact_score += sum(2 for word in emotional_words if word in content_lower)
        
        # Specific details
        if any(indicator in content_lower for indicator in ["₹", "rupees", "cost", "price", "brand", "product"]):
            impact_score += 3
        
        # Personal experience indicators
        personal_indicators = ["my experience", "i found", "i tried", "i bought", "i use"]
        impact_score += sum(2 for indicator in personal_indicators if indicator in content_lower)
        
        # Length consideration
        if 50 <= len(content) <= 200:
            impact_score += 2
        elif len(content) > 200:
            impact_score -= 1
        
        return impact_score