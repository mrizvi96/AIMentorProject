#!/bin/bash

# AI Mentor LLM Server Startup Script
# This script installs llama-cpp-python and starts the Mistral-7B server

set -e  # Exit on any error

echo "=========================================="
echo "AI Mentor LLM Server Setup"
echo "=========================================="

# Check if model file exists
MODEL_PATH="/workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: Model file not found at $MODEL_PATH"
    echo "Please upload the model file from your USB drive first!"
    echo ""
    echo "Upload instructions:"
    echo "1. Connect to Runpod via VS Code Remote-SSH"
    echo "2. Copy model from USB to a local folder"
    echo "3. In VS Code, right-click the model file and select 'Upload to...'"
    echo "4. Upload to /workspace/models/"
    exit 1
fi

echo "✓ Model file found: $MODEL_PATH"

# Activate virtual environment
echo ""
echo "Activating Python virtual environment..."
cd /root/AIMentorProject/backend
source venv/bin/activate
cd /root/AIMentorProject

# Install llama-cpp-python with CUDA support if not already installed
echo "Installing llama-cpp-python with CUDA support..."
pip show llama-cpp-python > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ llama-cpp-python already installed"
else
    echo "Installing llama-cpp-python..."
    CMAKE_ARGS="-DGGML_CUDA=on" pip install "llama-cpp-python[server]"
    echo "✓ Installation complete"
fi

# Start the LLM server
echo ""
echo "=========================================="
echo "Starting Mistral-7B Server on port 8080"
echo "=========================================="
echo ""
echo "Server will be accessible at:"
echo "  - Local: http://localhost:8080"
echo "  - OpenAI-compatible endpoint: http://localhost:8080/v1"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --n_gpu_layers -1 \
    --n_ctx 4096 \
    --host 0.0.0.0 \
    --port 8080 \
    --chat_format mistral-instruct
