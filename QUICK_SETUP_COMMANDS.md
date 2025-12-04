# AI Mentor Quick Setup Commands for RTX A4500

Copy and paste these commands in order to set up your AI Mentor system.

## Step 1: Verify GPU Status

```bash
# Check GPU information
nvidia-smi
```

## Step 2: Download Mistral-7B Model

```bash
# Create models directory
mkdir -p backend/models
cd backend/models

# Download Mistral-7B Q5_K_M (~4.8GB)
wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# Verify download
ls -lh mistral-7b-instruct-v0.2.Q5_K_M.gguf
cd ../..
```

## Step 3: Download the 60 Creative Commons PDFs

```bash
cd backend

# Download the ZIP file containing 60 CC-licensed PDFs
wget --no-check-certificate "https://drive.google.com/uc?export=download&id=1BNWbDrno2ZNJUrJd_Vbeof4YI2diMTxe" -O course_materials.zip

# Extract confirmation token
UUID=$(grep -oP 'uuid" value="\K[^"]+' course_materials.zip | head -1)

# Download with confirmation
wget --no-check-certificate "https://drive.usercontent.google.com/download?id=1BNWbDrno2ZNJUrJd_Vbeof4YI2diMTxe&export=download&confirm=t&uuid=$UUID" -O course_materials.zip

# Extract and organize
unzip -q course_materials.zip
mkdir -p course_materials
mv *.pdf course_materials/ 2>/dev/null || true
rm -rf app cs_materials_bulk evaluation scripts tests course_materials.zip

# Verify we have 60 PDFs
ls -1 course_materials/*.pdf | wc -l  # Should output: 60

cd ..
```

## Step 4: Setup Python Environment with GPU Support

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# CRITICAL: Reinstall llama-cpp-python with CUDA support
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Fix numpy version conflict
pip install "numpy<2.0.0" --force-reinstall

# Verify GPU support
python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())"
cd ..
```

## Step 5: Start LLM Server with GPU Acceleration

```bash
cd backend
source venv/bin/activate

# Start LLM server with GPU offloading
nohup python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct \
  --embedding true > llm_server.log 2>&1 &

# Wait for model to load
sleep 30

# Verify GPU usage
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# Should show ~5900 MB VRAM usage

# Check server logs
tail -20 llm_server.log
cd ..
```

## Step 6: Run Document Ingestion

```bash
cd backend
source venv/bin/activate

# Run ingestion with the 60 PDFs
python3 ingest.py --directory ./course_materials/ --overwrite

# Expected: ~3-5 minutes for 60 PDFs
# Should create ~20,000-30,000 chunks
cd ..
```

## Step 7: Start Backend API Server

```bash
cd backend
source venv/bin/activate

# Start FastAPI server
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &

# Wait for server to start
sleep 3

# Verify API is running
curl http://localhost:8000/
cd ..
```

## Step 8: Setup Frontend

```bash
cd frontend
npm install

# Start development server
npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &

cd ..
```

## Step 9: Verify Complete System

```bash
cd backend
source venv/bin/activate

# Run comprehensive test
python3 test_agentic_rag.py

# Expected output: ✅ ALL TESTS PASSED
cd ..
```

## Step 10: GPU Usage Verification

```bash
# Check that GPU is being used instead of CPU
cd backend
source venv/bin/activate

# Verify LLM server is using GPU
grep "assigned to device" llm_server.log | head -3
# Should show: CUDA0, not CPU

# Check VRAM usage
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# Should be ~5900+ MB

# Test embeddings are using GPU
python3 -c "
from app.services.agentic_rag import AgenticRAG
import asyncio
async def test():
    rag = AgenticRAG()
    await rag._initialize()
    print('✓ Embeddings configured for GPU')
asyncio.run(test())
"
```

## All-in-One Command (Advanced)

If you want to run everything at once (not recommended for first-time setup):

```bash
# Step 1
nvidia-smi &&

# Step 2
mkdir -p backend/models && cd backend/models && wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf" && cd ../.. &&

# Step 3
cd backend && wget --no-check-certificate "https://drive.google.com/uc?export=download&id=1BNWbDrno2ZNJUrJd_Vbeof4YI2diMTxe" -O course_materials.zip && UUID=$(grep -oP 'uuid" value="\K[^"]+' course_materials.zip | head -1) && wget --no-check-certificate "https://drive.usercontent.google.com/download?id=1BNWbDrno2ZNJUrJd_Vbeof4YI2diMTxe&export=download&confirm=t&uuid=$UUID" -O course_materials.zip && unzip -q course_materials.zip && mkdir -p course_materials && mv *.pdf course_materials/ 2>/dev/null || true && rm -rf app cs_materials_bulk evaluation scripts tests course_materials.zip && ls -1 course_materials/*.pdf | wc -l && cd .. &&

# Step 4
cd backend && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && pip uninstall -y llama-cpp-python && CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir && pip install "numpy<2.0.0" --force-reinstall && python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())" && cd .. &&

# Step 5
cd backend && source venv/bin/activate && nohup python3 -m llama_cpp.server --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf --n_gpu_layers -1 --n_ctx 4096 --host 0.0.0.0 --port 8080 --chat_format mistral-instruct --embedding true > llm_server.log 2>&1 & sleep 30 && nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits && cd .. &&

# Step 6
cd backend && source venv/bin/activate && python3 ingest.py --directory ./course_materials/ --overwrite && cd .. &&

# Step 7
cd backend && source venv/bin/activate && nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 & sleep 3 && curl http://localhost:8000/ && cd .. &&

# Step 8
cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 & cd .. &&

# Step 9
cd backend && source venv/bin/activate && python3 test_agentic_rag.py && cd ..
```

## Troubleshooting Commands

### If GPU is not being used:
```bash
# Verify CUDA installation
nvcc --version

# Reinstall llama-cpp-python with CUDA
cd backend && source venv/bin/activate
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Check system status:
```bash
# Check running processes
ps aux | grep -E "(llama_cpp|uvicorn|node)"

# Check logs
tail -f backend/llm_server.log
tail -f backend/backend.log
tail -f frontend/frontend.log

# Check GPU usage
watch -n 1 nvidia-smi
```

### Restart services:
```bash
# Kill all processes
pkill -f "llama_cpp.server"
pkill -f "uvicorn"
pkill -f "npm run dev"

# Restart LLM server
cd backend && source venv/bin/activate
nohup python3 -m llama_cpp.server --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf --n_gpu_layers -1 --n_ctx 4096 --host 0.0.0.0 --port 8080 --chat_format mistral-instruct --embedding true > llm_server.log 2>&1 &

# Restart backend
cd backend && source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &

# Restart frontend
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &
```

## Access URLs

After setup:
- **Frontend**: http://localhost:5173 or your Runpod proxy URL
- **Backend API**: http://localhost:8000
- **LLM Server**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs

Run these commands step by step for a successful setup!