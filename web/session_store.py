from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import secrets


SESSION_TTL = timedelta(hours=8)


@dataclass
class SessionData:
    session_id: str
    created_at: datetime
    is_authenticated: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionData] = {}

    def create_session(self) -> SessionData:
        session_id = secrets.token_urlsafe(32)
        session = SessionData(session_id=session_id, created_at=datetime.utcnow())
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if datetime.utcnow() - session.created_at > SESSION_TTL:
            self._sessions.pop(session_id, None)
            return None
        return session

    def require_session(self, session_id: Optional[str]) -> SessionData:
        if not session_id:
            raise KeyError("Missing session id")
        session = self.get_session(session_id)
        if session is None:
            raise KeyError("Session not found")
        return session

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


SESSION_STORE = SessionStore()
