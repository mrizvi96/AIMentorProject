# Runpod Quick Start Guide
**For AI Mentor Project - Weeks 1-2 Focus**

## Problem Statement
Runpod instances are ephemeral and datacenter-specific. We need a system where:
1. **No manual dependency installation** each time (Node.js, Claude Code, etc.)
2. **Model files** are readily available (~4.4GB Mistral model)
3. **Docker images** with dependencies are pre-built
4. **One-command startup** to get the entire stack running

---

## Solution Architecture

### Three-Layer Strategy:

**Layer 1: Custom Runpod Template** → Pre-installed system tools
**Layer 2: Pre-built Docker Images** → Pre-packaged services with dependencies
**Layer 3: Automated Startup Script** → One command to orchestrate everything

---

## PHASE 1: One-Time Preparation (Do This Once Locally)

### 1.1: Build Docker Image with Baked-in Model

This eliminates the need to download the 4.4GB model every time.

```bash
# Create a local directory
mkdir ~/ai-mentor-docker-build && cd ~/ai-mentor-docker-build

# Download Mistral model (one-time 4.4GB download)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.q5_k_m.gguf

# Create Dockerfile for LLM server
cat > Dockerfile.llm << 'EOF'
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

WORKDIR /app

# Install Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Configure for GPU support
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CMAKE=1

# Install llama-cpp-python with pinned version
RUN pip3 install --no-cache-dir "llama-cpp-python[server]==0.2.56"

# Create models directory
RUN mkdir /models

# *** KEY STEP: Bake model into image ***
COPY mistral-7b-instruct-v0.2.q5_k_m.gguf /models/

EXPOSE 8080

CMD ["python3", "-m", "llama_cpp.server", \
     "--model", "/models/mistral-7b-instruct-v0.2.q5_k_m.gguf", \
     "--n_gpu_layers", "-1", \
     "--n_ctx", "4096", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--chat_format", "mistral-instruct"]
EOF

# Build image (replace YOUR_USERNAME with your Docker Hub username)
docker build -f Dockerfile.llm -t YOUR_USERNAME/ai-mentor-llm:v1 .

# Push to Docker Hub (requires: docker login)
docker login
docker push YOUR_USERNAME/ai-mentor-llm:v1

# This will take time: ~10GB image upload
```

### 1.2: Create Backend Docker Image

```bash
# Create backend Dockerfile
cat > Dockerfile.backend << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with pinned versions
RUN pip install --no-cache-dir \
    "fastapi[all]==0.109.0" \
    "uvicorn[standard]==0.27.0" \
    "python-dotenv==1.0.0" \
    "llama-index==0.10.30" \
    "llama-index-vector-stores-milvus==0.1.5" \
    "llama-index-embeddings-huggingface==0.2.0" \
    "pymilvus==2.3.6" \
    "PyMuPDF==1.23.21" \
    "sentence-transformers==2.5.1"

# Copy application code (will be mounted as volume in practice)
COPY backend/ /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Note: For now, we'll build this later since we need the actual backend code
# This is just the template
```

---

## PHASE 2: Create Custom Runpod Template (One-Time)

### 2.1: Start a Fresh Runpod Instance

1. Go to Runpod dashboard
2. Deploy pod with: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
3. GPU: RTX A5000 (24GB VRAM)
4. Wait for pod to start

### 2.2: Install System-Level Tools

```bash
# SSH into the fresh pod
ssh root@<POD_IP>

# Install all required system packages
apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    htop \
    tmux \
    jq \
    docker.io \
    docker-compose-plugin

# Install Node.js 20 (for Claude Code)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install Claude Code CLI globally
npm install -g @anthropic-ai/claude-code

# Verify installations
node -v          # Should be v20.x
npm -v
docker --version
claude --version # Should show Claude Code version

# Test Docker
docker run hello-world
```

### 2.3: Pre-pull Common Docker Images

```bash
# Pre-pull images so they're cached in the template
docker pull quay.io/coreos/etcd:v3.5.5
docker pull minio/minio:RELEASE.2023-03-20T20-16-18Z
docker pull milvusdb/milvus:v2.3.10

# Pull your custom LLM image (replace YOUR_USERNAME)
docker pull YOUR_USERNAME/ai-mentor-llm:v1

# Verify
docker images
```

### 2.4: Save as Runpod Template

1. In Runpod UI: Go to your pod
2. Click "Save Template"
3. Name it: **"ai-mentor-ready-v1"**
4. This template now has:
   - Node.js 20
   - Claude Code CLI
   - Docker + Docker Compose
   - Pre-pulled Docker images (~10GB cached)

---

## PHASE 3: Every-Time Startup (Fast, Automated)

Now when you start a NEW Runpod instance:

### 3.1: Launch Pod from Custom Template

1. Runpod Dashboard → Deploy
2. **Select Template**: "ai-mentor-ready-v1"
3. GPU: RTX A5000 (24GB)
4. Start pod

### 3.2: Clone Repository and Run Startup Script

```bash
# SSH into pod
ssh root@<POD_IP>

# Navigate to workspace
cd /workspace  # Or /root, depending on Runpod config

# Clone your repository
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject

# Run the automated startup script
./runpod_startup.sh
```

That's it! The startup script handles everything.

---

## PHASE 4: Create the Automated Startup Script

Create `runpod_startup.sh` in your project root:

```bash
#!/bin/bash
# runpod_startup.sh - Automated startup for AI Mentor on Runpod

set -e  # Exit on error

echo "================================================"
echo "🚀 AI Mentor Runpod Startup Script"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get Runpod IP (if available)
RUNPOD_IP=$(hostname -I | awk '{print $1}')
echo -e "${BLUE}📍 Pod IP: $RUNPOD_IP${NC}"
echo ""

# ============================================
# Step 1: Start Milvus Stack (Docker Compose)
# ============================================
echo -e "${YELLOW}Step 1: Starting Milvus Vector Database...${NC}"

# Create volumes directories if they don't exist
mkdir -p volumes/{etcd,minio,milvus}

# Start docker-compose services
docker-compose up -d

echo -e "${GREEN}✓ Docker containers started${NC}"
echo "  Waiting 90 seconds for Milvus to be healthy..."
sleep 90

# Verify Milvus
docker-compose ps

echo ""

# ============================================
# Step 2: Start LLM Server (Docker)
# ============================================
echo -e "${YELLOW}Step 2: Starting LLM Inference Server...${NC}"

# Check if LLM container is already in docker-compose
# If not, start it manually
if ! docker-compose ps | grep -q "llm"; then
    echo "  Starting LLM container from pre-built image..."

    docker run -d \
        --name ai-mentor-llm \
        --gpus all \
        -p 8080:8080 \
        YOUR_USERNAME/ai-mentor-llm:v1

    echo -e "${GREEN}✓ LLM container started${NC}"
    echo "  Waiting 120 seconds for model to load..."
    sleep 120
else
    echo -e "${GREEN}✓ LLM service already running via docker-compose${NC}"
fi

# Test LLM server
echo "  Testing LLM server..."
curl -s http://localhost:8080/v1/models | jq '.data[0].id' || echo "  (LLM not ready yet, may need more time)"

echo ""

# ============================================
# Step 3: Setup Backend Python Environment
# ============================================
echo -e "${YELLOW}Step 3: Setting up Backend Environment...${NC}"

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "  Installing Python dependencies from requirements.txt..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    echo "  No requirements.txt found, installing from scratch..."
    pip install -q --upgrade pip
    pip install -q \
        "fastapi[all]==0.109.0" \
        "uvicorn[standard]==0.27.0" \
        "python-dotenv==1.0.0" \
        "llama-index==0.10.30" \
        "llama-index-vector-stores-milvus==0.1.5" \
        "llama-index-embeddings-huggingface==0.2.0" \
        "pymilvus==2.3.6" \
        "PyMuPDF==1.23.21" \
        "sentence-transformers==2.5.1"
fi

echo -e "${GREEN}✓ Backend environment ready${NC}"

# ============================================
# Step 4: Start Backend API Server (tmux)
# ============================================
echo "  Starting FastAPI server in tmux session..."

# Kill existing session if it exists
tmux kill-session -t api 2>/dev/null || true

# Start new session
tmux new-session -d -s api "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo -e "${GREEN}✓ FastAPI server started (tmux session: api)${NC}"

cd ..
echo ""

# ============================================
# Step 5: System Health Check
# ============================================
echo -e "${YELLOW}Step 4: Running Health Checks...${NC}"

sleep 5

# Check Milvus
echo -n "  Milvus:      "
if docker-compose ps | grep -q "milvus.*Up"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "❌ Not running"
fi

# Check LLM
echo -n "  LLM Server:  "
if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running (port 8080)${NC}"
else
    echo -e "❌ Not responding"
fi

# Check Backend API
echo -n "  Backend API: "
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running (port 8000)${NC}"
else
    echo -e "❌ Not responding"
fi

echo ""
echo "================================================"
echo -e "${GREEN}✅ Startup Complete!${NC}"
echo "================================================"
echo ""
echo "📌 Service URLs:"
echo "   • Backend API:  http://$RUNPOD_IP:8000"
echo "   • API Docs:     http://$RUNPOD_IP:8000/docs"
echo "   • LLM Server:   http://$RUNPOD_IP:8080"
echo "   • Milvus gRPC:  $RUNPOD_IP:19530"
echo ""
echo "🔧 Useful Commands:"
echo "   • View API logs:      tmux attach -t api"
echo "   • Docker logs:        docker-compose logs -f"
echo "   • Check GPU:          nvidia-smi"
echo "   • Stop all services:  docker-compose down"
echo ""
echo "📚 Next Steps:"
echo "   1. If this is first time: Run data ingestion"
echo "      cd backend && source venv/bin/activate"
echo "      python ingest.py --directory ../course_materials"
echo ""
echo "   2. Test the system:"
echo "      curl -X POST http://localhost:8000/api/chat \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"message\": \"What is Python?\"}' | jq"
echo ""
echo "   3. Start frontend (on local machine):"
echo "      cd frontend && npm run dev"
echo ""
```

Make it executable:
```bash
chmod +x runpod_startup.sh
git add runpod_startup.sh
git commit -m "Add automated Runpod startup script"
git push
```

---

## Updated docker-compose.yml

Update your `docker-compose.yml` to use the pre-built LLM image:

```yaml
version: '3.8'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ./volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - ai_mentor_network

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9001:9001"
      - "9000:9000"
    volumes:
      - ./volumes/minio:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - ai_mentor_network

  milvus:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.10
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ./volumes/milvus:/var/lib/milvus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    networks:
      - ai_mentor_network

  llm:
    container_name: ai-mentor-llm
    image: YOUR_USERNAME/ai-mentor-llm:v1  # Your pre-built image with model
    ports:
      - "8080:8080"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - ai_mentor_network
    restart: unless-stopped

networks:
  ai_mentor_network:
    driver: bridge
```

---

## Summary: What Gets Pulled Up Automatically

When you run `./runpod_startup.sh`:

✅ **Milvus** (etcd, minio, milvus) - from pre-pulled images
✅ **LLM Server** - from YOUR_USERNAME/ai-mentor-llm:v1 (model baked-in)
✅ **Backend Python** - dependencies from requirements.txt
✅ **FastAPI Server** - starts in tmux session

**Total startup time: ~3-5 minutes** (vs 30-60 minutes manual setup)

---

## Data Persistence Strategy

### Option A: Network Storage (if available)

```bash
# In runpod_startup.sh, add before docker-compose:
if [ -d "/runpod-volume" ]; then
    echo "Network storage detected, using persistent volumes..."
    ln -sf /runpod-volume/ai-mentor/volumes ./volumes
fi
```

### Option B: Manual Backup

```bash
# Before terminating pod
tar -czf milvus-backup.tar.gz volumes/
# Upload to S3, Google Drive, etc.

# On new pod
# Download backup
tar -xzf milvus-backup.tar.gz
```

---

## Timeline Impact on Weeks 1-2

### Old Process (Manual):
- Day 1-2: 10-12 hours (mostly waiting for downloads and installations)

### New Process (Automated):
- **Preparation (one-time)**: 2-3 hours to build Docker images
- **Every startup**: 3-5 minutes automated

**Time saved per session: ~2-3 hours**

---

## Troubleshooting

### Docker Images Not Found
```bash
# Check if images are pulled
docker images | grep ai-mentor

# Pull manually if needed
docker pull YOUR_USERNAME/ai-mentor-llm:v1
```

### GPU Not Detected
```bash
# Check GPU visibility
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

### Tmux Sessions Not Starting
```bash
# List sessions
tmux ls

# Attach to session
tmux attach -t api

# Kill and restart
tmux kill-session -t api
./runpod_startup.sh
```

---

## Next Steps

1. ✅ Complete one-time Docker image builds (Phase 1)
2. ✅ Create custom Runpod template (Phase 2)
3. ✅ Test startup script on fresh pod (Phase 3)
4. ✅ Commit startup script to repository
5. → Continue with Week 1-2 development tasks
