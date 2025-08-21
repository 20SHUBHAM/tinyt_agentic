"""
Discussion Framework Agent
Generates, refines, and validates comprehensive focus group discussion frameworks.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from core.llm_client import LLMClient
from core.config import llm_only


class DiscussionFrameworkAgent:
    def __init__(self) -> None:
        self._llm = LLMClient()

    def generate_framework(
        self,
        *,
        topic_brief: str,
        business_context: Optional[str] = None,
        research_goals: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self._llm.enabled:
            system = (
                "You are a research strategist. Create a comprehensive focus group framework. "
                "Return STRICT JSON with keys: research_objectives (string[]), discussion_phases ({name, objective, questions[]}[]), "
                "key_questions (string[]), participant_criteria ({demographics: string[], behaviors: string[], experiences: string[]}), "
                "business_context (string), expected_insights (string[]), success_metrics (string[])."
            )
            user = (
                f"Topic brief: {topic_brief}\n"
                f"Business context (optional): {business_context or ''}\n"
                f"Research goals (optional): {research_goals or ''}\n"
                "Constraints: 3-5 objectives, 4-6 phases (each with 2-3 questions), 8-12 key questions total."
            )
            try:
                data = self._llm.generate_json_sync(system, user, schema_hint="framework object")
                data["generated_at"] = datetime.now().isoformat()
                return data
            except Exception:
                if llm_only():
                    raise
        # Fallback heuristic framework
        if llm_only():
            raise RuntimeError("LLM_ONLY enabled but framework generation failed.")
        return {
            "research_objectives": [
                "Understand current behaviors and decision drivers",
                "Identify pain points and unmet needs",
                "Evaluate trust and credibility factors",
            ],
            "discussion_phases": [
                {"name": "Opening & Context", "objective": "Warm-up and establish context", "questions": [
                    "Please introduce yourself and your relationship with the topic.",
                    "What comes to mind first when you think about this topic?"
                ]},
                {"name": "Experiences", "objective": "Recent experiences and workflows", "questions": [
                    "Walk me through your most recent relevant experience.",
                    "What worked well and what didn't?"
                ]},
                {"name": "Deep Dive", "objective": "Pain points and trade-offs", "questions": [
                    "What are the biggest challenges you face?",
                    "How do you weigh price, quality, and convenience?"
                ]},
                {"name": "Wrap-up", "objective": "Synthesis and next steps", "questions": [
                    "What advice would you give others considering this?",
                    "What change would have the biggest impact?"
                ]},
            ],
            "key_questions": [
                "What drives your decisions?",
                "Where do you find trustworthy information?",
                "What trade-offs do you commonly make?",
            ],
            "participant_criteria": {
                "demographics": ["18-45", "Urban/Semi-urban"],
                "behaviors": ["Recent relevant purchase/usage", "Online research"],
                "experiences": ["At least one recent journey in last 60 days"],
            },
            "business_context": business_context or topic_brief,
            "expected_insights": ["Decision drivers", "Barriers", "Trust signals"],
            "success_metrics": ["Rich stories", "Clear themes", "Actionable opportunities"],
            "generated_at": datetime.now().isoformat(),
        }

    def refine_framework(self, framework: Dict[str, Any], edit_instructions: str) -> Dict[str, Any]:
        if self._llm.enabled:
            system = (
                "Refine the given framework JSON according to the instructions. "
                "Return STRICT JSON preserving the original schema keys."
            )
            user = (
                f"Framework JSON:\n{framework}\n\n"
                f"Instructions:\n{edit_instructions}"
            )
            try:
                data = self._llm.generate_json_sync(system, user, schema_hint="framework object")
                data["refined_at"] = datetime.now().isoformat()
                return data
            except Exception:
                if llm_only():
                    raise
        # Non-LLM fallback: attach note
        framework["refined_at"] = datetime.now().isoformat()
        framework.setdefault("notes", []).append(f"Manual refinement requested: {edit_instructions}")
        return framework

    def validate_framework(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        if self._llm.enabled:
            system = (
                "Evaluate the quality of a focus group framework. Return STRICT JSON with: "
                "score (0-100), strengths (string[]), risks (string[]), recommendations (string[])."
            )
            user = f"Framework JSON to evaluate:\n{framework}"
            try:
                return self._llm.generate_json_sync(system, user, schema_hint="{score:number}")
            except Exception:
                if llm_only():
                    raise
        # Heuristic validation
        score = 70
        strengths = ["Clear phases", "Action-oriented questions"]
        risks = ["Might need more participant diversity"]
        recommendations = ["Add success metrics tied to business goals"]
        return {"score": score, "strengths": strengths, "risks": risks, "recommendations": recommendations}

