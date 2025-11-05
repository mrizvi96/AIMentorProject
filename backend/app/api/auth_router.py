"""
GitHub OAuth authentication router
Handles login, callback, logout, and user info endpoints
"""
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.session_manager import create_session, delete_session
from app.core.auth import require_auth, optional_auth
from app.models.user import SessionInfo
import httpx
from urllib.parse import urlencode
from typing import Optional


router = APIRouter()


@router.get("/auth/github")
async def github_login():
    """
    Redirect user to GitHub OAuth authorization page

    User flow:
    1. User clicks "Sign in with GitHub"
    2. This endpoint redirects to GitHub
    3. GitHub shows authorization page
    4. User approves → GitHub redirects to /auth/github/callback
    """
    # Validate configuration
    if not settings.github_client_id:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured. Please set GITHUB_CLIENT_ID in .env"
        )

    # Build GitHub authorization URL
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "user:email",  # Request user email access
        "state": "random_state_string"  # TODO: Use CSRF token in production
    }

    github_auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    return RedirectResponse(url=github_auth_url)


@router.get("/auth/github/callback")
async def github_callback(code: str, response: Response):
    """
    Handle GitHub OAuth callback

    Flow:
    1. GitHub redirects here with authorization code
    2. Exchange code for access token
    3. Use token to fetch user info from GitHub API
    4. Create session and set cookie
    5. Redirect to frontend
    """
    # Validate configuration
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured. Please set credentials in .env"
        )

    # Step 1: Exchange authorization code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri
            },
            headers={"Accept": "application/json"}
        )

        token_data = token_response.json()

        if "error" in token_data:
            raise HTTPException(
                status_code=400,
                detail=f"GitHub OAuth error: {token_data.get('error_description', 'Unknown error')}"
            )

        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Failed to obtain access token from GitHub"
            )

        # Step 2: Fetch user information from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to fetch user info from GitHub"
            )

        user_data = user_response.json()

    # Step 3: Create session
    session_id = create_session(
        github_id=user_data["id"],
        github_login=user_data["login"],
        github_name=user_data.get("name"),
        github_avatar_url=user_data.get("avatar_url")
    )

    # Step 4: Set secure session cookie
    response = RedirectResponse(url="http://localhost:5173")  # Redirect to frontend
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,  # Cannot be accessed by JavaScript (XSS protection)
        secure=False,  # Set to True in production (requires HTTPS)
        samesite="lax",  # CSRF protection
        max_age=settings.session_expiry_seconds  # 1 hour
    )

    return response


@router.post("/auth/logout")
async def logout(session: SessionInfo = Depends(require_auth), response: Response = None):
    """
    Log out current user

    Flow:
    1. Extract session from cookie
    2. Delete session from session manager
    3. Clear session cookie
    """
    # Delete session
    delete_session(session.session_id)

    # Clear cookie
    response = Response(content='{"status": "logged out"}', media_type="application/json")
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=False,  # Match login cookie settings
        samesite="lax"
    )

    return response


@router.get("/auth/me")
async def get_current_user(session: Optional[SessionInfo] = Depends(optional_auth)):
    """
    Get current user info (or null if not logged in)

    Returns:
    - User object if authenticated
    - {"user": null} if not authenticated
    """
    if not session:
        return {"user": None}

    return {
        "user": {
            "github_id": session.user.github_id,
            "github_login": session.user.github_login,
            "github_name": session.user.github_name,
            "github_avatar_url": session.user.github_avatar_url,
            "session_id": session.session_id
        }
    }
