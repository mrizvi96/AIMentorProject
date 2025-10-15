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
tmux new-session -d -s api "cd $(pwd) && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

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
