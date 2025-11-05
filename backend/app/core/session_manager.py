"""
Session management for user authentication
Handles session lifecycle, storage, and cleanup
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.models.user import User, SessionInfo


# In-memory session storage (use Redis in production)
_sessions: Dict[str, SessionInfo] = {}


def create_session(
    github_id: int,
    github_login: str,
    github_name: Optional[str] = None,
    github_avatar_url: Optional[str] = None
) -> str:
    """Create a new session for authenticated user"""

    # Generate cryptographically secure session ID
    session_id = f"sess_{secrets.token_urlsafe(32)}"

    # Create user object
    user = User(
        github_id=github_id,
        github_login=github_login,
        github_name=github_name,
        github_avatar_url=github_avatar_url,
        session_id=session_id,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )

    # Store session
    _sessions[session_id] = SessionInfo(
        session_id=session_id,
        user=user,
        uploaded_docs=[],
        chroma_collection=None
    )

    return session_id


def get_session(session_id: str) -> Optional[SessionInfo]:
    """Get session by ID"""
    session = _sessions.get(session_id)

    if not session:
        return None

    # Check if session expired (1 hour idle)
    if datetime.utcnow() - session.user.last_activity > timedelta(hours=1):
        delete_session(session_id)
        return None

    return session


def update_session_activity(session_id: str):
    """Update last activity timestamp for session"""
    session = _sessions.get(session_id)
    if session:
        session.user.last_activity = datetime.utcnow()


def delete_session(session_id: str):
    """Delete session and clean up resources"""
    session = _sessions.get(session_id)

    if session:
        # TODO: Clean up ChromaDB collection if exists
        # TODO: Clean up temp files if any

        del _sessions[session_id]


def get_all_sessions() -> Dict[str, SessionInfo]:
    """Get all active sessions (for monitoring/cleanup)"""
    return _sessions


def cleanup_expired_sessions():
    """Clean up expired sessions (call periodically)"""
    now = datetime.utcnow()
    expired = []

    for session_id, session in _sessions.items():
        if now - session.user.last_activity > timedelta(hours=1):
            expired.append(session_id)

    for session_id in expired:
        delete_session(session_id)

    return len(expired)
