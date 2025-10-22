# Runpod Custom Docker Image Setup

**Updated approach using Runpod's custom Docker image workflow**

Reference: https://docs.runpod.io/tutorials/pods/build-docker-images

---

## Why Custom Docker Image?

The AI Mentor project needs:
- Milvus vector database (requires Docker containers)
- LLM server (llama.cpp)
- FastAPI backend
- Python dependencies

Instead of fighting Docker-in-Docker issues, we build a **custom Docker image** that includes everything pre-configured.

---

## Architecture Overview

```
Custom Docker Image
├── Base: runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
├── Milvus (etcd, minio, milvus-standalone) - via docker-compose
├── Python environment with all dependencies
├── LLM server setup (llama-cpp-python)
└── FastAPI backend code
```

---

## Step 1: Create Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
# Use Runpod's PyTorch base image with CUDA support
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

# Set working directory
WORKDIR /workspace/AIMentorProject

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    tmux \
    vim \
    docker.io \
    docker-compose \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /workspace/AIMentorProject/

# Create necessary directories
RUN mkdir -p /workspace/models \
    /workspace/AIMentorProject/volumes/etcd \
    /workspace/AIMentorProject/volumes/minio \
    /workspace/AIMentorProject/volumes/milvus \
    /workspace/AIMentorProject/course_materials

# Setup Python virtual environment and install dependencies
RUN cd /workspace/AIMentorProject/backend && \
    python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    CMAKE_ARGS="-DGGML_CUDA=on" pip install --no-cache-dir "llama-cpp-python[server]"

# Make scripts executable
RUN chmod +x /workspace/AIMentorProject/*.sh

# Expose ports
EXPOSE 8000 8080 19530 9091 5173

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE=/workspace/AIMentorProject

# Default command (can be overridden)
CMD ["/bin/bash"]
```

---

## Step 2: Build and Push Docker Image

### Option A: Build Locally and Push to Docker Hub

```bash
# On your local machine (with Docker installed)
cd /path/to/AIMentorProject

# Build the image
docker build -t YOUR_DOCKERHUB_USERNAME/ai-mentor:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push YOUR_DOCKERHUB_USERNAME/ai-mentor:latest
```

### Option B: Use GitHub Actions (Recommended)

Create `.github/workflows/docker-build.yml`:

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/ai-mentor:latest
```

---

## Step 3: Deploy on Runpod

### Using Runpod Web Interface

1. **Go to Runpod.io** and log in
2. **Click "Deploy"** → "GPU Pod"
3. **Select GPU**: RTX A5000 (24GB VRAM) or similar
4. **Under "Select a Template"**:
   - Click "Custom"
   - Enter your Docker image: `YOUR_DOCKERHUB_USERNAME/ai-mentor:latest`
5. **Configure Pod**:
   - Container Disk: 50GB minimum
   - Volume Disk: 100GB (for persistent storage - optional)
   - Enable SSH
   - Expose Ports: 8000, 8080, 19530, 5173
6. **Click "Deploy"**

### Using Runpod CLI (Alternative)

```bash
# Install runpodctl
wget https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-linux-amd64 -O runpodctl
chmod +x runpodctl
sudo mv runpodctl /usr/local/bin/

# Configure API key (get from Runpod dashboard)
runpodctl config --apiKey YOUR_API_KEY

# Deploy pod
runpodctl create pod \
  --name ai-mentor \
  --imageName YOUR_DOCKERHUB_USERNAME/ai-mentor:latest \
  --gpuType "NVIDIA RTX A5000" \
  --containerDiskSize 50 \
  --ports "8000/http,8080/http,19530/tcp,5173/http"
```

---

## Step 4: Upload Mistral Model

Once the pod is running:

### Option A: Via SCP (From Local Machine)

```bash
# Get your pod's SSH connection details from Runpod dashboard
# Example: ssh root@pod-xyz.runpod.io -p 12345

# Upload model
scp -P 12345 /path/to/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf root@pod-xyz.runpod.io:/workspace/models/
```

### Option B: Via Runpod Web Terminal

```bash
# Download directly on the pod
cd /workspace/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf
```

---

## Step 5: Start Services

SSH into your Runpod instance and run:

```bash
cd /workspace/AIMentorProject

# Start Milvus (Docker Compose)
docker-compose up -d

# Wait for Milvus to initialize
sleep 90

# Start LLM Server (in tmux)
tmux new-session -d -s llm './start_llm_server.sh'

# Start Backend API (in tmux)
tmux new-session -d -s backend 'cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload'

# Check services
docker-compose ps
curl http://localhost:8080/v1/models
curl http://localhost:8000/
```

---

## Step 6: Ingest Course Materials

```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials/
```

---

## Step 7: Access Your Application

From Runpod dashboard, you'll see your pod's public URLs:
- **Backend API**: `https://pod-xyz-8000.runpod.io`
- **LLM Server**: `https://pod-xyz-8080.runpod.io`
- **Frontend** (if running): `https://pod-xyz-5173.runpod.io`

Update your frontend API configuration to use the public URL:

```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = 'https://pod-xyz-8000.runpod.io'; // Replace with your actual URL
```

---

## Automated Startup Script

Create `/workspace/AIMentorProject/start_all_services.sh`:

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "AI Mentor - Starting All Services"
echo "=========================================="

cd /workspace/AIMentorProject

# Start Milvus
echo "Starting Milvus..."
docker-compose up -d
sleep 90

# Start LLM Server
echo "Starting LLM Server..."
tmux new-session -d -s llm './start_llm_server.sh'

# Start Backend
echo "Starting Backend API..."
tmux new-session -d -s backend 'cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload'

echo ""
echo "✅ All services started!"
echo ""
echo "Check status:"
echo "  - Milvus: docker-compose ps"
echo "  - LLM: tmux attach -t llm"
echo "  - Backend: tmux attach -t backend"
```

Make it executable:
```bash
chmod +x start_all_services.sh
```

---

## Benefits of This Approach

✅ **No Docker-in-Docker issues** - Everything runs cleanly
✅ **Fast deployment** - Pre-built image, just upload model
✅ **Reproducible** - Same environment every time
✅ **Version controlled** - Dockerfile in Git
✅ **CI/CD ready** - Automated builds with GitHub Actions

---

## Troubleshooting

### Docker Compose Fails

```bash
# Check Docker daemon
systemctl status docker
systemctl start docker

# Check Docker Compose version
docker-compose --version
```

### Ports Not Accessible

- Check Runpod dashboard port mappings
- Ensure firewall rules allow traffic
- Use Runpod's auto-generated URLs, not localhost

### Model Not Found

```bash
# Verify model location
ls -lh /workspace/models/

# Create symlink if filename differs
ln -s /workspace/models/ACTUAL_NAME.gguf /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf
```

---

## Next Steps

1. ✅ Create Dockerfile
2. ✅ Build and push to Docker Hub
3. ✅ Deploy on Runpod with custom image
4. ✅ Upload Mistral model
5. ✅ Start all services
6. ✅ Test the full stack
7. → Continue with Phase 2: Agentic RAG implementation

---

## Files to Create/Update

- `Dockerfile` (new)
- `.github/workflows/docker-build.yml` (new)
- `start_all_services.sh` (new)
- `.dockerignore` (new)
- Update `.gitignore` to exclude build artifacts
