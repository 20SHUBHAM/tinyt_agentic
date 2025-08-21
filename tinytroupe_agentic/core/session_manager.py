"""
Session Manager for handling focus group sessions
Maintains persistent memory of discussions and participants
"""

import json
import os
from typing import Dict, Optional, Any
from datetime import datetime

class SessionManager:
    """Manages focus group sessions with persistent storage"""
    
    def __init__(self, storage_path: str = "data/sessions"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._sessions = {}
        self._load_existing_sessions()
    
    def _load_existing_sessions(self):
        """Load existing sessions from storage"""
        try:
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    if filename.endswith('.json'):
                        session_id = filename.replace('.json', '')
                        with open(os.path.join(self.storage_path, filename), 'r') as f:
                            self._sessions[session_id] = json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def create_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Create a new session"""
        try:
            self._sessions[session_id] = session_data
            self._save_session(session_id, session_data)
            return True
        except Exception as e:
            print(f"Error creating session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update existing session"""
        try:
            if session_id in self._sessions:
                self._sessions[session_id].update(session_data)
                self._save_session(session_id, self._sessions[session_id])
                return True
            return False
        except Exception as e:
            print(f"Error updating session {session_id}: {e}")
            return False
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save session to persistent storage"""
        try:
            filepath = os.path.join(self.storage_path, f"{session_id}.json")
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """List all sessions"""
        return self._sessions.copy()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            if session_id in self._sessions:
                del self._sessions[session_id]
                filepath = os.path.join(self.storage_path, f"{session_id}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False