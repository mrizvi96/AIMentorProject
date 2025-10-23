# AI Mentor Deployment Checklist

## Pre-Deployment Checklist

### Local Repository Status
- [ ] All changes committed to Git
- [ ] Pushed to GitHub (`git push origin main`)
- [ ] No uncommitted changes (`git status` shows clean)
- [ ] Dockerfile present and up-to-date
- [ ] .dockerignore present and optimized
- [ ] start_all_services.sh executable (`chmod +x start_all_services.sh`)

### Docker Hub Setup
- [ ] Docker Hub account active: `mrizvi96`
- [ ] Repository created: `mrizvi96/ai-mentor`
- [ ] GitHub connected to Docker Hub
- [ ] Automated builds configured
- [ ] Build triggered successfully
- [ ] Build completed without errors (status: Success ✅)
- [ ] Image tagged as `latest`
- [ ] Image pull command verified: `docker pull mrizvi96/ai-mentor:latest`

---

## Runpod Deployment Checklist

### Pod Configuration
- [ ] Logged into Runpod: https://runpod.io
- [ ] GPU selected: RTX A5000 (24GB VRAM) or equivalent
- [ ] Custom template configured
- [ ] Docker image set: `mrizvi96/ai-mentor:latest`
- [ ] Ports exposed: `8000,8080,19530,5173`
- [ ] Container disk: ≥50GB
- [ ] Volume disk: ≥100GB (optional for persistence)
- [ ] Pod type selected: On-Demand or Spot
- [ ] Pod deployed successfully

### Connection Setup
- [ ] Pod status: Running
- [ ] SSH details noted:
  - [ ] IP address: `________________`
  - [ ] Port: `________________`
  - [ ] Password: `________________`
- [ ] Public URLs noted:
  - [ ] Backend: `https://pod-____-8000.runpod.io`
  - [ ] LLM Server: `https://pod-____-8080.runpod.io`
  - [ ] Frontend: `https://pod-____-5173.runpod.io`

### SSH Connection
- [ ] VS Code Remote-SSH extension installed (if using VS Code)
- [ ] SSH connection established
- [ ] Working directory verified: `/workspace/AIMentorProject`
- [ ] Project files present: `ls -la` shows expected structure

---

## Model Upload Checklist

### Mistral Model Setup
- [ ] Model downloaded locally: `Mistral-7B-Instruct-v0.2.Q5_K_M.gguf`
- [ ] Model location noted: `________________`
- [ ] Model size verified: ~5.1GB
- [ ] Upload method chosen:
  - [ ] Option A: SCP from local machine (~10 min)
  - [ ] Option B: Direct download on pod (~60 min)

### Upload via SCP (Option A)
```bash
# From local machine (PowerShell/Terminal)
scp -P [PORT] /path/to/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf root@[IP]:/workspace/models/
```
- [ ] SCP upload initiated
- [ ] Upload completed successfully
- [ ] Model verified on pod: `ls -lh /workspace/models/`

### Download on Pod (Option B)
```bash
# On Runpod SSH session
cd /workspace/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf
```
- [ ] Download initiated
- [ ] Download completed (~10-15 min)
- [ ] Model verified: `ls -lh` shows ~5.1GB file

---

## Service Startup Checklist

### Pre-Start Verification
- [ ] In project directory: `cd /workspace/AIMentorProject`
- [ ] Scripts are executable: `ls -l *.sh` shows `x` permissions
- [ ] Model file exists: `ls /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf`
- [ ] Docker daemon running: `docker ps` works

### Start All Services
```bash
./start_all_services.sh
```
- [ ] Script executed without errors
- [ ] Milvus starting (wait 90 seconds)
- [ ] LLM server starting in tmux session
- [ ] Backend API starting in tmux session

### Service Verification
- [ ] Milvus containers running:
  ```bash
  docker-compose ps
  # Should show: milvus-standalone, milvus-etcd, milvus-minio (all "Up")
  ```
- [ ] LLM server responding:
  ```bash
  curl http://localhost:8080/v1/models
  # Should return JSON with model info
  ```
- [ ] Backend API responding:
  ```bash
  curl http://localhost:8000/
  # Should return: {"status": "ok", "message": "AI Mentor API is running"}
  ```
- [ ] Tmux sessions active:
  ```bash
  tmux ls
  # Should show: llm, backend
  ```

---

## Data Ingestion Checklist

### Course Materials Preparation
- [ ] Course materials directory exists: `/workspace/AIMentorProject/course_materials`
- [ ] Sample PDFs present (or uploaded via SCP)
- [ ] Materials count: `ls -la course_materials/*.pdf | wc -l`

### Ingestion Process
```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials/
```
- [ ] Virtual environment activated
- [ ] Ingestion script running
- [ ] Documents loaded without errors
- [ ] Embeddings generated
- [ ] Data stored in Milvus
- [ ] Success message displayed: "✓ Document ingestion complete!"

---

## Backend Testing Checklist

### LLM Server Tests
- [ ] Models endpoint test:
  ```bash
  curl http://localhost:8080/v1/models | jq
  ```
  Expected: JSON response with model name

- [ ] Chat completion test:
  ```bash
  curl http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "Hello! What is Python?"}], "max_tokens": 100, "temperature": 0.7}' | jq
  ```
  Expected: JSON response with AI-generated answer

### Backend API Tests
- [ ] Root endpoint:
  ```bash
  curl http://localhost:8000/ | jq
  ```
  Expected: `{"status": "ok", "message": "AI Mentor API is running"}`

- [ ] Health check:
  ```bash
  curl http://localhost:8000/api/health | jq
  ```
  Expected: All services showing "running"

- [ ] RAG stats:
  ```bash
  curl http://localhost:8000/api/chat/stats | jq
  ```
  Expected: Document count and collection info

- [ ] Chat endpoint (RAG system):
  ```bash
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What is Python?", "conversation_id": "test-001"}' | jq
  ```
  Expected: AI response with sources and relevance scores

### Public URL Tests (from local machine)
- [ ] Backend public URL:
  ```bash
  curl https://pod-[ID]-8000.runpod.io/ | jq
  ```
  Expected: Same as localhost tests

- [ ] Chat via public URL:
  ```bash
  curl -X POST https://pod-[ID]-8000.runpod.io/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What is recursion?"}' | jq
  ```
  Expected: AI response with sources

---

## Frontend Testing Checklist

### Frontend Configuration
- [ ] Frontend API URL updated in `frontend/src/lib/api.ts`:
  ```typescript
  const API_BASE_URL = 'https://pod-[ID]-8000.runpod.io';
  ```
- [ ] Changes saved and committed locally

### Frontend Development Server (Local Machine)
```bash
cd frontend
npm install
npm run dev
```
- [ ] Dependencies installed
- [ ] Dev server started on `http://localhost:5173`
- [ ] No build errors in terminal

### Frontend UI Tests
- [ ] Browser opened to `http://localhost:5173`
- [ ] UI loads without errors
- [ ] Empty state displays with example questions
- [ ] Gradient theme renders correctly

### Chat Functionality Tests
- [ ] Click example question → message sent
- [ ] Type custom question: "What is object-oriented programming?"
- [ ] Press Enter → message sent
- [ ] User message appears in chat
- [ ] Loading spinner displays
- [ ] AI response appears (streaming or complete)
- [ ] Source documents displayed below response
- [ ] Sources expand/collapse on click
- [ ] Relevance scores visible

### Multiple Questions Test
- [ ] Ask: "Explain recursion"
- [ ] Ask: "What is a stack data structure?"
- [ ] Ask: "How does binary search work?"
- [ ] Auto-scroll works (scrolls to bottom on new messages)
- [ ] Can scroll up to read previous messages
- [ ] Auto-scroll pauses when scrolled up
- [ ] Auto-scroll resumes when at bottom

### Error Handling Tests
- [ ] Stop backend → ask question → error message displays
- [ ] Restart backend → chat recovers
- [ ] Network error handling works gracefully

---

## Success Criteria

### ✅ Deployment Successful If:

1. **Services Running:**
   - [ ] Milvus: All 3 containers up
   - [ ] LLM Server: Responds on port 8080
   - [ ] Backend API: Responds on port 8000
   - [ ] No service errors in logs

2. **Data Ingested:**
   - [ ] Documents loaded into Milvus
   - [ ] Collection created and queryable
   - [ ] Embedding generation successful

3. **Backend Functional:**
   - [ ] Chat endpoint returns responses
   - [ ] Sources retrieved from Milvus
   - [ ] Relevance scores calculated
   - [ ] Public URLs accessible

4. **Frontend Working:**
   - [ ] UI loads at localhost:5173
   - [ ] Can send messages
   - [ ] Receives AI responses
   - [ ] Sources display correctly
   - [ ] No console errors

---

## Post-Deployment Checklist

### Documentation
- [ ] Document any issues encountered
- [ ] Note Runpod SSH credentials in secure location
- [ ] Save public URLs for this session
- [ ] Update session notes with:
  - [ ] What worked
  - [ ] What didn't work
  - [ ] Performance observations
  - [ ] Errors and solutions

### Data Backup (Before Stopping Pod)
```bash
# Backup Milvus data
cd /workspace/AIMentorProject
tar -czf milvus-backup-$(date +%Y%m%d).tar.gz volumes/

# Download to local machine (from local PowerShell/Terminal)
scp -P [PORT] root@[IP]:/workspace/AIMentorProject/milvus-backup-*.tar.gz ./backups/
```
- [ ] Milvus data backed up
- [ ] Backup downloaded to local machine
- [ ] Backup verified (file size > 0)

### Save Work to GitHub
```bash
# On local machine
cd /path/to/AIMentorProject
git pull origin main
git add .
git commit -m "Update frontend API URL and deployment notes"
git push origin main
```
- [ ] Latest code pulled from GitHub
- [ ] Local changes committed
- [ ] Pushed to GitHub
- [ ] GitHub repository up-to-date

---

## Troubleshooting Reference

### If Milvus Won't Start
```bash
systemctl status docker
systemctl start docker
docker-compose logs -f milvus
docker-compose down
docker-compose up -d
```

### If LLM Server Won't Start
```bash
tmux attach -t llm  # Press Ctrl+B then D to detach
ls -lh /workspace/models/
tmux kill-session -t llm
tmux new-session -d -s llm "./start_llm_server.sh"
```

### If Backend API Won't Start
```bash
tmux attach -t backend  # Press Ctrl+B then D to detach
cd backend && source venv/bin/activate
python -c "from app.core.config import settings; print(settings)"
tmux kill-session -t backend
tmux new-session -d -s backend "cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

### If Frontend Can't Connect
- [ ] Check CORS in `backend/main.py` includes `http://localhost:5173`
- [ ] Verify Runpod ports 8000, 8080 are exposed
- [ ] Confirm API URL in `frontend/src/lib/api.ts` matches Runpod URL

---

## Time Tracking

| Phase | Task | Estimated Time | Actual Time |
|-------|------|---------------|-------------|
| 1 | Docker Hub setup | 15-20 min | _________ |
| - | Wait for build | 20-30 min | _________ |
| 2 | Deploy Runpod pod | 10-15 min | _________ |
| 3 | Upload model | 10-15 min | _________ |
| 4 | Start services | 5 min | _________ |
| 5 | Ingest documents | 10 min | _________ |
| 6 | Test backend | 10 min | _________ |
| 7 | Test frontend | 15 min | _________ |
| **Total** | | **1.5-2 hours** | _________ |

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

# Check port usage
lsof -i :8000
lsof -i :8080
lsof -i :19530
```

---

**Last Updated:** October 23, 2025
**Status:** Ready for Docker Hub setup and deployment
**Next Session:** Follow this checklist step-by-step for successful deployment
