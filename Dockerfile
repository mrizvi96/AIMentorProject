# AI Mentor - Runpod Custom Docker Image
# Base: PyTorch with CUDA support

FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

# Metadata
LABEL maintainer="AI Mentor Project"
LABEL description="Custom Docker image for AI Mentor RAG system with Milvus support"

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
    nano \
    htop \
    lsof \
    net-tools \
    docker.io \
    docker-compose \
    build-essential \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /workspace/AIMentorProject/

# Create necessary directories with proper permissions
RUN mkdir -p /workspace/models \
    /workspace/AIMentorProject/volumes/etcd \
    /workspace/AIMentorProject/volumes/minio \
    /workspace/AIMentorProject/volumes/milvus \
    /workspace/AIMentorProject/course_materials \
    /workspace/AIMentorProject/backend/logs \
    && chmod -R 755 /workspace/AIMentorProject

# Setup Python virtual environment
RUN cd /workspace/AIMentorProject/backend && \
    python3 -m venv venv

# Install Python dependencies
RUN cd /workspace/AIMentorProject/backend && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install llama-cpp-python with CUDA support (separate step for better caching)
RUN cd /workspace/AIMentorProject/backend && \
    . venv/bin/activate && \
    CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 pip install --no-cache-dir "llama-cpp-python[server]"

# Make scripts executable
RUN chmod +x /workspace/AIMentorProject/*.sh

# Copy and setup environment file
RUN if [ -f /workspace/AIMentorProject/backend/.env.example ]; then \
        cp /workspace/AIMentorProject/backend/.env.example /workspace/AIMentorProject/backend/.env; \
    fi

# Expose ports
# 8000: FastAPI Backend
# 8080: LLM Server (llama.cpp)
# 19530: Milvus gRPC
# 9091: Milvus HTTP
# 9001: MinIO Console
# 5173: Frontend (if running)
EXPOSE 8000 8080 19530 9091 9001 5173

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE=/workspace/AIMentorProject
ENV PATH="/workspace/AIMentorProject/backend/venv/bin:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Create startup script that will be run on container start
RUN echo '#!/bin/bash\n\
echo "AI Mentor Container Started"\n\
echo "=================================="\n\
echo "Working Directory: $WORKSPACE"\n\
echo ""\n\
echo "To start services, run:"\n\
echo "  cd /workspace/AIMentorProject"\n\
echo "  ./start_all_services.sh"\n\
echo ""\n\
echo "Or start individually:"\n\
echo "  1. Milvus: docker-compose up -d"\n\
echo "  2. LLM: ./start_llm_server.sh"\n\
echo "  3. Backend: cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"\n\
echo ""\n\
exec /bin/bash\n\
' > /usr/local/bin/start.sh && chmod +x /usr/local/bin/start.sh

# Default command
CMD ["/usr/local/bin/start.sh"]
