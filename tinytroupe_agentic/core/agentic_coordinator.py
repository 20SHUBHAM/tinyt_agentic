import json
from typing import Any, Dict, List, Optional

from core.llm_client import LLMClient


class AgenticCoordinator:
    """LLM-driven coordinator that proposes the next action in a discussion.

    It examines the topic, optional plan, personas, and recent transcript to decide the
    next event (ask_question, participant_turn, interrupt, wrap_up, end), returning a
    structured JSON directive that the moderator can execute.
    """

    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self._llm = llm or LLMClient()

    def propose_next_action(
        self,
        *,
        topic: str,
        personas: List[Dict[str, Any]],
        recent_transcript: List[Dict[str, Any]],
        plan_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a JSON directive for the next action.

        The response schema (example):
        {
          "action": "ask_question" | "participant_turn" | "interrupt" | "wrap_up" | "end",
          "moderator_question": "...",  # when action == ask_question
          "speaker": "ParticipantName",  # when action in {participant_turn, interrupt}
          "notes": "short rationale",
          "reason": "why this step follows",
        }
        """

        system_prompt = (
            "You are a senior discussion coordinator. Decide the next step of a focus group. "
            "Keep a balanced pacing: questions, responses, occasional interrupts, and follow-ups. "
            "Return a STRICT JSON object with keys: action, moderator_question (optional), speaker (optional), notes, reason."
        )

        participants_brief = [
            {
                "name": p.get("name"),
                "age": p.get("age"),
                "occupation": p.get("occupation"),
                "personality_type": p.get("personality_type"),
                "monthly_budget": p.get("monthly_budget"),
            }
            for p in personas
        ]

        recent_lines = [
            f"[{e.get('type','')}|{e.get('speaker','')}] {e.get('content','')}" for e in recent_transcript[-12:]
        ]

        plan_section = f"Plan (optional):\n{plan_text}\n\n" if plan_text else ""

        user_prompt = (
            f"Topic: {topic}\n\n"
            f"Participants (brief JSON): {json.dumps(participants_brief)[:3000]}\n\n"
            f"{plan_section}"
            f"Recent transcript (truncated):\n" + "\n".join(recent_lines) + "\n\n"
            "Choose next action among: ask_question, participant_turn, interrupt, wrap_up, end.\n"
            "- ask_question: Provide 'moderator_question'\n"
            "- participant_turn: Provide 'speaker'\n"
            "- interrupt: Provide 'speaker' who reacts briefly\n"
            "- wrap_up: brief moderator closing\n"
            "- end: finish the session\n"
        )

        result = self._llm.generate_json_sync(system_prompt, user_prompt, schema_hint="{action: string}")
        if not isinstance(result, dict):  # minimal guard
            return {"action": "wrap_up", "notes": "fallback", "reason": "invalid response"}
        return result

