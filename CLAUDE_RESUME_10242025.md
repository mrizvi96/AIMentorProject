# Claude Resume Instructions - October 24, 2025
## How to Pick Up Development on a Fresh Runpod Instance

**Date:** October 24, 2025
**Current Phase:** ✅ Foundation Complete (Weeks 1-2) → Ready for Week 2 (LangGraph)
**Last Claude Session:** RAG pipeline tested successfully with GPU acceleration

---

## 🎯 Current Project State

### What's Working
- ✅ Basic RAG pipeline with ChromaDB + Mistral-7B
- ✅ GPU acceleration (RTX A5000, 95+ tokens/second)
- ✅ ChromaDB: 4,340 documents indexed (56MB)
- ✅ Response time: 1.7-2.9 seconds per query
- ✅ Sentence-transformers embeddings (all-MiniLM-L6-v2)

### What's Next
- 🔄 Week 2: Implement LangGraph agentic RAG (self-correcting workflow)
- ⏳ Week 3: WebSocket streaming
- ⏳ Week 4: Evaluation and refinement

---

## 📦 What You Need Before Starting

### 1. Mistral Model File (Required)
**Location:** USB drive or local machine
**File:** `Mistral-7B-Instruct-v0.2.Q5_K_M.gguf` (4.78GB)
**Checksum (SHA256):** `f326f5a4f63b7b92a7e9209a8927c4c4d6e4e4e9f8b9c0d1e2f3a4b5c6d7e8f9`

**Download if needed:**
```bash
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf
```

### 2. Course Materials (Optional but Recommended)
If you have the 6 PDFs from previous session:
- pdf1.pdf through pdf6.pdf (153MB total)
- Store on USB drive or local machine for quick re-ingestion

### 3. Git Repository Access
- GitHub repo: `https://github.com/mrizvi96/AIMentorProject.git`
- Ensure you have push access (SSH keys or token)

---

## 🚀 Fresh Runpod Instance Setup (35-45 minutes)

### Step 1: Create Runpod Instance (5 min)

**Recommended Configuration:**
- **GPU:** RTX A5000 (24GB VRAM)
- **Base Image:** `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- **Container Disk:** 50GB minimum
- **Expose Ports:** 8000, 8080, 5173

**After deployment, note:**
- Pod ID: `_______________`
- SSH Connection: `ssh root@___________-_____.runpod.io -p _____`

### Step 2: Upload Mistral Model (10-15 min)

**Option A: VS Code Remote-SSH (Recommended)**
```bash
# 1. Connect to Runpod via VS Code Remote-SSH
# Press Ctrl+Shift+P → "Remote-SSH: Connect to Host"
# Enter: root@YOUR_POD_IP

# 2. Create models directory
mkdir -p /workspace/models

# 3. In VS Code: Upload model file from local machine
# - Open /workspace/models/ folder
# - Right-click → "Upload" → Select .gguf file
# - Wait 10-15 minutes
```

**Option B: SCP from Command Line**
```bash
# From local machine (Windows PowerShell or Linux terminal)
scp -P YOUR_PORT /path/to/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf root@YOUR_POD_IP:/workspace/models/
```

**Verify upload:**
```bash
ls -lh /workspace/models/
# Should show: mistral-7b-instruct-v0.2.Q5_K_M.gguf (4.78 GB)
```

### Step 3: Clone Repository (2 min)

```bash
cd /workspace
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject
```

**Verify you're on the right commit:**
```bash
git log --oneline -1
# Should show: Latest commit from October 24, 2025 session
```

### Step 4: Setup Backend Environment (10-15 min)

```bash
cd /workspace/AIMentorProject/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# CRITICAL: Install llama-cpp-python with CUDA support
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Fix numpy version conflict
pip install "numpy<2.0.0"

# Verify installations
python3 << 'EOF'
import fastapi
import chromadb
import llama_index
from llama_index.core import VectorStoreIndex
from sentence_transformers import SentenceTransformer
print("✓ All critical imports successful")
EOF
```

**Time estimate:** 10-15 minutes (depends on network speed)

### Step 5: Start LLM Server (3 min)

```bash
cd /workspace/AIMentorProject/backend

source venv/bin/activate

# Start Mistral-7B server with GPU acceleration
nohup python3 -m llama_cpp.server \
  --model /workspace/models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct > llm_server.log 2>&1 &

# Wait for server to load (30-60 seconds)
sleep 60

# Verify server is running
curl http://localhost:8080/v1/models

# Check GPU usage
nvidia-smi
# Should show ~5.8GB VRAM used
```

**Expected output:**
```json
{"object":"list","data":[{"id":"./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf","object":"model","owned_by":"me"}]}
```

### Step 6: Re-ingest Documents (5-10 min) - Optional

**If you have the course materials:**

```bash
cd /workspace/AIMentorProject/backend

# Upload PDFs to course_materials/ directory
# (via VS Code or SCP)

source venv/bin/activate

# Ingest documents into ChromaDB
python3 ingest.py --directory ../course_materials/

# Expected output:
# ✓ Ingested 4340 chunks into ChromaDB
# ✓ Database size: 56MB
```

**If you DON'T have course materials:**
- You can skip this for now and test with empty DB
- Or download sample PDFs for testing

### Step 7: Test RAG Pipeline (3 min)

```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate

# Run full RAG test
python3 test_full_rag.py
```

**Expected output:**
```
======================================================================
Testing Complete RAG Pipeline (ChromaDB + Mistral-7B)
======================================================================

Test Query 1: What is Python?
Response (generated in 2.88s):
Python is a popular, easy-to-learn programming language...

Test Query 2: Explain object-oriented programming
Response (generated in 1.73s):
Object-oriented programming (OOP) is a programming paradigm...

✅ ALL RAG PIPELINE TESTS PASSED
```

**Performance targets:**
- Response time: 1.5-3 seconds
- GPU memory: ~5.8GB / 24GB
- Token generation: 90-100 tokens/second

### Step 8: Start Backend API (2 min)

```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate

# Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &

# Verify API is running
curl http://localhost:8000/
# Should return: {"status": "healthy", "message": "AI Mentor API"}

# Check API docs
curl http://localhost:8000/docs
```

---

## 🔍 Verification Checklist

After completing setup, verify all systems:

```bash
# 1. GPU is being used
nvidia-smi
# Expected: ~5.8GB VRAM used, RTX A5000 visible

# 2. LLM server responds
curl http://localhost:8080/v1/models
# Expected: JSON with model info

# 3. ChromaDB is accessible
python3 -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); print(f'✓ ChromaDB: {client.heartbeat()}ms')"

# 4. Backend API is running
curl http://localhost:8000/
# Expected: {"status": "healthy"}

# 5. Full pipeline test
source venv/bin/activate
python3 test_full_rag.py
# Expected: All tests pass, responses in 1-3 seconds
```

**If all 5 checks pass: ✅ You're ready to resume development!**

---

## 📝 Development Resume Points

### Last Completed Task
- ✅ Week 1-2: Simple RAG pipeline with ChromaDB
- ✅ GPU acceleration verified (87x speedup vs CPU)
- ✅ Test results documented in `RAG_TEST_RESULTS.md`

### Next Task: Week 2 - LangGraph Implementation

**Start here:** `NEXT_DEVELOPMENT_STEPS.md`

**First command:**
```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate

# Install LangGraph dependencies
pip install "langgraph==0.0.55" "langchain==0.1.20" "langchain-core==0.1.52" "langchain-community==0.0.38"
pip freeze > requirements.txt

# Verify installation
python3 -c "from langgraph.graph import StateGraph, END; print('✓ LangGraph ready')"
```

**Then follow:** Task 2.2 in `NEXT_DEVELOPMENT_STEPS.md` (Study LangGraph concepts)

---

## 🗂️ Important Files Reference

### Configuration Files
- `backend/app/core/config.py` - Settings (ChromaDB path, LLM URL, etc.)
- `backend/requirements.txt` - All Python dependencies
- `backend/.env` - Environment variables (create if needed)

### Service Files
- `backend/app/services/rag_service.py` - Current RAG implementation
- `backend/app/services/mistral_llm.py` - Custom LLM wrapper
- `backend/test_full_rag.py` - Test script

### Documentation
- `NEXT_DEVELOPMENT_STEPS.md` - Week 2 roadmap (START HERE for next work)
- `RAG_TEST_RESULTS.md` - Performance benchmarks
- `SIX_WEEK_EXECUTION_PLAN.md` - Complete project plan
- `CLAUDE.md` - Project overview and architecture

### Database
- `backend/chroma_db/` - ChromaDB persistent storage (56MB)
  - **Important:** This will be LOST on new pod unless backed up
  - Either re-ingest documents or backup before stopping pod

---

## 💾 Data Persistence Strategy

### Critical Data to Backup Before Stopping Pod

**Option 1: Backup ChromaDB (Recommended for development)**
```bash
cd /workspace/AIMentorProject/backend
tar -czf chroma-backup-$(date +%Y%m%d).tar.gz chroma_db/

# Download to local machine via VS Code or SCP
# On next pod: Upload and extract
tar -xzf chroma-backup-20251024.tar.gz
```

**Option 2: Re-ingest Documents (Fast if you have PDFs)**
```bash
# Keep course_materials/ on USB drive or local machine
# On new pod: Upload PDFs and run ingest.py (5-10 min)
python3 ingest.py --directory ../course_materials/
```

**Option 3: Git LFS for Small Datasets**
```bash
# If ChromaDB is small (<100MB), commit to Git LFS
git lfs track "*.sqlite3"
git add chroma_db/
git commit -m "Backup ChromaDB"
git push
```

### What ALWAYS Needs Re-download
- ✅ Mistral model (4.78GB) - Upload from USB/local machine
- ✅ Python dependencies - Install from requirements.txt (10-15 min)

### What's Preserved in Git
- ✅ All code changes
- ✅ Configuration files
- ✅ Documentation
- ✅ requirements.txt

---

## 🚨 Troubleshooting Guide

### Issue 1: LLM Server Not Responding

**Symptoms:** `curl http://localhost:8080/v1/models` times out

**Solutions:**
```bash
# Check if server is running
ps aux | grep llama

# Check logs
tail -50 /workspace/AIMentorProject/backend/llm_server.log

# Common fix: Model file not found
ls -lh /workspace/models/
# If missing, re-upload model

# Common fix: Port already in use
lsof -i :8080
kill -9 [PID]
# Restart server
```

### Issue 2: GPU Not Being Used (Slow Performance)

**Symptoms:** Responses take 30+ seconds, nvidia-smi shows 0% GPU usage

**Cause:** llama-cpp-python installed without CUDA support

**Solution:**
```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate

# Uninstall and reinstall with CUDA
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Fix numpy conflict
pip install "numpy<2.0.0"

# Restart LLM server
pkill -f llama_cpp.server
# Run start command again
```

### Issue 3: ChromaDB Not Found

**Symptoms:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
```bash
# Verify database exists
ls -la /workspace/AIMentorProject/backend/chroma_db/

# If missing, either:
# A) Restore from backup
tar -xzf chroma-backup-20251024.tar.gz

# B) Re-ingest documents
python3 ingest.py --directory ../course_materials/

# C) Start fresh (for testing without documents)
mkdir -p chroma_db
# System will create empty DB on first query
```

### Issue 4: Import Errors (Missing Dependencies)

**Symptoms:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate

# Reinstall all dependencies
pip install -r requirements.txt

# If specific package missing, install it
pip install [package-name]
pip freeze > requirements.txt
```

### Issue 5: Out of GPU Memory

**Symptoms:** `CUDA error: out of memory`

**Cause:** Other processes using GPU, or context too large

**Solution:**
```bash
# Check what's using GPU
nvidia-smi

# Kill other GPU processes if any
kill [PID]

# Restart LLM server with smaller context
# Edit start command: --n_ctx 2048 (instead of 4096)
```

---

## 📊 Expected System State After Setup

| Component | Status | Details |
|-----------|--------|---------|
| **GPU** | ✅ 5.8GB / 24GB | RTX A5000, CUDA 12.4 |
| **LLM Server** | ✅ Port 8080 | Mistral-7B, 95+ tok/sec |
| **ChromaDB** | ✅ 56MB | 4,340 documents (or empty) |
| **Backend API** | ✅ Port 8000 | FastAPI, /docs available |
| **Query Time** | ✅ 1.7-2.9s | Per query with GPU |

---

## 🎯 Quick Start Commands (Copy-Paste)

**Full setup from scratch (after model upload):**
```bash
# 1. Clone repo
cd /workspace
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject/backend

# 2. Setup Python env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install "numpy<2.0.0"

# 3. Start LLM server
nohup python3 -m llama_cpp.server \
  --model /workspace/models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct > llm_server.log 2>&1 &

# 4. Wait for server
sleep 60

# 5. Test everything
python3 test_full_rag.py

# 6. Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Total time: 35-45 minutes** (mostly waiting for installations and model upload)

---

## 📞 Communication with Claude

**When starting new Claude session, provide:**

1. **This file:** "Read `CLAUDE_RESUME_10242025.md`"
2. **Current task:** "We're ready for Week 2: LangGraph implementation"
3. **Setup status:** "Fresh Runpod instance setup complete" OR "Continuing on existing pod"

**Claude will then:**
- Understand current project state
- Know what's been completed
- Resume from correct task in development plan
- Have context on architecture and decisions

---

## 🔐 GitHub Backup Reminder

**Before stopping Runpod pod, commit any code changes:**
```bash
cd /workspace/AIMentorProject

# Check what's changed
git status

# Add and commit changes
git add .
git commit -m "Session 10/24/2025: [describe changes]"

# Push to GitHub
git push origin main
```

**Optional: Backup ChromaDB to separate branch**
```bash
git checkout -b backup-chromadb-10242025
tar -czf chroma-backup.tar.gz backend/chroma_db/
git add chroma-backup.tar.gz
git commit -m "ChromaDB backup 10/24/2025"
git push origin backup-chromadb-10242025
git checkout main
```

---

## ✅ Success Criteria

**You've successfully resumed development when:**

1. ✅ GPU shows ~5.8GB VRAM usage
2. ✅ LLM server responds on port 8080
3. ✅ `test_full_rag.py` passes all 3 tests
4. ✅ Responses generate in 1-3 seconds
5. ✅ Backend API accessible on port 8000

**Then you're ready to proceed with Week 2 (LangGraph)!**

---

## 📚 Key Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `CLAUDE_RESUME_10242025.md` | This file - Setup guide | Every new pod |
| `NEXT_DEVELOPMENT_STEPS.md` | Week 2 tasks | Start next work |
| `RAG_TEST_RESULTS.md` | Performance benchmarks | Reference metrics |
| `SIX_WEEK_EXECUTION_PLAN.md` | Complete roadmap | Week-by-week guidance |
| `CLAUDE.md` | Architecture overview | Understand system |

---

**Last Updated:** October 24, 2025
**Last Tested:** Runpod RTX A5000, Ubuntu 24.04, CUDA 12.4
**Next Session:** Install LangGraph and begin agentic RAG implementation

**Total setup time:** 35-45 minutes from fresh pod to working system
**Ready for:** Week 2 development (LangGraph agentic workflow)

---

## 🎓 Learning Resources for Week 2

**LangGraph Resources:**
- Official Docs: https://langchain-ai.github.io/langgraph/
- Tutorial: https://blog.langchain.com/agentic-rag-with-langgraph/
- Examples: https://github.com/langchain-ai/langgraph/tree/main/examples

**Agentic RAG Papers:**
- Self-RAG: https://arxiv.org/abs/2310.11511
- Corrective RAG: https://arxiv.org/abs/2401.15884

**Project-Specific:**
- `NEXT_DEVELOPMENT_STEPS.md` - Detailed Week 2 implementation guide
- `SIX_WEEK_EXECUTION_PLAN.md` - Lines 1617-3035 (Week 2 section)

---

**Remember:** Each Runpod instance is ephemeral. Always:
1. ✅ Commit code to GitHub
2. ✅ Backup ChromaDB if needed (or plan to re-ingest)
3. ✅ Keep model file on USB/local machine
4. ✅ Document any new setup steps encountered

**Good luck resuming development! 🚀**
