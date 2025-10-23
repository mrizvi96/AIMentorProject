# AI Mentor - Runpod Deployment with Milvus Lite

## Overview

This guide explains how to deploy AI Mentor on Runpod GPU instances using **Milvus Lite** instead of Docker-based Milvus. This approach eliminates the Docker-in-Docker limitation and simplifies deployment.

**Key Changes:**
- ✅ No Docker/docker-compose required for Milvus
- ✅ Milvus Lite uses file-based storage (SQLite backend)
- ✅ Simpler setup - just clone repo and run script
- ✅ Data persists in `backend/milvus_data/` directory
- ✅ Can commit small databases to Git for portability

---

## Why Milvus Lite?

### Problem with Docker-based Milvus
- Runpod GPU pods don't support Docker-in-Docker
- Can't run `docker-compose` inside the pod
- Would need complex workarounds or pre-built images

### Solution: Milvus Lite
- **File-based vector database** (no server needed)
- Embedded in your Python application
- Stores data in local SQLite file: `backend/milvus_data/ai_mentor.db`
- Same API as full Milvus (code mostly unchanged)
- Perfect for development and moderate workloads

### Trade-offs
| Feature | Full Milvus (Docker) | Milvus Lite (File-based) |
|---------|----------------------|--------------------------|
| Setup complexity | High (docker-compose) | Low (Python package) |
| Performance | Excellent (distributed) | Good (single-node) |
| Scalability | High (multi-node) | Moderate (single file) |
| Data size | Unlimited | ~100K-1M documents |
| Deployment | Docker required | No external dependencies |
| **Works on Runpod?** | ❌ No (Docker-in-Docker issue) | ✅ Yes |

---

## Quick Start

### Prerequisites
- Runpod GPU instance (RTX A5000 or similar)
- Base image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- SSH access to the pod

### Step-by-Step Deployment

#### 1. Start Runpod Instance
```bash
# From Runpod dashboard:
# - GPU: RTX A5000 (24GB VRAM)
# - Template: runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
# - Container Disk: 50GB minimum
# - Expose Ports: 8000, 8080
```

#### 2. Connect via SSH
```bash
# From your local machine
ssh root@[RUNPOD_IP] -p [RUNPOD_PORT]

# Or use VS Code Remote-SSH extension (recommended)
```

#### 3. Clone Repository
```bash
cd /workspace
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject
```

#### 4. Run Startup Script
```bash
./runpod_simple_startup.sh
```

**This script will:**
1. Download Mistral model (~30 min, only first time)
2. Setup Python environment
3. Install dependencies (including Milvus Lite)
4. Start LLM server in tmux
5. Start Backend API in tmux

**Total time:** ~35-40 minutes first run, ~5 minutes subsequent runs

#### 5. Ingest Course Materials (First Time Only)
```bash
cd backend
source venv/bin/activate
python ingest.py --directory ../course_materials/
```

This creates `backend/milvus_data/ai_mentor.db` with embedded course content.

#### 6. Test the System
```bash
# Test backend
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is Python?", "conversation_id": "test"}' | jq

# Expected: JSON response with AI answer and source documents
```

---

## File Structure

```
AIMentorProject/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py          # Updated: milvus_uri instead of host/port
│   │   └── services/
│   │       └── rag_service.py     # Updated: Uses Milvus Lite
│   ├── ingest.py                  # Updated: Uses Milvus Lite
│   ├── milvus_data/               # NEW: Milvus Lite data directory
│   │   └── ai_mentor.db           # SQLite database file (created after ingestion)
│   ├── requirements.txt           # Already has milvus package
│   └── venv/
├── frontend/
│   └── ... (unchanged)
├── runpod_simple_startup.sh       # NEW: Simplified startup script
└── docker-compose.yml             # DEPRECATED: No longer needed
```

---

## Data Persistence Strategy

### Challenge
Runpod pods are ephemeral - data is lost when pod stops.

### Solutions

#### Option 1: Commit Small Databases to Git (Recommended for Development)
```bash
# After ingesting documents
cd /workspace/AIMentorProject
git add backend/milvus_data/
git commit -m "Add ingested course materials (Milvus Lite DB)"
git push origin main

# On next Runpod instance:
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
./runpod_simple_startup.sh
# Database is already there, no need to re-ingest!
```

**Best for:**
- Small datasets (<100 MB)
- Development/testing
- Quick iteration

**Limitations:**
- Git has 100 MB file size limit per file
- Large databases will slow down git operations

#### Option 2: Backup and Restore Manually
```bash
# Before stopping pod - create backup
cd /workspace/AIMentorProject
tar -czf milvus-backup-$(date +%Y%m%d).tar.gz backend/milvus_data/

# Download to local machine (from local machine):
scp -P [PORT] root@[IP]:/workspace/AIMentorProject/milvus-backup-*.tar.gz ./backups/

# On next pod - upload and restore
scp -P [PORT] ./backups/milvus-backup-*.tar.gz root@[IP]:/workspace/AIMentorProject/
ssh root@[IP] -p [PORT]
cd /workspace/AIMentorProject
tar -xzf milvus-backup-*.tar.gz
```

**Best for:**
- Large datasets (>100 MB)
- Occasional updates
- Production-like testing

#### Option 3: Re-ingest on Each Instance
```bash
# Keep course_materials/ in Git
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
./runpod_simple_startup.sh
cd backend && source venv/bin/activate
python ingest.py --directory ../course_materials/
```

**Best for:**
- Frequently changing documents
- Testing ingestion pipeline
- Small document sets (< 5-10 min ingestion time)

---

## Configuration

### Milvus Lite Settings

In `backend/app/core/config.py`:

```python
# Milvus Lite Configuration (file-based, no Docker needed)
milvus_uri: str = "./milvus_data/ai_mentor.db"  # Local SQLite-based storage
milvus_collection_name: str = "course_materials"
```

**To change storage location:**
```python
# Relative path (from backend/ directory)
milvus_uri: str = "./milvus_data/ai_mentor.db"

# Absolute path
milvus_uri: str = "/workspace/persistent/milvus/ai_mentor.db"

# In-memory (data lost on restart - for testing only)
milvus_uri: str = ":memory:"
```

### Environment Variables

Create `backend/.env` for custom settings:

```bash
# LLM Configuration
LLM_BASE_URL=http://localhost:8080/v1
LLM_MODEL_NAME=mistral-7b-instruct-v0.2.q5_k_m.gguf
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512

# Milvus Lite Configuration
MILVUS_URI=./milvus_data/ai_mentor.db
MILVUS_COLLECTION_NAME=course_materials

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=3
```

---

## Troubleshooting

### Milvus Lite Issues

#### Error: "Permission denied" when creating database file
```bash
# Solution: Ensure directory exists and is writable
cd /workspace/AIMentorProject/backend
mkdir -p milvus_data
chmod 755 milvus_data
```

#### Error: "Database is locked"
```bash
# Solution: Only one process can access the database
# Kill existing backend server
tmux kill-session -t backend
# Remove lock file
rm -f backend/milvus_data/ai_mentor.db-wal
rm -f backend/milvus_data/ai_mentor.db-shm
# Restart
cd /workspace/AIMentorProject
./runpod_simple_startup.sh
```

#### Error: "Collection not found" when querying
```bash
# Solution: Run ingestion first
cd backend && source venv/bin/activate
python ingest.py --directory ../course_materials/
```

### General Issues

#### LLM Server Won't Start
```bash
# Check if model file exists
ls -lh /workspace/models/mistral-7b-instruct-v0.2.Q5_K_M.gguf

# Check tmux logs
tmux attach -t llm
# (Ctrl+B then D to detach)

# Restart manually
tmux kill-session -t llm
cd /workspace/AIMentorProject
source backend/venv/bin/activate
python3 -m llama_cpp.server \
    --model /workspace/models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
    --n_gpu_layers -1 \
    --n_ctx 4096 \
    --host 0.0.0.0 \
    --port 8080 \
    --chat_format mistral-instruct
```

#### Backend API Errors
```bash
# Check backend logs
tmux attach -t backend

# Check if Milvus Lite database exists
ls -lh backend/milvus_data/

# Test database connection
cd backend && source venv/bin/activate
python -c "from milvus import default_server; default_server.start(); print('Milvus Lite OK')"
```

---

## Testing Checklist

### ✅ Fresh Runpod Instance Test
- [ ] Clone repository
- [ ] Run `./runpod_simple_startup.sh`
- [ ] Model downloads successfully (~30 min)
- [ ] LLM server starts (tmux session: llm)
- [ ] Backend API starts (tmux session: backend)
- [ ] `curl http://localhost:8080/v1/models` returns JSON
- [ ] `curl http://localhost:8000/` returns API status

### ✅ Ingestion Test
- [ ] `cd backend && source venv/bin/activate`
- [ ] `python ingest.py --directory ../course_materials/`
- [ ] Milvus Lite database created: `ls backend/milvus_data/ai_mentor.db`
- [ ] No errors during ingestion
- [ ] Collection stats show documents: `curl http://localhost:8000/api/chat/stats`

### ✅ Query Test
- [ ] Send test query: `curl -X POST http://localhost:8000/api/chat -H 'Content-Type: application/json' -d '{"message": "What is Python?"}'`
- [ ] Response includes AI-generated answer
- [ ] Response includes source documents
- [ ] Relevance scores present

### ✅ Data Persistence Test
- [ ] Commit database to Git: `git add backend/milvus_data/ && git commit && git push`
- [ ] Stop pod
- [ ] Start new pod
- [ ] Clone repository (database already present)
- [ ] Run startup script
- [ ] Query works without re-ingesting

---

## Performance Considerations

### Milvus Lite Limits
- **Recommended:** Up to 100K-1M small documents
- **Maximum database size:** ~10 GB (SQLite limit is 281 TB, but practical limit is lower)
- **Concurrent queries:** Limited (single-file locking)

### When to Upgrade to Full Milvus
Consider full Milvus (Docker-based) if:
- Dataset > 1M documents
- Database file > 10 GB
- Need distributed queries
- Multiple concurrent users (>100)
- Production deployment

For those cases, deploy Milvus on a separate server (not Runpod pod) and connect remotely.

---

## Frontend Connection

### Update Frontend API URL

Edit `frontend/src/lib/api.ts`:

```typescript
// Change from localhost to Runpod public URL
const API_BASE_URL = 'https://[POD-ID]-8000.runpod.io';
```

### Test Frontend Locally

```bash
# On your local machine (not Runpod)
cd frontend
npm install
npm run dev

# Open browser to: http://localhost:5173
```

Frontend connects to Runpod backend via public URL.

---

## Comparison: Old vs New Workflow

| Aspect | Old (Docker Milvus) | New (Milvus Lite) |
|--------|---------------------|-------------------|
| **Docker required** | ✅ Yes (docker-compose) | ❌ No |
| **Setup complexity** | High (volumes, networks) | Low (Python package) |
| **Works on Runpod** | ❌ No (Docker-in-Docker issue) | ✅ Yes |
| **Startup time** | ~90 sec (Milvus startup) | ~5 sec (file open) |
| **Data persistence** | Backup volumes | Commit to Git or backup file |
| **Scalability** | High (distributed) | Moderate (single-file) |
| **Performance** | Excellent | Good (sufficient for dev/testing) |

---

## Summary

**Milvus Lite Benefits:**
- ✅ No Docker-in-Docker issues
- ✅ Simpler deployment (clone & run script)
- ✅ Faster startup (no container overhead)
- ✅ Easy data persistence (commit to Git)
- ✅ Perfect for development and testing

**Workflow:**
1. Clone repo on fresh Runpod instance
2. Run `./runpod_simple_startup.sh` (downloads model + starts services)
3. Ingest documents once: `python ingest.py`
4. Commit database to Git: `git add backend/milvus_data/ && git push`
5. Next time: Just clone and run startup script (database already there!)

**Estimated Time:**
- First run: ~35-40 minutes (model download)
- Subsequent runs: ~5 minutes (no download needed)
- With database in Git: ~3 minutes (no ingestion needed)

---

**Happy developing! 🚀**

For questions or issues, check the troubleshooting section or open a GitHub issue.
