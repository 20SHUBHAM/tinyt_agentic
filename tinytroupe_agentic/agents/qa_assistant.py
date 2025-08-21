"""
Q&A Assistant Agent
Interactive assistant for answering questions about focus group discussions
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.llm_client import LLMClient

class QAAssistantAgent:
    """Agent that provides interactive Q&A capabilities over discussion transcripts"""
    
    def __init__(self):
        self.question_categories = self._load_question_categories()
        self.context_memory = {}
        self._llm = LLMClient()
    
    def _load_question_categories(self) -> Dict[str, List[str]]:
        """Load common question categories and templates"""
        return {
            "participant_specific": [
                "What did {participant} say about {topic}?",
                "How did {participant} react to {topic}?",
                "What was {participant}'s main concern about {topic}?"
            ],
            "theme_analysis": [
                "What were the main themes discussed?",
                "What topics generated the most discussion?",
                "Where did participants agree/disagree?"
            ],
            "behavioral_insights": [
                "What drives purchasing decisions for this group?",
                "What are the main barriers to adoption?",
                "How do participants research before buying?"
            ],
            "demographic_analysis": [
                "How did different age groups respond?",
                "What personality types were most engaged?",
                "Which participants were most influential?"
            ],
            "sentiment_analysis": [
                "What was the overall sentiment about {topic}?",
                "Which topics were received most positively?",
                "What concerns were raised most frequently?"
            ],
            "comparative_analysis": [
                "How do online vs offline preferences compare?",
                "What are the differences between price-sensitive and premium segments?",
                "How do brand loyalists differ from switchers?"
            ],
            "actionable_insights": [
                "What are the key recommendations from this discussion?",
                "What opportunities were identified?",
                "What risks should we be aware of?"
            ]
        }
    
    async def answer_question(self, question: str, transcript: List[Dict[str, Any]], 
                            summary: Dict[str, Any], personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer a question based on discussion data. Prefer LLM, fallback to rules."""

        question_category = self._categorize_question(question)
        context = self._extract_relevant_context(question, transcript, summary, personas)

        if self._llm.enabled:
            system_prompt = (
                "You are a Q&A assistant over a focus group transcript and its summary. "
                "Answer succinctly (2-6 bullet points or short paragraph), cite participants by name, and stay grounded."
            )
            transcript_snip = "\n".join(
                f"[{e.get('speaker','')}|{e.get('type','')}] {e.get('content','')}" for e in transcript[:600]
            )
            summary_text = json.dumps(summary)[:4000]
            user_prompt = (
                f"Question: {question}\nCategory: {question_category}\n\n"
                f"Transcript excerpt (truncated):\n{transcript_snip}\n\n"
                f"Summary (truncated JSON):\n{summary_text}\n\n"
                "Respond clearly."
            )
            try:
                answer_text = self._llm.generate_text_sync(system_prompt, user_prompt, temperature=0.4, max_tokens=220)
                if answer_text:
                    result = {
                        "answer": answer_text,
                        "category": question_category,
                        "confidence": "high",
                        "source_type": "llm"
                    }
                    self.context_memory[question] = {
                        "answer": result,
                        "category": question_category,
                        "context": context,
                        "timestamp": datetime.now().isoformat()
                    }
                    return result
            except Exception:
                pass

        # Fallback to deterministic logic
        answer = self._generate_answer(question, question_category, context, transcript, summary, personas)
        self.context_memory[question] = {
            "answer": answer,
            "category": question_category,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        return answer
    
    def _categorize_question(self, question: str) -> str:
        """Categorize the question to determine response approach"""
        
        question_lower = question.lower()
        
        # Check for participant-specific questions
        if any(word in question_lower for word in ["who", "which participant", "what did", "how did"]):
            return "participant_specific"
        
        # Check for theme analysis questions
        if any(word in question_lower for word in ["theme", "topic", "discuss", "main", "primary"]):
            return "theme_analysis"
        
        # Check for behavioral questions
        if any(word in question_lower for word in ["buy", "purchase", "decision", "behavior", "drive", "motivate"]):
            return "behavioral_insights"
        
        # Check for demographic questions
        if any(word in question_lower for word in ["age", "demographic", "personality", "type", "group"]):
            return "demographic_analysis"
        
        # Check for sentiment questions
        if any(word in question_lower for word in ["sentiment", "feel", "opinion", "positive", "negative", "reaction"]):
            return "sentiment_analysis"
        
        # Check for comparative questions
        if any(word in question_lower for word in ["compare", "difference", "versus", "vs", "contrast"]):
            return "comparative_analysis"
        
        # Check for actionable insights
        if any(word in question_lower for word in ["recommend", "suggest", "opportunity", "action", "next step"]):
            return "actionable_insights"
        
        return "general"
    
    def _extract_relevant_context(self, question: str, transcript: List[Dict[str, Any]], 
                                summary: Dict[str, Any], personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant context for answering the question"""
        
        context = {
            "relevant_responses": [],
            "relevant_interactions": [],
            "relevant_participants": [],
            "relevant_summary_sections": {},
            "keywords": []
        }
        
        # Extract keywords from question
        question_words = question.lower().split()
        stop_words = {"what", "how", "who", "when", "where", "why", "is", "are", "was", "were", "the", "a", "an"}
        keywords = [word for word in question_words if word not in stop_words and len(word) > 2]
        context["keywords"] = keywords
        
        # Find relevant responses
        for entry in transcript:
            if entry.get("type") == "response":
                content_lower = entry.get("content", "").lower()
                if any(keyword in content_lower for keyword in keywords):
                    context["relevant_responses"].append(entry)
        
        # Find relevant interactions
        for entry in transcript:
            if entry.get("type") == "interaction":
                content_lower = entry.get("content", "").lower()
                if any(keyword in content_lower for keyword in keywords):
                    context["relevant_interactions"].append(entry)
        
        # Find relevant participants (if question mentions specific traits)
        for persona in personas:
            persona_text = f"{persona.get('name', '')} {persona.get('background', '')}".lower()
            if any(keyword in persona_text for keyword in keywords):
                context["relevant_participants"].append(persona)
        
        # Extract relevant summary sections
        for section_name, section_data in summary.items():
            if isinstance(section_data, dict):
                section_text = json.dumps(section_data).lower()
                if any(keyword in section_text for keyword in keywords):
                    context["relevant_summary_sections"][section_name] = section_data
        
        return context
    
    def _generate_answer(self, question: str, category: str, context: Dict[str, Any], 
                        transcript: List[Dict[str, Any]], summary: Dict[str, Any], 
                        personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate answer based on question category and context"""
        
        if category == "participant_specific":
            return self._answer_participant_specific(question, context, transcript, personas)
        elif category == "theme_analysis":
            return self._answer_theme_analysis(question, context, summary)
        elif category == "behavioral_insights":
            return self._answer_behavioral_insights(question, context, summary)
        elif category == "demographic_analysis":
            return self._answer_demographic_analysis(question, context, summary, personas)
        elif category == "sentiment_analysis":
            return self._answer_sentiment_analysis(question, context, summary)
        elif category == "comparative_analysis":
            return self._answer_comparative_analysis(question, context, transcript, summary)
        elif category == "actionable_insights":
            return self._answer_actionable_insights(question, context, summary)
        else:
            return self._answer_general(question, context, transcript, summary, personas)
    
    def _answer_participant_specific(self, question: str, context: Dict[str, Any], 
                                   transcript: List[Dict[str, Any]], personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer participant-specific questions"""
        
        # Try to identify which participant is being asked about
        participant_name = None
        for persona in personas:
            if persona["name"].lower() in question.lower():
                participant_name = persona["name"]
                break
        
        if participant_name:
            # Find all responses from this participant
            participant_responses = [
                entry for entry in transcript 
                if entry.get("speaker") == participant_name and entry.get("type") == "response"
            ]
            
            # Find participant's persona info
            participant_info = next((p for p in personas if p["name"] == participant_name), {})
            
            answer_text = f"**{participant_name}** shared several important perspectives during the discussion:\n\n"
            
            if participant_responses:
                # Group responses by topic/theme
                for i, response in enumerate(participant_responses[:4], 1):  # Show up to 4 responses
                    content = response['content']
                    # Truncate long responses
                    if len(content) > 300:
                        content = content[:297] + "..."
                    answer_text += f"**Response {i}:** {content}\n\n"
                
                if len(participant_responses) > 4:
                    answer_text += f"*({participant_name} made {len(participant_responses)} total contributions throughout the discussion)*\n\n"
            else:
                answer_text += f"{participant_name} did not provide specific responses to the main discussion questions, but was present as a participant.\n\n"
            
            # Add detailed persona context
            if participant_info:
                answer_text += f"**Participant Profile:**\n"
                answer_text += f"• **Age:** {participant_info.get('age', 'N/A')} years old\n"
                answer_text += f"• **Occupation:** {participant_info.get('occupation', 'Professional')}\n"
                answer_text += f"• **Location:** {participant_info.get('location', 'Not specified')}\n"
                answer_text += f"• **Personality Type:** {participant_info.get('personality_type', 'balanced').replace('_', ' ').title()}\n"
                answer_text += f"• **Monthly Budget:** {participant_info.get('monthly_budget', 'Not specified')}\n"
                
                if participant_info.get('background'):
                    background = participant_info['background']
                    if len(background) > 200:
                        background = background[:197] + "..."
                    answer_text += f"• **Background:** {background}\n"
            
            return {
                "answer": answer_text,
                "participant": participant_name,
                "response_count": len(participant_responses),
                "confidence": "high" if participant_responses else "medium",
                "source_type": "participant_specific"
            }
        
        else:
            # General participant question without specific name
            relevant_responses = context["relevant_responses"][:6]  # Top 6 relevant responses
            
            answer_text = "Based on participant responses related to your question:\n\n"
            
            if relevant_responses:
                for i, response in enumerate(relevant_responses, 1):
                    content = response['content']
                    if len(content) > 250:
                        content = content[:247] + "..."
                    answer_text += f"**{response['speaker']}:** {content}\n\n"
            else:
                # Fallback to general participant overview
                answer_text = "Here's an overview of the participants and their contributions:\n\n"
                for persona in personas[:5]:  # Show up to 5 participants
                    participant_responses = [
                        entry for entry in transcript 
                        if entry.get("speaker") == persona["name"] and entry.get("type") == "response"
                    ]
                    answer_text += f"**{persona['name']}** ({persona.get('personality_type', 'balanced').replace('_', ' ').title()}): "
                    answer_text += f"{len(participant_responses)} contributions\n"
                
            return {
                "answer": answer_text,
                "response_count": len(relevant_responses),
                "confidence": "medium" if relevant_responses else "low",
                "source_type": "multiple_participants"
            }
    
    def _answer_theme_analysis(self, question: str, context: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Answer theme analysis questions"""
        
        # Use the new summary format
        key_insights = summary.get("key_insights", [])
        supporting_quotes = summary.get("supporting_quotes", [])
        
        answer_text = "Based on the thematic analysis of the discussion:\n\n"
        
        if key_insights:
            answer_text += "**Main Themes Identified:**\n"
            for i, insight in enumerate(key_insights, 1):
                answer_text += f"{i}. {insight}\n"
            answer_text += "\n"
        
        # Add supporting evidence from quotes
        if supporting_quotes:
            answer_text += "**Supporting Evidence:**\n"
            for quote in supporting_quotes[:2]:  # Show up to 2 quotes
                answer_text += f"• {quote.get('quote', '')} - *{quote.get('speaker', 'Participant')}*\n"
            answer_text += "\n"
        
        # Analyze question for specific theme requests
        question_lower = question.lower()
        if "most discussed" in question_lower or "popular" in question_lower:
            answer_text += "**Most Discussed Topics:**\n"
            answer_text += "Based on participant engagement, the themes that generated the most discussion were those related to practical decision-making factors and personal experiences.\n\n"
        
        if "consensus" in question_lower or "agreement" in question_lower:
            answer_text += "**Areas of Consensus:**\n"
            answer_text += "Participants generally agreed on the importance of authentic experiences and value-driven decisions, though specific preferences varied by personality type.\n\n"
        
        if "different" in question_lower or "disagree" in question_lower:
            answer_text += "**Divergent Viewpoints:**\n"
            answer_text += "The main differences emerged around price sensitivity, risk tolerance, and preferred information sources, reflecting the diverse personality types in the group.\n"
        
        return {
            "answer": answer_text,
            "themes_identified": len(key_insights),
            "confidence": "high" if key_insights else "medium",
            "source_type": "thematic_analysis"
        }
    
    def _answer_behavioral_insights(self, question: str, context: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Answer behavioral insights questions"""
        
        # Use new summary format
        key_insights = summary.get("key_insights", [])
        opportunities = summary.get("opportunities_recommendations", [])
        supporting_quotes = summary.get("supporting_quotes", [])
        
        answer_text = "Based on the behavioral analysis from the discussion:\n\n"
        
        question_lower = question.lower()
        
        # Decision-making behavior
        if any(word in question_lower for word in ["decision", "choose", "buy", "purchase"]):
            answer_text += "**Decision-Making Behavior:**\n"
            decision_insights = [insight for insight in key_insights if any(word in insight.lower() for word in ["decision", "choice", "prefer", "select"])]
            if decision_insights:
                for insight in decision_insights[:3]:
                    answer_text += f"• {insight}\n"
            else:
                answer_text += "• Participants showed varied decision-making patterns based on their personality types\n"
                answer_text += "• Price, quality, and peer recommendations were key decision factors\n"
                answer_text += "• Research behavior varied from extensive comparison to impulse decisions\n"
            answer_text += "\n"
        
        # Purchase drivers
        if any(word in question_lower for word in ["drive", "motivate", "influence", "factor"]):
            answer_text += "**Key Purchase Drivers:**\n"
            driver_insights = [insight for insight in key_insights if any(word in insight.lower() for word in ["drive", "factor", "important", "key"])]
            if driver_insights:
                for insight in driver_insights:
                    answer_text += f"• {insight}\n"
            else:
                answer_text += "• Quality and reliability are primary motivators\n"
                answer_text += "• Value for money considerations\n"
                answer_text += "• Social proof and peer recommendations\n"
                answer_text += "• Brand trust and reputation\n"
            answer_text += "\n"
        
        # Barriers and concerns
        if any(word in question_lower for word in ["barrier", "concern", "problem", "issue", "prevent"]):
            answer_text += "**Main Barriers & Concerns:**\n"
            # Extract barrier-related insights
            barrier_insights = [insight for insight in key_insights if any(word in insight.lower() for word in ["barrier", "concern", "problem", "difficult"])]
            if barrier_insights:
                for insight in barrier_insights:
                    answer_text += f"• {insight}\n"
            else:
                answer_text += "• Price sensitivity and budget constraints\n"
                answer_text += "• Trust and credibility concerns\n"
                answer_text += "• Information overload and confusion\n"
                answer_text += "• Previous negative experiences\n"
            answer_text += "\n"
        
        # Add supporting quotes if available
        if supporting_quotes and len(supporting_quotes) > 0:
            answer_text += "**Participant Perspectives:**\n"
            for quote in supporting_quotes[:2]:
                clean_quote = quote.get('quote', '').replace('"', '')
                answer_text += f"• *\"{clean_quote}\"* - {quote.get('speaker', 'Participant')}\n"
            answer_text += "\n"
        
        # Research behavior
        if any(word in question_lower for word in ["research", "information", "learn", "find out"]):
            answer_text += "**Research Behavior:**\n"
            answer_text += "• Participants showed diverse information-seeking patterns\n"
            answer_text += "• Online reviews and peer recommendations are highly valued\n"
            answer_text += "• Social media and influencer content influence research\n"
            answer_text += "• Traditional advertising has limited impact on this demographic\n"
        
        return {
            "answer": answer_text,
            "insights_count": len(key_insights),
            "confidence": "high" if key_insights else "medium",
            "source_type": "behavioral_analysis"
        }
    
    def _answer_demographic_analysis(self, question: str, context: Dict[str, Any], 
                                   summary: Dict[str, Any], personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer demographic analysis questions"""
        
        participant_analysis = summary.get("participant_analysis", {})
        
        answer_text = "Based on the demographic analysis:\n\n"
        
        if "demographic_breakdown" in participant_analysis:
            breakdown = participant_analysis["demographic_breakdown"]
            answer_text += f"**Participant Overview:**\n"
            answer_text += f"• Total participants: {breakdown.get('total_participants', 0)}\n"
            
            if "personality_distribution" in breakdown:
                answer_text += "• Personality distribution:\n"
                for personality, count in breakdown["personality_distribution"].items():
                    answer_text += f"  - {personality.replace('_', ' ').title()}: {count}\n"
            answer_text += "\n"
        
        if "engagement_levels" in participant_analysis:
            engagement = participant_analysis["engagement_levels"]
            answer_text += "**Engagement Patterns:**\n"
            answer_text += f"• Most active: {engagement.get('most_active_participant', 'N/A')}\n"
            answer_text += f"• Average responses per participant: {engagement.get('average_responses_per_participant', 0):.1f}\n\n"
        
        # Add persona details
        answer_text += "**Participant Profiles:**\n"
        for persona in personas[:3]:  # Show first 3 personas
            answer_text += f"• {persona['name']}: {persona.get('age', 'N/A')} years old, "
            answer_text += f"{persona.get('occupation', 'N/A')}, {persona.get('personality_type', 'balanced')} personality\n"
        
        return {
            "answer": answer_text,
            "participant_count": len(personas),
            "confidence": "high",
            "source_type": "demographic_analysis"
        }
    
    def _answer_sentiment_analysis(self, question: str, context: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Answer sentiment analysis questions"""
        
        sentiment_analysis = summary.get("sentiment_analysis", {})
        
        answer_text = "Based on the sentiment analysis:\n\n"
        
        if "overall_sentiment" in sentiment_analysis:
            overall = sentiment_analysis["overall_sentiment"]
            answer_text += "**Overall Sentiment Distribution:**\n"
            answer_text += f"• Positive responses: {overall.get('positive', 0)}\n"
            answer_text += f"• Negative responses: {overall.get('negative', 0)}\n"
            answer_text += f"• Neutral responses: {overall.get('neutral', 0)}\n"
            answer_text += f"• Dominant sentiment: {overall.get('dominant_sentiment', 'neutral').title()}\n\n"
        
        if "emotional_triggers" in sentiment_analysis:
            answer_text += "**Key Emotional Triggers:**\n"
            for trigger in sentiment_analysis["emotional_triggers"][:4]:
                answer_text += f"• {trigger}\n"
            answer_text += "\n"
        
        if "participant_sentiment" in sentiment_analysis:
            answer_text += "**Participant Sentiment:**\n"
            for participant, sentiment in list(sentiment_analysis["participant_sentiment"].items())[:4]:
                answer_text += f"• {participant}: {sentiment.title()}\n"
        
        return {
            "answer": answer_text,
            "dominant_sentiment": sentiment_analysis.get("overall_sentiment", {}).get("dominant_sentiment", "neutral"),
            "confidence": "high" if sentiment_analysis else "medium",
            "source_type": "sentiment_analysis"
        }
    
    def _answer_comparative_analysis(self, question: str, context: Dict[str, Any], 
                                   transcript: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Answer comparative analysis questions"""
        
        # Extract comparison elements from question
        comparison_terms = self._extract_comparison_terms(question)
        
        answer_text = f"Based on the comparative analysis:\n\n"
        
        if comparison_terms:
            answer_text += f"**Comparing {' vs '.join(comparison_terms)}:**\n\n"
            
            # Find responses that mention these terms
            relevant_responses = []
            for entry in transcript:
                if entry.get("type") == "response":
                    content_lower = entry.get("content", "").lower()
                    if any(term.lower() in content_lower for term in comparison_terms):
                        relevant_responses.append(entry)
            
            # Group responses by comparison terms
            for term in comparison_terms:
                term_responses = [r for r in relevant_responses if term.lower() in r["content"].lower()]
                if term_responses:
                    answer_text += f"**{term.title()} perspective:**\n"
                    for response in term_responses[:2]:  # Show up to 2 responses per term
                        answer_text += f"• {response['speaker']}: {response['content'][:150]}...\n"
                    answer_text += "\n"
        
        # Add behavioral insights if available
        behavioral_insights = summary.get("behavioral_insights", {})
        if "behavioral_patterns" in behavioral_insights:
            patterns = behavioral_insights["behavioral_patterns"]
            answer_text += "**Key Behavioral Patterns:**\n"
            for pattern, value in patterns.items():
                answer_text += f"• {pattern.replace('_', ' ').title()}: {value}\n"
        
        return {
            "answer": answer_text,
            "comparison_terms": comparison_terms,
            "confidence": "medium" if comparison_terms else "low",
            "source_type": "comparative_analysis"
        }
    
    def _answer_actionable_insights(self, question: str, context: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Answer actionable insights questions"""
        
        # Use new summary format
        opportunities_recommendations = summary.get("opportunities_recommendations", [])
        next_steps = summary.get("next_steps", [])
        key_insights = summary.get("key_insights", [])
        
        answer_text = "Based on the discussion, here are the key actionable insights:\n\n"
        
        question_lower = question.lower()
        
        # Opportunities and recommendations
        if opportunities_recommendations:
            if any(word in question_lower for word in ["recommend", "suggest", "should", "action"]):
                answer_text += "**Strategic Recommendations:**\n"
                for i, rec in enumerate(opportunities_recommendations, 1):
                    answer_text += f"{i}. {rec}\n"
                answer_text += "\n"
        
        # Next steps
        if next_steps:
            if any(word in question_lower for word in ["next", "follow", "step", "future", "plan"]):
                answer_text += "**Immediate Next Steps:**\n"
                for i, step in enumerate(next_steps, 1):
                    answer_text += f"{i}. {step}\n"
                answer_text += "\n"
        
        # Opportunity identification
        if any(word in question_lower for word in ["opportunity", "potential", "chance", "possibility"]):
            answer_text += "**Key Opportunities Identified:**\n"
            opportunity_insights = [insight for insight in key_insights if any(word in insight.lower() for word in ["opportunity", "potential", "could", "should"])]
            if opportunity_insights:
                for insight in opportunity_insights:
                    answer_text += f"• {insight}\n"
            else:
                # Derive opportunities from recommendations
                if opportunities_recommendations:
                    for opp in opportunities_recommendations[:3]:
                        answer_text += f"• {opp}\n"
            answer_text += "\n"
        
        # Implementation priorities
        if any(word in question_lower for word in ["priority", "important", "first", "urgent"]):
            answer_text += "**Implementation Priorities:**\n"
            if opportunities_recommendations:
                answer_text += f"**High Priority:** {opportunities_recommendations[0]}\n\n"
                if len(opportunities_recommendations) > 1:
                    answer_text += f"**Medium Priority:** {opportunities_recommendations[1]}\n\n"
                if len(opportunities_recommendations) > 2:
                    answer_text += "**Additional Considerations:**\n"
                    for rec in opportunities_recommendations[2:4]:
                        answer_text += f"• {rec}\n"
            answer_text += "\n"
        
        # Risk mitigation
        if any(word in question_lower for word in ["risk", "concern", "avoid", "prevent"]):
            answer_text += "**Risk Mitigation Strategies:**\n"
            answer_text += "• Address price sensitivity through clear value communication\n"
            answer_text += "• Build trust through transparent processes and social proof\n"
            answer_text += "• Ensure mobile-optimized experiences for digital-native users\n"
            answer_text += "• Provide educational content to reduce confusion and uncertainty\n"
        
        # If no specific category, show comprehensive actionable summary
        if not any(word in question_lower for word in ["recommend", "next", "opportunity", "priority", "risk"]):
            if opportunities_recommendations:
                answer_text += "**Key Recommendations:**\n"
                for rec in opportunities_recommendations[:4]:
                    answer_text += f"• {rec}\n"
                answer_text += "\n"
            
            if next_steps:
                answer_text += "**Next Steps:**\n"
                for step in next_steps[:3]:
                    answer_text += f"• {step}\n"
        
        return {
            "answer": answer_text,
            "recommendations_count": len(opportunities_recommendations),
            "next_steps_count": len(next_steps),
            "confidence": "high" if opportunities_recommendations or next_steps else "medium",
            "source_type": "actionable_insights"
        }
    
    def _answer_general(self, question: str, context: Dict[str, Any], transcript: List[Dict[str, Any]], 
                       summary: Dict[str, Any], personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer general questions using available context"""
        
        relevant_responses = context["relevant_responses"][:3]
        relevant_summary = context["relevant_summary_sections"]
        
        answer_text = "Based on the discussion data:\n\n"
        
        if relevant_responses:
            answer_text += "**Relevant Participant Responses:**\n"
            for response in relevant_responses:
                answer_text += f"• {response['speaker']}: {response['content'][:200]}...\n"
            answer_text += "\n"
        
        if relevant_summary:
            answer_text += "**Summary Insights:**\n"
            for section_name, section_data in relevant_summary.items():
                answer_text += f"• {section_name.replace('_', ' ').title()}: Key findings available\n"
            answer_text += "\n"
        
        # Add general discussion stats
        answer_text += "**Discussion Overview:**\n"
        answer_text += f"• Total participants: {len(personas)}\n"
        answer_text += f"• Total responses analyzed: {len([e for e in transcript if e.get('type') == 'response'])}\n"
        answer_text += f"• Discussion phases covered: {len(set(e.get('phase', 'unknown') for e in transcript if e.get('phase')))}\n"
        
        return {
            "answer": answer_text,
            "confidence": "medium" if relevant_responses or relevant_summary else "low",
            "source_type": "general_analysis"
        }
    
    def _extract_comparison_terms(self, question: str) -> List[str]:
        """Extract terms being compared from the question"""
        
        comparison_indicators = ["vs", "versus", "compared to", "difference between", "contrast"]
        
        for indicator in comparison_indicators:
            if indicator in question.lower():
                # Try to extract the terms around the indicator
                parts = question.lower().split(indicator)
                if len(parts) == 2:
                    # Extract key terms from each part
                    term1_words = parts[0].strip().split()[-2:]  # Last 2 words before indicator
                    term2_words = parts[1].strip().split()[:2]   # First 2 words after indicator
                    
                    term1 = " ".join(term1_words).strip()
                    term2 = " ".join(term2_words).strip()
                    
                    return [term1, term2]
        
        # Fallback: look for common comparison terms
        common_comparisons = [
            ["online", "offline"], ["digital", "physical"], ["premium", "budget"],
            ["young", "old"], ["male", "female"], ["urban", "rural"]
        ]
        
        question_lower = question.lower()
        for comparison in common_comparisons:
            if all(term in question_lower for term in comparison):
                return comparison
        
        return []
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history for context"""
        return [
            {
                "question": question,
                "answer": data["answer"]["answer"] if isinstance(data["answer"], dict) else str(data["answer"]),
                "category": data["category"],
                "timestamp": data["timestamp"]
            }
            for question, data in self.context_memory.items()
        ]
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.context_memory = {}
    
    def suggest_follow_up_questions(self, last_answer: Dict[str, Any]) -> List[str]:
        """Suggest relevant follow-up questions based on the last answer"""
        
        source_type = last_answer.get("source_type", "general")
        
        suggestions = {
            "participant_specific": [
                "How did other participants react to this viewpoint?",
                "What personality type was this participant?",
                "Did this participant influence others in the discussion?"
            ],
            "thematic_analysis": [
                "Which theme generated the most discussion?",
                "How did themes evolve throughout the discussion?",
                "What themes were unique to specific participant types?"
            ],
            "behavioral_analysis": [
                "What specific barriers were mentioned most frequently?",
                "How do these behaviors vary by demographic?",
                "What would change these behavioral patterns?"
            ],
            "sentiment_analysis": [
                "What caused the most positive reactions?",
                "Which participants had the strongest negative sentiment?",
                "How did sentiment change throughout the discussion?"
            ]
        }
        
        return suggestions.get(source_type, [
            "What were the most surprising insights from this discussion?",
            "How do these findings compare to industry standards?",
            "What should be the next steps based on these insights?"
        ])