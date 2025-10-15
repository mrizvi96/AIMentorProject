# AI Mentor Project - Quick Reference Card

## 📋 File Guide

| File | What It Does |
|------|--------------|
| `RUNPOD_QUICK_START.md` | **START HERE** - Complete Runpod setup guide |
| `runpod_startup.sh` | **RUN THIS** - Automated startup script |
| `SIX_WEEK_EXECUTION_PLAN.md` | Week-by-week development roadmap |
| `CLAUDE.md` | Project overview for Claude Code |
| `WEEKS_1-2_SUMMARY.md` | Summary of storage integration changes |
| `plan for storage.txt` | Original storage problem statement |

---

## 🚀 Quick Commands

### First Time Setup (One-Time, ~2-3 hours)
```bash
# On LOCAL MACHINE - Build Docker image with model
mkdir ~/ai-mentor-docker-build && cd ~/ai-mentor-docker-build
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.q5_k_m.gguf
# Create Dockerfile (see RUNPOD_QUICK_START.md)
docker build -t YOUR_USERNAME/ai-mentor-llm:v1 .
docker push YOUR_USERNAME/ai-mentor-llm:v1

# On RUNPOD - Create custom template
apt-get install -y nodejs npm docker.io
npm install -g @anthropic-ai/claude-code
docker pull YOUR_USERNAME/ai-mentor-llm:v1
# Save as "ai-mentor-ready-v1" template in Runpod UI
```

---

### Every Time Startup (~3-5 minutes)
```bash
# 1. Launch Runpod pod from "ai-mentor-ready-v1" template

# 2. SSH and clone
ssh root@<POD_IP>
cd /workspace
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject

# 3. Run startup script
./runpod_startup.sh

# 4. Access services
# Backend API: http://<POD_IP>:8000
# LLM Server: http://<POD_IP>:8080
```

---

## 🔧 Common Operations

### View Service Logs
```bash
# API logs (tmux)
tmux attach -t api

# LLM logs (Docker)
docker logs ai-mentor-llm

# Milvus logs
docker-compose logs -f milvus
```

### Restart Services
```bash
# Restart all Docker services
docker-compose restart

# Restart just LLM
docker restart ai-mentor-llm

# Restart API (kill tmux and re-run script)
tmux kill-session -t api
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Stop Everything
```bash
docker-compose down
tmux kill-session -t api
```

---

## 🗄️ Data Management

### Backup Milvus Data
```bash
tar -czf milvus-backup-$(date +%Y%m%d).tar.gz volumes/
# Upload to cloud storage
```

### Restore Milvus Data
```bash
# Download backup
tar -xzf milvus-backup-YYYYMMDD.tar.gz
./runpod_startup.sh
```

### Re-ingest Documents
```bash
cd backend
source venv/bin/activate
python ingest.py --directory ../course_materials
```

---

## 🔍 Health Checks

### Check All Services
```bash
# Quick status
curl http://localhost:8000/api/health | jq

# Detailed checks
docker-compose ps                    # Milvus stack
curl http://localhost:8080/v1/models | jq  # LLM
curl http://localhost:8000/          # Backend API
nvidia-smi                           # GPU
```

---

## 📊 Week 1-2 Focus Areas

### Week 1 (Simple RAG)
- **Goal:** Basic question-answering system
- **Key files:** `backend/app/services/simple_rag.py`, `backend/app/api/chat.py`
- **Deliverable:** Working `/api/chat` endpoint

### Week 2 (Continue Simple RAG + Frontend)
- **Goal:** Complete MVP with UI
- **Key files:** `frontend/src/lib/components/`, `frontend/src/routes/+page.svelte`
- **Deliverable:** End-to-end chat interface

---

## ⏱️ Time Saved

| Task | Before | After | Savings |
|------|--------|-------|---------|
| Runpod setup | 60+ min | 5 min | **55 min** |
| Model download | 20 min | 0 min | **20 min** |
| Dependency install | 15 min | 2 min | **13 min** |
| Service startup | 10 min | 2 min | **8 min** |
| **Total per session** | **105 min** | **9 min** | **96 min** |

---

## 🆘 Troubleshooting

### "Port already in use"
```bash
# Find process using port
lsof -i :8080
lsof -i :8000

# Kill process
kill -9 <PID>
```

### "GPU not detected"
```bash
# Check GPU
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

### "Docker daemon not running"
```bash
systemctl start docker
systemctl enable docker
```

### "Milvus not responding"
```bash
# Wait longer (needs 90+ seconds)
sleep 60
docker-compose ps

# Check logs
docker-compose logs milvus

# Restart
docker-compose restart
```

---

## 📝 Next Steps

1. ✅ Complete one-time Docker image build
2. ✅ Create custom Runpod template
3. ✅ Test startup script
4. → Begin Week 1 development tasks
5. → Follow `SIX_WEEK_EXECUTION_PLAN.md`

---

**Questions?** See `RUNPOD_QUICK_START.md` for detailed instructions.
