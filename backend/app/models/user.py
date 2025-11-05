"""
User model for session-based authentication
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model (session-based, not persisted to database)"""
    github_id: int
    github_login: str
    github_name: Optional[str] = None
    github_avatar_url: Optional[str] = None
    session_id: str
    created_at: datetime
    last_activity: datetime


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    user: User
    uploaded_docs: list = []
    chroma_collection: Optional[str] = None
