# 🚀 Runpod Deployment Checklist

**Complete setup guide for deploying AI Mentor on a fresh Runpod instance**

---

## ✅ Pre-Deployment (One-Time)

- ✅ GitHub repository created: https://github.com/mrizvi96/AIMentorProject
- ✅ All code committed and pushed
- ✅ Google Drive textbooks accessible (6 PDFs, 153MB)
- ✅ Download script created (`download_textbooks.sh`)

---

## 🎯 Deployment Steps (On Every New Runpod Instance)

### Step 1: Clone Repository (30 seconds)

```bash
cd /root
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject
```

---

### Step 2: Download Mistral Model (5-10 minutes)

```bash
mkdir -p /workspace/models
cd /workspace/models

wget -O Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# Verify download (should show ~4.8GB)
ls -lh Mistral-7B-Instruct-v0.2.Q5_K_M.gguf

cd /root/AIMentorProject
```

---

### Step 3: Download Course Materials (2-3 minutes)

```bash
# Download all 6 textbooks from Google Drive
./download_textbooks.sh

# Verify (should show 6 PDFs, ~153MB total)
ls -lh course_materials/
```

**Expected output:**
```
textbook_1.pdf  39M
textbook_2.pdf  5.3M
textbook_3.pdf  41M
textbook_4.pdf  23M
textbook_5.pdf  39M
textbook_6.pdf  8.3M
```

---

### Step 4: Start Milvus Vector Database (1-2 minutes)

```bash
# Start Docker daemon
systemctl start docker

# Start Milvus containers
docker-compose up -d

# Wait for services to be healthy (~30-60 seconds)
sleep 30
docker-compose ps

# All services should show "healthy"
```

---

### Step 5: Setup Backend Environment (3-5 minutes)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# This installs:
# - FastAPI, Uvicorn
# - LlamaIndex + Milvus integration
# - sentence-transformers
# - PyMuPDF
# - llama-cpp-python (with CUDA)
# Takes ~3-5 minutes
```

---

### Step 6: Ingest Course Materials (5-10 minutes)

```bash
# Make sure you're in backend/ with venv activated
cd /root/AIMentorProject/backend
source venv/bin/activate

# Run ingestion script
python ingest.py --directory ../course_materials
```

**What happens:**
1. Loads all 6 PDFs from `course_materials/`
2. Splits into 512-token chunks with 50-token overlap
3. Generates embeddings using sentence-transformers
4. Stores in Milvus vector database
5. **Time:** ~5-10 minutes for 153MB of PDFs

**Expected output:**
```
Loading documents from ../course_materials...
Found 6 PDF files
Loaded 6 documents
Created XXX chunks from 6 documents
Generating embeddings and storing in Milvus...
Progress: 10/XXX chunks processed
...
✓ Document ingestion complete!
Total documents: 6
Total chunks: XXX
Collection: course_materials
```

---

### Step 7: Start LLM Server (Terminal 1)

```bash
# Install tmux for managing multiple terminals
apt-get install -y tmux

# Start tmux session
tmux new -s aimentor

# Start LLM server
cd /root/AIMentorProject
./start_llm_server.sh
```

**Expected output:**
```
✓ Model file found: /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf
Activating Python virtual environment...
Installing llama-cpp-python with CUDA support...
✓ Installation complete

Starting Mistral-7B Server on port 8080
...
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

**Detach from tmux:** Press `Ctrl+B` then `D`

---

### Step 8: Start Backend API (Terminal 2)

```bash
# Attach to tmux and create new window
tmux attach -t aimentor
# Press Ctrl+B then C to create new window

cd /root/AIMentorProject/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/root/AIMentorProject/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Detach:** `Ctrl+B` then `D`

---

### Step 9: Start Frontend (Terminal 3)

```bash
# Attach to tmux and create new window
tmux attach -t aimentor
# Press Ctrl+B then C to create new window

cd /root/AIMentorProject/frontend
npm run dev -- --host 0.0.0.0
```

**Expected output:**
```
VITE v5.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: http://0.0.0.0:5173/
➜  press h + enter to show help
```

**Detach:** `Ctrl+B` then `D`

---

### Step 10: Verify Everything is Running

```bash
# Check all services
curl http://localhost:8080/v1/models   # LLM server
curl http://localhost:8000/            # Backend API
curl http://localhost:5173/            # Frontend

# Check Milvus
docker-compose ps
# All should show "healthy"

# Check tmux sessions
tmux ls
# Should show: aimentor: 3 windows
```

---

## 🎉 Access the Application

### Option A: Local Access (via SSH tunnel)

On your local laptop:
```bash
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 root@RUNPOD_IP
```

Then open: http://localhost:5173

### Option B: Runpod Public URL

1. Go to your Runpod dashboard
2. Click on your pod
3. Find "Connect" section
4. Look for HTTP ports: 5173, 8000, 8080
5. Use the public URLs provided

---

## 🧪 Test the System

### Test 1: Ask a Simple Question

Open http://localhost:5173 and ask:
```
"What topics are covered in these textbooks?"
```

Should return a summary based on your 6 PDFs.

### Test 2: Specific Technical Question

```
"Explain how binary search trees work"
```

Should retrieve relevant chunks and explain based on textbook content.

### Test 3: Check Sources

Verify that responses include:
- ✅ Source documents with filenames
- ✅ Relevance scores
- ✅ Text snippets from PDFs

---

## 📊 Monitoring

### View Logs

```bash
# Attach to tmux
tmux attach -t aimentor

# Navigate between windows
# Ctrl+B then 0 (LLM server)
# Ctrl+B then 1 (Backend)
# Ctrl+B then 2 (Frontend)

# Detach: Ctrl+B then D
```

### Check GPU Usage

```bash
watch -n 1 nvidia-smi
```

### Check Milvus Status

```bash
docker-compose logs -f milvus
```

---

## 🛑 Stopping Services

```bash
# Stop all servers
tmux kill-session -t aimentor

# Stop Milvus
cd /root/AIMentorProject
docker-compose down
```

---

## 🔄 Restarting After Stop

```bash
# Start Milvus
cd /root/AIMentorProject
docker-compose up -d

# Restart tmux session and servers
tmux new -s aimentor

# Window 1: LLM Server
./start_llm_server.sh
# Ctrl+B then D

# Window 2: Backend
tmux attach -t aimentor && Ctrl+B then C
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# Ctrl+B then D

# Window 3: Frontend
tmux attach -t aimentor && Ctrl+B then C
cd frontend && npm run dev -- --host 0.0.0.0
# Ctrl+B then D
```

---

## ⏱️ Time Breakdown

| Step | Time | Can Run Parallel? |
|------|------|-------------------|
| Clone repo | 30s | - |
| Download model | 5-10 min | ✅ Can run while setting up |
| Download textbooks | 2-3 min | ✅ Can run with model |
| Start Milvus | 1-2 min | - |
| Setup backend | 3-5 min | ✅ Can run during model download |
| Ingest PDFs | 5-10 min | ❌ Needs Milvus running |
| Start servers | 1-2 min | - |

**Total Sequential Time:** ~20-30 minutes
**Optimized Parallel Time:** ~15-20 minutes

---

## ✅ Success Checklist

- [ ] Repository cloned
- [ ] Mistral model downloaded (4.8GB)
- [ ] All 6 textbooks downloaded (153MB)
- [ ] Milvus running (docker-compose ps shows healthy)
- [ ] Backend venv created and dependencies installed
- [ ] PDFs ingested into Milvus (no errors)
- [ ] LLM server running on port 8080
- [ ] Backend API running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can access UI in browser
- [ ] Test query returns relevant results with sources

---

## 🐛 Troubleshooting

### Model not found
```bash
ls -lh /workspace/models/
# Should show Mistral-7B-Instruct-v0.2.Q5_K_M.gguf (~4.8GB)
# Re-run download if missing
```

### Textbook download fails
```bash
# Re-run download script
./download_textbooks.sh
# Or download individual files manually
```

### Milvus won't start
```bash
docker-compose down
docker-compose up -d
sleep 30
docker-compose ps
```

### Ingestion fails
```bash
# Check Milvus is running
docker-compose ps

# Check PDFs exist
ls -lh course_materials/

# Try with verbose output
cd backend && source venv/bin/activate
python ingest.py --directory ../course_materials
```

### GPU out of memory
```bash
# Check GPU usage
nvidia-smi

# Restart LLM server to free memory
# In tmux window 0:
# Ctrl+C to stop, then run again:
./start_llm_server.sh
```

---

## 📚 Documentation Reference

- **QUICKSTART.md** - Fast 5-step setup guide
- **README.md** - Complete technical documentation
- **SETUP_STATUS.md** - Implementation status and details
- **UPLOAD_TEXTBOOKS_GUIDE.md** - Alternative upload methods
- **GITHUB_BACKUP_COMPLETE.md** - Backup verification

---

**Ready to deploy!** Follow these steps on your Runpod instance and you'll have a fully functional AI Mentor system in ~15-20 minutes.
