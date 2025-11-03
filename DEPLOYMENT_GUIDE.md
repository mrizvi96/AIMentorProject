# AI Mentor Deployment Guide

Complete guide for deploying the AI Mentor system on Runpod (or similar GPU instances).

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Service Management](#service-management)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Evaluation](#evaluation)
7. [Troubleshooting](#troubleshooting)
8. [Production Considerations](#production-considerations)

---

## Quick Start

For experienced users who want to get up and running quickly:

```bash
# 1. Clone repository
cd /root
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject

# 2. Download model and PDFs (see CLAUDE_LOG.md for download commands)

# 3. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install "numpy<2.0.0" --force-reinstall

# 4. Start services
cd ..
./service_manager.sh start

# 5. Ingest documents
cd backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite

# 6. Test system
python3 test_agentic_rag.py
```

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- GPU: NVIDIA GPU with 12GB+ VRAM (RTX 3060 12GB or better)
- RAM: 16GB system memory
- Storage: 30GB free space
- CUDA: Version 11.x or 12.x

**Recommended (Current Setup):**
- GPU: NVIDIA RTX A5000 (24GB VRAM)
- RAM: 32GB+ system memory
- Storage: 50GB+ free space
- CUDA: 12.8.1

### Software Requirements

- **OS**: Ubuntu 24.04 LTS (or compatible Linux)
- **Python**: 3.12+ (pre-installed on runpod/pytorch image)
- **CUDA**: Pre-installed on GPU instances
- **Git**: For repository management
- **Node.js**: 18+ (for frontend, optional)

---

## Initial Setup

### Step 1: Clone Repository

```bash
cd /root
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject
```

### Step 2: Download Model

The system uses Mistral-7B-Instruct-v0.2 Q5_K_M (4.8GB):

```bash
mkdir -p backend/models
cd backend/models
wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
cd ../..
```

**Download time:** ~2-3 minutes on Runpod (depends on region)

### Step 3: Download Course Materials

```bash
# Install gdown for Google Drive downloads
pip3 install gdown

# Download PDFs
mkdir -p backend/course_materials
cd backend/course_materials

gdown "1DECFKmdQjbLRQpJWQUd1J6KViRIPf6ab"  # Computer Science Big Fat Notebook
gdown "1WVTdiVOhe7Oov2TDG3AXIg3c8HIthSac"  # MIT Textbook
gdown "1YAqEenI_z6CyZBSEUPgO2gjAELw5bwIt"  # Self-Taught Programmer
gdown "1mgJSWWzcA1PnHytQVp0kt5dyXx2NzIn0"  # Introduction to Algorithms
gdown "1nR4Mrx8BdTAOxGL_SXk80RRb9Oy-oeiZ"  # Computer Science Notebook
gdown "1sAEmzgyx63SMQCGmCuSddnzxfXrUKFZE"  # Practical Programming

cd ../..
```

**Note:** These are placeholder PDFs for testing. Replace with your actual course materials for production use.

### Step 4: Setup Backend Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# CRITICAL: Reinstall llama-cpp-python with CUDA support
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Fix numpy version compatibility
pip install "numpy<2.0.0" --force-reinstall

# Verify GPU support
python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())"
# Should output: CUDA: True
```

### Step 5: Start Services

```bash
cd ..  # Back to project root
./service_manager.sh start
```

**Expected output:**
```
Starting LLM Server...
  Waiting for model to load (30s)...
✓ LLM Server started

Starting Backend API...
  Waiting for API to initialize (5s)...
✓ Backend API started

✅ All services started successfully
```

### Step 6: Ingest Documents

```bash
cd backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
```

**Expected time:** ~3-5 minutes for 6 PDFs
**Output:** ~3,700 chunks created in ChromaDB

### Step 7: Verify Installation

```bash
# Test agentic RAG system
python3 test_agentic_rag.py

# Should see:
# ✅ ALL TESTS PASSED
```

---

## Service Management

The service_manager.sh script provides comprehensive service control.

### Available Commands

```bash
# Start all services
./service_manager.sh start

# Stop all services
./service_manager.sh stop

# Restart all services
./service_manager.sh restart

# Check service status
./service_manager.sh status

# View logs
./service_manager.sh logs llm      # LLM server logs
./service_manager.sh logs backend  # Backend API logs
```

### Service Status Output

```
================================================
AI Mentor Service Status
================================================

LLM Server (port 8080):     ✓ Running
  Model: ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf

Backend API (port 8000):    ✓ Running
  Health: ok

ChromaDB (file-based):      ✓ Database exists (104M)

GPU Status:                 ✓ NVIDIA RTX A5000 (5897 MB)

================================================
```

### Manual Service Control

If you need more control:

```bash
# Start LLM server manually
cd backend
source venv/bin/activate
python3 -m llama_cpp.server \
    --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
    --n_gpu_layers -1 \
    --n_ctx 4096 \
    --host 0.0.0.0 \
    --port 8080 \
    --chat_format mistral-instruct \
    --embedding true

# Start backend API manually
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Monitoring & Maintenance

### Health Monitoring

Use the health monitor for continuous service monitoring:

```bash
# Run continuous health monitoring
./health_monitor.sh

# Run single health check
./health_monitor.sh --once
```

The monitor will:
- Check services every 60 seconds
- Auto-restart failed services after 3 failures
- Display real-time status

### Log Management

Logs are stored in `backend/`:

```bash
# View LLM server logs
tail -f backend/llm_server.log

# View backend API logs
tail -f backend/backend.log

# Check for errors
grep -i error backend/llm_server.log
grep -i error backend/backend.log
```

### Resource Monitoring

```bash
# GPU utilization
nvidia-smi

# Detailed GPU monitoring (refresh every 1s)
watch -n 1 nvidia-smi

# Check VRAM usage
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits

# Process monitoring
ps aux | grep -E "llama_cpp|uvicorn"

# Disk space
df -h
```

### Expected Resource Usage

- **LLM Server**: ~5.8-6.0GB VRAM
- **ChromaDB**: ~100-200MB disk (for 6 PDFs)
- **CPU**: Minimal (most processing on GPU)
- **RAM**: ~4-6GB system memory

---

## Evaluation

### Running Evaluations

Full evaluation guide: [backend/evaluation/EVALUATION_GUIDE.md](backend/evaluation/EVALUATION_GUIDE.md)

**Quick evaluation:**

```bash
cd backend/evaluation
source ../venv/bin/activate

# Run evaluation
python3 run_evaluation.py --mode direct

# Manual scoring (edit JSON file)
nano results/evaluation_*.json

# Generate analysis
python3 analyze_results.py results/evaluation_*.json --output report.md

# View report
cat report.md
```

### When to Evaluate

1. After ingesting new document corpus
2. After significant code changes
3. Before production deployment
4. Periodically (monthly/quarterly)

⚠️ **Important:** Current evaluation with 6 PDFs is for framework testing only. Real evaluation requires production-scale corpus.

---

## Troubleshooting

### Services Won't Start

**Problem:** `service_manager.sh start` fails

**Solutions:**
```bash
# Check if ports are already in use
lsof -i :8080  # LLM server
lsof -i :8000  # Backend API

# Kill existing processes
pkill -f "llama_cpp.server"
pkill -f "uvicorn"

# Check logs for errors
cat backend/llm_server.log
cat backend/backend.log
```

### GPU Not Being Used

**Problem:** CPU inference instead of GPU

**Solution:**
```bash
# Verify llama-cpp-python has CUDA support
cd backend
source venv/bin/activate
python3 -c "from llama_cpp import llama_supports_gpu_offload; print(llama_supports_gpu_offload())"

# Should output: CUDA: True
# If False, reinstall with CUDA:
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Slow Responses

**Problem:** Queries take >30 seconds

**Possible causes:**
1. GPU not being used (see above)
2. Model not fully loaded in VRAM
3. Large context window

**Check VRAM usage:**
```bash
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# Should show ~5800-6000 MB
```

### ChromaDB Errors

**Problem:** `Collection does not exist`

**Solution:**
```bash
# Re-run ingestion
cd backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
```

### Out of Memory Errors

**Problem:** CUDA out of memory

**Solutions:**
1. Reduce context window: `--n_ctx 2048` (instead of 4096)
2. Use smaller model quantization (Q4 instead of Q5)
3. Reduce batch size in ingestion

---

## Production Considerations

### Security

1. **API Authentication**: Add API keys or OAuth
2. **Rate Limiting**: Prevent abuse
3. **Input Validation**: Sanitize user queries
4. **HTTPS**: Use reverse proxy (nginx) with SSL
5. **Environment Variables**: Never commit secrets to Git

### Scalability

**Current Setup Limitations:**
- Single GPU instance
- No load balancing
- ChromaDB file-based (not distributed)

**Scaling Options:**
1. **Multiple Instances**: Deploy on multiple GPUs with load balancer
2. **Vector DB**: Migrate to Milvus/Weaviate for distributed storage
3. **Caching**: Add Redis for frequent queries
4. **Queue System**: Add Celery for async processing

### Backup & Recovery

```bash
# Backup ChromaDB
tar -czf chroma-backup-$(date +%Y%m%d).tar.gz backend/chroma_db/

# Backup configuration
cp backend/.env backend/.env.backup

# Download backups (from local machine)
scp runpod:/root/AIMentorProject/chroma-backup-*.tar.gz ./
```

### Cost Optimization (Runpod)

1. **Stop Pod When Idle**: Save on compute costs
2. **Use Spot Instances**: 50-70% cheaper (risk of interruption)
3. **Network Storage**: Use Runpod network volumes for persistent data
4. **Scheduled Scaling**: Auto-start/stop based on usage patterns

### Monitoring in Production

Consider adding:
- **Prometheus + Grafana**: Metrics visualization
- **Sentry**: Error tracking
- **Uptime Robot**: Availability monitoring
- **CloudWatch/DataDog**: Comprehensive monitoring

---

## Updates & Maintenance

### Updating Code

```bash
cd /root/AIMentorProject
git pull origin main

# Reinstall dependencies if requirements.txt changed
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Restart services
cd ..
./service_manager.sh restart
```

### Updating Documents

```bash
# Add new PDFs to course_materials/
cp /path/to/new/*.pdf backend/course_materials/

# Re-run ingestion
cd backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite

# Restart backend to pick up changes
cd ..
./service_manager.sh restart
```

### Updating Model

```bash
# Download new model
cd backend/models
wget "https://huggingface.co/NEW_MODEL_URL"

# Update model path in start command or create new script

# Restart services
cd ../..
./service_manager.sh restart
```

---

## Quick Reference

### Useful Commands

```bash
# Service management
./service_manager.sh {start|stop|restart|status|logs}

# Health monitoring
./health_monitor.sh

# Run tests
cd backend && source venv/bin/activate && python3 test_agentic_rag.py

# Check GPU
nvidia-smi

# View logs
tail -f backend/llm_server.log
tail -f backend/backend.log
```

### Port Mappings

- **8080**: LLM inference server
- **8000**: Backend API
- **5173**: Frontend dev server (optional)

### File Locations

```
/root/AIMentorProject/
├── backend/
│   ├── models/              # LLM model files
│   ├── course_materials/    # PDF documents
│   ├── chroma_db/           # Vector database
│   ├── venv/                # Python environment
│   ├── llm_server.log       # LLM logs
│   └── backend.log          # API logs
├── service_manager.sh       # Service control
├── health_monitor.sh        # Health monitoring
└── DEPLOYMENT_GUIDE.md      # This file
```

---

## Support

For issues:
1. Check [CLAUDE_LOG.md](CLAUDE_LOG.md) for common errors and fixes
2. Review [EVALUATION_GUIDE.md](backend/evaluation/EVALUATION_GUIDE.md) for evaluation help
3. Check service logs: `./service_manager.sh logs {llm|backend}`
4. Run health check: `./service_manager.sh status`

---

**Last Updated:** 2025-11-03
**Version:** 1.0
