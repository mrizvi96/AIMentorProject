#!/bin/bash

# AI Mentor - Service Startup Script
# Run this script on your Runpod instance to start all services

set -e

echo "=============================================="
echo "AI Mentor - Starting All Services"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Step 1: Start Milvus
echo "Step 1/5: Starting Milvus vector database..."
docker-compose up -d
echo "✓ Milvus containers started"
echo ""

# Wait for Milvus to be healthy
echo "Waiting for Milvus to be healthy (this may take 30-60 seconds)..."
sleep 10
for i in {1..12}; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✓ Milvus is healthy!"
        break
    fi
    echo "Still waiting... ($i/12)"
    sleep 5
done
echo ""

# Step 2: Check if venv exists
echo "Step 2/5: Setting up Python environment..."
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Step 3: Install dependencies
echo "Step 3/5: Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
cd ..
echo ""

# Step 4: Check for course materials
echo "Step 4/5: Checking for course materials..."
if [ -z "$(ls -A course_materials/*.pdf 2>/dev/null)" ]; then
    echo "⚠️  WARNING: No PDF files found in course_materials/"
    echo ""
    echo "Please upload your course materials (PDFs) to the course_materials/ directory"
    echo "before running data ingestion."
    echo ""
    read -p "Do you want to continue without ingesting data? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    PDF_COUNT=$(ls -1 course_materials/*.pdf 2>/dev/null | wc -l)
    echo "✓ Found $PDF_COUNT PDF file(s)"
    echo ""
    read -p "Do you want to ingest these PDFs now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Ingesting course materials..."
        cd backend
        source venv/bin/activate
        python ingest.py --directory ../course_materials
        cd ..
        echo "✓ Data ingestion complete"
    else
        echo "Skipping ingestion. You can run it later with:"
        echo "  cd backend && source venv/bin/activate && python ingest.py"
    fi
fi
echo ""

# Step 5: Instructions for starting servers
echo "Step 5/5: Service startup instructions"
echo "=============================================="
echo ""
echo "All prerequisites are ready! Now start the servers:"
echo ""
echo "Terminal 1 - LLM Server (llama.cpp):"
echo "  cd $(pwd)"
echo "  ./start_llm_server.sh"
echo ""
echo "Terminal 2 - Backend API (FastAPI):"
echo "  cd $(pwd)/backend"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Terminal 3 - Frontend (SvelteKit):"
echo "  cd $(pwd)/frontend"
echo "  npm run dev -- --host 0.0.0.0"
echo ""
echo "=============================================="
echo "Once all servers are running:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - LLM Server: http://localhost:8080/v1"
echo "=============================================="
echo ""
echo "✓ Setup complete!"
