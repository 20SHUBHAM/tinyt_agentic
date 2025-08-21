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

class TinyPerson:
    """Simplified TinyPerson implementation for the agentic system"""
    
    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        self.conversation_history = []
    
    def define(self, key: str, value: Any):
        """Define an attribute for this person"""
        self.attributes[key] = value
    
    def listen(self, message: str):
        """Listen to a message/prompt"""
        self.conversation_history.append({"type": "listen", "content": message, "timestamp": datetime.now().isoformat()})
    
    def act(self) -> str:
        """Generate a response based on personality and context"""
        # This would integrate with your AI model (OpenAI, etc.)
        # For now, returning a realistic simulation
        
        if not self.conversation_history:
            return f"Hi, I'm {self.name}!"
        
        last_prompt = self.conversation_history[-1]["content"]
        
        # Generate contextual response based on persona attributes
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
    """Simplified TinyWorld implementation"""
    
    def __init__(self, name: str, agents: List[TinyPerson]):
        self.name = name
        self.agents = agents
        self.conversation_log = []
    
    def run_conversation(self, topic: str, questions: List[str]) -> List[Dict[str, Any]]:
        """Run a conversation between agents"""
        conversation = []
        
        for question in questions:
            conversation.append({
                "type": "moderator",
                "speaker": "Moderator",
                "content": question,
                "timestamp": datetime.now().isoformat()
            })
            
            # Each agent responds
            for agent in self.agents:
                agent.listen(f"Question: {question}")
                response = agent.act()
                
                conversation.append({
                    "type": "participant",
                    "speaker": agent.name,
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Add some realistic delays
                time.sleep(0.1)
        
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
    
    def checkpoint(self):
        """Create a checkpoint"""
        pass
    
    def end(self):
        """End the session"""
        self.session_active = False

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