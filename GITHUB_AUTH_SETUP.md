# GitHub OAuth Setup Guide

This guide walks you through setting up GitHub OAuth authentication for the AI Mentor project.

## Prerequisites

- GitHub account
- Backend and frontend code complete (already done!)
- Access to GitHub Developer Settings

---

## Step 1: Create GitHub OAuth App (5 minutes)

1. Go to https://github.com/settings/developers
2. Click **"New OAuth App"** button
3. Fill in the form:
   - **Application name**: `AI Mentor (Development)`
   - **Homepage URL**: `http://localhost:5173`
   - **Application description**: (optional) `Educational AI tutor with RAG`
   - **Authorization callback URL**: `http://localhost:8000/api/auth/github/callback`
4. Click **"Register application"**
5. You'll see your **Client ID** displayed
6. Click **"Generate a new client secret"**
7. Copy both the **Client ID** and **Client Secret** (save them securely!)

---

## Step 2: Configure Backend Environment

1. Navigate to the backend directory:
   ```bash
   cd /root/AIMentorProject/backend
   ```

2. Create `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your GitHub credentials:
   ```bash
   # GitHub OAuth (for user authentication)
   GITHUB_CLIENT_ID=your_actual_client_id_here
   GITHUB_CLIENT_SECRET=your_actual_client_secret_here
   GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback

   # Session Management
   SESSION_SECRET_KEY=your_random_secret_key_here  # Generate a random string!
   SESSION_EXPIRY_SECONDS=3600
   ```

4. Generate a secure session secret key:
   ```bash
   # Use Python to generate a random secret
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and use it as your `SESSION_SECRET_KEY`

---

## Step 3: Start the Services

### Option A: Using Runpod Startup Script (Recommended)

If you're on Runpod:
```bash
cd /root/AIMentorProject
./runpod_startup.sh
```

This will start:
- Milvus vector database (if needed)
- LLM inference server (if needed)
- Backend FastAPI server

### Option B: Manual Startup

#### Start Backend:
```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start Frontend (in a new terminal/tmux session):
```bash
cd /root/AIMentorProject/frontend
npm run dev
```

---

## Step 4: Test the Authentication Flow

1. Open your browser and go to: **http://localhost:5173**

2. You should see the AI Mentor interface with a **"Sign in with GitHub"** button in the header

3. Click **"Sign in with GitHub"**

4. You'll be redirected to GitHub's authorization page

5. Click **"Authorize"** to grant access

6. You'll be redirected back to the app

7. You should now see your GitHub avatar and username in the header

8. Click **"Logout"** to test the logout flow

---

## Troubleshooting

### Issue: "GitHub OAuth not configured" error

**Solution**: Make sure you created the `.env` file and added your GitHub credentials

### Issue: "Failed to fetch user info from GitHub"

**Solution**: Check that your Client Secret is correct (GitHub only shows it once when generated)

### Issue: Redirect doesn't work after GitHub authorization

**Solution**: Verify the callback URL in your GitHub OAuth app matches exactly:
```
http://localhost:8000/api/auth/github/callback
```

### Issue: Session cookie not being set

**Solution**: Check CORS configuration in `backend/main.py`:
- `allow_credentials=True` must be set
- Frontend origin must be in `allow_origins`

### Issue: Frontend shows "Sign in" button even after successful auth

**Solution**: Open browser console and check for errors. Likely causes:
- Backend not running on port 8000
- CORS blocking cookies
- Session expired (default 1 hour)

---

## Verify Everything Works

### Backend Health Check:
```bash
curl http://localhost:8000/
# Should return: {"status":"ok","message":"AI Mentor API is running",...}
```

### Auth Endpoint Check:
```bash
curl http://localhost:8000/api/auth/me
# Should return: {"user":null} if not logged in
```

### Check Backend Logs:
Look for startup messages confirming the auth router is loaded:
```
INFO: Application startup complete.
```

---

## Security Notes

### Development vs Production

**Current Setup (Development)**:
- Session cookies: `secure=False` (works with HTTP)
- Session storage: In-memory dictionary
- Secret key: Can be simple for testing

**Production Requirements**:
- Session cookies: `secure=True` (requires HTTPS)
- Session storage: Redis or database
- Secret key: Cryptographically secure random string
- Rate limiting on auth endpoints
- Session cleanup background task
- Logging for security events

### Session Management

- **Session duration**: 1 hour (configurable via `SESSION_EXPIRY_SECONDS`)
- **Storage**: In-memory (lost on server restart)
- **Cleanup**: Manual cleanup function exists (`cleanup_expired_sessions()`)
- **Cookie settings**:
  - `httponly=True` (prevents JavaScript access)
  - `samesite="lax"` (CSRF protection)
  - `secure=False` in dev, `True` in production

---

## Testing Checklist

- [ ] **Login Flow**
  - [ ] Click "Sign in" redirects to GitHub
  - [ ] GitHub shows authorization page
  - [ ] After authorizing, redirects back to app
  - [ ] User info (avatar + username) displayed in header
  - [ ] Session cookie set in browser

- [ ] **Session Persistence**
  - [ ] Refresh page maintains login state
  - [ ] Open new tab shows logged-in state

- [ ] **Logout Flow**
  - [ ] Click "Logout" clears session
  - [ ] UI updates to show "Sign in" button
  - [ ] Session cookie removed from browser

- [ ] **API Endpoints**
  - [ ] `GET /api/auth/github` - Redirects to GitHub
  - [ ] `GET /api/auth/github/callback` - Handles OAuth callback
  - [ ] `GET /api/auth/me` - Returns user info or null
  - [ ] `POST /api/auth/logout` - Clears session

---

## Next Steps (Phase 2)

After authentication works:

1. **User-specific document uploads**
   - Upload endpoint: `POST /api/documents`
   - Per-user ChromaDB collections

2. **Session-scoped RAG**
   - Query only user's uploaded documents
   - Merge with global course materials

3. **Upload UI component**
   - File picker in frontend
   - Upload progress indicator
   - Document list display

See [USER_PDF_UPLOAD_PLAN.md](USER_PDF_UPLOAD_PLAN.md) for detailed roadmap.

---

## Support

If you encounter issues:
1. Check browser console for JavaScript errors
2. Check backend logs for Python errors
3. Verify all services are running (backend on 8000, frontend on 5173)
4. Verify `.env` file has correct GitHub credentials
5. Check GitHub OAuth app settings match the URLs exactly

---

**Status**: Implementation complete, ready for testing!
**Time to Test**: ~10 minutes
**Difficulty**: Easy (mostly clicking through GitHub OAuth)
