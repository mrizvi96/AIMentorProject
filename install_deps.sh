#!/bin/bash
# Install system and Python dependencies for AI Mentor

set -e

echo "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
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

echo "Setting up Python virtual environment..."
cd /workspace/AIMentorProject/backend
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Installing llama-cpp-python with CUDA..."
CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 pip install --no-cache-dir "llama-cpp-python[server]"

echo "Making scripts executable..."
chmod +x /workspace/AIMentorProject/*.sh

echo "Setup complete!"
