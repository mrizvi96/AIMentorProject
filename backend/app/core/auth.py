"""
Authentication middleware and utilities
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional
from app.core.session_manager import get_session, update_session_activity
from app.models.user import SessionInfo


security = HTTPBearer(auto_error=False)


async def get_current_session(request: Request) -> Optional[SessionInfo]:
    """Get current session from cookie (optional)"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        return None

    session = get_session(session_id)

    if not session:
        return None

    # Update last activity
    update_session_activity(session_id)

    return session


async def require_auth(request: Request) -> SessionInfo:
    """Require authentication (raises 401 if not authenticated)"""
    session = await get_current_session(request)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in with GitHub."
        )

    return session


async def optional_auth(request: Request) -> Optional[SessionInfo]:
    """Optional authentication (returns None if not authenticated)"""
    return await get_current_session(request)
