# AI Mentor - Quick Start Guide

**⏱️ Total Time: ~15-20 minutes** (including model download)

## Prerequisites Checklist

- [ ] Runpod instance with RTX A5000 (24GB VRAM)
- [ ] Base image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- [ ] SSH access configured

## 🚀 5-Step Setup

### Step 1: Clone Repository (30 seconds)

```bash
cd /root
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject
```

### Step 2: Download Model (5-10 minutes)

```bash
mkdir -p /workspace/models
cd /workspace/models
wget -O Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
cd ~/AIMentorProject
```

**Verify download:**
```bash
ls -lh /workspace/models/
# Should show ~4.8GB file
```

### Step 3: Automated Setup (3-5 minutes)

```bash
./START_SERVICES.sh
```

This script will:
- ✅ Start Milvus vector database
- ✅ Create Python virtual environment
- ✅ Install all dependencies (backend + frontend)
- ✅ Check for course materials
- ✅ Optionally run data ingestion

**Note:** You'll be prompted to upload PDFs. Answer 'n' for now if you don't have materials ready.

### Step 4: Upload Course Materials

**Required:** Upload scholarly PDF documents to test the system.

```bash
# Create directory
mkdir -p /root/AIMentorProject/course_materials

# Upload via SCP (from your local machine)
scp /path/to/textbook.pdf root@RUNPOD_IP:/root/AIMentorProject/course_materials/

# Or use VS Code Remote-SSH:
# 1. Connect to Runpod via Remote-SSH
# 2. Navigate to course_materials/ folder
# 3. Right-click → Upload files
```

**Then ingest:**
```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials
```

### Step 5: Start Servers (3 terminals)

**Use tmux or separate SSH sessions:**

```bash
# Install tmux if needed
apt-get install -y tmux

# Create tmux session
tmux new -s aimentor
```

**Terminal 1 - LLM Server:**
```bash
cd /root/AIMentorProject
./start_llm_server.sh

# Wait for: "Uvicorn running on http://0.0.0.0:8080"
# Press Ctrl+B then D to detach
```

**Terminal 2 - Backend API:**
```bash
# Create new tmux window: Ctrl+B then C
cd /root/AIMentorProject/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Wait for: "Application startup complete"
# Press Ctrl+B then D to detach
```

**Terminal 3 - Frontend:**
```bash
# Create new tmux window: Ctrl+B then C
cd /root/AIMentorProject/frontend
npm run dev -- --host 0.0.0.0

# Wait for: "Local: http://localhost:5173"
# Press Ctrl+B then D to detach
```

## ✅ Verify Everything is Running

```bash
# Check all services
curl http://localhost:8080/v1/models  # LLM server
curl http://localhost:8000/           # Backend API
curl http://localhost:5173/           # Frontend (returns HTML)

# Check Milvus
docker-compose ps
# All should show "healthy"
```

## 🎉 Access the Application

**If using Runpod:**
1. Go to your Runpod instance page
2. Find the "Connect" button
3. Look for HTTP ports 5173, 8000, 8080
4. Use the provided public URLs

**Local access (via SSH tunnel):**
```bash
# On your local machine
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 root@RUNPOD_IP
```

Then open: http://localhost:5173

## 🧪 Test the System

1. **Open the frontend** (http://localhost:5173 or Runpod public URL)
2. **Ask a question** about your course materials
3. **Verify response** includes:
   - Relevant answer based on documents
   - Source citations
   - Relevance scores

**Example questions:**
- "Explain the concept of recursion"
- "What are the main data structures covered?"
- "Summarize the chapter on algorithms"

## 📊 Monitor Services

**View tmux sessions:**
```bash
tmux ls                    # List sessions
tmux attach -t aimentor    # Attach to session
# Ctrl+B then [0-2]        # Switch between windows
# Ctrl+B then D            # Detach
```

**View logs:**
```bash
# LLM server log
tail -f /tmp/llm_server.log  # If redirected

# Backend logs
cd /root/AIMentorProject/backend
# Logs appear in terminal

# Milvus logs
docker-compose logs -f milvus
```

## 🛑 Stop Services

```bash
# Stop all servers
tmux kill-session -t aimentor

# Stop Milvus
cd /root/AIMentorProject
docker-compose down

# Or stop Runpod instance (all data lost unless backed up)
```

## 🔄 Restart After Stop

```bash
cd /root/AIMentorProject

# Start Milvus
docker-compose up -d

# Restart servers (in tmux)
tmux new -s aimentor

# Window 1: LLM
./start_llm_server.sh

# Window 2: Backend (Ctrl+B then C to create)
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Window 3: Frontend (Ctrl+B then C to create)
cd frontend
npm run dev -- --host 0.0.0.0
```

## 🐛 Common Issues

### "Model not found"
```bash
# Check model exists
ls -lh /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf

# Re-download if needed
cd /workspace/models
wget -O Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
```

### "Cannot connect to Milvus"
```bash
# Check Milvus status
docker-compose ps

# Restart Milvus
docker-compose down
docker-compose up -d

# Wait 30 seconds for health check
sleep 30
docker-compose ps
```

### "CUDA out of memory"
```bash
# Check GPU usage
nvidia-smi

# Restart LLM server (frees memory)
# In tmux window 1:
# Ctrl+C to stop, then run again:
./start_llm_server.sh
```

### "Port already in use"
```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>

# Or for port 8080
lsof -i :8080
kill -9 <PID>
```

### "npm install fails"
```bash
# Clear npm cache
cd /root/AIMentorProject/frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## 💡 Pro Tips

1. **Use tmux** for persistent sessions (survives SSH disconnects)
2. **Save course_materials/** to external storage (Git LFS, cloud)
3. **Backup Milvus data** before stopping instance:
   ```bash
   tar -czf milvus-backup.tar.gz volumes/
   ```
4. **Monitor GPU** with `watch -n 1 nvidia-smi`
5. **Test incrementally** - verify each service before starting next

## 📚 Next Steps

1. ✅ System is running
2. 📖 Read [SETUP_STATUS.md](./SETUP_STATUS.md) for detailed documentation
3. 🔧 Customize settings in `backend/.env`
4. 📊 Explore API at http://localhost:8000/docs
5. 🚀 Begin Phase 2: Agentic RAG with LangGraph

---

**Need Help?**
- Check [README.md](./README.md) for full documentation
- Review [SETUP_STATUS.md](./SETUP_STATUS.md) for troubleshooting
- Open GitHub issue for bugs
