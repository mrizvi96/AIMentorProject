# Runpod Quick Start Guide
**For AI Mentor Project - USB Drive Workflow**

## Problem Statement
Runpod instances are ephemeral and datacenter-specific. We need a system where:
1. **No repetitive model downloads** (4.8GB Mistral model takes 60+ minutes)
2. **Portable model storage** across different Runpod instances
3. **Quick startup** to get the LLM server running (~10-15 minutes)

---

## Solution: USB Drive Workflow

Instead of downloading the model from HuggingFace every time or building complex Docker images, we use a **portable USB drive** to store the model and upload it to each new Runpod instance.

**Benefits:**
- ✅ Model file always available on USB drive
- ✅ Upload from USB (~5-10 minutes) vs download from HuggingFace (~60+ minutes)
- ✅ Works across any Runpod instance (no datacenter dependency)
- ✅ Simple, reliable workflow

---

## Prerequisites

### On Your Local Machine
- USB drive with 10GB+ free space
- Mistral-7B-Instruct-v0.2.Q5_K_M.gguf (5.13 GB) stored on USB drive
- VS Code with Remote-SSH extension installed
- Windows 10/11 with PowerShell

### On Runpod
- GPU instance with RTX A5000 (24GB VRAM) or similar
- Base image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- SSH access enabled

---

## Quick Start Workflow

### Step 1: Start Runpod Instance

1. Go to Runpod dashboard
2. Deploy new pod:
   - **GPU:** RTX A5000 (24GB VRAM)
   - **Template:** `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
   - **Container Disk:** 50GB minimum
3. Wait for pod to start
4. Note the SSH connection details (IP address)

### Step 2: Connect via VS Code Remote-SSH

1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
3. Type "Remote-SSH: Connect to Host"
4. Enter: `root@[RUNPOD_IP]` (replace with your pod's IP)
5. Enter password when prompted
6. Wait for connection to establish

### Step 3: Upload Model from USB Drive

**Option A: Via VS Code (Recommended)**

1. In VS Code (connected to Runpod), open terminal: `` Ctrl+` ``
2. Create models directory:
   ```bash
   mkdir -p /workspace/models
   ```

3. On your Windows machine:
   - Plug in USB drive (appears as D: or E:)
   - Copy `Mistral-7B-Instruct-v0.2.Q5_K_M.gguf` from USB to `C:\temp\`

4. In VS Code:
   - Open Explorer sidebar (Ctrl+Shift+E)
   - Navigate to `/workspace/models/`
   - Right-click and select "Upload..."
   - Select the model file from `C:\temp\`
   - **Wait 5-10 minutes** for upload to complete

5. Verify upload:
   ```bash
   ls -lh /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf
   # Should show: 4.8G or 5.1G
   ```

**Option B: Via SCP (Command Line)**

```powershell
# From Windows PowerShell
# Copy model from USB to temp folder first
Copy-Item -Path "D:\Mistral-7B-Instruct-v0.2.Q5_K_M.gguf" -Destination "C:\temp\"

# Upload to Runpod via SCP
scp "C:\temp\Mistral-7B-Instruct-v0.2.Q5_K_M.gguf" root@[RUNPOD_IP]:/workspace/models/
```

### Step 4: Clone Repository and Setup

```bash
# On Runpod instance (via VS Code terminal)
cd /workspace

# Clone your repository
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject

# Make startup script executable
chmod +x start_llm_server.sh
```

### Step 5: Start LLM Server

```bash
# Run the automated startup script
./start_llm_server.sh
```

The script will:
- Install llama-cpp-python with CUDA support (~2-3 minutes)
- Start Mistral-7B server on port 8080
- Display server status and access URLs

**Total time: ~10-15 minutes** (mostly model upload)

---

## Testing the Setup

### Test 1: Verify LLM Server

```bash
# Check if server is running
curl http://localhost:8080/v1/models

# Expected output:
# {
#   "data": [
#     {
#       "id": "mistral-7b-instruct-v0.2.q5_k_m.gguf",
#       ...
#     }
#   ]
# }
```

### Test 2: Test Chat Completion

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello! What is Python?"}],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

You should see a JSON response with the AI's answer.

---

## Starting Additional Services

Once the LLM server is running, start the rest of your stack:

### Start Milvus Vector Database

```bash
cd /workspace/AIMentorProject

# Start Docker Compose services
docker-compose up -d

# Wait for services to be healthy (~90 seconds)
sleep 90

# Verify
docker-compose ps
# Should show: milvus-standalone, milvus-etcd, milvus-minio (all "Up")
```

### Start Backend API

```bash
cd /workspace/AIMentorProject/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server (in tmux for persistence)
tmux new-session -d -s backend "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# Check if running
curl http://localhost:8000/
# Should return: {"status": "AI Mentor API is running"}
```

### Check All Services

```bash
# LLM Server (port 8080)
curl -s http://localhost:8080/v1/models | jq

# Backend API (port 8000)
curl -s http://localhost:8000/ | jq

# Milvus (port 19530 - gRPC, no curl test)
docker-compose ps | grep milvus
```

---

## Workflow Summary

### First Time Setup (One-Time)
1. Download Mistral model to USB drive (if not already done)
2. Keep USB drive in safe place

### Every New Runpod Instance
1. Start Runpod pod (2 minutes)
2. Connect via VS Code Remote-SSH (1 minute)
3. Upload model from USB (5-10 minutes)
4. Clone repository (30 seconds)
5. Run `./start_llm_server.sh` (2-3 minutes)
6. Start Milvus and Backend (optional, 2-3 minutes)

**Total: 10-20 minutes** vs 60-90 minutes downloading from HuggingFace!

---

## Comparison: Old vs New Workflow

| Step | Old Workflow (HuggingFace Download) | New Workflow (USB Upload) |
|------|-------------------------------------|---------------------------|
| Model acquisition | Download from HF: 60+ min | Upload from USB: 5-10 min |
| Dependencies | Install llama-cpp-python: 2-3 min | Install llama-cpp-python: 2-3 min |
| Start server | 10 seconds | 10 seconds |
| **Total Time** | **60-65 minutes** | **10-15 minutes** |
| **Time Saved** | - | **50+ minutes** |

---

## Troubleshooting

### Model Upload Fails or Times Out

**Solution 1: Use SCP with compression**
```powershell
# From Windows PowerShell
scp -C "C:\temp\Mistral-7B-Instruct-v0.2.Q5_K_M.gguf" root@[RUNPOD_IP]:/workspace/models/
```

**Solution 2: Use tmux to keep upload alive**
```bash
# On Runpod, create tmux session
tmux new -s upload

# Then use scp from local machine
# If connection drops, reattach: tmux attach -s upload
```

### llama-cpp-python Installation Fails

**Check CUDA availability:**
```bash
nvidia-smi
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Reinstall with explicit CUDA support:**
```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install --no-cache-dir --force-reinstall "llama-cpp-python[server]"
```

### Server Won't Start - Port Already in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process
kill -9 [PID]

# Restart server
./start_llm_server.sh
```

### Model File Not Found

```bash
# Verify model location and name
ls -lh /workspace/models/

# The script expects:
# /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf

# If filename is different, create symlink:
ln -s /workspace/models/[ACTUAL_NAME].gguf /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf
```

---

## Data Persistence Strategy

### Challenge
Runpod volumes are ephemeral. When you stop the pod, **all data in /workspace is lost** (unless you have network storage).

### Solutions

#### Option A: Backup Milvus Data Before Stopping Pod

```bash
# Create backup
cd /workspace/AIMentorProject
tar -czf milvus-backup-$(date +%Y%m%d).tar.gz volumes/

# Upload to cloud storage (example: Google Drive, S3, etc.)
# Or download to local machine via VS Code

# On next pod startup, restore:
tar -xzf milvus-backup-20241016.tar.gz
```

#### Option B: Use Runpod Network Storage (if available)

```bash
# Check if network storage is available
ls -l /runpod-volume

# If yes, create symlink
ln -s /runpod-volume/ai-mentor/volumes /workspace/AIMentorProject/volumes
```

#### Option C: Re-ingest Documents (For Development)

```bash
# Keep course_materials in Git or on USB drive
# Re-run ingestion on each new pod (takes 5-10 min for small datasets)
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials/
```

---

## Advanced: Automated Full Startup Script

For convenience, you can create a single script that starts **all services** automatically.

Create `/workspace/AIMentorProject/runpod_full_startup.sh`:

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "AI Mentor Full Stack Startup"
echo "=========================================="

# Start LLM server
echo "1. Starting LLM server..."
./start_llm_server.sh &
LLM_PID=$!

# Start Milvus
echo "2. Starting Milvus..."
docker-compose up -d
sleep 90

# Setup backend
echo "3. Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

# Start backend in tmux
echo "4. Starting backend API..."
tmux kill-session -t backend 2>/dev/null || true
tmux new-session -d -s backend "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

cd ..

echo ""
echo "=========================================="
echo "Startup Complete!"
echo "=========================================="
echo "Services:"
echo "  - LLM Server: http://localhost:8080"
echo "  - Backend API: http://localhost:8000"
echo "  - Milvus gRPC: localhost:19530"
echo ""
echo "View logs:"
echo "  - LLM: Check terminal output"
echo "  - Backend: tmux attach -t backend"
echo "  - Milvus: docker-compose logs -f"
```

Make it executable and run:
```bash
chmod +x runpod_full_startup.sh
./runpod_full_startup.sh
```

---

## Next Steps

1. ✅ Complete model upload to Runpod
2. ✅ Start LLM server with `./start_llm_server.sh`
3. ✅ Start additional services (Milvus, Backend)
4. → Begin Week 1 development tasks
5. → Test the RAG pipeline with sample documents

---

## Summary

**USB Drive Workflow Benefits:**
- **Fast:** 10-15 min setup (vs 60+ min download)
- **Portable:** Works across any Runpod instance
- **Reliable:** No dependency on HuggingFace availability
- **Simple:** No complex Docker builds or registries

**Keep your USB drive safe** - it's your portable AI model storage that saves you 50+ minutes every time you start a new Runpod instance!
