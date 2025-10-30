# 🚀 Next Session - Start Here!

**Last Updated**: October 30, 2025
**Status**: ✅ System fully configured and saved to `/workspace`

---

## Quick Start After Pod Reset

### Option 1: Automated Startup (Recommended)
```bash
cd /workspace/AIMentorProject
./runpod_restart.sh
```
**Time**: ~5 minutes
**What it does**: Installs Python packages, starts all 3 services (LLM, Backend, Frontend)

### Option 2: Manual Startup
See detailed steps in `SETUP_COMPLETE.md`

---

## What's Been Completed

### ✅ Full System Setup
- [x] Downloaded Mistral-7B model (4.8GB) → in `/workspace/AIMentorProject/backend/models/`
- [x] Downloaded 6 CS textbooks (153MB) → in `/workspace/AIMentorProject/backend/course_materials/`
- [x] Ingested 7,838 chunks into ChromaDB → in `/workspace/AIMentorProject/backend/chroma_db/`
- [x] Tested both Simple RAG and Agentic RAG endpoints
- [x] Wired frontend to Simple RAG via HTTP
- [x] Everything committed to GitHub

### ✅ Architecture Validated
- **Simple RAG** (implemented): 2-3s latency, HTTP endpoint, sufficient for 80% queries
- **Agentic RAG** (available): 3-7s latency, self-correcting, better for complex queries
- Both endpoints working and tested

### ✅ Files in Persistent Storage (`/workspace`)
```
/workspace/AIMentorProject/
├── backend/
│   ├── models/mistral-7b-instruct-v0.2.Q5_K_M.gguf  # 4.8GB - persists!
│   ├── course_materials/*.pdf                       # 6 PDFs - persists!
│   ├── chroma_db/                                   # 7,838 chunks - persists!
│   └── venv/                                        # needs reinstall each reset
├── frontend/
│   └── node_modules/                                # needs reinstall each reset
└── runpod_restart.sh                                # ⭐ use this!
```

**What persists**: Model, course materials, vector database, all code
**What needs reinstall**: Python venv, node_modules (automated in script)

---

## Current System Architecture

```
Frontend (port 5173)
    ↓ HTTP POST
Backend API (port 8000)
    ↓
Simple RAG Service
    ↓
┌─────────────┴─────────────┐
↓                           ↓
Mistral-7B LLM         ChromaDB
(port 8080)            (7,838 chunks)
GPU: 5.8GB VRAM
```

**Current Mode**: Simple RAG (fast, reliable)
**Alternative Available**: Agentic RAG (self-correcting, slower)

---

## Accessing the Application

### After Running Restart Script

**Via VSCode Port Forwarding (Easiest)**:
1. In VSCode, open the **PORTS** tab (bottom panel)
2. Click "Forward a Port" → enter `5173`
3. Click the localhost URL that appears
4. You should see the AI Tutor UI!

**Via Runpod Public URL**:
1. Go to Runpod dashboard
2. Click your pod → Edit → TCP Port Mappings
3. Add ports: 5173 (Frontend), 8000 (Backend)
4. Access via: `https://<pod-id>-5173.proxy.runpod.net`

**Test Page**: http://localhost:5173/test.html

---

## API Endpoints Available

### Simple RAG (Currently Active)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Python?", "conversation_id": "test"}'
```
**Response time**: 2-3 seconds
**Quality**: High, grounded in source materials

### Agentic RAG (Also Available)
```bash
curl -X POST http://localhost:8000/api/chat-agentic \
  -H "Content-Type: application/json" \
  -d '{"message": "What is recursion?", "conversation_id": "test"}'
```
**Response time**: 3-7 seconds
**Features**: Query rewriting, document grading, self-correction

---

## Key Documentation Files

| File | Purpose |
|------|---------|
| `SETUP_COMPLETE.md` | Full system documentation, how to use |
| `CLAUDE_LOG.md` | Troubleshooting guide, error fixes |
| `backend/rag_comparison_results.md` | Simple vs Agentic RAG analysis |
| `Gemini_10302025.md` | Original plan that guided this setup |
| `runpod_restart.sh` | ⭐ Quick restart script |

---

## Common Tasks

### Start Services
```bash
cd /workspace/AIMentorProject
./runpod_restart.sh  # Starts everything
```

### Stop Services
```bash
pkill -f "llama_cpp.server"
pkill -f "uvicorn main:app"
pkill -f "vite dev"
```

### Check Status
```bash
# Running processes
ps aux | grep -E "(llama_cpp|uvicorn|vite)" | grep -v grep

# GPU usage
nvidia-smi

# Test endpoints
curl http://localhost:8000/
curl http://localhost:5173/
```

### View Logs
```bash
cd /workspace/AIMentorProject/backend
tail -f llm_server.log  # LLM server
tail -f backend.log     # Backend API

cd ../frontend
tail -f frontend.log    # Frontend dev server
```

---

## Next Development Steps

### Immediate (Access the App)
1. ✅ System is ready - just need to configure port forwarding in Runpod
2. Or use VSCode port forwarding (easier)
3. Test the UI end-to-end

### Short Term (Week 2)
1. **Evaluate System Performance**
   - Test with 20+ diverse questions
   - Measure accuracy and hallucination rates
   - Compare Simple vs Agentic RAG on same questions

2. **UI Enhancements**
   - Add sample questions UI
   - Show source documents inline
   - Add "Quick" vs "Detailed" mode selector

3. **Public Deployment**
   - Configure Runpod persistent ports
   - Set up proper authentication
   - Add rate limiting

### Medium Term (Weeks 3-4)
1. **Advanced Features**
   - Multi-turn conversations
   - Follow-up question handling
   - User feedback collection

2. **Optimization**
   - Response caching
   - Query history
   - Fine-tune retrieval parameters

---

## Troubleshooting

### "Services won't start"
```bash
cd /workspace/AIMentorProject
./runpod_restart.sh  # Should fix everything
```

### "Frontend won't load in browser"
- Make sure you're using VSCode port forwarding or Runpod public URL
- `localhost:5173` only works if you're on the Runpod machine itself
- Check: `curl http://localhost:5173/` should return HTML

### "Backend returns errors"
- Check logs: `tail -f backend/backend.log`
- Verify LLM server: `curl http://localhost:8080/v1/models`
- Restart services with the restart script

### "Out of VRAM"
- Current usage: 6.3GB / 24GB (26%)
- RTX A5000 has plenty of headroom
- If issues: check `nvidia-smi`

---

## Important Notes

⚠️ **After Pod Reset**:
- Everything in `/root` is LOST
- Everything in `/workspace` PERSISTS
- Run `./runpod_restart.sh` to get back up and running

✅ **What's Saved**:
- Model (4.8GB)
- Course materials (6 PDFs)
- Vector database (7,838 chunks)
- All code and configuration

⚙️ **What Needs Reinstall** (automated):
- Python venv and packages
- Node.js packages
- Services need to be restarted

---

## Git Repository

**Location**: https://github.com/mrizvi96/AIMentorProject
**Latest Commit**: feat: Complete fresh Runpod setup with Simple RAG MVP
**Branch**: main

All changes from this session are committed and pushed!

---

## Success Metrics

✅ **System Operational**: All 3 services running
✅ **GPU Accelerated**: 5.8GB VRAM, all layers offloaded
✅ **Database Ready**: 7,838 chunks indexed
✅ **Endpoints Tested**: Both Simple and Agentic RAG working
✅ **Frontend Wired**: HTTP connection to backend
✅ **Code Saved**: Committed to GitHub
✅ **Persistence**: Everything in /workspace

**You're ready to go! Just run the restart script and forward the ports.** 🚀
