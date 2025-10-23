#!/bin/bash
# Simplified Runpod Startup Script - No Docker Required!
# Uses Milvus Lite (file-based) instead of Docker-based Milvus

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================================"
echo -e "${BLUE}🚀 AI Mentor Runpod Startup (Milvus Lite)${NC}"
echo "================================================"
echo ""

RUNPOD_IP=$(hostname -I | awk '{print $1}')
echo -e "${BLUE}📍 Pod IP: $RUNPOD_IP${NC}"
echo ""

# ============================================
# Step 1: Download Mistral Model (if needed)
# ============================================
echo -e "${YELLOW}Step 1: Checking Mistral Model...${NC}"

MODEL_DIR="/workspace/models"
MODEL_FILE="$MODEL_DIR/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
MODEL_URL="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_FILE" ]; then
    echo -e "${GREEN}✓ Model already exists ($(du -h "$MODEL_FILE" | cut -f1))${NC}"
else
    echo -e "${YELLOW}⏳ Downloading Mistral model from HuggingFace...${NC}"
    echo "   Size: ~5.1 GB | Time: ~30 minutes"
    echo "   URL: $MODEL_URL"
    echo ""

    cd "$MODEL_DIR"
    wget --progress=bar:force:noscroll "$MODEL_URL" -O "$MODEL_FILE"

    echo ""
    echo -e "${GREEN}✓ Model download complete ($(du -h "$MODEL_FILE" | cut -f1))${NC}"
fi

echo ""

# ============================================
# Step 2: Setup Backend Python Environment
# ============================================
echo -e "${YELLOW}Step 2: Setting up Backend Environment...${NC}"

cd /workspace/AIMentorProject/backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "  Installing Python dependencies..."
pip install -q --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
else
    echo -e "${RED}⚠️  requirements.txt not found!${NC}"
    exit 1
fi

# Install llama-cpp-python with CUDA support
echo "  Installing llama-cpp-python with CUDA..."
CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 pip install --no-cache-dir "llama-cpp-python[server]"

echo -e "${GREEN}✓ Backend environment ready${NC}"
echo ""

# ============================================
# Step 3: Start LLM Server (tmux)
# ============================================
echo -e "${YELLOW}Step 3: Starting LLM Inference Server...${NC}"

# Kill existing session if it exists
tmux kill-session -t llm 2>/dev/null || true

# Start LLM server in tmux
tmux new-session -d -s llm "cd /workspace/AIMentorProject && source backend/venv/bin/activate && python3 -m llama_cpp.server \
    --model '$MODEL_FILE' \
    --n_gpu_layers -1 \
    --n_ctx 4096 \
    --host 0.0.0.0 \
    --port 8080 \
    --chat_format mistral-instruct"

echo -e "${GREEN}✓ LLM server started in tmux session 'llm'${NC}"
echo "  Waiting 30 seconds for model to load into GPU..."
sleep 30

echo ""

# ============================================
# Step 4: Start Backend API Server (tmux)
# ============================================
echo -e "${YELLOW}Step 4: Starting Backend API Server...${NC}"

# Kill existing session if it exists
tmux kill-session -t backend 2>/dev/null || true

# Start backend API in tmux
tmux new-session -d -s backend "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo -e "${GREEN}✓ Backend API started in tmux session 'backend'${NC}"
echo "  Waiting 5 seconds for API server to initialize..."
sleep 5

echo ""

# ============================================
# Step 5: System Health Check
# ============================================
echo -e "${YELLOW}Step 5: Running Health Checks...${NC}"
echo ""

# Check LLM Server
echo -n "  • LLM Server:   "
if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
    MODEL_NAME=$(curl -s http://localhost:8080/v1/models | jq -r '.data[0].id' 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Running (model: $MODEL_NAME)${NC}"
else
    echo -e "${YELLOW}⏳ Still loading (check: tmux attach -t llm)${NC}"
fi

# Check Backend API
echo -n "  • Backend API:  "
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running on port 8000${NC}"
else
    echo -e "${YELLOW}⏳ Still starting (check: tmux attach -t backend)${NC}"
fi

# Check GPU
echo -n "  • GPU:          "
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    echo -e "${GREEN}✓ $GPU_NAME (${GPU_MEM} MB used)${NC}"
else
    echo -e "${RED}✗ nvidia-smi not found${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}✅ Startup Complete!${NC}"
echo "================================================"
echo ""
echo "📌 Service URLs (Public - if ports exposed):"
echo "   Replace '[POD-ID]' with your actual Runpod pod ID"
echo "   • Backend API:  https://[POD-ID]-8000.runpod.io"
echo "   • API Docs:     https://[POD-ID]-8000.runpod.io/docs"
echo "   • LLM Server:   https://[POD-ID]-8080.runpod.io"
echo ""
echo "📌 Service URLs (Internal):"
echo "   • Backend API:  http://localhost:8000"
echo "   • LLM Server:   http://localhost:8080"
echo "   • Milvus Lite:  ./backend/milvus_data/ai_mentor.db (file-based)"
echo ""
echo "🔧 Useful Commands:"
echo "   • View LLM logs:       tmux attach -t llm"
echo "   • View API logs:       tmux attach -t backend"
echo "   • Detach from tmux:    Ctrl+B then D"
echo "   • Check GPU usage:     nvidia-smi"
echo "   • Stop LLM:            tmux kill-session -t llm"
echo "   • Stop Backend:        tmux kill-session -t backend"
echo "   • Stop all:            tmux kill-session -t llm && tmux kill-session -t backend"
echo ""
echo "📚 Next Steps:"
echo ""
echo "   ${YELLOW}1. Ingest course materials (first time only):${NC}"
echo "      cd backend && source venv/bin/activate"
echo "      python ingest.py --directory ../course_materials/"
echo "      ${BLUE}Note: This creates the Milvus Lite database file${NC}"
echo ""
echo "   ${YELLOW}2. Test the backend:${NC}"
echo "      curl -X POST http://localhost:8000/api/chat \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"message\": \"What is Python?\", \"conversation_id\": \"test\"}' | jq"
echo ""
echo "   ${YELLOW}3. Setup frontend (on your local machine):${NC}"
echo "      cd frontend"
echo "      # Edit frontend/src/lib/api.ts:"
echo "      # Change API_BASE_URL to: 'https://[POD-ID]-8000.runpod.io'"
echo "      npm install"
echo "      npm run dev"
echo ""
echo "   ${YELLOW}4. Preserve data before stopping pod:${NC}"
echo "      # Commit Milvus database to Git (if small enough)"
echo "      cd backend"
echo "      git add milvus_data/"
echo "      git commit -m \"Add ingested course materials\""
echo "      git push"
echo "      ${BLUE}OR backup manually:${NC}"
echo "      tar -czf milvus-backup-\$(date +%Y%m%d).tar.gz backend/milvus_data/"
echo "      # Download via VS Code or SCP"
echo ""
echo "================================================"
echo -e "${GREEN}Happy coding! 🎉${NC}"
echo "================================================"
echo ""
