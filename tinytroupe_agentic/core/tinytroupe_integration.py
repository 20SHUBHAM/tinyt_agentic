"""
TinyTroupe Integration Layer
Handles the integration with TinyTroupe for persona creation and discussion execution
"""

import json
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.llm_client import LLMClient

_HAS_TINYTROUPE = False
try:
    import tinytroupe  # type: ignore
    from tinytroupe.agent import TinyPerson as TTinyPerson  # type: ignore
    try:
        from tinytroupe.environment import TinyWorld as TTinyWorld  # type: ignore
    except Exception:  # pragma: no cover
        TTinyWorld = None  # type: ignore
    try:
        from tinytroupe import control as TControl  # type: ignore
    except Exception:  # pragma: no cover
        TControl = None  # type: ignore
    _HAS_TINYTROUPE = True
except Exception:
    _HAS_TINYTROUPE = False

class TinyPerson:
    """Abstraction over participant agent.

    Uses tinytroupe.agent.TinyPerson if available; otherwise a local stub with
    LLM-driven responses.
    """

    def __init__(self, name: str):
        self.name = name
        self.attributes: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self._llm = LLMClient()
        self._impl = TTinyPerson(name) if _HAS_TINYTROUPE else None
    
    def define(self, key: str, value: Any):
        """Define an attribute for this person (and underlying tinytroupe if present)"""
        self.attributes[key] = value
        if self._impl is not None:
            try:
                self._impl.define(key, value)
            except Exception:
                pass
    
    def listen(self, message: str):
        """Listen to a message/prompt"""
        self.conversation_history.append({"type": "listen", "content": message, "timestamp": datetime.now().isoformat()})
        if self._impl is not None:
            try:
                self._impl.listen(message)
            except Exception:
                pass
    
    def act(self) -> str:
        """Generate a response based on personality and context"""
        if self._impl is not None:
            try:
                response = self._impl.act()
                if response:
                    self.conversation_history.append({"type": "act", "content": response, "timestamp": datetime.now().isoformat()})
                    return response
            except Exception:
                pass

        # Local LLM-driven fallback
        if not self.conversation_history:
            return f"Hi, I'm {self.name}!"
        last_prompt = self.conversation_history[-1]["content"]
        if self._llm.enabled:
            system_prompt = (
                "You are a realistic focus group participant. Speak naturally, briefly (2-4 sentences), "
                "and in first person. Stay consistent with the provided persona attributes."
            )
            persona_json = json.dumps(self.attributes, ensure_ascii=False)
            history_snippets = []
            for msg in self.conversation_history[-6:]:
                role = msg.get("type", "listen")
                content = msg.get("content", "")
                history_snippets.append(f"{role}: {content}")
            history_text = "\n".join(history_snippets)
            user_prompt = (
                f"Persona name: {self.name}\n"
                f"Persona attributes (JSON): {persona_json}\n"
                f"Recent history:\n{history_text}\n\n"
                f"Respond to the latest moderator question or group message above."
            )
            try:
                response = self._llm.generate_text_sync(system_prompt, user_prompt, temperature=0.8, max_tokens=180)
                response = (response or "").strip()
                if not response:
                    response = self._generate_response(last_prompt)
            except Exception:
                response = self._generate_response(last_prompt)
        else:
            response = self._generate_response(last_prompt)

        self.conversation_history.append({"type": "act", "content": response, "timestamp": datetime.now().isoformat()})
        return response
    
    def _generate_response(self, prompt: str) -> str:
        """Generate a realistic response based on persona attributes"""
        # This is where you'd integrate with your AI model
        # For demonstration, using template responses based on attributes
        
        age = self.attributes.get("age", 25)
        occupation = self.attributes.get("occupation", "Student")
        background = self.attributes.get("background", "")
        
        # Extract personality traits from background
        if "enthusiastic" in background.lower():
            responses = [
                f"Oh my god, yes! As a {occupation}, I totally relate to this!",
                f"This is so interesting! I've actually experienced something similar...",
                f"Wait, can I share something? This reminds me of when I..."
            ]
        elif "skeptical" in background.lower():
            responses = [
                f"I'm not sure about that. As someone who works in {occupation}, I think...",
                f"That sounds expensive. How much does that actually cost?",
                f"I need to understand the practical side of this..."
            ]
        elif "budget" in background.lower():
            responses = [
                f"That's way over my budget! I usually spend around...",
                f"I track all my expenses, and I found a cheaper alternative...",
                f"Let me calculate the cost per use on that..."
            ]
        else:
            responses = [
                f"Interesting perspective. As a {age}-year-old {occupation}, I think...",
                f"I've had some experience with this topic...",
                f"Let me share my thoughts on this..."
            ]
        
        return random.choice(responses)

class TinyWorld:
    """Abstraction over environment/world. Uses tinytroupe if available."""

    def __init__(self, name: str, agents: List[TinyPerson]):
        self.name = name
        self.agents = agents
        self.conversation_log: List[Dict[str, Any]] = []
        self._impl = None
        if _HAS_TINYTROUPE and 'TTinyWorld' in globals() and TTinyWorld is not None:
            try:
                # Convert to underlying tinytroupe TinyPerson instances
                ttagents = [a._impl if getattr(a, "_impl", None) is not None else a for a in agents]
                self._impl = TTinyWorld(name, ttagents)
            except Exception:
                self._impl = None

    def run_conversation(self, topic: str, questions: List[str]) -> List[Dict[str, Any]]:
        conversation: List[Dict[str, Any]] = []
        # Drive via our question loop to preserve deterministic structure,
        # leveraging tinytroupe persons' listen/act behavior.
        for question in questions:
            conversation.append({
                "type": "moderator",
                "speaker": "Moderator",
                "content": question,
                "timestamp": datetime.now().isoformat()
            })
            for agent in self.agents:
                agent.listen(f"Question: {question}")
                response = agent.act()
                conversation.append({
                    "type": "participant",
                    "speaker": agent.name,
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                time.sleep(0.05)
        self.conversation_log = conversation
        return conversation

class ControlManager:
    """Simplified control manager for session management"""
    
    def __init__(self):
        self.session_active = False
        self.cache_file = None
    
    def begin(self, cache_filename: str):
        """Begin a session"""
        self.session_active = True
        self.cache_file = cache_filename
        if _HAS_TINYTROUPE and 'TControl' in globals() and TControl is not None:
            try:
                TControl.begin(cache_filename)
            except Exception:
                pass
    
    def checkpoint(self):
        """Create a checkpoint"""
        if _HAS_TINYTROUPE and 'TControl' in globals() and TControl is not None:
            try:
                TControl.checkpoint()
            except Exception:
                pass
    
    def end(self):
        """End the session"""
        self.session_active = False
        if _HAS_TINYTROUPE and 'TControl' in globals() and TControl is not None:
            try:
                TControl.end()
            except Exception:
                pass

class TinyTroupeManager:
    """Main manager for TinyTroupe integration"""
    
    def __init__(self):
        self.control = ControlManager()
        self.current_world = None
        self.current_session = None
    
    def create_personas(self, persona_configs: List[Dict[str, Any]]) -> List[TinyPerson]:
        """Create TinyPerson objects from configuration"""
        personas = []
        
        for config in persona_configs:
            person = TinyPerson(config["name"])
            
            # Set attributes
            for key, value in config.items():
                if key != "name":
                    person.define(key, value)
            
            personas.append(person)
        
        return personas
    
    def create_world(self, name: str, personas: List[TinyPerson]) -> TinyWorld:
        """Create a discussion world"""
        self.current_world = TinyWorld(name, personas)
        return self.current_world
    
    def start_session(self, session_id: str):
        """Start a new session"""
        self.current_session = session_id
        cache_filename = f"data/cache/{session_id}.cache.json"
        os.makedirs("data/cache", exist_ok=True)
        self.control.begin(cache_filename)
    
    def end_session(self):
        """End the current session"""
        if self.control.session_active:
            self.control.end()
        self.current_session = None
    
    def conduct_discussion(self, personas: List[TinyPerson], topic: str, questions: List[str]) -> List[Dict[str, Any]]:
        """Conduct a full discussion"""
        if not self.current_world:
            self.current_world = self.create_world("Focus Group", personas)
        
        return self.current_world.run_conversation(topic, questions)