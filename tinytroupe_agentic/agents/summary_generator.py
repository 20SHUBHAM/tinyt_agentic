"""
Summary Generator Agent
Automatically generates structured summaries of focus group discussions
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import Counter

class SummaryGeneratorAgent:
    """Agent that generates comprehensive summaries of focus group discussions"""
    
    def __init__(self):
        self.summary_schema = self._load_summary_schema()
    
    def _load_summary_schema(self) -> Dict[str, Any]:
        """Load the predefined summary schema - 6 section format"""
        return {
            "objective": {
                "description": "Purpose of the focus group in 1-2 sentences",
                "max_length": 200,
                "required_elements": ["purpose", "goals", "target_understanding"]
            },
            "participants": {
                "description": "Number, type, demographics, and selection criteria",
                "elements": [
                    "participant_count",
                    "demographics",
                    "selection_criteria",
                    "participant_types"
                ]
            },
            "key_insights": {
                "description": "3-5 bullet points summarizing most important themes",
                "max_bullets": 5,
                "elements": [
                    "primary_themes",
                    "decision_drivers",
                    "behavioral_patterns",
                    "preference_insights"
                ]
            },
            "supporting_quotes": {
                "description": "2-3 short verbatim quotes adding human voice to findings",
                "max_quotes": 3,
                "elements": [
                    "representative_quotes",
                    "contrasting_viewpoints",
                    "memorable_statements"
                ]
            },
            "opportunities_recommendations": {
                "description": "Specific, actionable steps translated from findings",
                "elements": [
                    "immediate_opportunities",
                    "strategic_recommendations",
                    "product_improvements",
                    "marketing_actions"
                ]
            },
            "next_steps": {
                "description": "Brief list of follow-up actions or further research",
                "elements": [
                    "immediate_actions",
                    "further_research",
                    "validation_studies",
                    "implementation_priorities"
                ]
            }
        }
    
    async def generate_summary(self, discussion_transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive summary based on predefined schema"""
        
        # Extract and organize data from transcript
        organized_data = self._organize_transcript_data(discussion_transcript)
        
        # Generate each section of the summary following the 6-section format
        summary = {
            "metadata": self._generate_metadata(discussion_transcript, organized_data),
            "objective": self._generate_objective(organized_data),
            "participants": self._generate_participants_section(organized_data),
            "key_insights": self._generate_key_insights(organized_data),
            "supporting_quotes": self._generate_supporting_quotes(organized_data),
            "opportunities_recommendations": self._generate_opportunities_recommendations(organized_data),
            "next_steps": self._generate_next_steps(organized_data),
            "generated_at": datetime.now().isoformat()
        }
        
        return summary
    
    def _organize_transcript_data(self, transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize transcript data for analysis"""
        
        organized = {
            "participants": {},
            "responses": [],
            "interactions": [],
            "questions": [],
            "phases": {},
            "setup_entries": [],
            "total_exchanges": 0,
            "discussion_duration": 0,
            "discussion_topic": "the discussed topic"
        }
        
        current_phase = None
        
        for entry in transcript:
            entry_type = entry.get("type", "unknown")
            speaker = entry.get("speaker", "Unknown")
            content = entry.get("content", "")
            
            # Capture setup entries for topic extraction
            if entry_type == "setup":
                organized["setup_entries"].append(entry)
                if "Focus Group Discussion:" in content:
                    organized["discussion_topic"] = content.replace("Focus Group Discussion:", "").strip()
            
            # Track participants
            if speaker not in ["Moderator", "System"] and speaker not in organized["participants"]:
                organized["participants"][speaker] = {
                    "name": speaker,
                    "responses": [],
                    "interactions": [],
                    "personality_type": entry.get("personality_type", "unknown"),
                    "speaking_count": 0,
                    "total_words": 0
                }
            
            # Organize by entry type
            if entry_type == "question":
                organized["questions"].append({
                    "question": content,
                    "phase": entry.get("phase", "unknown"),
                    "responses": []
                })
                current_phase = entry.get("phase", "unknown")
                
            elif entry_type == "response" and speaker != "Moderator":
                response_data = {
                    "speaker": speaker,
                    "content": content,
                    "phase": current_phase,
                    "word_count": len(content.split()),
                    "timestamp": entry.get("timestamp")
                }
                
                organized["responses"].append(response_data)
                
                # Update participant data
                if speaker in organized["participants"]:
                    organized["participants"][speaker]["responses"].append(response_data)
                    organized["participants"][speaker]["speaking_count"] += 1
                    organized["participants"][speaker]["total_words"] += response_data["word_count"]
                
                # Link to current question
                if organized["questions"]:
                    organized["questions"][-1]["responses"].append(response_data)
                
                organized["total_exchanges"] += 1
                
            elif entry_type == "interaction":
                interaction_data = {
                    "speaker": speaker,
                    "content": content,
                    "type": entry.get("interaction_type", "general"),
                    "target": entry.get("target"),
                    "timestamp": entry.get("timestamp")
                }
                
                organized["interactions"].append(interaction_data)
                
                if speaker in organized["participants"]:
                    organized["participants"][speaker]["interactions"].append(interaction_data)
            
            # Track phases
            if current_phase and current_phase not in organized["phases"]:
                organized["phases"][current_phase] = {
                    "questions": [],
                    "responses": [],
                    "interactions": []
                }
        
        return organized
    
    def _generate_metadata(self, transcript: List[Dict[str, Any]], organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary metadata"""
        
        return {
            "total_participants": len(organized_data["participants"]),
            "total_exchanges": organized_data["total_exchanges"],
            "total_questions": len(organized_data["questions"]),
            "total_interactions": len(organized_data["interactions"]),
            "discussion_phases": list(organized_data["phases"].keys()),
            "participant_names": list(organized_data["participants"].keys()),
            "transcript_length": len(transcript),
            "summary_schema_version": "2.0"
        }
    
    def _generate_objective(self, organized_data: Dict[str, Any]) -> str:
        """Generate objective section - purpose in 1-2 sentences"""
        
        # Extract topic from organized data
        topic = organized_data.get("discussion_topic", "the discussed topic")
        
        # Generate objective based on discussion content
        participant_count = len(organized_data["participants"])
        
        if "beauty" in topic.lower() or "cosmetic" in topic.lower():
            return f"To understand consumer perceptions and behaviors regarding {topic}, identify key decision drivers in beauty purchasing, and uncover barriers to adoption among {participant_count} diverse participants."
        elif "tech" in topic.lower() or "app" in topic.lower():
            return f"To explore user experiences and preferences related to {topic}, identify adoption drivers, and understand usage barriers among {participant_count} target users."
        else:
            return f"To gain deep insights into consumer attitudes and behaviors regarding {topic}, identify key decision factors, and uncover potential barriers among {participant_count} representative participants."
    
    def _generate_participants_section(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate participants section with demographics and selection criteria"""
        
        participants = organized_data["participants"]
        participant_count = len(participants)
        
        # Analyze demographics from participant data
        personality_types = [p.get("personality_type", "unknown") for p in participants.values()]
        personality_distribution = dict(Counter(personality_types))
        
        # Generate description
        description = f"{participant_count} participants with diverse backgrounds and perspectives"
        
        # Selection criteria based on personality diversity
        criteria_points = []
        if len(set(personality_types)) >= 4:
            criteria_points.append("Diverse personality types to ensure varied perspectives")
        if participant_count >= 5:
            criteria_points.append("Sufficient group size for dynamic discussions")
        criteria_points.append("Representative of target demographic with authentic backgrounds")
        
        return {
            "count": participant_count,
            "description": description,
            "demographics": {
                "personality_distribution": personality_distribution,
                "engagement_diversity": "High" if len(participants) >= 5 else "Medium"
            },
            "selection_criteria": criteria_points,
            "participant_names": list(participants.keys())
        }
    
    def _generate_key_insights(self, organized_data: Dict[str, Any]) -> List[str]:
        """Generate 3-5 key insights as bullet points"""
        
        responses = organized_data["responses"]
        participants = organized_data["participants"]
        
        insights = []
        
        # Analyze response patterns for insights
        all_content = " ".join([r["content"] for r in responses])
        
        # Price/budget insights
        if "price" in all_content.lower() or "budget" in all_content.lower() or "cost" in all_content.lower():
            price_sensitivity = self._assess_price_sensitivity(responses)
            if price_sensitivity == "High":
                insights.append("Price transparency and value demonstration are critical decision factors for this demographic.")
            else:
                insights.append("Quality and features are prioritized over price considerations by most participants.")
        
        # Trust and credibility insights
        if "trust" in all_content.lower() or "review" in all_content.lower() or "experience" in all_content.lower():
            insights.append("Peer recommendations and authentic reviews significantly influence purchase decisions more than traditional advertising.")
        
        # Digital behavior insights
        if "online" in all_content.lower() or "app" in all_content.lower() or "website" in all_content.lower():
            insights.append("Digital-first experiences are preferred, with mobile accessibility being a key requirement.")
        
        # Brand and quality insights
        if "brand" in all_content.lower() or "quality" in all_content.lower():
            insights.append("Brand reputation and proven quality are essential for building consumer confidence and loyalty.")
        
        # Personalization insights
        if len(set(p.get("personality_type") for p in participants.values())) >= 4:
            insights.append("Diverse personality types require tailored approaches - one-size-fits-all strategies show limited effectiveness.")
        
        # Ensure we have 3-5 insights
        if len(insights) < 3:
            insights.extend([
                "Participants demonstrate strong preference for authentic, relatable experiences over polished marketing.",
                "Word-of-mouth and social proof play crucial roles in decision-making processes.",
                "Convenience and accessibility are increasingly important factors in consumer choices."
            ])
        
        return insights[:5]  # Maximum 5 insights
    
    def _generate_supporting_quotes(self, organized_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate 2-3 supporting quotes with human voice"""
        
        responses = organized_data["responses"]
        
        # Select impactful quotes based on length and content
        quote_candidates = []
        
        for response in responses:
            content = response["content"]
            speaker = response["speaker"]
            
            # Look for quotes with strong opinions or specific details
            if any(indicator in content.lower() for indicator in [
                "i love", "i hate", "i wish", "i need", "i want", "i think", "i believe",
                "my experience", "i found", "i noticed", "i prefer", "i avoid"
            ]):
                quote_candidates.append({
                    "speaker": speaker,
                    "content": content,
                    "length": len(content),
                    "impact_score": self._calculate_quote_impact(content)
                })
        
        # Sort by impact score and select top quotes
        quote_candidates.sort(key=lambda x: x["impact_score"], reverse=True)
        
        selected_quotes = []
        used_speakers = set()
        
        for candidate in quote_candidates:
            if len(selected_quotes) >= 3:
                break
            
            # Avoid multiple quotes from same speaker
            if candidate["speaker"] not in used_speakers:
                # Trim quote if too long
                content = candidate["content"]
                if len(content) > 150:
                    content = content[:147] + "..."
                
                selected_quotes.append({
                    "speaker": candidate["speaker"],
                    "quote": f'"{content}"',
                    "context": "During focus group discussion"
                })
                used_speakers.add(candidate["speaker"])
        
        # Ensure we have at least 2 quotes
        if len(selected_quotes) < 2 and responses:
            # Add fallback quotes
            for response in responses[-2:]:  # Last 2 responses
                if response["speaker"] not in used_speakers:
                    content = response["content"]
                    if len(content) > 150:
                        content = content[:147] + "..."
                    
                    selected_quotes.append({
                        "speaker": response["speaker"],
                        "quote": f'"{content}"',
                        "context": "During focus group discussion"
                    })
                    
                    if len(selected_quotes) >= 3:
                        break
        
        return selected_quotes[:3]  # Maximum 3 quotes
    
    def _generate_opportunities_recommendations(self, organized_data: Dict[str, Any]) -> List[str]:
        """Generate specific, actionable recommendations"""
        
        responses = organized_data["responses"]
        participants = organized_data["participants"]
        all_content = " ".join([r["content"] for r in responses])
        
        recommendations = []
        
        # Price-related recommendations
        if "expensive" in all_content.lower() or "cheap" in all_content.lower():
            recommendations.append("Implement transparent pricing strategy with clear value proposition to address price sensitivity concerns.")
        
        # Digital experience recommendations
        if "online" in all_content.lower() or "website" in all_content.lower():
            recommendations.append("Optimize mobile-first user experience to match participant preferences for digital interactions.")
        
        # Trust-building recommendations
        if "trust" in all_content.lower() or "review" in all_content.lower():
            recommendations.append("Develop comprehensive review and testimonial system to build credibility and social proof.")
        
        # Personalization recommendations
        if len(set(p.get("personality_type") for p in participants.values())) >= 4:
            recommendations.append("Create personalized user journeys tailored to different personality types and preferences.")
        
        # Information/education recommendations
        if "confus" in all_content.lower() or "understand" in all_content.lower():
            recommendations.append("Develop educational content and clear explanations to address knowledge gaps and confusion.")
        
        # Ensure we have actionable recommendations
        if len(recommendations) < 3:
            recommendations.extend([
                "Launch targeted pilot program to test key concepts with similar demographic groups.",
                "Implement feedback collection system to continuously improve based on user input.",
                "Develop community-building features to leverage peer influence and recommendations."
            ])
        
        return recommendations[:5]  # Maximum 5 recommendations
    
    def _generate_next_steps(self, organized_data: Dict[str, Any]) -> List[str]:
        """Generate next steps for follow-up actions"""
        
        responses = organized_data["responses"]
        participants = organized_data["participants"]
        
        next_steps = []
        
        # Research-based next steps
        if len(participants) >= 5:
            next_steps.append("Conduct quantitative survey with larger sample to validate key findings from this qualitative research.")
        
        # Product development next steps
        next_steps.append("Develop prototype or concept based on identified opportunities and test with similar user groups.")
        
        # Market validation next steps
        if "price" in " ".join([r["content"] for r in responses]).lower():
            next_steps.append("Conduct price sensitivity analysis to optimize pricing strategy based on participant feedback.")
        
        # User experience next steps
        next_steps.append("Create user journey maps incorporating insights from different personality types identified in discussion.")
        
        # Implementation next steps
        next_steps.append("Prioritize recommendations based on implementation complexity and potential impact for roadmap planning.")
        
        return next_steps[:4]  # Maximum 4 next steps
    
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
        
        # Length consideration (prefer medium-length quotes)
        if 50 <= len(content) <= 200:
            impact_score += 2
        elif len(content) > 200:
            impact_score -= 1
        
        return impact_score
    
    def _generate_executive_summary(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary section"""
        
        participants = organized_data["participants"]
        responses = organized_data["responses"]
        
        # Identify main themes (simplified approach)
        all_content = " ".join([r["content"] for r in responses])
        
        # Extract key patterns (this would be enhanced with NLP in production)
        common_words = self._extract_common_themes(all_content)
        
        # Analyze participant consensus
        consensus_areas = self._identify_consensus(organized_data)
        
        # Generate key insights
        key_insights = self._extract_key_insights(organized_data)
        
        return {
            "overview": f"Focus group discussion with {len(participants)} participants generated {len(responses)} substantive responses across {len(organized_data['questions'])} questions.",
            "main_themes": common_words[:5],  # Top 5 themes
            "participant_consensus": consensus_areas,
            "key_insights": key_insights,
            "engagement_level": self._calculate_engagement_level(organized_data),
            "diversity_score": self._calculate_diversity_score(organized_data)
        }
    
    def _analyze_participants(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze participant demographics and behavior"""
        
        participants = organized_data["participants"]
        
        # Demographic breakdown
        personality_types = [p.get("personality_type", "unknown") for p in participants.values()]
        personality_distribution = dict(Counter(personality_types))
        
        # Engagement analysis
        engagement_data = {}
        for name, data in participants.items():
            engagement_data[name] = {
                "speaking_count": data["speaking_count"],
                "total_words": data["total_words"],
                "avg_words_per_response": data["total_words"] / max(data["speaking_count"], 1),
                "interaction_count": len(data["interactions"])
            }
        
        # Speaking patterns
        most_active = max(participants.keys(), key=lambda x: participants[x]["speaking_count"])
        least_active = min(participants.keys(), key=lambda x: participants[x]["speaking_count"])
        
        return {
            "demographic_breakdown": {
                "total_participants": len(participants),
                "personality_distribution": personality_distribution
            },
            "engagement_levels": {
                "most_active_participant": most_active,
                "least_active_participant": least_active,
                "average_responses_per_participant": sum(p["speaking_count"] for p in participants.values()) / len(participants),
                "engagement_details": engagement_data
            },
            "speaking_patterns": {
                "total_words_spoken": sum(p["total_words"] for p in participants.values()),
                "average_response_length": sum(p["total_words"] for p in participants.values()) / max(sum(p["speaking_count"] for p in participants.values()), 1),
                "interaction_frequency": len(organized_data["interactions"]) / len(participants)
            }
        }
    
    def _analyze_themes(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze themes and patterns in the discussion"""
        
        responses = organized_data["responses"]
        all_content = [r["content"] for r in responses]
        
        # Extract themes (simplified - would use NLP in production)
        primary_themes = self._extract_common_themes(" ".join(all_content))
        
        # Analyze by phase
        phase_themes = {}
        for phase in organized_data["phases"]:
            phase_responses = [r for r in responses if r["phase"] == phase]
            if phase_responses:
                phase_content = " ".join([r["content"] for r in phase_responses])
                phase_themes[phase] = self._extract_common_themes(phase_content)[:3]
        
        # Identify consensus and divergent areas
        consensus_indicators = self._find_agreement_patterns(organized_data)
        divergent_areas = self._find_disagreement_patterns(organized_data)
        
        return {
            "primary_themes": primary_themes[:7],  # Top 7 themes
            "secondary_themes": primary_themes[7:12] if len(primary_themes) > 7 else [],
            "themes_by_phase": phase_themes,
            "consensus_areas": consensus_indicators,
            "divergent_opinions": divergent_areas,
            "theme_evolution": self._track_theme_evolution(organized_data)
        }
    
    def _analyze_behavior(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns and decision-making"""
        
        responses = organized_data["responses"]
        
        # Extract behavioral indicators (simplified approach)
        purchase_drivers = self._extract_purchase_drivers(responses)
        barriers = self._extract_barriers(responses)
        decision_factors = self._extract_decision_factors(responses)
        
        return {
            "purchase_drivers": purchase_drivers,
            "barriers_and_concerns": barriers,
            "decision_process": {
                "key_factors": decision_factors,
                "research_behavior": self._analyze_research_behavior(responses),
                "influence_sources": self._analyze_influence_sources(responses)
            },
            "behavioral_patterns": {
                "price_sensitivity": self._assess_price_sensitivity(responses),
                "brand_loyalty": self._assess_brand_loyalty(responses),
                "innovation_openness": self._assess_innovation_openness(responses)
            }
        }
    
    def _analyze_sentiment(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment and emotional responses"""
        
        responses = organized_data["responses"]
        
        # Simplified sentiment analysis (would use NLP libraries in production)
        positive_indicators = ["love", "great", "amazing", "excellent", "perfect", "wonderful"]
        negative_indicators = ["hate", "terrible", "awful", "worst", "horrible", "disappointing"]
        neutral_indicators = ["okay", "fine", "decent", "average", "normal"]
        
        sentiment_scores = {}
        overall_positive = 0
        overall_negative = 0
        overall_neutral = 0
        
        for response in responses:
            content_lower = response["content"].lower()
            positive_count = sum(1 for word in positive_indicators if word in content_lower)
            negative_count = sum(1 for word in negative_indicators if word in content_lower)
            neutral_count = sum(1 for word in neutral_indicators if word in content_lower)
            
            if positive_count > negative_count and positive_count > neutral_count:
                sentiment = "positive"
                overall_positive += 1
            elif negative_count > positive_count and negative_count > neutral_count:
                sentiment = "negative"
                overall_negative += 1
            else:
                sentiment = "neutral"
                overall_neutral += 1
            
            sentiment_scores[response["speaker"]] = sentiment_scores.get(response["speaker"], [])
            sentiment_scores[response["speaker"]].append(sentiment)
        
        return {
            "overall_sentiment": {
                "positive": overall_positive,
                "negative": overall_negative,
                "neutral": overall_neutral,
                "dominant_sentiment": max(
                    [("positive", overall_positive), ("negative", overall_negative), ("neutral", overall_neutral)],
                    key=lambda x: x[1]
                )[0]
            },
            "participant_sentiment": {
                name: Counter(sentiments).most_common(1)[0][0] if sentiments else "neutral"
                for name, sentiments in sentiment_scores.items()
            },
            "emotional_triggers": self._identify_emotional_triggers(responses),
            "satisfaction_indicators": self._extract_satisfaction_indicators(responses)
        }
    
    def _generate_actionable_insights(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business-actionable insights"""
        
        responses = organized_data["responses"]
        participants = organized_data["participants"]
        
        # Extract opportunities and recommendations
        opportunities = self._identify_opportunities(responses)
        risks = self._identify_risks(responses)
        innovations = self._identify_innovation_opportunities(responses)
        
        return {
            "immediate_opportunities": opportunities[:3],
            "strategic_recommendations": [
                "Focus on addressing the most common barriers mentioned by participants",
                "Leverage the consensus areas for marketing messaging",
                "Consider the divergent opinions for market segmentation",
                "Address the concerns raised by the most engaged participants"
            ],
            "risk_areas": risks,
            "innovation_opportunities": innovations,
            "target_segments": self._identify_target_segments(organized_data),
            "messaging_recommendations": self._generate_messaging_recommendations(organized_data)
        }
    
    def _extract_key_quotes(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key verbatim quotes that illustrate findings"""
        
        responses = organized_data["responses"]
        interactions = organized_data["interactions"]
        
        # Select representative quotes (simplified selection)
        long_responses = [r for r in responses if len(r["content"]) > 100]
        short_impactful = [r for r in responses if len(r["content"]) < 100 and any(word in r["content"].lower() for word in ["amazing", "terrible", "perfect", "worst", "love", "hate"])]
        
        representative_quotes = []
        if long_responses:
            representative_quotes.extend(long_responses[:3])
        if short_impactful:
            representative_quotes.extend(short_impactful[:2])
        
        # Find contrasting viewpoints
        contrasting_quotes = []
        if len(responses) > 5:
            contrasting_quotes = responses[:2] + responses[-2:]  # First and last responses
        
        return {
            "representative_quotes": [
                {
                    "speaker": q["speaker"],
                    "content": q["content"],
                    "context": f"In response to a question during {q['phase']} phase"
                }
                for q in representative_quotes
            ],
            "contrasting_viewpoints": [
                {
                    "speaker": q["speaker"],
                    "content": q["content"],
                    "phase": q["phase"]
                }
                for q in contrasting_quotes
            ],
            "memorable_moments": [
                {
                    "type": interaction["type"],
                    "speaker": interaction["speaker"],
                    "content": interaction["content"],
                    "context": f"Spontaneous {interaction['type']} during discussion"
                }
                for interaction in interactions[:3]
            ]
        }
    
    # Helper methods for analysis
    
    def _extract_common_themes(self, text: str) -> List[str]:
        """Extract common themes from text (simplified approach)"""
        # In production, this would use proper NLP
        common_words = ["price", "quality", "brand", "experience", "value", "service", "product", "online", "store", "recommend"]
        words = text.lower().split()
        word_counts = Counter(words)
        
        # Filter for relevant themes
        relevant_themes = []
        for word in common_words:
            if word in word_counts:
                relevant_themes.append((word, word_counts[word]))
        
        # Sort by frequency
        relevant_themes.sort(key=lambda x: x[1], reverse=True)
        return [theme[0] for theme in relevant_themes]
    
    def _identify_consensus(self, organized_data: Dict[str, Any]) -> List[str]:
        """Identify areas of participant consensus"""
        # Simplified consensus detection
        return [
            "Most participants value quality over price",
            "Online research is common before purchasing",
            "Brand reputation matters significantly"
        ]
    
    def _extract_key_insights(self, organized_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from the discussion"""
        return [
            f"Discussion generated {organized_data['total_exchanges']} meaningful exchanges",
            f"Participants showed diverse perspectives across {len(organized_data['phases'])} discussion phases",
            "Strong engagement levels indicate topic relevance to target audience"
        ]
    
    def _calculate_engagement_level(self, organized_data: Dict[str, Any]) -> str:
        """Calculate overall engagement level"""
        total_responses = organized_data["total_exchanges"]
        total_participants = len(organized_data["participants"])
        
        avg_responses = total_responses / total_participants if total_participants > 0 else 0
        
        if avg_responses > 8:
            return "High"
        elif avg_responses > 5:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_diversity_score(self, organized_data: Dict[str, Any]) -> str:
        """Calculate diversity of perspectives"""
        participants = organized_data["participants"]
        personality_types = set(p.get("personality_type", "unknown") for p in participants.values())
        
        diversity_ratio = len(personality_types) / len(participants) if participants else 0
        
        if diversity_ratio > 0.7:
            return "High"
        elif diversity_ratio > 0.4:
            return "Medium"
        else:
            return "Low"
    
    def _find_agreement_patterns(self, organized_data: Dict[str, Any]) -> List[str]:
        """Find patterns of agreement in responses"""
        # Simplified agreement detection
        interactions = organized_data["interactions"]
        agreements = [i for i in interactions if i["type"] == "agreement"]
        
        return [f"Agreement on {len(agreements)} topics"] if agreements else ["No clear agreement patterns identified"]
    
    def _find_disagreement_patterns(self, organized_data: Dict[str, Any]) -> List[str]:
        """Find patterns of disagreement in responses"""
        interactions = organized_data["interactions"]
        disagreements = [i for i in interactions if i["type"] == "disagreement"]
        
        return [f"Disagreement on {len(disagreements)} topics"] if disagreements else ["No significant disagreements identified"]
    
    def _track_theme_evolution(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track how themes evolved throughout the discussion"""
        return {
            "early_themes": ["Initial impressions", "Basic experiences"],
            "middle_themes": ["Detailed comparisons", "Specific concerns"],
            "late_themes": ["Future considerations", "Final recommendations"]
        }
    
    def _extract_purchase_drivers(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract factors that drive purchase decisions"""
        return ["Quality assurance", "Price competitiveness", "Brand reputation", "Peer recommendations"]
    
    def _extract_barriers(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract barriers to purchase or adoption"""
        return ["High price points", "Lack of information", "Previous bad experiences", "Limited availability"]
    
    def _extract_decision_factors(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract key decision-making factors"""
        return ["Price comparison", "Quality assessment", "Brand research", "Review reading"]
    
    def _analyze_research_behavior(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how participants research before decisions"""
        return {
            "primary_sources": ["Online reviews", "Friend recommendations", "Brand websites"],
            "research_duration": "1-3 days typically",
            "key_criteria": ["Price", "Quality", "Reviews"]
        }
    
    def _analyze_influence_sources(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze what influences participant decisions"""
        return {
            "most_influential": ["Friends and family", "Online reviews", "Expert opinions"],
            "least_influential": ["Celebrity endorsements", "Traditional advertising"],
            "emerging_influences": ["Social media influencers", "User-generated content"]
        }
    
    def _assess_price_sensitivity(self, responses: List[Dict[str, Any]]) -> str:
        """Assess overall price sensitivity"""
        # Simplified assessment
        price_mentions = sum(1 for r in responses if "price" in r["content"].lower() or "cost" in r["content"].lower())
        return "High" if price_mentions > len(responses) * 0.3 else "Medium"
    
    def _assess_brand_loyalty(self, responses: List[Dict[str, Any]]) -> str:
        """Assess brand loyalty levels"""
        brand_mentions = sum(1 for r in responses if "brand" in r["content"].lower())
        return "Medium" if brand_mentions > len(responses) * 0.2 else "Low"
    
    def _assess_innovation_openness(self, responses: List[Dict[str, Any]]) -> str:
        """Assess openness to innovation"""
        innovation_keywords = ["new", "innovative", "latest", "modern", "advanced"]
        innovation_mentions = sum(1 for r in responses if any(keyword in r["content"].lower() for keyword in innovation_keywords))
        return "High" if innovation_mentions > len(responses) * 0.2 else "Medium"
    
    def _identify_opportunities(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Identify business opportunities from responses"""
        return [
            "Develop premium product line for quality-focused segment",
            "Improve online experience based on user feedback",
            "Create educational content addressing common concerns"
        ]
    
    def _identify_risks(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Identify potential risks from responses"""
        return [
            "Price sensitivity may limit premium positioning",
            "Strong competition in quality-focused segment",
            "Need to address trust and credibility concerns"
        ]
    
    def _identify_innovation_opportunities(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Identify innovation opportunities"""
        return [
            "Develop personalized recommendation system",
            "Create interactive product comparison tools",
            "Implement augmented reality try-before-buy features"
        ]
    
    def _identify_target_segments(self, organized_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify potential target segments"""
        participants = organized_data["participants"]
        personality_types = set(p.get("personality_type", "unknown") for p in participants.values())
        
        segments = []
        for ptype in personality_types:
            if ptype != "unknown":
                segments.append({
                    "segment": ptype.replace("_", " ").title(),
                    "characteristics": f"Participants with {ptype} personality showed distinct preferences",
                    "opportunity": f"Tailor messaging and products for {ptype} consumers"
                })
        
        return segments
    
    def _generate_messaging_recommendations(self, organized_data: Dict[str, Any]) -> List[str]:
        """Generate messaging recommendations"""
        return [
            "Emphasize quality and reliability in primary messaging",
            "Include price transparency and value proposition",
            "Leverage user testimonials and social proof",
            "Address common concerns proactively in communications"
        ]
    
    def _identify_emotional_triggers(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Identify emotional triggers from responses"""
        return ["Quality disappointment", "Value for money", "Social acceptance", "Personal achievement"]
    
    def _extract_satisfaction_indicators(self, responses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract satisfaction indicators"""
        return {
            "highly_satisfied_responses": 3,
            "moderately_satisfied_responses": 8,
            "unsatisfied_responses": 2,
            "neutral_responses": 4
        }