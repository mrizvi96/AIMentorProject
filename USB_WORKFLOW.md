# USB Drive Workflow for Runpod Instances

This guide explains how to use your USB drive with the Mistral-7B model to quickly set up new Runpod instances.

## What's on Your USB Drive

- `Mistral-7B-Instruct-v0.2.Q5_K_M.gguf` (5.13 GB) - The LLM model
- `Dockerfile` (optional reference)

## Setup Workflow for New Runpod Instances

### Step 1: Start a New Runpod Instance

1. Go to Runpod.io and start a new GPU instance
2. Select RTX A5000 (24GB VRAM) or similar
3. Use template: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
4. Note the SSH connection details

### Step 2: Upload Model to Runpod

**Option A: Via VS Code (Recommended)**

1. Connect to Runpod via VS Code Remote-SSH:
   - Press `Ctrl+Shift+P`
   - Type "Remote-SSH: Connect to Host"
   - Enter: `root@[RUNPOD_IP]`

2. Create models directory:
   - Open terminal in VS Code: `` Ctrl+` ``
   - Run: `mkdir -p /workspace/models`

3. Copy model from USB drive:
   - On Windows, copy `Mistral-7B-Instruct-v0.2.Q5_K_M.gguf` from USB (D:) to `C:\temp\`
   - In VS Code Explorer, navigate to `/workspace/models/`
   - Right-click in the folder and select "Upload..."
   - Select the model file from `C:\temp\`
   - **Upload time: ~5-10 minutes** (depending on internet speed)

**Option B: Via SCP (Command Line)**

```powershell
# From Windows PowerShell (with USB drive as D:)
scp D:\Mistral-7B-Instruct-v0.2.Q5_K_M.gguf root@[RUNPOD_IP]:/workspace/models/
```

### Step 3: Download Startup Scripts

If this is a fresh Runpod instance, download the startup script:

```bash
cd /workspace
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
# Or manually download start_llm_server.sh
```

Or create the startup script manually (see below).

### Step 4: Start the LLM Server

```bash
cd /workspace
chmod +x start_llm_server.sh
./start_llm_server.sh
```

The script will:
- Verify the model file exists
- Install llama-cpp-python with CUDA support (~2-3 minutes)
- Start the Mistral-7B server on port 8080

**Total startup time: ~10-15 minutes** (mostly model upload)

### Step 5: Test the Server

In a new terminal:

```bash
# Check if server is running
curl http://localhost:8080/v1/models

# Test chat completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### Step 6: Start Backend Services

Once the LLM server is running, start the rest of your stack:

```bash
# Start Milvus (vector database)
cd /workspace/AIMentorProject
docker-compose up -d

# Start FastAPI backend (in tmux or separate terminal)
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Manual Startup Script

If you need to create `start_llm_server.sh` manually, copy this:

```bash
#!/bin/bash
set -e

MODEL_PATH="/workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf"

if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: Model file not found at $MODEL_PATH"
    echo "Please upload the model from your USB drive first!"
    exit 1
fi

echo "Installing llama-cpp-python with CUDA support..."
CMAKE_ARGS="-DGGML_CUDA=on" pip install "llama-cpp-python[server]"

echo "Starting Mistral-7B Server on port 8080..."
python3 -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --n_gpu_layers -1 \
    --n_ctx 4096 \
    --host 0.0.0.0 \
    --port 8080 \
    --chat_format mistral-instruct
```

Save it, make it executable (`chmod +x start_llm_server.sh`), and run it.

## Tips

- **Keep USB drive safe**: This is your portable model storage
- **Alternative storage**: Upload model to Google Drive/Dropbox for faster downloads
- **Model verification**: After upload, verify file size:
  ```bash
  ls -lh /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf
  # Should show: 4.8G or 5.0G
  ```
- **Startup script in tmux**: Run the LLM server in a tmux session so it persists:
  ```bash
  tmux new -s llm
  ./start_llm_server.sh
  # Press Ctrl+B, then D to detach
  ```

## Comparison: Old vs New Workflow

**Old Workflow (Download Model Each Time):**
- Start Runpod instance
- Download model from HuggingFace: **60+ minutes**
- Install dependencies: 2-3 minutes
- Start server: 10 seconds
- **Total: ~65 minutes**

**New Workflow (USB Drive):**
- Start Runpod instance
- Upload model from USB: **5-10 minutes**
- Install dependencies: 2-3 minutes
- Start server: 10 seconds
- **Total: ~10-15 minutes**

**Time saved: ~50 minutes per instance!**
