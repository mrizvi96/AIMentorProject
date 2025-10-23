# Next Session Plan - Docker Hub Automated Builds

## Goal
Get AI Mentor deployed and running on Runpod with full end-to-end testing.

**Estimated Time:** 1.5-2 hours

---

## Phase 1: Setup Docker Hub Automated Builds (15-20 min)

### Step 1: Create Docker Hub Repository (5 min)

1. Go to https://hub.docker.com
2. Login with username: `mrizvi96`
3. Click **"Repositories"** → **"Create Repository"**
4. Repository details:
   - **Name:** `ai-mentor`
   - **Description:** "AI Mentor - Agentic RAG system for CS education"
   - **Visibility:** Public (or Private if you prefer)
5. Click **"Create"**

### Step 2: Configure Automated Builds (10 min)

1. In your new `ai-mentor` repository, click the **"Builds"** tab
2. Click **"Configure Automated Builds"**
3. Click **"Connect to GitHub"** (if not already connected)
4. Authorize Docker Hub to access your GitHub account
5. Select repository: `mrizvi96/AIMentorProject`
6. Configure build settings:
   - **Source Type:** Branch
   - **Source:** main
   - **Docker Tag:** latest
   - **Dockerfile location:** `/Dockerfile`
   - **Build Context:** `/`
   - **Autobuild:** ON
7. Click **"Save and Build"**

### Step 3: Monitor Build Progress (20-30 min - passive wait)

1. Click the **"Builds"** tab
2. Watch the build progress
3. The build will take 20-30 minutes
4. ☕ **Take a break while it builds!**
5. Come back when you see: **"Success"** with a green checkmark

**Expected Result:** `mrizvi96/ai-mentor:latest` available on Docker Hub

---

## Phase 2: Deploy to Runpod (10-15 min)

### Step 1: Create New Runpod Pod (5 min)

1. Go to https://runpod.io
2. Click **"Deploy"** → **"GPU Pod"**
3. **Select GPU:**
   - RTX A5000 (24GB VRAM) - recommended
   - OR RTX 4090 / A6000 (if A5000 unavailable)
4. **Template:** Click **"Custom"**
   - Docker Image Name: `mrizvi96/ai-mentor:latest`
5. **Configuration:**
   - Container Disk: 50GB minimum
   - Volume Disk: 100GB (optional, for persistence)
   - **Expose TCP Ports:** `8000,8080,19530,5173`
   - **Expose HTTP Ports:** `8000,8080,5173`
6. Click **"Deploy On-Demand"** or **"Deploy Spot"** (spot is cheaper)
7. Wait for pod to start (2-3 minutes)

### Step 2: Note Connection Details (1 min)

Once pod is running, note:
- **SSH Command:** `ssh root@X.X.X.X -p XXXXX`
- **Password:** (shown in Runpod dashboard)
- **Public URLs:**
  - Backend: `https://pod-xyz-8000.runpod.io`
  - LLM Server: `https://pod-xyz-8080.runpod.io`
  - Frontend: `https://pod-xyz-5173.runpod.io`

### Step 3: SSH into Pod (2 min)

**Option A: VS Code Remote-SSH (Recommended)**
1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type: "Remote-SSH: Connect to Host"
4. Enter: `root@X.X.X.X -p XXXXX`
5. Enter password when prompted

**Option B: Terminal/PowerShell**
```bash
ssh root@X.X.X.X -p XXXXX
# Enter password when prompted
```

**Verify you're connected:**
```bash
pwd
# Should show: /workspace or /root
ls
# Should show AIMentorProject folder (if image built correctly)
```

---

## Phase 3: Upload Mistral Model (10-15 min)

### Option A: Upload from Local Machine (Recommended if you have the model)

**From your local machine (PowerShell):**
```powershell
# If model is on USB drive
scp -P XXXXX D:\path\to\Mistral-7B-Instruct-v0.2.Q5_K_M.gguf root@X.X.X.X:/workspace/models/
```

**Or if you need to download the model first:**
1. Download from: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf
2. Save to D drive (USB)
3. Upload via SCP (command above)

### Option B: Download Directly on Runpod

**On the Runpod SSH session:**
```bash
cd /workspace/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf

# Wait ~10-15 minutes for download
# Verify:
ls -lh
# Should show ~5.1GB file
```

---

## Phase 4: Start All Services (5 min)

### Step 1: Navigate to Project Directory

```bash
cd /workspace/AIMentorProject
```

### Step 2: Check Files Exist

```bash
ls -la
# Should see: start_all_services.sh, docker-compose.yml, backend/, etc.

# Make sure model exists
ls -lh /workspace/models/
# Should show: Mistral-7B-Instruct-v0.2.Q5_K_M.gguf (~5.1GB)
```

### Step 3: Start All Services

```bash
# Run the automated startup script
./start_all_services.sh
```

**This will:**
- Start Milvus (Docker Compose) - 90 seconds
- Start LLM Server (tmux session) - 30 seconds
- Start Backend API (tmux session) - 5 seconds

**Wait for it to complete** (~2-3 minutes total)

### Step 4: Verify Services Running

```bash
# Check Milvus
docker-compose ps
# Should show: milvus-standalone, milvus-etcd, milvus-minio (all "Up")

# Check LLM Server
curl http://localhost:8080/v1/models
# Should return JSON with model info

# Check Backend API
curl http://localhost:8000/
# Should return: {"status": "ok", "message": "AI Mentor API is running"}

# Check tmux sessions
tmux ls
# Should show: llm, backend
```

---

## Phase 5: Ingest Course Materials (10 min)

### Step 1: Add Sample Documents (if not already present)

```bash
cd /workspace/AIMentorProject/course_materials

# Check if any PDFs exist
ls -la

# If no PDFs, you can:
# 1. Upload from local machine via SCP
# 2. Download sample PDFs
# 3. Use the download_textbooks.sh script (if configured)
```

### Step 2: Run Ingestion

```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials/
```

**Expected output:**
- "Loading documents from ../course_materials..."
- "Found X PDF files"
- "Loaded X documents"
- "Generating embeddings and storing in Milvus..."
- "✓ Document ingestion complete!"

**This takes 5-10 minutes** depending on document size.

---

## Phase 6: Test Backend (10 min)

### Test 1: LLM Server Health

```bash
# Test models endpoint
curl http://localhost:8080/v1/models | jq

# Test chat completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello! What is Python?"}],
    "max_tokens": 100,
    "temperature": 0.7
  }' | jq
```

**Expected:** JSON response with AI-generated answer about Python

### Test 2: Backend API Health

```bash
# Test root endpoint
curl http://localhost:8000/ | jq

# Test detailed health check
curl http://localhost:8000/api/health | jq

# Test RAG stats
curl http://localhost:8000/api/chat/stats | jq
```

**Expected:** All services show "running"

### Test 3: Chat Endpoint (RAG System)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python?",
    "conversation_id": "test-001"
  }' | jq
```

**Expected:**
- Response with AI-generated answer
- List of source documents with relevance scores
- Citations from course materials

### Test 4: Via Public URL

From your **local machine** (not SSH):
```bash
# Replace with your actual Runpod URL
curl https://pod-xyz-8000.runpod.io/ | jq

curl -X POST https://pod-xyz-8000.runpod.io/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is recursion?"}' | jq
```

**Expected:** Same results as localhost tests

---

## Phase 7: Test Frontend (15 min)

### Step 1: Update Frontend API URL

**On your local machine:**

Edit `frontend/src/lib/api.ts`:
```typescript
// Change this line:
const API_BASE_URL = 'http://localhost:8000';

// To your Runpod public URL:
const API_BASE_URL = 'https://pod-xyz-8000.runpod.io';
```

### Step 2: Start Frontend Dev Server

```bash
# On your local machine
cd D:\ai-mentor-build\AIMentorProject\frontend

# Install dependencies (if not done)
npm install

# Start dev server
npm run dev
```

### Step 3: Open Browser and Test

1. Open browser to: `http://localhost:5173`
2. You should see the AI Mentor UI
3. **Test the empty state:**
   - See example questions
   - Clean, gradient UI
4. **Test asking a question:**
   - Type: "What is object-oriented programming?"
   - Press Enter
   - **Watch for:**
     - User message appears
     - Loading spinner shows
     - AI response appears
     - Source documents are shown (expandable)
     - Relevance scores displayed
5. **Test multiple questions:**
   - "Explain recursion"
   - "What is a stack data structure?"
   - "How does binary search work?"
6. **Verify:**
   - Auto-scroll works
   - Sources expand/collapse
   - Loading states work
   - Error handling works (try with backend off)

---

## Phase 8: Troubleshooting (If Needed)

### If Milvus Won't Start

```bash
# Check Docker daemon
systemctl status docker
systemctl start docker

# Check logs
docker-compose logs -f milvus

# Restart
docker-compose down
docker-compose up -d
```

### If LLM Server Won't Start

```bash
# Check tmux session
tmux attach -t llm
# Press Ctrl+B then D to detach

# Check if model file exists
ls -lh /workspace/models/

# Restart manually
tmux kill-session -t llm
tmux new-session -d -s llm "cd /workspace/AIMentorProject && ./start_llm_server.sh"
```

### If Backend API Won't Start

```bash
# Check tmux session
tmux attach -t backend
# Press Ctrl+B then D to detach

# Check for errors
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python -c "from app.core.config import settings; print(settings)"

# Restart
tmux kill-session -t backend
tmux new-session -d -s backend "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

### If Frontend Can't Connect

1. **Check CORS settings** in `backend/main.py`
   - Should include your local dev server: `http://localhost:5173`
2. **Check Runpod firewall**
   - Ports should be exposed: 8000, 8080
3. **Verify API URL** in `frontend/src/lib/api.ts`
   - Should match Runpod public URL

### If Ingestion Fails

```bash
# Check Milvus is running
curl http://localhost:19530/healthz

# Check if collection exists
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python -c "from pymilvus import connections, utility; connections.connect('default', host='localhost', port='19530'); print(utility.list_collections())"

# Re-run with --overwrite if needed
python ingest.py --directory ../course_materials/ --overwrite
```

---

## Success Criteria

### ✅ Deployment Successful If:

1. **Services Running:**
   - Milvus: `docker-compose ps` shows all "Up"
   - LLM: `curl localhost:8080/v1/models` returns JSON
   - Backend: `curl localhost:8000/` returns status OK

2. **Data Ingested:**
   - Ingestion completed without errors
   - Documents stored in Milvus
   - Can query collection

3. **Backend Works:**
   - Chat endpoint returns responses
   - Sources are retrieved
   - Relevance scores present

4. **Frontend Works:**
   - UI loads at localhost:5173
   - Can send messages
   - Receives responses
   - Sources display correctly

---

## After Successful Testing

### Document Any Issues

Create a new session summary noting:
- What worked
- What didn't work
- Performance observations
- Any errors encountered

### Next Development Steps (Phase 2)

Once everything works:
1. ✅ **Phase 1 Complete:** Simple RAG is working
2. → **Phase 2:** Implement Agentic RAG with LangGraph
   - Add document grading
   - Add query rewriting
   - Add self-correction loop
   - Create `/api/chat/agentic` endpoint
   - Update frontend to show agent status

### Save Your Work

```bash
# On local machine
cd D:\ai-mentor-build\AIMentorProject
git pull origin main
git add .
git commit -m "Update frontend API URL for Runpod deployment"
git push origin main
```

---

## Time Breakdown Summary

| Phase | Task | Time |
|-------|------|------|
| 1 | Setup Docker Hub builds | 15-20 min |
| - | Wait for build (passive) | 20-30 min |
| 2 | Deploy Runpod pod | 10-15 min |
| 3 | Upload model | 10-15 min |
| 4 | Start services | 5 min |
| 5 | Ingest documents | 10 min |
| 6 | Test backend | 10 min |
| 7 | Test frontend | 15 min |
| **Total Active Time** | | **1.5-2 hours** |
| **Total Including Build** | | **2-2.5 hours** |

---

## Important Notes

- **Save Runpod SSH details** - you'll need them
- **Don't stop the pod** until you backup data
- **Milvus data is ephemeral** - back up before stopping
- **Model upload only needed once per pod**
- **Services start automatically** with `./start_all_services.sh`

---

## Backup Strategy (Before Stopping Pod)

```bash
# Backup Milvus data
cd /workspace/AIMentorProject
tar -czf milvus-backup-$(date +%Y%m%d).tar.gz volumes/

# Download to local machine (from local machine PowerShell):
scp -P XXXXX root@X.X.X.X:/workspace/AIMentorProject/milvus-backup-*.tar.gz D:\backups\

# On next pod startup:
scp -P XXXXX D:\backups\milvus-backup-*.tar.gz root@X.X.X.X:/workspace/AIMentorProject/
ssh root@X.X.X.X -p XXXXX
cd /workspace/AIMentorProject
tar -xzf milvus-backup-*.tar.gz
```

---

## Quick Reference Commands

```bash
# View LLM logs
tmux attach -t llm

# View Backend logs
tmux attach -t backend

# View Milvus logs
docker-compose logs -f milvus

# Restart everything
docker-compose restart
tmux kill-session -t llm
tmux kill-session -t backend
./start_all_services.sh

# Check GPU usage
nvidia-smi

# Check disk space
df -h
```

---

**Ready to start next session!** 🚀

Follow this plan step-by-step and you'll have a working AI Mentor system deployed and testable in ~2 hours.
