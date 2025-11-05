# User PDF Upload Feature - Comprehensive Implementation Plan

**Feature**: Allow authenticated users to upload PDFs for session-based RAG enhancement
**Authentication**: GitHub OAuth
**Persistence**: Non-persistent (session-only)
**Status**: Planning phase

---

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Architecture Design](#architecture-design)
3. [Authentication System](#authentication-system)
4. [Document Management](#document-management)
5. [Implementation Phases](#implementation-phases)
6. [Security Considerations](#security-considerations)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Plan](#deployment-plan)

---

## Feature Overview

### User Story

**As a student**, I want to upload my own course materials (PDFs) so that the AI Mentor can answer questions specific to my coursework, without my documents being stored permanently.

### Key Requirements

#### Functional Requirements
1. **Authentication**
   - Users must authenticate with GitHub before uploading
   - Session-based authentication (no persistent user database needed initially)
   - Logout functionality

2. **PDF Upload**
   - Upload button in chat interface
   - Support multiple PDFs per session
   - Max file size: 10MB per PDF
   - Max total session documents: 50MB
   - Supported format: PDF only

3. **Document Processing**
   - Automatic ingestion upon upload
   - Documents added to session-specific vector store
   - Visual feedback during processing (progress indicator)

4. **Session Management**
   - Documents exist only for current session
   - Clear session state on logout
   - Automatic cleanup after session expiry (1 hour idle)

5. **Query Enhancement**
   - Queries search both base collection AND user-uploaded docs
   - User docs prioritized in retrieval (higher weight)
   - Clear indication when answer comes from user-uploaded docs

#### Non-Functional Requirements
1. **Performance**
   - Upload processing: < 30 seconds for 5MB PDF
   - No impact on base RAG performance
   - Concurrent user support (isolated sessions)

2. **Security**
   - User docs isolated per session
   - No cross-user document access
   - Secure file upload (validation, sanitization)
   - GitHub OAuth secure implementation

3. **Scalability**
   - Support 10+ concurrent users
   - Graceful degradation under load

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ GitHub Login │  │ Upload Button│  │  Chat UI     │     │
│  │   Component  │  │   Component  │  │  Component   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND API                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   /auth/*   │  │  /upload/*  │  │   /chat/*   │        │
│  │  endpoints  │  │  endpoints  │  │  endpoints  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                 │                 │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐       │
│  │   Auth      │  │  Document   │  │   Session   │       │
│  │  Middleware │  │  Processor  │  │   Manager   │       │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘       │
│                           │                 │               │
└───────────────────────────┼─────────────────┼───────────────┘
                            │                 │
                            ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Base ChromaDB   │  │ Session ChromaDB │                │
│  │   Collection     │  │   Collections    │                │
│  │ (persistent)     │  │ (session-based)  │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  Session Collections: user_{session_id}                     │
│  Lifecycle: Created on first upload, deleted on logout      │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. **Frontend Components** (SvelteKit)

**New Components**:
- `AuthButton.svelte` - GitHub login/logout
- `UploadButton.svelte` - PDF upload with progress
- `DocumentList.svelte` - Show uploaded docs in session
- `SessionStatus.svelte` - Display auth status and doc count

**Modified Components**:
- `+page.svelte` - Add auth check and upload UI
- `MessageList.svelte` - Indicate source (base vs user doc)

#### 2. **Backend Services** (FastAPI)

**New Modules**:
```
backend/
├── app/
│   ├── api/
│   │   ├── auth_router.py          # NEW: GitHub OAuth endpoints
│   │   ├── upload_router.py        # NEW: PDF upload endpoints
│   │   └── chat_router.py          # MODIFIED: Session-aware querying
│   ├── core/
│   │   ├── auth.py                 # NEW: Auth middleware, JWT handling
│   │   ├── session_manager.py     # NEW: Session lifecycle management
│   │   └── config.py               # MODIFIED: Add auth config
│   ├── services/
│   │   ├── document_processor.py  # NEW: User PDF ingestion
│   │   ├── session_rag_service.py # NEW: Multi-collection RAG
│   │   └── rag_service.py         # EXISTING: Base RAG (unchanged)
│   └── models/
│       ├── user.py                 # NEW: User model (session-based)
│       ├── document.py             # NEW: Document model
│       └── session.py              # NEW: Session model
```

#### 3. **Storage Architecture**

**ChromaDB Collections**:
1. **Base Collection** (persistent): `course_materials`
   - Existing course PDFs
   - Never modified by user uploads
   - Shared across all users

2. **Session Collections** (temporary): `user_{session_id}`
   - Created on first upload
   - Contains only user-uploaded docs for that session
   - Deleted on logout or after 1-hour idle timeout

**Session Data Structure** (in-memory or Redis):
```python
{
    "session_id": "sess_abc123",
    "user_github_id": "12345",
    "user_github_login": "johndoe",
    "created_at": "2025-11-05T12:00:00Z",
    "last_activity": "2025-11-05T12:30:00Z",
    "uploaded_docs": [
        {
            "filename": "my_notes.pdf",
            "upload_time": "2025-11-05T12:15:00Z",
            "size_bytes": 1024000,
            "chunk_count": 42
        }
    ],
    "chroma_collection": "user_sess_abc123"
}
```

---

## Authentication System

### GitHub OAuth Flow

#### Step 1: Frontend Login

```svelte
<!-- AuthButton.svelte -->
<script>
  async function login() {
    // Redirect to backend /auth/github endpoint
    window.location.href = '/api/auth/github';
  }
</script>

<button on:click={login}>
  <GitHubIcon /> Sign in with GitHub
</button>
```

#### Step 2: Backend OAuth Initiation

```python
# backend/app/api/auth_router.py

@router.get("/auth/github")
async def github_login():
    """Redirect user to GitHub OAuth"""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=read:user"
    )
    return RedirectResponse(github_auth_url)
```

#### Step 3: GitHub Callback

```python
@router.get("/auth/github/callback")
async def github_callback(code: str, response: Response):
    """Handle GitHub OAuth callback"""
    # 1. Exchange code for access token
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code
        },
        headers={"Accept": "application/json"}
    )
    access_token = token_response.json()["access_token"]

    # 2. Get user info from GitHub
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_data = user_response.json()

    # 3. Create session
    session_id = create_session(
        github_id=user_data["id"],
        github_login=user_data["login"]
    )

    # 4. Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600  # 1 hour
    )

    # 5. Redirect to app
    return RedirectResponse("/")
```

#### Step 4: Session Validation Middleware

```python
# backend/app/core/auth.py

async def require_auth(request: Request):
    """Middleware to require authentication"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = get_session(session_id)

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Update last activity
    update_session_activity(session_id)

    return session
```

### Configuration

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # Existing settings...

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/auth/github/callback"

    # Session management
    session_secret_key: str = ""  # For signing session IDs
    session_expiry_seconds: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
```

**.env file**:
```bash
# GitHub OAuth (get from https://github.com/settings/developers)
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback

# Session security
SESSION_SECRET_KEY=your_random_secret_key_here
```

---

## Document Management

### Upload Flow

#### 1. **Frontend: Upload UI**

```svelte
<!-- UploadButton.svelte -->
<script>
  let uploading = false;
  let progress = 0;

  async function handleUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    uploading = true;
    progress = 0;

    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'  // Send session cookie
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      console.log('Uploaded:', result);

      // Refresh document list
      await fetchUserDocuments();

    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      uploading = false;
    }
  }
</script>

<input
  type="file"
  accept=".pdf"
  multiple
  on:change={handleUpload}
  disabled={uploading}
/>

{#if uploading}
  <ProgressBar value={progress} />
{/if}
```

#### 2. **Backend: Upload Endpoint**

```python
# backend/app/api/upload_router.py

@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    session: Session = Depends(require_auth)
):
    """Upload PDF documents for current session"""

    # 1. Validate files
    for file in files:
        # Check file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Only PDF files allowed")

        # Check file size (10MB max)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(400, f"File {file.filename} exceeds 10MB limit")

    # 2. Check total session size (50MB max)
    current_size = get_session_total_size(session.session_id)
    new_size = sum(file.size for file in files)

    if current_size + new_size > 50 * 1024 * 1024:
        raise HTTPException(400, "Session document limit (50MB) exceeded")

    # 3. Save files temporarily
    temp_dir = Path(f"/tmp/sessions/{session.session_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    uploaded_docs = []

    for file in files:
        # Save file
        file_path = temp_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 4. Process document (async task)
        doc_info = await process_user_document(
            session_id=session.session_id,
            file_path=file_path,
            filename=file.filename
        )

        uploaded_docs.append(doc_info)

    return {
        "status": "success",
        "documents": uploaded_docs,
        "session_document_count": len(session.uploaded_docs) + len(uploaded_docs)
    }
```

#### 3. **Document Processing**

```python
# backend/app/services/document_processor.py

async def process_user_document(
    session_id: str,
    file_path: Path,
    filename: str
) -> Dict:
    """Process user-uploaded PDF and add to session collection"""

    # 1. Get or create session-specific ChromaDB collection
    collection_name = f"user_{session_id}"
    chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
    collection = chroma_client.get_or_create_collection(collection_name)

    # 2. Extract text from PDF (using PyMuPDF)
    documents = []
    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            documents.append({
                "text": text,
                "metadata": {
                    "filename": filename,
                    "page": page_num + 1,
                    "source": "user_upload",
                    "session_id": session_id
                }
            })

    # 3. Chunk documents
    text_splitter = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    nodes = []
    for doc in documents:
        chunks = text_splitter.split_text(doc["text"])
        for chunk in chunks:
            nodes.append({
                "text": chunk,
                "metadata": doc["metadata"]
            })

    # 4. Generate embeddings
    embed_model = HuggingFaceEmbedding(
        model_name=settings.embedding_model_name
    )

    embeddings = []
    for node in nodes:
        embedding = embed_model.get_text_embedding(node["text"])
        embeddings.append(embedding)

    # 5. Add to ChromaDB
    collection.add(
        documents=[node["text"] for node in nodes],
        embeddings=embeddings,
        metadatas=[node["metadata"] for node in nodes],
        ids=[f"{session_id}_{filename}_{i}" for i in range(len(nodes))]
    )

    # 6. Update session info
    update_session_documents(session_id, {
        "filename": filename,
        "chunk_count": len(nodes),
        "size_bytes": file_path.stat().st_size
    })

    # 7. Clean up temp file
    file_path.unlink()

    return {
        "filename": filename,
        "chunks": len(nodes),
        "status": "processed"
    }
```

### Multi-Collection RAG Query

```python
# backend/app/services/session_rag_service.py

class SessionRAGService:
    """RAG service that queries both base and session collections"""

    async def query(
        self,
        question: str,
        session_id: Optional[str] = None
    ) -> Dict:
        """Query both base and user collections"""

        # 1. Query base collection (top_k=2)
        base_results = await self.base_rag.query_collection(
            collection_name="course_materials",
            query=question,
            top_k=2
        )

        # 2. Query user collection if exists (top_k=2, higher weight)
        user_results = []
        if session_id:
            user_collection = f"user_{session_id}"
            if self.collection_exists(user_collection):
                user_results = await self.base_rag.query_collection(
                    collection_name=user_collection,
                    query=question,
                    top_k=2
                )

                # Boost user document scores (2x weight)
                for result in user_results:
                    result['score'] *= 2.0

        # 3. Combine and re-rank results
        all_results = user_results + base_results
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # Take top 3 overall
        top_results = all_results[:3]

        # 4. Generate response with combined context
        response = await self.generate_response(question, top_results)

        return {
            'response': response,
            'sources': top_results,
            'used_user_docs': len([r for r in top_results if r['metadata'].get('source') == 'user_upload']) > 0
        }
```

---

## Implementation Phases

### **Phase 1: Authentication Foundation** (Week 1, ~8 hours)

**Goal**: Get GitHub OAuth working end-to-end

#### Backend Tasks:
- [ ] Set up GitHub OAuth app in GitHub settings
- [ ] Add auth configuration to `config.py`
- [ ] Create `auth_router.py` with OAuth endpoints
- [ ] Implement session management (in-memory dict initially)
- [ ] Create auth middleware (`require_auth`)
- [ ] Add logout endpoint

#### Frontend Tasks:
- [ ] Create `AuthButton.svelte` component
- [ ] Add auth state management (store)
- [ ] Update `+page.svelte` to show auth status
- [ ] Handle OAuth callback redirect

#### Testing:
- [ ] Test login flow
- [ ] Test logout flow
- [ ] Test session expiry
- [ ] Test unauthorized access (should redirect)

**Deliverable**: Users can log in with GitHub and see their username

---

### **Phase 2: File Upload UI** (Week 2, ~6 hours)

**Goal**: Allow users to upload PDFs (no processing yet)

#### Backend Tasks:
- [ ] Create `upload_router.py`
- [ ] Implement upload endpoint with validation
- [ ] Add file size limits (10MB per file, 50MB per session)
- [ ] Store uploaded files in temp directory

#### Frontend Tasks:
- [ ] Create `UploadButton.svelte` component
- [ ] Add file type validation (PDF only)
- [ ] Show upload progress
- [ ] Display uploaded file list
- [ ] Handle upload errors gracefully

#### Testing:
- [ ] Test single file upload
- [ ] Test multiple file upload
- [ ] Test file size limits
- [ ] Test invalid file types (should reject)
- [ ] Test upload without auth (should reject)

**Deliverable**: Authenticated users can upload PDFs (stored but not processed)

---

### **Phase 3: Document Processing** (Week 3, ~12 hours)

**Goal**: Process uploaded PDFs and add to session collection

#### Backend Tasks:
- [ ] Create `document_processor.py` service
- [ ] Implement PDF text extraction (PyMuPDF)
- [ ] Implement chunking logic (reuse existing)
- [ ] Create session-specific ChromaDB collections
- [ ] Add embeddings generation
- [ ] Store chunks in session collection
- [ ] Update session metadata

#### Infrastructure Tasks:
- [ ] Add cleanup task for expired sessions
- [ ] Add background job for async processing
- [ ] Add disk space monitoring

#### Testing:
- [ ] Test PDF extraction (various PDF types)
- [ ] Test chunking (verify chunk count)
- [ ] Test embedding generation
- [ ] Test ChromaDB collection creation
- [ ] Test concurrent uploads

**Deliverable**: Uploaded PDFs are processed and stored in session-specific ChromaDB collections

---

### **Phase 4: Multi-Collection Querying** (Week 4, ~10 hours)

**Goal**: Query both base and user collections

#### Backend Tasks:
- [ ] Create `session_rag_service.py`
- [ ] Implement multi-collection query logic
- [ ] Add result re-ranking (boost user docs)
- [ ] Modify prompt to handle mixed sources
- [ ] Update `chat_router.py` to use session-aware service

#### Frontend Tasks:
- [ ] Update `Message.svelte` to show source type
- [ ] Add visual indicator for user-uploaded sources
- [ ] Show document count in session status

#### Testing:
- [ ] Test query with only base collection
- [ ] Test query with user collection
- [ ] Test query with both collections
- [ ] Verify user docs are prioritized
- [ ] Test source attribution accuracy

**Deliverable**: Queries return results from both base and user-uploaded documents

---

### **Phase 5: Session Lifecycle** (Week 5, ~6 hours)

**Goal**: Properly manage session lifecycle and cleanup

#### Backend Tasks:
- [ ] Implement session expiry (1 hour idle)
- [ ] Add background cleanup task
- [ ] Delete expired session collections
- [ ] Clean up temp files
- [ ] Add session extension on activity

#### Frontend Tasks:
- [ ] Show session expiry warning (5 min before)
- [ ] Add "Keep alive" button
- [ ] Clear UI state on logout

#### Testing:
- [ ] Test session expiry
- [ ] Test cleanup task
- [ ] Test multiple concurrent sessions
- [ ] Verify collection deletion
- [ ] Verify temp file cleanup

**Deliverable**: Sessions properly expire and clean up resources

---

### **Phase 6: Polish & Production** (Week 6, ~8 hours)

**Goal**: Production-ready feature

#### Backend Tasks:
- [ ] Add comprehensive error handling
- [ ] Add logging and monitoring
- [ ] Add rate limiting (max 10 uploads/hour)
- [ ] Add usage metrics collection
- [ ] Optimize performance (async where possible)

#### Frontend Tasks:
- [ ] Add loading states and spinners
- [ ] Improve error messages
- [ ] Add help text and tooltips
- [ ] Mobile responsive design
- [ ] Accessibility improvements

#### Documentation:
- [ ] User guide (how to upload docs)
- [ ] API documentation
- [ ] Deployment guide
- [ ] Monitoring guide

#### Testing:
- [ ] Load testing (10+ concurrent users)
- [ ] Security audit
- [ ] End-to-end testing
- [ ] Browser compatibility testing

**Deliverable**: Production-ready feature with monitoring and documentation

---

## Security Considerations

### 1. **Authentication Security**

- [ ] **Secure OAuth flow**: Use state parameter to prevent CSRF
- [ ] **Secure session cookies**: httponly, secure, samesite
- [ ] **Session secret rotation**: Rotate secret key periodically
- [ ] **Token expiry**: Sessions expire after 1 hour idle

### 2. **File Upload Security**

- [ ] **File type validation**: Only allow PDF files (check magic bytes, not just extension)
- [ ] **File size limits**: 10MB per file, 50MB per session
- [ ] **Virus scanning**: Optional integration with ClamAV
- [ ] **Path traversal prevention**: Sanitize filenames
- [ ] **Content validation**: Verify PDF structure

### 3. **Data Isolation**

- [ ] **Session isolation**: Each session has unique collection
- [ ] **Access control**: Users can only access their own collections
- [ ] **Collection naming**: Use cryptographically secure session IDs
- [ ] **Cleanup**: Delete collections on logout

### 4. **Rate Limiting**

- [ ] **Upload rate limit**: 10 uploads per hour per user
- [ ] **Query rate limit**: 100 queries per hour per user
- [ ] **Bandwidth limit**: 50MB uploads per hour per user

### 5. **Error Handling**

- [ ] **No information leakage**: Don't expose internal errors
- [ ] **Sanitized error messages**: User-friendly messages only
- [ ] **Logging**: Log security events (failed auth, rate limits)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_auth.py
def test_github_oauth_flow():
    # Test OAuth redirect
    # Test callback handling
    # Test session creation

# tests/test_upload.py
def test_file_upload_validation():
    # Test PDF validation
    # Test size limits
    # Test unauthorized upload

# tests/test_document_processor.py
def test_pdf_extraction():
    # Test text extraction
    # Test chunking
    # Test embedding generation

# tests/test_session_rag.py
def test_multi_collection_query():
    # Test base only
    # Test user only
    # Test combined query
```

### Integration Tests

```python
# tests/integration/test_upload_flow.py
def test_end_to_end_upload_and_query():
    # 1. Login with GitHub
    # 2. Upload PDF
    # 3. Wait for processing
    # 4. Query with uploaded doc context
    # 5. Verify answer uses uploaded doc
    # 6. Logout
    # 7. Verify collection deleted
```

### Load Tests

```python
# tests/load/test_concurrent_users.py
def test_10_concurrent_users():
    # Simulate 10 users uploading and querying
    # Verify no cross-contamination
    # Verify performance acceptable
```

---

## Deployment Plan

### Environment Variables

```bash
# .env.production
GITHUB_CLIENT_ID=prod_client_id
GITHUB_CLIENT_SECRET=prod_client_secret
GITHUB_REDIRECT_URI=https://yourdomain.com/api/auth/github/callback
SESSION_SECRET_KEY=prod_secret_key_here

# Session config
SESSION_EXPIRY_SECONDS=3600
MAX_UPLOAD_SIZE_MB=10
MAX_SESSION_SIZE_MB=50
```

### Infrastructure Changes

1. **Disk Space**: Allocate 10GB for temp uploads (auto-cleanup)
2. **ChromaDB**: Separate path for session collections
3. **Monitoring**: Add metrics for:
   - Active sessions count
   - Upload rate
   - Storage usage
   - Query latency

### Deployment Steps

1. **Deploy backend changes**
   - Update environment variables
   - Run database migrations (if any)
   - Deploy new API endpoints

2. **Deploy frontend changes**
   - Update OAuth redirect URLs
   - Deploy new components

3. **Verify**
   - Test login flow in production
   - Test upload in production
   - Monitor logs for errors

4. **Rollback Plan**
   - Feature flag to disable uploads
   - Revert to previous version if critical issues

---

## Monitoring & Maintenance

### Metrics to Track

1. **Usage Metrics**
   - Daily active users (DAU)
   - Uploads per day
   - Average session duration
   - Average documents per session

2. **Performance Metrics**
   - Upload processing time (p50, p95, p99)
   - Query latency with user docs
   - ChromaDB collection creation time

3. **Resource Metrics**
   - Disk space used (temp files + ChromaDB)
   - Memory usage (sessions in memory)
   - Active session count

4. **Error Metrics**
   - Failed uploads (by error type)
   - Authentication failures
   - Rate limit hits

### Maintenance Tasks

- **Daily**: Check disk space, review error logs
- **Weekly**: Review usage metrics, optimize slow queries
- **Monthly**: Rotate session secret, review security logs

---

## Future Enhancements (Post-MVP)

### Phase 7: Enhanced Features

1. **Document Management**
   - View uploaded documents
   - Delete individual documents
   - Rename documents
   - Preview documents

2. **Session Persistence** (Optional)
   - Save session across browser restarts
   - Export/import session state
   - Share session with others (read-only)

3. **Advanced Authentication**
   - Support multiple OAuth providers (Google, Microsoft)
   - Email/password authentication
   - Two-factor authentication (2FA)

4. **Usage Analytics**
   - Personal usage dashboard
   - Most queried topics from user docs
   - Suggested improvements

5. **Collaborative Features**
   - Share documents with team
   - Collaborative question history
   - Team knowledge base

---

## Risk Assessment

### High Risk
- **Security**: OAuth misconfiguration, session hijacking
  - **Mitigation**: Security audit, penetration testing

- **Performance**: Large PDFs (100+ pages) slow down system
  - **Mitigation**: Async processing, queue system

### Medium Risk
- **Storage**: Disk space fills up with abandoned sessions
  - **Mitigation**: Aggressive cleanup, disk monitoring

- **Scalability**: ChromaDB performance with many collections
  - **Mitigation**: Load testing, consider sharding

### Low Risk
- **UX**: Users confused by upload process
  - **Mitigation**: Clear instructions, tooltips

---

## Success Criteria

### MVP Success
- [ ] Users can authenticate with GitHub
- [ ] Users can upload PDFs (10MB limit)
- [ ] PDFs are processed within 30 seconds
- [ ] Queries return results from user docs
- [ ] Sessions expire and clean up properly
- [ ] No security vulnerabilities

### Production Success (3 months)
- [ ] 100+ users have uploaded documents
- [ ] 90% upload success rate
- [ ] < 5 second query latency (with user docs)
- [ ] Zero security incidents
- [ ] Positive user feedback (>4.0/5.0)

---

## Timeline Summary

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 | 1 week | Authentication |
| Phase 2 | 1 week | File upload UI |
| Phase 3 | 1.5 weeks | Document processing |
| Phase 4 | 1.5 weeks | Multi-collection querying |
| Phase 5 | 1 week | Session lifecycle |
| Phase 6 | 1 week | Polish & production |
| **Total** | **7-8 weeks** | **MVP to production** |

---

**Status**: Planning complete, ready for Phase 1 implementation
**Next Step**: Set up GitHub OAuth app and begin Phase 1

