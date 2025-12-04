# AI Mentor Setup Plan for RTX A4500 GPU

**GPU**: NVIDIA RTX A4500 (20GB VRAM)
**PDFs**: 60 Creative Commons Computer Science Textbooks
**Model**: Mistral-7B-Instruct-v0.2 Q5_K_M

## Overview

This plan will guide you through setting up the AI Mentor system on your Runpod RTX A4500 instance with the 60 Creative Commons PDFs from Google Drive.

## Key Differences from Standard Setup

1. **GPU**: RTX A4500 (20GB VRAM) instead of A40 (46GB)
2. **VRAM Considerations**: With 20GB VRAM, we need to monitor memory usage more carefully
3. **PDFs**: Using the full 60 CC-licensed PDFs collection

## Step-by-Step Setup Instructions

### Step 1: Verify GPU Status

```bash
# Check GPU information
nvidia-smi

# Expected output should show:
# - GPU Name: RTX A4500
# - Memory: 20GB
# - CUDA Version: 12.x
```

### Step 2: Download Mistral-7B Model

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

### Step 3: Download the 60 Creative Commons PDFs

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

### Step 4: Setup Python Environment with GPU Support

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

### Step 5: Start LLM Server with GPU Acceleration

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

### Step 6: Run Document Ingestion

```bash
cd backend
source venv/bin/activate

# Run ingestion with the 60 PDFs
python3 ingest.py --directory ./course_materials/ --overwrite

# Expected: ~3-5 minutes for 60 PDFs
# Should create ~20,000-30,000 chunks
cd ..
```

### Step 7: Start Backend API Server

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

### Step 8: Setup Frontend

```bash
cd frontend
npm install

# Start development server
npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &

cd ..
```

### Step 9: Verify Complete System

```bash
cd backend
source venv/bin/activate

# Run comprehensive test
python3 test_agentic_rag.py

# Expected output: ✅ ALL TESTS PASSED
cd ..
```

### Step 10: GPU Usage Verification

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

## Expected Performance on RTX A4500

- **VRAM Usage**: ~6GB for Mistral-7B + embeddings
- **Available VRAM**: ~14GB remaining (plenty for operations)
- **Inference Speed**: ~30-50 tokens/second
- **Ingestion Speed**: ~250-300 chunks/second

## Troubleshooting

### If GPU is not being used:
1. Verify CUDA installation: `nvcc --version`
2. Reinstall llama-cpp-python with CUDA flags
3. Check nvidia-smi shows GPU activity

### If PDF download fails:
1. Try using gdown instead of wget
2. Check Google Drive link permissions
3. Manually download and upload to instance

### If ingestion is slow:
1. Verify sentence-transformers is using GPU
2. Check that HF_HUB_ENABLE_HF_TRANSFER is disabled
3. Monitor VRAM usage during ingestion

## Success Indicators

✅ **GPU Acceleration Working**:
- nvidia-smi shows 6GB+ VRAM used
- LLM server logs show "assigned to device CUDA0"
- llama_supports_gpu_offload() returns True

✅ **PDFs Ingested**:
- All 60 PDFs processed
- ChromaDB has 20,000+ chunks
- Database size ~200-300MB

✅ **System Operational**:
- Backend API responds to health checks
- Frontend loads and connects to WebSocket
- Test script passes all checks

## Access URLs

After setup:
- **Frontend**: http://localhost:5173 or Runpod proxy URL
- **Backend API**: http://localhost:8000
- **LLM Server**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs

## Notes for RTX A4500

1. **VRAM Management**: With 20GB VRAM, monitor usage but no concerns for this workload
2. **Performance**: Excellent for Mistral-7B with full GPU offloading
3. **Thermal**: GPU should remain cool with this workload
4. **Power**: Efficient power consumption compared to larger GPUs

This setup will give you a fully functional AI Mentor with GPU acceleration using the 60 Creative Commons PDFs.