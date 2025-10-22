#!/bin/bash

# AI Mentor - Start All Services
# This script starts Milvus, LLM Server, and Backend API

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AI Mentor - Starting All Services"
echo "=========================================="
echo ""

cd /workspace/AIMentorProject

# Check if model exists
if [ ! -f "/workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf" ]; then
    echo -e "${YELLOW}⚠ Warning: Model file not found at /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf${NC}"
    echo "Please upload the model file before starting services."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Start Milvus
echo -e "${BLUE}Step 1/3: Starting Milvus Vector Database...${NC}"
docker-compose up -d

echo -e "${GREEN}✓ Milvus containers started${NC}"
echo -e "${YELLOW}Waiting 90 seconds for Milvus to initialize...${NC}"
sleep 90

# Verify Milvus
if docker-compose ps | grep -q "milvus.*Up"; then
    echo -e "${GREEN}✓ Milvus is running${NC}"
else
    echo -e "${YELLOW}⚠ Milvus may still be starting up${NC}"
fi

echo ""

# Step 2: Start LLM Server
echo -e "${BLUE}Step 2/3: Starting LLM Server...${NC}"

# Kill existing tmux session if it exists
tmux kill-session -t llm 2>/dev/null || true

# Start LLM server in tmux
tmux new-session -d -s llm "cd /workspace/AIMentorProject && ./start_llm_server.sh"

echo -e "${GREEN}✓ LLM Server starting in tmux session 'llm'${NC}"
echo "  View logs: tmux attach -t llm"
echo ""

# Wait a bit for LLM to start
sleep 5

# Step 3: Start Backend API
echo -e "${BLUE}Step 3/3: Starting Backend API...${NC}"

cd backend

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Kill existing backend session
tmux kill-session -t backend 2>/dev/null || true

# Start backend in tmux
tmux new-session -d -s backend "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo -e "${GREEN}✓ Backend API starting in tmux session 'backend'${NC}"
echo "  View logs: tmux attach -t backend"

cd ..
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}✅ All Services Started!${NC}"
echo "=========================================="
echo ""
echo "Service Status:"
echo "  - Milvus: docker-compose ps"
echo "  - LLM Server: tmux attach -t llm"
echo "  - Backend API: tmux attach -t backend"
echo ""
echo "Wait ~30 seconds for LLM server to fully load, then test:"
echo ""
echo "Test Commands:"
echo "  # Test LLM Server"
echo "  curl http://localhost:8080/v1/models"
echo ""
echo "  # Test Backend API"
echo "  curl http://localhost:8000/"
echo ""
echo "  # Test Chat Endpoint"
echo "  curl -X POST http://localhost:8000/api/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"What is Python?\"}'"
echo ""
echo "Next Steps:"
echo "  1. Ingest course materials (if not done):"
echo "     cd backend && source venv/bin/activate && python ingest.py"
echo ""
echo "  2. Access services via Runpod URLs (check dashboard for URLs)"
echo ""
echo "=========================================="
