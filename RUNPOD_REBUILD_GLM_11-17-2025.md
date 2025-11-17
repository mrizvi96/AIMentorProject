# RUNPOD REBUILD GLM - Complete Fresh Instance Setup Guide

**Date:** 2025-11-17
**Purpose:** Rebuild AI Mentor from scratch on fresh Runpod instance
**Target Environment:** Runpod RTX A5000 (24GB VRAM)
**Final Result:** Working AI Mentor at http://localhost:5173/

---

## 🚀 Prerequisites

### Fresh Runpod Instance Requirements
- **GPU Template:** `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- **GPU:** RTX A5000 (24GB VRAM)
- **Storage:** Minimum 50GB
- **Network:** Public IP for GitHub access

### Required Software (already in template)
- CUDA 12.8.1
- PyTorch 2.8.0
- Python 3.x
- Docker & Docker Compose
- Ubuntu 24.04

---

## 📋 Step-by-Step Rebuild Process

### Step 1: Instance Setup and SSH Configuration

```bash
# SSH into your fresh Runpod instance
# Note: VS Code Remote-SSH works best for development

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential tools if missing
sudo apt install -y git curl wget htop tmux vim

# Verify Docker is available
docker --version
docker-compose --version
```

### Step 2: Clone Repository and Navigate

```bash
# Clone the main repository
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject

# Verify we're in the right place
pwd  # Should show /root/AIMentorProject or similar
ls  # Should show backend/, frontend/, docker-compose.yml, etc.
```

### Step 3: Download Required Models

```bash
# Create models directory
mkdir -p backend/models
cd backend/models

# Download Mistral-7B-Instruct model (Q5_K_M quantization)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.q5_k_m.gguf

# Verify download
ls -lh mistral-7b-instruct-v0.2.q5_k_m.gguf
# Should be ~4.8GB

cd ../..
```

### Step 4: Backend Environment Setup

```bash
cd backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install "fastapi[all]" \
            "uvicorn[standard]" \
            "python-dotenv" \
            "pymilvus" \
            "llama-index" \
            "langgraph" \
            "llama-cpp-python[server]" \
            "PyMuPDF"

# Verify installation
pip list | grep -E "(fastapi|pymilvus|llama-index|langgraph|llama-cpp)"

cd ..
```

### Step 5: Start Milvus Vector Database

```bash
# From project root directory
docker-compose up -d

# Wait for services to be ready (usually 30-60 seconds)
docker-compose ps

# Verify all containers are running
# Should show etcd, minio, milvus-standalone all as "Up"

# Test Milvus connection
curl http://localhost:9091/health
```

### Step 6: Start LLM Inference Server

```bash
cd backend

# Activate virtual environment if not already active
source venv/bin/activate

# Start llama.cpp server in background
nohup python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.q5_k_m.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct \
  > llm_server.log 2>&1 &

# Wait for server to initialize (30-60 seconds)
sleep 45

# Test LLM server
curl http://localhost:8080/v1/models
# Should return JSON with model info

# Check if server is running properly
ps aux | grep llama_cpp

cd ..
```

### Step 7: Start FastAPI Backend

```bash
cd backend

# Activate virtual environment if not already active
source venv/bin/activate

# Start FastAPI server in tmux session
tmux new-session -d -s 'fastapi' "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# Wait for FastAPI to start
sleep 10

# Test FastAPI health endpoint
curl http://localhost:8000/
# Should return {"status": "healthy", "message": "AI Mentor API is running"}

# Test chat endpoint (should return error about missing data, which is expected)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "conversation_id": "test"}'

cd ..
```

### Step 8: Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# If this fails, ensure Node.js 16+ is available
# On Runpod, might need: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
# sudo apt-get install -y nodejs

# Verify installation
npm run lint

cd ..
```

### Step 9: Start Frontend Development Server

```bash
cd frontend

# Start dev server in another tmux session
tmux new-session -d -s 'frontend' "npm run dev -- --host 0.0.0.0 --port 5173"

# Wait for dev server to start
sleep 15

# Test frontend is accessible
curl http://localhost:5173/
# Should return HTML content

cd ..
```

### Step 10: Verify Complete System

```bash
# Check all services are running
tmux ls
# Should show 'fastapi' and 'frontend' sessions

# Test backend health
curl http://localhost:8000/

# Test LLM server
curl http://localhost:8080/v1/models

# Check Milvus status
docker-compose ps

# Test frontend accessibility
curl -I http://localhost:5173/
# Should return 200 OK
```

---

## 🔗 Access Your AI Mentor

**Primary Access:** http://localhost:5173/

### SSH Port Forwarding (for local access)
```bash
# From your local machine terminal:
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 -L 8080:localhost:8080 root@YOUR_RUNPOD_IP

# Then access http://localhost:5173/ in your local browser
```

### Direct Runpod Access
If your Runpod instance has a public URL, access directly:
`http://YOUR_RUNPOD_IP:5173/`

---

## 🧪 Quick System Test

1. **Open Browser:** Navigate to http://localhost:5173/
2. **Send Test Message:** Type "Hello, how does this system work?"
3. **Expected Response:** Should see AI response about educational tutoring (may mention no documents loaded)
4. **Check Console:** Browser console should show no WebSocket errors

---

## 📊 Service Status Commands

```bash
# Check all running services
tmux ls                    # Shows tmux sessions
ps aux | grep uvicorn      # Shows FastAPI process
ps aux | grep llama_cpp    # Shows LLM server process
docker-compose ps         # Shows Milvus containers

# View logs for each service
tmux attach -t fastapi     # FastAPI logs (Ctrl+B D to detach)
tmux attach -t frontend    # Frontend logs (Ctrl+B D to detach)
tail -f backend/llm_server.log  # LLM server logs
docker-compose logs -f     # Milvus logs

# Restart services if needed
tmux kill-session -t fastapi && tmux new-session -d -s 'fastapi' "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

---

## 🚨 Troubleshooting Common Issues

### Issue 1: LLM Server Fails to Start
```bash
# Check model file exists
ls -lh backend/models/mistral-7b-instruct-v0.2.q5_k_m.gguf

# Check GPU memory
nvidia-smi

# Try manual start
cd backend
source venv/bin/activate
python3 -m llama_cpp.server --model ./models/mistral-7b-instruct-v0.2.q5_k_m.gguf --n_gpu_layers -1 --host 0.0.0.0 --port 8080
```

### Issue 2: Frontend Can't Connect to Backend
```bash
# Check CORS configuration
grep -r "localhost:5173" backend/

# Check if backend is running
curl http://localhost:8000/

# Check network connectivity
netstat -tlnp | grep :8000
netstat -tlnp | grep :5173
```

### Issue 3: Milvus Connection Issues
```bash
# Restart Milvus
docker-compose down
docker-compose up -d

# Check ports
netstat -tlnp | grep :19530
netstat -tlnp | grep :9091

# View logs
docker-compose logs milvus-standalone
```

### Issue 4: Out of Memory Errors
```bash
# Check GPU memory usage
nvidia-smi

# Check system memory
free -h

# Reduce LLM context if needed
# Edit start command to use smaller --n_ctx (like 2048 instead of 4096)
```

---

## 📁 File Structure After Setup

```
AIMentorProject/
├── backend/
│   ├── venv/                    # Python virtual environment
│   ├── models/
│   │   └── mistral-7b-instruct-v0.2.q5_k_m.gguf  # 4.8GB LLM model
│   ├── llm_server.log          # LLM server logs
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt        # Python deps
│   └── app/                    # Application code
├── frontend/
│   ├── node_modules/           # Node.js deps
│   ├── package.json            # Node.js config
│   └── src/                    # SvelteKit app
├── volumes/                    # Milvus data persistence
├── docker-compose.yml          # Milvus configuration
└── RUNPOD_REBUILD_GLM_11-17-2025.md  # This file
```

---

## ⚡ Performance Optimizations

### Memory Management
- LLM uses `--n_gpu_layers -1` (all layers on GPU)
- Context window: 4096 tokens (adjustable based on VRAM)
- Milvus runs embedded, no extra memory overhead

### Startup Time Optimization
- Total cold start: ~8-12 minutes
- Subsequent starts: ~3-5 minutes (with cached Docker images)

### Model Alternatives
If memory is tight, consider smaller models:
- `mistral-7b-instruct-v0.2.q4_k_m.gguf` (~3.5GB)
- `llama-3-8b-instruct-q4_k_m.gguf` (~4.7GB)

---

## 🔧 Service Management Commands

### Complete System Restart
```bash
#!/bin/bash
# Save as restart_all.sh
chmod +x restart_all.sh

echo "Stopping all services..."
tmux kill-server
docker-compose down
pkill -f llama_cpp

echo "Starting services..."
docker-compose up -d
sleep 30

cd backend
source venv/bin/activate
nohup python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.q5_k_m.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct \
  > llm_server.log 2>&1 &

sleep 45
tmux new-session -d -s 'fastapi' "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

cd ../frontend
tmux new-session -d -s 'frontend' "npm run dev -- --host 0.0.0.0 --port 5173"

echo "All services started!"
```

### Health Check Script
```bash
#!/bin/bash
# Save as health_check.sh
chmod +x health_check.sh

echo "=== AI Mentor System Health Check ==="
echo "LLM Server:"
curl -s http://localhost:8080/v1/models | jq '.data[0].id' || echo "❌ LLM Server Down"

echo "FastAPI Backend:"
curl -s http://localhost:8000/ | jq '.status' || echo "❌ Backend Down"

echo "Milvus Status:"
docker-compose ps | grep milvus | grep Up || echo "❌ Milvus Down"

echo "Frontend:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ | grep 200 && echo "✅ Frontend OK" || echo "❌ Frontend Down"

echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits
```

---

## 📝 Verification Checklist

- [ ] Repository cloned successfully
- [ ] Model file downloaded (4.8GB)
- [ ] Python virtual environment created
- [ ] Dependencies installed without errors
- [ ] Milvus containers running (3 containers)
- [ ] LLM server responding on port 8080
- [ ] FastAPI backend responding on port 8000
- [ ] Frontend dev server running on port 5173
- [ ] Browser loads chat interface at localhost:5173
- [ ] Test chat message gets response
- [ ] No console errors in browser
- [ ] All tmux sessions running
- [ ] GPU memory usage reasonable (<15GB)

---

## 🎯 Success Indicators

When setup is complete, you should see:

1. **Browser:** Chat interface loads at http://localhost:5173/
2. **Response:** AI replies to test messages
3. **Performance:** Response time under 30 seconds for simple queries
4. **Stability:** Services remain running after initial tests
5. **Logs:** Clean logs without critical errors

---

## 📞 Support and Next Steps

If issues persist:
1. Check each service individually using troubleshooting section
2. Verify all prerequisites are met
3. Ensure sufficient storage and GPU memory
4. Check network connectivity for model download

**After successful setup:**
- Consider ingesting course materials using the ingest pipeline
- Configure automated startup scripts
- Set up monitoring and logging
- Document any customizations for your specific use case

---

**Expected Total Time:** 45-60 minutes (first time)
**Expected Total Time:** 15-20 minutes (subsequent runs with cached resources)

🎉 **Your AI Mentor should now be fully operational at http://localhost:5173!**