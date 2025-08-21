"""
Persona Generator Agent
Automatically generates TinyPersons based on user context prompts
"""

import json
import random
from typing import Dict, List, Any
from datetime import datetime
from core.llm_client import LLMClient

class PersonaGeneratorAgent:
    """Agent responsible for generating diverse, realistic personas"""
    
    def __init__(self):
        self.persona_templates = self._load_persona_templates()
        self._llm = LLMClient()
    
    def _load_persona_templates(self) -> Dict[str, Any]:
        """Load persona generation templates"""
        return {
            "age_ranges": {
                "gen_z": [18, 19, 20, 21, 22, 23, 24, 25],
                "millennial": [26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
                "gen_x": [36, 37, 38, 39, 40, 41, 42, 43, 44, 45]
            },
            "occupations": {
                "student": ["College Student", "University Student", "Graduate Student", "MBA Student"],
                "tech": ["Software Developer", "Data Analyst", "UX Designer", "Product Manager"],
                "creative": ["Graphic Designer", "Content Creator", "Marketing Executive", "Social Media Manager"],
                "traditional": ["Teacher", "Nurse", "Accountant", "HR Executive", "Sales Executive"],
                "service": ["Retail Associate", "Customer Service Rep", "Restaurant Manager", "Freelancer"]
            },
            "locations": {
                "metro": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad"],
                "tier2": ["Pune", "Jaipur", "Ahmedabad", "Kochi", "Indore", "Bhopal"],
                "tier3": ["Nagpur", "Vadodara", "Coimbatore", "Madurai", "Chandigarh"]
            },
            "personality_traits": {
                "enthusiastic": ["energetic", "talkative", "optimistic", "social", "expressive"],
                "analytical": ["logical", "questioning", "detail-oriented", "practical", "skeptical"],
                "trendy": ["fashion-forward", "social-media-savvy", "influencer-following", "brand-conscious"],
                "cautious": ["risk-averse", "traditional", "careful", "budget-conscious", "research-oriented"],
                "expert": ["knowledgeable", "experienced", "confident", "industry-insider", "influential"],
                "budget-focused": ["price-sensitive", "deal-hunter", "value-conscious", "comparison-shopper"]
            },
            "income_brackets": {
                "low": {"range": "₹15,000-25,000", "budget": "₹500-1,500"},
                "lower_middle": {"range": "₹25,000-40,000", "budget": "₹1,500-3,000"},
                "middle": {"range": "₹40,000-70,000", "budget": "₹3,000-6,000"},
                "upper_middle": {"range": "₹70,000-1,50,000", "budget": "₹6,000-15,000"},
                "high": {"range": "₹1,50,000+", "budget": "₹15,000+"}
            }
        }
    
    async def generate_personas(self, context_prompt: str, discussion_topic: str, num_personas: int = 6) -> List[Dict[str, Any]]:
        """Generate diverse personas based on context prompt"""
        
        # Try LLM-first approach for dynamic, topic-aware personas
        if self._llm.enabled:
            system_prompt = (
                "You are generating realistic participant personas for a focus group. "
                "Return a JSON array of personas with keys: name, age, occupation, location, "
                "income_range, monthly_budget, personality_type, traits (string[]), background."
            )
            user_prompt = (
                f"Context prompt: {context_prompt}\n"
                f"Topic: {discussion_topic}\n"
                f"Count: {num_personas}\n"
                "Ensure diversity in age, occupation, location, income and personality_type."
            )
            try:
                data = self._llm.generate_json_sync(system_prompt, user_prompt, schema_hint="Persona[]")
                if isinstance(data, list) and data:
                    # Basic normalization and timestamps
                    normalized: List[Dict[str, Any]] = []
                    used_names = set()
                    for p in data:
                        if not isinstance(p, dict):
                            continue
                        name = p.get("name") or f"Person_{len(normalized)+1}"
                        if name in used_names:
                            name = f"{name}_{len(normalized)+1}"
                        used_names.add(name)
                        p["name"] = name
                        p.setdefault("created_at", datetime.now().isoformat())
                        normalized.append(p)
                    if normalized:
                        return normalized[:num_personas]
            except Exception:
                pass
        
        # Fallback to template-driven generation
        context_analysis = self._analyze_context(context_prompt, discussion_topic)
        personas: List[Dict[str, Any]] = []
        used_names = set()
        for i in range(num_personas):
            persona = self._create_individual_persona(context_analysis, used_names)
            personas.append(persona)
            used_names.add(persona["name"])
        return personas
    
    def _analyze_context(self, context_prompt: str, discussion_topic: str) -> Dict[str, Any]:
        """Analyze context prompt to extract requirements"""
        context_lower = context_prompt.lower()
        topic_lower = discussion_topic.lower()
        
        analysis = {
            "target_demographic": "gen_z",  # default
            "focus_areas": [],
            "required_traits": [],
            "income_diversity": True,
            "geographic_diversity": True,
            "topic_relevance": []
        }
        
        # Demographic detection
        if any(term in context_lower for term in ["gen z", "generation z", "young adult", "18-25"]):
            analysis["target_demographic"] = "gen_z"
        elif any(term in context_lower for term in ["millennial", "25-35", "young professional"]):
            analysis["target_demographic"] = "millennial"
        elif any(term in context_lower for term in ["gen x", "35-45", "experienced"]):
            analysis["target_demographic"] = "gen_x"
        
        # Topic-specific traits
        if any(term in topic_lower for term in ["beauty", "cosmetics", "skincare", "makeup"]):
            analysis["topic_relevance"].extend(["beauty-conscious", "skincare-focused", "brand-aware"])
        elif any(term in topic_lower for term in ["tech", "technology", "app", "software"]):
            analysis["topic_relevance"].extend(["tech-savvy", "early-adopter", "digital-native"])
        elif any(term in topic_lower for term in ["food", "restaurant", "dining"]):
            analysis["topic_relevance"].extend(["foodie", "dining-enthusiast", "taste-conscious"])
        
        # Extract specific requirements from context
        if "budget" in context_lower or "price" in context_lower:
            analysis["focus_areas"].append("budget_sensitivity")
        if "premium" in context_lower or "luxury" in context_lower:
            analysis["focus_areas"].append("premium_segment")
        if "online" in context_lower or "digital" in context_lower:
            analysis["focus_areas"].append("digital_behavior")
        
        return analysis
    
    def _create_individual_persona(self, context_analysis: Dict[str, Any], used_names: set) -> Dict[str, Any]:
        """Create a single realistic persona"""
        
        # Generate unique name
        indian_names = [
            "Aditi", "Rahul", "Priya", "Arjun", "Sneha", "Vikram", "Meera", "Rohan",
            "Zoya", "Karan", "Neha", "Aarav", "Kavya", "Ishaan", "Riya", "Aryan",
            "Ananya", "Sidharth", "Pooja", "Harsh", "Tara", "Dev", "Naina", "Yash"
        ]
        
        available_names = [name for name in indian_names if name not in used_names]
        if not available_names:
            available_names = [f"Person_{len(used_names) + 1}"]
        
        name = random.choice(available_names)
        
        # Determine age based on demographic
        age_range = self.persona_templates["age_ranges"][context_analysis["target_demographic"]]
        age = random.choice(age_range)
        
        # Select occupation
        occupation_categories = list(self.persona_templates["occupations"].keys())
        category = random.choice(occupation_categories)
        occupation = random.choice(self.persona_templates["occupations"][category])
        
        # Select location
        location_tiers = list(self.persona_templates["locations"].keys())
        tier = random.choice(location_tiers)
        location = random.choice(self.persona_templates["locations"][tier])
        
        # Determine income bracket
        income_brackets = list(self.persona_templates["income_brackets"].keys())
        income_bracket = random.choice(income_brackets)
        income_info = self.persona_templates["income_brackets"][income_bracket]
        
        # Select personality traits
        trait_categories = list(self.persona_templates["personality_traits"].keys())
        primary_trait = random.choice(trait_categories)
        traits = self.persona_templates["personality_traits"][primary_trait]
        
        # Generate detailed background
        background = self._generate_detailed_background(
            name, age, occupation, location, income_info, traits, primary_trait, context_analysis
        )
        
        persona = {
            "name": name,
            "age": age,
            "occupation": occupation,
            "location": location,
            "income_range": income_info["range"],
            "monthly_budget": income_info["budget"],
            "personality_type": primary_trait,
            "traits": traits,
            "background": background,
            "created_at": datetime.now().isoformat()
        }
        
        return persona
    
    def _generate_detailed_background(self, name: str, age: int, occupation: str, location: str, 
                                    income_info: Dict[str, str], traits: List[str], 
                                    personality_type: str, context_analysis: Dict[str, Any]) -> str:
        """Generate detailed, realistic background for persona"""
        
        # Base background template
        background_parts = [
            f"You are {name}, a {age}-year-old {occupation} from {location}."
        ]
        
        # Add income and budget details
        background_parts.append(
            f"Your monthly income is in the {income_info['range']} range, "
            f"and you typically budget {income_info['budget']} for the discussion topic."
        )
        
        # Add personality-specific details
        if personality_type == "enthusiastic":
            background_parts.append(
                "You are highly enthusiastic and love sharing your experiences. "
                "You often interrupt with excitement, use phrases like 'OMG same!' and "
                "share very specific details about your purchases and experiences."
            )
        elif personality_type == "analytical":
            background_parts.append(
                "You approach everything logically and always question prices and value. "
                "You ask practical questions like 'Why would anyone pay that much?' and "
                "often pause conversations to understand the reasoning behind decisions."
            )
        elif personality_type == "trendy":
            background_parts.append(
                "You are highly trend-conscious and follow influencers religiously. "
                "You speak fast, use current slang, and constantly reference what's trending. "
                "You get animated when discussing new trends and often finish others' sentences."
            )
        elif personality_type == "cautious":
            background_parts.append(
                "You are risk-averse and prefer traditional, tested options. "
                "You speak softly, often start with 'Sorry to interrupt, but...' and "
                "share detailed cautionary tales about bad experiences you've had."
            )
        elif personality_type == "expert":
            background_parts.append(
                "You have insider knowledge and extensive experience in this area. "
                "You speak confidently, often educate others, and casually drop "
                "industry insights and behind-the-scenes information."
            )
        elif personality_type == "budget-focused":
            background_parts.append(
                "You are extremely budget-conscious and track every expense. "
                "You interrupt with specific price comparisons, mention exact discounts you found, "
                "and always calculate cost-per-use for purchases."
            )
        
        # Add topic-specific context
        topic_context = self._get_topic_specific_context(context_analysis, personality_type)
        if topic_context:
            background_parts.append(topic_context)
        
        # Add realistic behavioral details
        behavioral_details = self._get_behavioral_details(personality_type, age, location)
        background_parts.append(behavioral_details)
        
        return " ".join(background_parts)
    
    def _get_topic_specific_context(self, context_analysis: Dict[str, Any], personality_type: str) -> str:
        """Get topic-specific background context"""
        
        topic_relevance = context_analysis.get("topic_relevance", [])
        
        if "beauty-conscious" in topic_relevance:
            if personality_type == "enthusiastic":
                return "You love trying new beauty products and follow Korean skincare trends religiously."
            elif personality_type == "budget-focused":
                return "You research ingredients extensively and always look for dupes of expensive products."
            elif personality_type == "trendy":
                return "You follow beauty influencers and always know about the latest launches and trends."
            elif personality_type == "cautious":
                return "You prefer buying from physical stores where you can test products first."
        
        elif "tech-savvy" in topic_relevance:
            if personality_type == "expert":
                return "You work in tech and understand the technical aspects of digital products."
            elif personality_type == "analytical":
                return "You evaluate tech products based on specifications and practical utility."
        
        return ""
    
    def _get_behavioral_details(self, personality_type: str, age: int, location: str) -> str:
        """Get realistic behavioral and lifestyle details"""
        
        details = []
        
        # Age-based details
        if age <= 23:
            details.append("You live in a PG or shared accommodation.")
        elif age <= 28:
            details.append("You're establishing your career and managing student loans.")
        else:
            details.append("You have more disposable income and established preferences.")
        
        # Location-based shopping behavior
        if location in ["Mumbai", "Delhi", "Bangalore"]:
            details.append("You shop online frequently and have access to premium brands.")
        else:
            details.append("You rely more on local stores and are selective about online purchases.")
        
        # Personality-based shopping patterns
        if personality_type == "trendy":
            details.append("You make impulse purchases based on social media recommendations.")
        elif personality_type == "budget-focused":
            details.append("You maintain detailed expense tracking and wait for sales.")
        elif personality_type == "cautious":
            details.append("You read reviews extensively and prefer established brands.")
        
        return " ".join(details)
    
    def validate_personas(self, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate generated personas for diversity and completeness"""
        
        validation = {
            "total_personas": len(personas),
            "age_diversity": len(set(p["age"] for p in personas)),
            "occupation_diversity": len(set(p["occupation"] for p in personas)),
            "personality_diversity": len(set(p["personality_type"] for p in personas)),
            "location_diversity": len(set(p["location"] for p in personas)),
            "income_diversity": len(set(p["income_range"] for p in personas)),
            "issues": []
        }
        
        # Check for sufficient diversity
        if validation["personality_diversity"] < 4:
            validation["issues"].append("Insufficient personality diversity")
        
        if validation["income_diversity"] < 3:
            validation["issues"].append("Insufficient income diversity")
        
        # Check for name uniqueness
        names = [p["name"] for p in personas]
        if len(names) != len(set(names)):
            validation["issues"].append("Duplicate names found")
        
        validation["is_valid"] = len(validation["issues"]) == 0
        
        return validation