"""
Q&A Assistant Agent
Interactive assistant for answering questions about focus group discussions
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.llm_client import LLMClient
from core.config import llm_only

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
                if llm_only():
                    raise
                pass

        # Fallback to deterministic logic
        if llm_only():
            raise RuntimeError("LLM_ONLY is enabled but Q&A via LLM failed.")
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
    
    # ... existing code ...