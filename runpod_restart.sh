#!/bin/bash
# Runpod AI Mentor - Quick Restart Script
# Use this after pod reset to quickly get everything running again
# Total time: ~5 minutes (model and data already in /workspace)

set -e  # Exit on error

echo "=============================================="
echo "AI Mentor - Runpod Restart Script"
echo "=============================================="
echo ""

# Change to project directory
cd /workspace/AIMentorProject

echo "📍 Working directory: $(pwd)"
echo ""

# Step 1: Setup Python environment
echo "🐍 Step 1/5: Setting up Python environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel --quiet
pip install -r requirements.txt --quiet

# Critical: Reinstall llama-cpp-python with GPU support
echo "🔧 Rebuilding llama-cpp-python with CUDA support..."
pip uninstall -y llama-cpp-python --quiet
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --quiet
pip install "numpy<2.0.0" --force-reinstall --quiet

# Verify GPU support
echo "✓ Verifying GPU support..."
python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())" || echo "⚠️  GPU support verification failed"

echo ""
echo "✅ Step 1 complete!"
echo ""

# Step 2: Start LLM Server
echo "🚀 Step 2/5: Starting LLM server..."
nohup python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct \
  --embedding true > llm_server.log 2>&1 &

echo "⏳ Waiting for model to load (30 seconds)..."
sleep 30

# Check if LLM server is responding
if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
    echo "✅ LLM server is running!"
else
    echo "⚠️  LLM server may not have started correctly. Check llm_server.log"
fi

echo ""

# Step 3: Start Backend API
echo "🔌 Step 3/5: Starting backend API..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
sleep 3

# Check if backend is responding
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend API is running!"
else
    echo "⚠️  Backend API may not have started correctly. Check backend.log"
fi

echo ""

# Step 4: Start Frontend (optional)
echo "🎨 Step 4/5: Starting frontend dev server..."
cd ../frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm packages..."
    npm install --quiet
fi

nohup npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &
sleep 5

echo "✅ Frontend dev server started!"
echo ""

# Step 5: Status check
echo "📊 Step 5/5: System status check..."
echo ""
echo "Running services:"
ps aux | grep -E "(llama_cpp|uvicorn|vite)" | grep -v grep | awk '{print $11, $12, $13, $14, $15}'
echo ""

echo "GPU Memory Usage:"
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk '{print $1 " MB VRAM in use"}'
echo ""

echo "Service URLs:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend:  http://localhost:8000"
echo "  - LLM API:  http://localhost:8080"
echo ""

echo "=============================================="
echo "✅ AI Mentor is ready!"
echo "=============================================="
echo ""
echo "Access via VSCode port forwarding:"
echo "  1. Open the PORTS tab in VSCode"
echo "  2. Forward port 5173"
echo "  3. Click the localhost URL"
echo ""
echo "Or expose ports in Runpod dashboard:"
echo "  - Port 5173 (Frontend)"
echo "  - Port 8000 (Backend)"
echo ""
echo "View logs:"
echo "  - LLM:      tail -f backend/llm_server.log"
echo "  - Backend:  tail -f backend/backend.log"
echo "  - Frontend: tail -f frontend/frontend.log"
echo ""
