"""
Discussion Moderator Agent
Automatically conducts focus group discussions with generated personas
"""

import random
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.tinytroupe_integration import TinyTroupeManager, TinyPerson
from core.llm_client import LLMClient
from core.config import llm_only
from core.agentic_coordinator import AgenticCoordinator

class DiscussionModeratorAgent:
    """Agent that moderates focus group discussions"""
    
    def __init__(self):
        self.discussion_templates = self._load_discussion_templates()
        self.moderator_persona = self._create_moderator_persona()
        self._llm = LLMClient()
        self._coordinator = AgenticCoordinator(self._llm)
    
    def _load_discussion_templates(self) -> Dict[str, Any]:
        """Load discussion flow templates"""
        return {
            "opening_questions": [
                "Let's start by getting to know each other. Please introduce yourself and share what initially drew you to this topic.",
                "Before we dive deep, I'd love to hear about your current relationship with {topic}. What's your experience been like?",
                "To break the ice, could you each share one word that comes to mind when you think about {topic}?"
            ],
            "exploration_questions": [
                "Tell me about your most recent experience with {topic}. Walk me through it from start to finish.",
                "What influences your decisions when it comes to {topic}? I'd love to hear different perspectives.",
                "Let's talk about challenges. What frustrates you most about {topic}?",
                "How do you typically research or learn about {topic}? What sources do you trust?"
            ],
            "deep_dive_questions": [
                "I'm hearing some interesting viewpoints. Let's explore the money aspect - how do budget considerations affect your choices?",
                "What would make you completely change your current approach to {topic}?",
                "If you had to convince a friend about {topic}, what would be your main arguments?",
                "What's one thing about {topic} that you wish more people understood?"
            ],
            "comparison_questions": [
                "I'm noticing some different approaches here. Let's compare - online vs offline experiences with {topic}.",
                "How important is brand reputation vs price when it comes to {topic}?",
                "What role do recommendations from friends vs influencers vs experts play in your decisions?",
                "Traditional vs modern approaches to {topic} - where do you stand?"
            ],
            "future_focused_questions": [
                "Looking ahead, how do you see your relationship with {topic} evolving?",
                "What innovations or changes would excite you most in the {topic} space?",
                "If you could design the perfect {topic} experience, what would it look like?",
                "What advice would you give to someone just starting with {topic}?"
            ],
            "wrap_up_questions": [
                "Before we conclude, what's the most important insight you're taking away from today's discussion?",
                "Is there anything about {topic} that we haven't discussed that you feel is important?",
                "Any final thoughts or questions for the group?"
            ]
        }
    
    def _create_moderator_persona(self) -> Dict[str, str]:
        """Create experienced moderator persona"""
        return {
            "name": "Kavya Sharma",
            "role": "Senior Market Research Moderator",
            "experience": "12+ years moderating focus groups across India",
            "style": "Warm, encouraging, skilled at managing group dynamics",
            "phrases": [
                "That's fascinating, tell me more about that.",
                "I'm seeing some head nods - what do others think?",
                "Let's pause there and hear from someone who hasn't spoken yet.",
                "I notice some different reactions - let's explore that.",
                "Before we move on, does anyone want to build on what was shared?"
            ]
        }
    
    async def conduct_discussion(self, personas: List[Dict[str, Any]], topic: str, 
                               tinytroupe_manager: TinyTroupeManager, plan_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """Conduct a complete focus group discussion"""
        
        # Initialize session
        session_id = f"discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tinytroupe_manager.start_session(session_id)
        
        try:
            # Create TinyPerson objects
            tiny_personas = tinytroupe_manager.create_personas(personas)
            
            # Create discussion world
            world = tinytroupe_manager.create_world("Focus Group Discussion", tiny_personas)
            
            # Generate discussion flow
            if plan_text and self._llm.enabled:
                # Ask LLM to translate plan text to phases/questions
                from core.llm_client import LLMClient
                llm = self._llm
                system_prompt = (
                    "You are a focus group moderator. Convert the following plan into a JSON object "
                    "with keys (phase slugs) -> list of 2-4 open-ended questions."
                )
                user_prompt = f"Plan:\n{plan_text}\n\nTopic: {topic}"
                try:
                    flow_json = llm.generate_json_sync(system_prompt, user_prompt, schema_hint="{phase: string[]}")
                    if isinstance(flow_json, dict) and flow_json:
                        discussion_flow = {}
                        for phase, qs in flow_json.items():
                            if isinstance(qs, list):
                                discussion_flow[phase] = [str(q).replace("{topic}", topic) for q in qs if isinstance(q, (str,))]
                    else:
                        discussion_flow = self._generate_discussion_flow(topic)
                except Exception:
                    if llm_only():
                        raise
                    discussion_flow = self._generate_discussion_flow(topic)
            else:
                if llm_only():
                    # Generate from topic directly via LLM when no plan provided
                    try:
                        system_prompt = (
                            "Generate discussion phases for the topic with 3-4 open questions per phase as JSON."
                        )
                        user_prompt = f"Topic: {topic}"
                        flow_json = self._llm.generate_json_sync(system_prompt, user_prompt, schema_hint="{phase: string[]}")
                        if isinstance(flow_json, dict) and flow_json:
                            discussion_flow = {}
                            for phase, qs in flow_json.items():
                                if isinstance(qs, list):
                                    discussion_flow[phase] = [str(q) for q in qs if isinstance(q, (str,))]
                        else:
                            raise RuntimeError("Invalid LLM flow JSON")
                    except Exception:
                        raise
                else:
                    discussion_flow = self._generate_discussion_flow(topic)
            
            # Conduct discussion
            full_transcript = []
            
            # Add opening context
            full_transcript.append({
                "type": "setup",
                "speaker": "System",
                "content": f"Focus Group Discussion: {topic}",
                "timestamp": datetime.now().isoformat(),
                "participants": [p["name"] for p in personas]
            })
            
            # Pre-discussion setup
            pre_discussion = self._create_pre_discussion_moments(tiny_personas)
            full_transcript.extend(pre_discussion)
            
            # If LLM-only or coordinator available, run agentic loop; else use static phases
            if self._llm.enabled:
                full_transcript.extend(
                    await self._run_agentic_loop(topic, tiny_personas, plan_text)
                )
            else:
                for phase_name, questions in discussion_flow.items():
                    phase_transcript = await self._conduct_discussion_phase(
                        phase_name, questions, tiny_personas, topic
                    )
                    full_transcript.extend(phase_transcript)
                    transition = self._create_phase_transition(phase_name)
                    if transition:
                        full_transcript.append(transition)
            
            # Post-discussion wrap-up
            wrap_up = self._create_post_discussion_moments(tiny_personas)
            full_transcript.extend(wrap_up)
            
            return full_transcript
            
        finally:
            tinytroupe_manager.end_session()

    async def _run_agentic_loop(self, topic: str, personas: List[TinyPerson], plan_text: Optional[str]) -> List[Dict[str, Any]]:
        transcript: List[Dict[str, Any]] = []
        max_turns = 30
        turn = 0
        # initial opening by moderator
        transcript.append({
            "type": "phase_start",
            "speaker": "Moderator",
            "content": f"Let's begin our discussion about {topic}.",
            "timestamp": datetime.now().isoformat(),
            "phase": "agentic_flow"
        })
        while turn < max_turns:
            turn += 1
            directive = self._coordinator.propose_next_action(
                topic=topic,
                personas=[p.attributes | {"name": p.name} for p in personas],
                recent_transcript=transcript,
                plan_text=plan_text,
            )
            action = (directive.get("action") or "").lower()
            if action == "end":
                break
            if action == "wrap_up":
                transcript.append({
                    "type": "wrap_up",
                    "speaker": "Moderator",
                    "content": "Thank you all for the insightful discussion.",
                    "timestamp": datetime.now().isoformat()
                })
                break
            if action == "ask_question":
                q = directive.get("moderator_question") or f"Could you share more about {topic}?"
                transcript.append({
                    "type": "question",
                    "speaker": "Moderator",
                    "content": q,
                    "timestamp": datetime.now().isoformat(),
                    "phase": "agentic_flow"
                })
                # let all personas respond quickly
                responses = await self._get_participant_responses(q, personas, topic)
                transcript.extend(responses)
                continue
            if action in {"participant_turn", "interrupt"}:
                name = directive.get("speaker")
                target = next((p for p in personas if p.name == name), None)
                if not target:
                    target = personas[0]
                prompt = f"Please share your thoughts about {topic}."
                target.listen(prompt)
                content = target.act()
                transcript.append({
                    "type": "response" if action == "participant_turn" else "interaction",
                    "speaker": target.name,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                continue
            # default: ask a generic question
            transcript.append({
                "type": "question",
                "speaker": "Moderator",
                "content": f"What stands out to you regarding {topic}?",
                "timestamp": datetime.now().isoformat(),
                "phase": "agentic_flow"
            })
            responses = await self._get_participant_responses(f"Regarding {topic}", personas, topic)
            transcript.extend(responses)
        return transcript
    
    def _generate_discussion_flow(self, topic: str) -> Dict[str, List[str]]:
        """Generate discussion flow dynamically via LLM, with template fallback."""

        if self._llm.enabled:
            system_prompt = (
                "You are an expert focus group moderator. Given a topic, generate a structured "
                "set of phases with 3-4 open-ended, non-leading questions per phase."
            )
            user_prompt = (
                f"Topic: {topic}\n"
                "Phases: opening_questions, exploration_questions, deep_dive_questions, comparison_questions, future_focused_questions, wrap_up_questions.\n"
                "Return JSON with those exact keys and list of strings as values."
            )
            try:
                flow = self._llm.generate_json_sync(system_prompt, user_prompt, schema_hint="{phase: string[]}")
                # Validate basic structure
                if isinstance(flow, dict) and any(isinstance(v, list) for v in flow.values()):
                    # Ensure formatting for {topic}
                    normalized: Dict[str, List[str]] = {}
                    for phase, questions in flow.items():
                        if not isinstance(questions, list):
                            continue
                        customized_questions: List[str] = []
                        for q in questions:
                            if isinstance(q, str):
                                customized_questions.append(q.replace("{topic}", topic))
                        if customized_questions:
                            normalized[phase] = customized_questions
                    if normalized:
                        return normalized
            except Exception:
                pass

        # Fallback to templated questions
        flow: Dict[str, List[str]] = {}
        for phase, question_templates in self.discussion_templates.items():
            customized_questions = []
            for template in question_templates:
                if "{topic}" in template:
                    customized_questions.append(template.format(topic=topic))
                else:
                    customized_questions.append(template)
            flow[phase] = customized_questions
        return flow
    
    def _create_pre_discussion_moments(self, personas: List[TinyPerson]) -> List[Dict[str, Any]]:
        """Create realistic pre-discussion setup moments"""
        
        moments = []
        
        moments.append({
            "type": "setup",
            "speaker": "Moderator",
            "content": "Welcome everyone! Please make yourselves comfortable. We'll begin in just a moment.",
            "timestamp": datetime.now().isoformat()
        })
        
        # Natural pre-discussion chatter
        casual_moments = [
            f"{personas[0].name}: This room is quite nice! I've never done a focus group before.",
            f"{personas[1].name}: Same here! Are we being recorded?",
            f"{personas[2].name}: I brought some notes just in case.",
            "Moderator: Perfect! I love seeing preparation. Let's officially begin."
        ]
        
        for moment in casual_moments:
            speaker, content = moment.split(": ", 1)
            moments.append({
                "type": "casual",
                "speaker": speaker,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
        return moments
    
    async def _conduct_discussion_phase(self, phase_name: str, questions: List[str], 
                                      personas: List[TinyPerson], topic: str) -> List[Dict[str, Any]]:
        """Conduct a single discussion phase"""
        
        phase_transcript = []
        
        # Phase introduction
        phase_transcript.append({
            "type": "phase_start",
            "speaker": "Moderator",
            "content": f"Let's move into {phase_name.replace('_', ' ')}.",
            "timestamp": datetime.now().isoformat(),
            "phase": phase_name
        })
        
        for question in questions:
            # Moderator asks question
            phase_transcript.append({
                "type": "question",
                "speaker": "Moderator",
                "content": question,
                "timestamp": datetime.now().isoformat(),
                "phase": phase_name
            })
            
            # Get responses from participants
            responses = await self._get_participant_responses(question, personas, topic)
            phase_transcript.extend(responses)
            
            # Add natural group dynamics
            dynamics = self._create_group_dynamics(personas, question)
            phase_transcript.extend(dynamics)
            
            # Moderator follow-up
            follow_up = self._generate_moderator_follow_up(responses)
            if follow_up:
                phase_transcript.append(follow_up)
        
        return phase_transcript
    
    async def _get_participant_responses(self, question: str, personas: List[TinyPerson], 
                                       topic: str) -> List[Dict[str, Any]]:
        """Get responses from all participants"""
        
        responses = []
        
        # Randomize speaking order for natural flow
        speaking_order = random.sample(personas, len(personas))
        
        for i, persona in enumerate(speaking_order):
            # Create contextual prompt
            prompt = self._create_response_prompt(question, persona, topic, i == 0)
            
            # Get response
            persona.listen(prompt)
            response_content = persona.act()
            
            if response_content:
                responses.append({
                    "type": "response",
                    "speaker": persona.name,
                    "content": response_content,
                    "timestamp": datetime.now().isoformat(),
                    "speaking_order": i + 1,
                    "personality_type": persona.attributes.get("personality_type", "unknown")
                })
                
                # Add realistic pauses
                await asyncio.sleep(0.1)
        
        return responses
    
    def _create_response_prompt(self, question: str, persona: TinyPerson, 
                              topic: str, is_first_speaker: bool) -> str:
        """Create contextual prompt for persona response"""
        
        base_prompt = f"""
        The moderator just asked: "{question}"
        
        As {persona.name}, respond naturally based on your personality and background.
        Topic: {topic}
        
        Your response should:
        - Be authentic to your personality type: {persona.attributes.get('personality_type', 'balanced')}
        - Include specific details about your experiences
        - Mention realistic prices, brands, or locations when relevant
        - Show your budget constraints: {persona.attributes.get('monthly_budget', 'moderate budget')}
        - Reflect your age ({persona.attributes.get('age', 25)}) and occupation ({persona.attributes.get('occupation', 'professional')})
        """
        
        if is_first_speaker:
            base_prompt += "\nYou're speaking first, so set the tone for the discussion."
        else:
            base_prompt += "\nBuild on what others have shared or offer a different perspective."
        
        return base_prompt
    
    def _create_group_dynamics(self, personas: List[TinyPerson], question: str) -> List[Dict[str, Any]]:
        """Create natural group interaction moments"""
        
        dynamics = []
        
        # Random chance of spontaneous interactions
        if random.random() > 0.6:  # 40% chance
            # Select two personas for interaction
            interacting_personas = random.sample(personas, 2)
            
            interaction_types = [
                "agreement", "disagreement", "curiosity", "clarification"
            ]
            
            interaction_type = random.choice(interaction_types)
            
            if interaction_type == "agreement":
                content = f"Yes, exactly! I completely agree with {interacting_personas[1].name}."
            elif interaction_type == "disagreement":
                content = f"I have to respectfully disagree with {interacting_personas[1].name} on this."
            elif interaction_type == "curiosity":
                content = f"That's interesting, {interacting_personas[1].name}. Can you tell me more about that?"
            else:  # clarification
                content = f"Sorry {interacting_personas[1].name}, could you clarify what you meant by that?"
            
            dynamics.append({
                "type": "interaction",
                "speaker": interacting_personas[0].name,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "interaction_type": interaction_type,
                "target": interacting_personas[1].name
            })
        
        return dynamics
    
    def _generate_moderator_follow_up(self, responses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate natural moderator follow-up"""
        
        if not responses or random.random() > 0.7:  # 30% chance
            return None
        
        follow_up_phrases = self.moderator_persona["phrases"]
        selected_phrase = random.choice(follow_up_phrases)
        
        return {
            "type": "moderator_follow_up",
            "speaker": "Moderator",
            "content": selected_phrase,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_phase_transition(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """Create natural transitions between phases"""
        
        transitions = {
            "opening_questions": "Great introductions everyone. Now let's dive deeper.",
            "exploration_questions": "I'm hearing some fascinating experiences. Let's explore this further.",
            "deep_dive_questions": "These insights are really valuable. Let's compare different approaches.",
            "comparison_questions": "Excellent perspectives. Let's think about the future.",
            "future_focused_questions": "Wonderful forward-thinking ideas. Let's start wrapping up."
        }
        
        transition_text = transitions.get(phase_name)
        if transition_text:
            return {
                "type": "transition",
                "speaker": "Moderator",
                "content": transition_text,
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    def _create_post_discussion_moments(self, personas: List[TinyPerson]) -> List[Dict[str, Any]]:
        """Create realistic post-discussion wrap-up"""
        
        moments = []
        
        moments.append({
            "type": "wrap_up",
            "speaker": "Moderator",
            "content": "Thank you all for such an engaging discussion! This has been incredibly insightful.",
            "timestamp": datetime.now().isoformat()
        })
        
        # Natural post-discussion chatter
        if len(personas) >= 2:
            moments.append({
                "type": "casual",
                "speaker": personas[0].name,
                "content": "This was really interesting! I learned a lot from everyone.",
                "timestamp": datetime.now().isoformat()
            })
            
            moments.append({
                "type": "casual",
                "speaker": personas[1].name,
                "content": "Same here! Thanks for sharing your experiences, everyone.",
                "timestamp": datetime.now().isoformat()
            })
        
        moments.append({
            "type": "conclusion",
            "speaker": "System",
            "content": "Focus group discussion completed successfully.",
            "timestamp": datetime.now().isoformat()
        })
        
        return moments