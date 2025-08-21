"""
Agentic Focus Group Discussion System
Complete end-to-end automation for TinyTroupe focus group discussions
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
from pydantic import BaseModel
from core.llm_client import LLMClient

# Import our custom agents
from agents.persona_generator import PersonaGeneratorAgent
from agents.discussion_moderator import DiscussionModeratorAgent
from agents.summary_generator import SummaryGeneratorAgent
from agents.qa_assistant import QAAssistantAgent
from core.session_manager import SessionManager
from core.tinytroupe_integration import TinyTroupeManager

app = FastAPI(title="Agentic Focus Group System", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global session manager
session_manager = SessionManager()

class PersonaRequest(BaseModel):
    context_prompt: str
    discussion_topic: str
    session_id: Optional[str] = None

class EditPersonasRequest(BaseModel):
    session_id: str
    personas: List[Dict]
    topic: str

class QARequest(BaseModel):
    session_id: str
    question: str

class PlanRequest(BaseModel):
    topic_brief: str
    business_context: Optional[str] = None
    research_goals: Optional[str] = None

class AcceptPlanRequest(BaseModel):
    session_id: str
    plan_text: Optional[str] = None
    framework: Optional[Dict] = None
    discussion_topic: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-personas")
async def generate_personas(request: PersonaRequest):
    """Step 1: Generate TinyPersons based on context prompt"""
    try:
        # Create or reuse session
        session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize persona generator agent
        persona_agent = PersonaGeneratorAgent()
        
        # Generate personas based on context
        personas = await persona_agent.generate_personas(
            context_prompt=request.context_prompt,
            discussion_topic=request.discussion_topic
        )
        
        # Store or update session data
        session_data = session_manager.get_session(session_id) or {}
        session_data.update({
            "session_id": session_id,
            "context_prompt": request.context_prompt,
            "discussion_topic": request.discussion_topic,
            "personas": personas,
            "updated_at": datetime.now().isoformat(),
            "status": "personas_generated"
        })
        
        if not session_manager.get_session(session_id):
            session_manager.create_session(session_id, session_data)
        else:
            session_manager.update_session(session_id, session_data)
        
        return {
            "success": True,
            "session_id": session_id,
            "personas": personas,
            "context": request.context_prompt,
            "topic": request.discussion_topic
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating personas: {str(e)}")

@app.post("/update-personas")
async def update_personas(request: EditPersonasRequest):
    """Step 2: Allow user to edit personas and topic"""
    try:
        session_data = session_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session with edited personas and topic
        session_data["personas"] = request.personas
        session_data["discussion_topic"] = request.topic
        session_data["status"] = "personas_edited"
        session_data["updated_at"] = datetime.now().isoformat()
        
        session_manager.update_session(request.session_id, session_data)
        
        return {"success": True, "message": "Personas updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating personas: {str(e)}")

@app.post("/start-discussion/{session_id}")
async def start_discussion(session_id: str):
    """Step 3: Start automated discussion"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Initialize discussion moderator
        moderator = DiscussionModeratorAgent()
        tinytroupe_manager = TinyTroupeManager()
        
        # Update session status
        session_data["status"] = "discussion_in_progress"
        session_manager.update_session(session_id, session_data)
        
        # Start discussion in background
        asyncio.create_task(run_discussion(session_id, session_data, moderator, tinytroupe_manager))
        
        return {"success": True, "message": "Discussion started", "session_id": session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting discussion: {str(e)}")

async def run_discussion(session_id: str, session_data: Dict, moderator: DiscussionModeratorAgent, tinytroupe_manager: TinyTroupeManager):
    """Run the complete discussion workflow"""
    try:
        # Execute discussion
        plan_text = session_data.get("discussion_plan")
        discussion_transcript = await moderator.conduct_discussion(
            personas=session_data["personas"],
            topic=session_data["discussion_topic"],
            tinytroupe_manager=tinytroupe_manager,
            plan_text=plan_text
        )
        
        # Update session with transcript
        session_data["discussion_transcript"] = discussion_transcript
        session_data["status"] = "discussion_completed"
        session_data["discussion_completed_at"] = datetime.now().isoformat()
        session_manager.update_session(session_id, session_data)
        
        # Do not auto-generate summary here. Frontend will prompt user
        # for desired summary schema and call the custom summary endpoint.
        
    except Exception as e:
        session_data["status"] = "error"
        session_data["error"] = str(e)
        session_manager.update_session(session_id, session_data)

@app.get("/session-status/{session_id}")
async def get_session_status(session_id: str):
    """Get current session status"""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session_data.get("status"),
        "has_transcript": "discussion_transcript" in session_data,
        "has_summary": "summary" in session_data
    }

@app.get("/discussion-results/{session_id}")
async def get_discussion_results(session_id: str):
    """Get discussion transcript and summary"""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "transcript": session_data.get("discussion_transcript", []),
        "summary": session_data.get("summary", {}),
        "personas": session_data.get("personas", []),
        "topic": session_data.get("discussion_topic", "")
    }

@app.post("/ask-question")
async def ask_question(request: QARequest):
    """Interactive Q&A about the discussion"""
    try:
        session_data = session_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if "discussion_transcript" not in session_data:
            raise HTTPException(status_code=400, detail="No discussion transcript available")
        
        # Initialize Q&A assistant
        qa_assistant = QAAssistantAgent()
        
        # Get answer based on discussion transcript
        answer = await qa_assistant.answer_question(
            question=request.question,
            transcript=session_data["discussion_transcript"],
            summary=session_data.get("summary", {}),
            personas=session_data["personas"]
        )
        
        return {"success": True, "answer": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

class CustomSummaryRequest(BaseModel):
    session_id: str
    summary_schema: str

@app.post("/generate-custom-summary")
async def generate_custom_summary(request: CustomSummaryRequest):
    """Generate custom summary based on user-provided schema"""
    try:
        session_data = session_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if "discussion_transcript" not in session_data:
            raise HTTPException(status_code=400, detail="No discussion transcript available")
        
        # Initialize custom summary generator
        from agents.custom_summary_generator import CustomSummaryGeneratorAgent
        custom_summary_agent = CustomSummaryGeneratorAgent()
        
        # Generate custom summary based on user schema
        custom_summary = await custom_summary_agent.generate_custom_summary(
            transcript=session_data["discussion_transcript"],
            personas=session_data["personas"],
            schema=request.summary_schema,
            topic=session_data["discussion_topic"]
        )
        
        # Update session with custom summary
        session_data["summary"] = custom_summary
        session_data["status"] = "summary_generated"
        session_data["summary_type"] = "custom"
        session_data["custom_schema"] = request.summary_schema
        session_data["summary_generated_at"] = datetime.now().isoformat()
        session_manager.update_session(request.session_id, session_data)
        
        return {"success": True, "summary": custom_summary}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating custom summary: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# New: Plan generation endpoints
@app.post("/generate-plan")
async def generate_plan(request: PlanRequest):
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        llm = LLMClient()
        topic_brief = request.topic_brief.strip()
        if not topic_brief:
            raise HTTPException(status_code=400, detail="topic_brief required")

        # Use framework agent to build structured framework
        from agents.discussion_framework_agent import DiscussionFrameworkAgent
        fw_agent = DiscussionFrameworkAgent()
        framework = fw_agent.generate_framework(
            topic_brief=topic_brief,
            business_context=request.business_context,
            research_goals=request.research_goals,
        )

        # Render a backward-compatible text version for existing UI
        def _render_plan_text(fw: Dict) -> str:
            lines = []
            lines.append("Discussion Framework\n")
            if fw.get("research_objectives"):
                lines.append("Research Objectives:")
                for o in fw["research_objectives"]:
                    lines.append(f"- {o}")
                lines.append("")
            if fw.get("discussion_phases"):
                lines.append("Discussion Phases:")
                for ph in fw["discussion_phases"]:
                    name = ph.get("name", "Phase")
                    obj = ph.get("objective", "")
                    lines.append(f"- {name}: {obj}")
                    for q in ph.get("questions", [])[:3]:
                        lines.append(f"  • {q}")
                lines.append("")
            if fw.get("key_questions"):
                lines.append("Key Questions:")
                for q in fw["key_questions"]:
                    lines.append(f"- {q}")
                lines.append("")
            pc = fw.get("participant_criteria") or {}
            if pc:
                lines.append("Participant Criteria:")
                for k, arr in pc.items():
                    if isinstance(arr, list) and arr:
                        lines.append(f"- {k.title()}: {', '.join(arr)}")
                lines.append("")
            if fw.get("business_context"):
                lines.append("Business Context:")
                lines.append(fw["business_context"])
                lines.append("")
            if fw.get("expected_insights"):
                lines.append("Expected Insights:")
                for it in fw["expected_insights"]:
                    lines.append(f"- {it}")
                lines.append("")
            if fw.get("success_metrics"):
                lines.append("Success Metrics:")
                for it in fw["success_metrics"]:
                    lines.append(f"- {it}")
                lines.append("")
            return "\n".join(lines).strip()

        plan_text = _render_plan_text(framework)

        session_data = {
            "session_id": session_id,
            "topic_brief": topic_brief,
            "discussion_plan": framework,
            "status": "plan_generated",
            "created_at": datetime.now().isoformat()
        }
        session_manager.create_session(session_id, session_data)

        return {"success": True, "session_id": session_id, "framework": framework, "plan_text": plan_text, "topic_brief": topic_brief}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")

@app.post("/accept-plan")
async def accept_plan(request: AcceptPlanRequest):
    try:
        session_data = session_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        # Update plan and optionally discussion topic
        if request.framework is not None:
            session_data["discussion_plan"] = request.framework
        elif request.plan_text is not None:
            session_data["discussion_plan"] = request.plan_text
        if request.discussion_topic:
            session_data["discussion_topic"] = request.discussion_topic
        session_data["status"] = "plan_accepted"
        session_data["updated_at"] = datetime.now().isoformat()
        session_manager.update_session(request.session_id, session_data)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accepting plan: {str(e)}")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("agents", exist_ok=True)
    os.makedirs("core", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)