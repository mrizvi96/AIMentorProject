# Claude Log - Runpod Setup & Error Fixes

**Purpose**: Document all errors encountered during Runpod instance setup and their solutions to minimize repeated debugging in new sessions.

**Last Updated**: October 26, 2025
**Instance**: NVIDIA A40 (46GB VRAM), Ubuntu 24.04, CUDA 12.7

---

## 🚀 FRESH RUNPOD INSTANCE - COPY/PASTE BOOT SCRIPT

**What this does**: Sets up everything needed for a new Runpod instance in ~10 minutes.

**Prerequisites**:
- Runpod instance with NVIDIA GPU (A40, RTX A5000, or similar)
- Ubuntu 24.04 or similar
- Git installed

### Step 1: Clone Repository
```bash
cd /root
git clone https://github.com/mrizvi96/AIMentorProject.git AIMentorProject-1
cd AIMentorProject-1
```

### Step 2: Download Model (~2 minutes)
```bash
mkdir -p backend/models
cd backend/models
wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
cd ../..
```

### Step 3: Download Course Materials (~1 minute)
```bash
pip3 install gdown
cd backend

# Download CC-licensed computer science PDFs from Google Drive folder
# This folder contains 14 verified open-source textbooks (CC BY, CC BY-SA, CC0, Public Domain)
# All materials verified to allow commercial AI training (no NC/ND restrictions)
gdown --folder "1kRGaPosd1ZcX6u918NZD5V1Q_S8C2anp" -O course_materials/

# Move files from nested directory if needed
if [ -d "course_materials/freeCSbooks" ]; then
    mv course_materials/freeCSbooks/* course_materials/
    rmdir course_materials/freeCSbooks
fi

# Run harvester to download additional 7 PDFs (to reach 21 total, ~243MB)
# Uses curated sources from scripts/cs_textbooks_catalog.json
source venv/bin/activate
pip install -q requests beautifulsoup4 PyPDF2
python3 scripts/practical_harvester.py --max-items 10 --output-dir course_materials

# Copy harvested PDFs from bulk collection to course_materials
cp cs_materials_bulk/*.pdf course_materials/ 2>/dev/null

# Verify we have 21 PDFs
ls -1 course_materials/*.pdf | wc -l  # Should output: 21

cd ..
```

### Step 4: Setup Python Environment (~3-5 minutes)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# CRITICAL: Reinstall llama-cpp-python with GPU support
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install "numpy<2.0.0" --force-reinstall

# Install WebSocket testing library
pip install websockets
cd ..
```

### Step 5: Start LLM Server (~30 seconds to load)
```bash
cd backend
source venv/bin/activate
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
cd ..
```

### Step 6: Verify GPU Acceleration
```bash
cd backend
source venv/bin/activate
python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())"
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# Should show ~5900 MB VRAM usage
cd ..
```

### Step 7: Run Document Ingestion (~3-5 minutes)
```bash
cd backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
cd ..
```

### Step 8: Test System
```bash
cd backend
source venv/bin/activate
python3 test_agentic_rag.py
# Should see: ✅ ALL TESTS PASSED
cd ..
```

### ✅ System Ready!
Your AI Mentor is now operational. Total setup time: ~10 minutes.

---

## Quick Start Checklist for New Runpod Instance (Detailed)

### 1. System Verification
```bash
nvidia-smi  # Should show NVIDIA A40 with 46GB VRAM
python3 --version  # Should be 3.12+
```

### 2. Download Model & Data
```bash
# Download Mistral-7B Q5_K_M (~5GB, takes ~2 min)
mkdir -p /root/AIMentorProject-1/backend/models
cd /root/AIMentorProject-1/backend/models
wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# Download course PDFs using gdown
pip install gdown
cd /root/AIMentorProject-1/backend/course_materials
gdown "1DECFKmdQjbLRQpJWQUd1J6KViRIPf6ab"  # Computer Science Big Fat Notebook
gdown "1WVTdiVOhe7Oov2TDG3AXIg3c8HIthSac"  # MIT Textbook
gdown "1YAqEenI_z6CyZBSEUPgO2gjAELw5bwIt"  # Self-Taught Programmer
gdown "1mgJSWWzcA1PnHytQVp0kt5dyXx2NzIn0"  # Introduction to Algorithms
gdown "1nR4Mrx8BdTAOxGL_SXk80RRb9Oy-oeiZ"  # Computer Science Notebook (duplicate)
gdown "1sAEmzgyx63SMQCGmCuSddnzxfXrUKFZE"  # Practical Programming
```

### 3. Setup Python Environment with GPU Support
```bash
cd /root/AIMentorProject-1/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# CRITICAL: Reinstall llama-cpp-python with CUDA support
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Fix numpy version conflict
pip install "numpy<2.0.0" --force-reinstall

# Verify GPU support
python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())"
# Should output: CUDA: True, Device 0: NVIDIA A40
```

### 4. Start LLM Server (Mistral-7B on GPU)
```bash
cd /root/AIMentorProject-1/backend
source venv/bin/activate

nohup python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct \
  --embedding true > llm_server.log 2>&1 &

# Verify (wait 30 seconds for model to load)
sleep 30
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits  # Should show ~5900 MB
curl -s http://localhost:8080/v1/models | python3 -m json.tool
```

### 5. Run Document Ingestion
```bash
cd /root/AIMentorProject-1/backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
# Expected time: 3-5 minutes for 6 PDFs with sentence-transformers
```

### 6. Test System
```bash
python3 test_agentic_rag.py  # Test the RAG workflow
```

---

## Error Log & Fixes

### ERROR 1: GPU Not Being Used (CPU Inference)

**Symptoms**:
- `nvidia-smi` shows only 2MB VRAM instead of ~5.9GB
- Server logs show "assigned to device CPU" instead of "CUDA0"
- Inference very slow (30+ seconds per response)

**Root Cause**:
llama-cpp-python installed from requirements.txt without CUDA support. Default pip installation is CPU-only.

**Fix**:
```bash
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install "numpy<2.0.0" --force-reinstall  # Fix numpy conflict
```

**Verification**:
```bash
python3 -c "from llama_cpp import llama_supports_gpu_offload; print(llama_supports_gpu_offload())"
# Output: True (with "Device 0: NVIDIA A40..." message)

nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# Output: 5900+ MB after starting LLM server

grep "assigned to device" llm_server.log | head -3
# Should show: CUDA0, not CPU
```

---

### ERROR 2: Slow Ingestion (2 seconds per chunk)

**Symptoms**:
- Ingestion takes 30-40 minutes for 6 PDFs
- Processing at ~0.5 chunks per second
- Using Mistral-7B for embeddings

**Root Cause**:
Using full 7B instruction model (Mistral) for embeddings is overkill. Designed for text generation, not embeddings.

**Why Previous Session Used This**:
Previous attempt with sentence-transformers failed due to `HF_HUB_ENABLE_HF_TRANSFER` environment variable being set without the hf_transfer package.

**Fix**:
Use dedicated embedding model (sentence-transformers) on GPU instead of LLM server.

**File Changes**:

**1. `backend/ingest.py`** - Lines 1-7 (add at top):
```python
"""
Document Ingestion Script
"""
import os
# Disable hf_transfer before any other imports
os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)
```

**2. `backend/ingest.py`** - Lines 11-17 (update imports):
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

from app.core.config import settings
```

**3. `backend/ingest.py`** - Lines 83-97 (update setup_embedding_model):
```python
def setup_embedding_model():
    """Setup embedding model using sentence-transformers (GPU-accelerated)"""
    try:
        logger.info("Configuring embeddings via sentence-transformers (GPU-accelerated)")
        embed_model = HuggingFaceEmbedding(
            model_name="all-MiniLM-L6-v2",  # Fast, lightweight embedding model
            device="cuda"  # Use GPU for fast embeddings
        )
        logger.info("✓ Embedding model configured (sentence-transformers on GPU)")
        return embed_model
    except Exception as e:
        logger.error(f"Failed to configure embedding model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**4. `backend/app/services/agentic_rag.py`** - Lines 8-12 (update imports):
```python
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from .mistral_llm import MistralLLM
import chromadb
```

**5. `backend/app/services/agentic_rag.py`** - Lines 34-44 (update _initialize):
```python
        # Configure embedding model (using sentence-transformers on GPU)
        logger.info("  Configuring embeddings via sentence-transformers...")
        import os
        # Disable hf_transfer to avoid dependency issues
        os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)

        embed_model = HuggingFaceEmbedding(
            model_name="all-MiniLM-L6-v2",  # Fast, lightweight embedding model
            device="cuda"  # Use GPU for fast embeddings
        )
        Settings.embed_model = embed_model
```

**Performance Improvement**:
- **Before**: ~2 seconds per chunk (0.5 chunks/second)
- **After**: ~0.003 seconds per chunk (250-310 chunks/second)
- **Speed increase**: ~600x faster!
- **Time for 6 PDFs**: 3-5 minutes instead of 30-40 minutes

---

### ERROR 3: HuggingFace Download Fails (HF_HUB_ENABLE_HF_TRANSFER)

**Full Error**:
```
ValueError: Fast download using 'hf_transfer' is enabled (HF_HUB_ENABLE_HF_TRANSFER=1)
but 'hf_transfer' package is not available in your environment.
Try `pip install hf_transfer`.
```

**Root Cause**:
Environment variable `HF_HUB_ENABLE_HF_TRANSFER=1` is set (likely system-wide in Runpod), but `hf_transfer` package is not installed.

**Fix**:
Disable the environment variable before importing huggingface libraries:

```python
import os
os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)
```

**Where to Add**: At the very top of scripts that use HuggingFace models (before any imports).

**Files Modified**:
- `backend/ingest.py` (line 5-7)
- `backend/app/services/agentic_rag.py` (line 36-38 in _initialize method)

---

### ERROR 4: Wrong Embedding Model Name

**Error**:
```
OSError: Can't load the configuration of 'sentence-transformers/all-MiniLM-L6-v2'
```

**Root Cause**:
Using `sentence-transformers/all-MiniLM-L6-v2` or `BAAI/bge-small-en-v1.5` as model names. HuggingFaceEmbedding internally prepends prefixes, causing path issues.

**Fix**:
Use simple model name without prefix:
- ❌ Wrong: `"sentence-transformers/all-MiniLM-L6-v2"`
- ❌ Wrong: `"BAAI/bge-small-en-v1.5"`
- ✅ Correct: `"all-MiniLM-L6-v2"`

**Verification**:
```bash
source venv/bin/activate
python3 -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda'); print('✓ Model loaded')"
```

---

## Architecture Notes

### Two-Model System

The AI Mentor uses TWO separate models for different jobs:

**1. Embedding Model (sentence-transformers, ~80MB)**
- **Job**: Convert text → vectors for similarity search
- **When**: During ingestion + when user asks a question
- **Model**: all-MiniLM-L6-v2 on GPU
- **Speed**: ~300 batches/second

**2. LLM (Mistral-7B, 4.8GB)**
- **Job**: AI reasoning, answer generation, document grading
- **When**: During agentic RAG workflow (retrieve → grade → rewrite → generate)
- **Model**: Mistral-7B-Instruct-v0.2 Q5_K_M on GPU
- **VRAM**: 5.9GB

**Why This Works**:
- Embedding model handles fast vectorization
- Mistral-7B does the actual "thinking"
- Both run on same GPU (A40 has 46GB, plenty of room)
- Answer quality SAME or BETTER than using Mistral for embeddings

---

## VRAM Usage

**Does more VRAM help?**
- ❌ **No** - Current setup uses 5.9GB out of 46GB available
- VRAM is NOT the bottleneck
- More VRAM would only help if using larger models (13B+)

**What Actually Matters**:
- ✅ GPU acceleration enabled (CMAKE_ARGS="-DGGML_CUDA=on")
- ✅ Using dedicated embedding model
- ✅ All layers offloaded to GPU (`--n_gpu_layers -1`)

---

## Common Debugging Commands

```bash
# Check GPU usage
nvidia-smi
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits

# Check if LLM server is running
ps aux | grep llama_cpp.server
curl -s http://localhost:8080/v1/models | python3 -m json.tool

# Check LLM server logs
tail -50 llm_server.log
grep "assigned to device" llm_server.log | head -5  # Should show CUDA0

# Test embeddings endpoint
curl -s -X POST http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "test", "model": "text-embedding-ada-002"}' | head -20

# Check ChromaDB status
python3 << 'EOF'
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
try:
    collection = client.get_collection(name="course_materials")
    print(f"Total chunks in database: {collection.count()}")
except:
    print("Collection does not exist yet")
EOF
```

---

## File Locations

```
/root/AIMentorProject-1/
├── backend/
│   ├── models/
│   │   └── mistral-7b-instruct-v0.2.Q5_K_M.gguf  # 4.8GB
│   ├── course_materials/                          # 6 PDFs, 153MB
│   ├── chroma_db/                                 # Vector database (created during ingestion)
│   ├── venv/                                      # Python virtual environment
│   ├── ingest.py                                  # Modified for sentence-transformers
│   ├── app/services/agentic_rag.py               # Modified for sentence-transformers
│   └── llm_server.log                            # LLM server output
└── CLAUDE_LOG.md                                  # This file
```

---

## Success Indicators

✅ **GPU Acceleration Working**:
- `nvidia-smi` shows 5.9GB VRAM used
- LLM server logs show "assigned to device CUDA0"
- `llama_supports_gpu_offload()` returns True

✅ **Embeddings Working**:
- Model loads in ~2 seconds
- Ingestion processes 250-310 batches/second
- No HF_HUB_ENABLE_HF_TRANSFER errors

✅ **Ingestion Complete**:
- All 6 PDFs processed
- ChromaDB collection has ~3000-4000 chunks
- `chroma_db/` directory ~50-100MB

✅ **System Ready**:
- Test script passes
- Backend API responds to `/` health check
- WebSocket chat works

---

## Quick Recovery Commands

If something breaks mid-session:

```bash
# Restart LLM server
pkill -f "llama_cpp.server"
cd /root/AIMentorProject-1/backend
source venv/bin/activate
nohup python3 -m llama_cpp.server --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf --n_gpu_layers -1 --n_ctx 4096 --host 0.0.0.0 --port 8080 --chat_format mistral-instruct --embedding true > llm_server.log 2>&1 &

# Re-run ingestion (if it failed mid-way)
python3 ingest.py --directory ./course_materials/ --overwrite

# Check background processes
ps aux | grep python3
```

---

### ERROR 5: WebSocket Streaming - stream_chat() AttributeError

**Full Error**:
```
AttributeError: 'dict' object has no attribute 'role'
  File "/root/AIMentorProject-1/backend/app/services/agentic_rag.py", line 452
    stream_response = self.llm.stream_chat([{"role": "user", "content": generation_prompt}])
  File ".../mistral_llm.py", line 80, in stream_chat
    prompt = self.messages_to_prompt(messages)
  File ".../generic_utils.py", line 35, in messages_to_prompt
    role = message.role
AttributeError: 'dict' object has no attribute 'role'
```

**Symptoms**:
- WebSocket connection succeeds
- Workflow events stream correctly (retrieve, grade, generate)
- Error occurs when trying to stream answer tokens
- No answer returned to user

**Root Cause**:
`stream_chat()` expects LlamaIndex `ChatMessage` objects (with `.role` and `.content` attributes), not plain Python dictionaries.

**Fix**:
Use `stream_complete(prompt_string)` instead of `stream_chat(messages_list)` for the MistralLLM class.

**File: `backend/app/services/agentic_rag.py`** - Lines 450-463:

**❌ WRONG (causes error)**:
```python
stream_response = self.llm.stream_chat([{"role": "user", "content": generation_prompt}])
```

**✅ CORRECT**:
```python
stream_response = self.llm.stream_complete(generation_prompt)

answer_buffer = ""
for chunk in stream_response:
    # Extract token from CompletionResponse
    token = chunk.text if hasattr(chunk, 'text') else str(chunk)

    answer_buffer += token
    yield {
        "type": "token",
        "content": token
    }
```

**Why This Works**:
- `stream_complete()` accepts a plain string prompt (from `mistral_llm.py:50`)
- `stream_chat()` wraps `stream_complete()` but expects structured message objects
- For custom LLM implementations like MistralLLM, use `stream_complete()` directly

**Testing WebSocket Streaming**:
```bash
cd /root/AIMentorProject-1/backend
source venv/bin/activate

# Start backend server (in background)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &

# Run WebSocket test
python3 test_streaming_ws.py

# Expected output:
# ✓ WebSocket connected
# [WORKFLOW] Running retrieve...
# [WORKFLOW] Running grade_documents...
# [WORKFLOW] Running generate...
# <streamed answer tokens>
# ✓ Answer received (777+ chars)
```

---

## Testing Commands

```bash
# Test WebSocket streaming (single question)
cd /root/AIMentorProject-1/backend
source venv/bin/activate
python3 test_streaming_ws.py

# Test multiple questions in sequence
python3 test_streaming_ws.py multi

# Test agentic RAG (non-streaming)
python3 test_agentic_rag.py
```

---

### ERROR 6: Frontend lib/ Directory Ignored by Git

**Full Error**:
```
The following paths are ignored by one of your .gitignore files:
frontend/src/lib
hint: Use -f if you really want to add them.
```

**Symptoms**:
- Frontend source files (components, stores, API) not tracked by Git
- `git status` shows only modified files, not new lib/ directory
- Changes to frontend components don't appear in repository

**Root Cause**:
Root-level `.gitignore` contains `lib/` pattern intended to exclude Python virtual environment directories (`lib/` and `lib64/`), but it also catches the frontend SvelteKit `src/lib/` directory which contains important source code.

**Fix**:
Force-add the frontend lib directory:

```bash
git add -f frontend/src/lib/
```

**Better Long-Term Fix**:
Update root `.gitignore` to be more specific:

```gitignore
# Python virtual environment (change from lib/ to:)
venv/lib/
venv/lib64/
backend/venv/lib/
backend/venv/lib64/
```

This prevents the pattern from catching frontend source directories.

**Verification**:
```bash
git status
# Should now show:
#   new file:   frontend/src/lib/api.ts
#   new file:   frontend/src/lib/components/...
```

---

### ERROR 7: WebSocket Connection 403 Forbidden

**Full Error in Backend Logs**:
```
INFO:     ('127.0.0.1', 41558) - "WebSocket /ws/chat/14aebee9-d07c-4fb6-a7e3-6bf590ed9758" 403
INFO:     connection rejected (403 Forbidden)
INFO:     connection closed
```

**Frontend Error**:
```
⚠️ Connection error. Please check if the backend is running.
```

**Symptoms**:
- Frontend sends WebSocket connection request
- Backend rejects with 403 Forbidden
- Chat input remains disabled with spinning loading indicator
- No response to user queries

**Root Cause**:
WebSocket endpoint path mismatch between frontend and backend:
- **Frontend**: `/ws/chat/{conversation_id}` (with parameter)
- **Backend**: `/api/ws/chat` (no parameter)

Additionally, frontend was sending plain string instead of JSON format.

**Fix**:

**File: `frontend/src/lib/api.ts`** - Line 49:

**❌ WRONG**:
```typescript
socket = new WebSocket(`${WS_BASE}/ws/chat/${currentConversationId}`);
socket.onopen = () => {
    socket?.send(userMessage);  // Plain string
}
```

**✅ CORRECT**:
```typescript
socket = new WebSocket(`${WS_BASE}/api/ws/chat`);
socket.onopen = () => {
    socket?.send(JSON.stringify({
        message: userMessage,
        max_retries: 2
    }));
}
```

**Why This Works**:
- Backend WebSocket endpoint defined at `/api/ws/chat` in `chat_ws.py:17`
- Backend expects JSON: `{"message": "...", "max_retries": 2}`
- No conversation_id parameter needed (stateless per connection)

**Verification**:
```bash
# Check backend logs after fix
tail -f backend/backend.log
# Should see:
# INFO:     WebSocket connection established
# INFO:     Received question: What is python?...
```

---

### ERROR 8: Loading State Not Clearing After Response

**Symptoms**:
- User asks a question
- Response streams successfully
- Sources display correctly
- BUT input field remains disabled
- Spinning loading indicator never disappears
- User cannot ask follow-up questions

**Root Cause**:
Frontend receives "complete" event from backend but never clears the `isLoading` store or closes the WebSocket. The connection stays open indefinitely, keeping the UI in loading state.

**Fix**:

**File: `frontend/src/lib/api.ts`** - Lines 114-138:

**❌ WRONG (missing cleanup)**:
```typescript
} else if (data.type === 'complete') {
    // Add sources to message
    messages.update(msgs => {
        return msgs.map(m =>
            m.id === assistantMessageId
                ? { ...m, sources: sourceNames }
                : m
        );
    });
    // Missing: isLoading.set(false) and socket.close()
}
```

**✅ CORRECT**:
```typescript
} else if (data.type === 'complete') {
    // Backend sends final completion with sources
    const sourceNames = data.sources?.map((s: any, i: number) =>
        `Source ${i + 1}: ${s.text.substring(0, 100)}...`
    ) || [];

    // Add sources to message
    messages.update(msgs => {
        return msgs.map(m =>
            m.id === assistantMessageId
                ? { ...m, sources: sourceNames }
                : m
        );
    });

    // Response is complete - clear loading state
    isLoading.set(false);
    currentWorkflow.set([]);

    // Close the socket since we're done
    if (socket) {
        socket.close();
        socket = null;
    }
}
```

**Why This Works**:
- `isLoading.set(false)` re-enables the chat input
- `currentWorkflow.set([])` clears workflow visualization
- `socket.close()` properly terminates the WebSocket connection
- Sets socket to `null` to prevent reuse

**Verification**:
1. Ask a question in the UI
2. Wait for complete response
3. Input field should become enabled immediately
4. Spinning indicator should disappear
5. Can type new question right away

---

### ERROR 9: Numpy Version Conflict After CUDA Reinstall

**Full Error**:
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
llama-index-core 0.10.68.post1 requires numpy<2.0.0, but you have numpy 2.3.4 which is incompatible.
```

**Symptoms**:
- After reinstalling llama-cpp-python with CUDA support, numpy 2.3.4 is automatically installed
- llama-index-core requires numpy<2.0.0
- Version conflict warnings appear during pip install
- May cause runtime errors when using llama-index

**Root Cause**:
When rebuilding llama-cpp-python from source with CMAKE_ARGS="-DGGML_CUDA=on", pip installs the latest numpy version (2.3.4) as a dependency. However, llama-index-core specifically requires numpy<2.0.0 due to API compatibility issues.

**Fix**:
Downgrade numpy immediately after CUDA reinstall:

```bash
source venv/bin/activate
pip install "numpy<2.0.0" --force-reinstall
```

**Verification**:
```bash
python3 -c "import numpy; print('Numpy version:', numpy.__version__)"
# Should output: Numpy version: 1.26.4 (or any version <2.0.0)
```

**Why This Works**:
- Numpy 1.26.x is compatible with both llama-cpp-python and llama-index-core
- The --force-reinstall flag ensures the correct version is installed even if a newer version exists
- This step must be done AFTER the CUDA reinstall, not before

**Important Note**:
This fix is REQUIRED for the system to work correctly. Without it, you may encounter runtime errors when using the RAG services that depend on llama-index.

---

### ERROR 10: ChromaDB Ingestion Silent Failure - Empty Database

**Symptoms**:
- Ingestion script runs successfully and reports chunks created (e.g., "9,485 chunks")
- ChromaDB collection shows 0 documents when queried
- Evaluation returns "Empty Response" for all queries with 0 sources
- ChromaDB database file (`chroma_db/chroma.sqlite3`) is abnormally small (~144KB)

**Discovery Process**:
1. Ran automated evaluation (20 questions) - all returned "Empty Response"
2. Manually tested RAG service directly - initially worked, then failed
3. Added debug logging to evaluation script
4. Discovered ChromaDB collection count was 0 despite ingestion logs

**Investigation**:
```bash
# Check ChromaDB document count
cd /root/AIMentorProject/backend
source venv/bin/activate
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection(name='course_materials')
print(f'Total documents: {collection.count()}')
"
# Output with bug: Total documents: 0
# Expected: Total documents: 33757 (for 21 PDFs)
```

**Root Cause**:
Unknown - potentially a timing/state issue with first ingestion run. The ingestion process completed without errors but data was not persisted to ChromaDB. This appears to be an intermittent issue that occurred during the initial ingestion after fresh instance setup.

**Fix**:
Re-run ingestion with --overwrite flag:

```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
```

**Expected Output**:
```
2025-11-05 04:11:39 - INFO - ✓ Document ingestion complete!
2025-11-05 04:11:39 - INFO - Successful PDFs: 21/21
2025-11-05 04:11:39 - INFO - Total chunks: 33757
2025-11-05 04:11:39 - INFO - Collection: course_materials
```

**Verification**:
```bash
# Verify document count
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection(name='course_materials')
print(f'Total documents: {collection.count()}')
"
# Should output: Total documents: 33757

# Check database file size
ls -lh chroma_db/chroma.sqlite3
# Should be ~60-80MB for 21 PDFs, not 144KB

# Test RAG query manually
python3 -c "
from app.services.rag_service import RAGService
import asyncio
async def test():
    rag = RAGService()
    rag.initialize()
    result = await rag.query('What is Python?')
    print(f'Response length: {len(result[\"response\"])} chars')
    print(f'Sources: {len(result[\"sources\"])}')
asyncio.run(test())
"
# Should show response with multiple sources
```

**Discrepancy Note**:
- First ingestion reported: 9,485 chunks
- Second ingestion reported: 33,757 chunks
- This suggests the first run may have processed fewer PDFs or encountered silent failures

**Prevention Recommendations**:
1. Always verify ChromaDB document count after ingestion
2. Check database file size (should be ~3MB per PDF on average)
3. Run a test query before proceeding to evaluation
4. Consider adding automatic verification to ingestion script

**Impact**:
CRITICAL - Without this fix, the entire RAG system is non-functional. All queries return empty responses because there are no documents to retrieve from the vector database.

---

### ERROR 11: Evaluation Returns "Empty Response" - Relative Path Bug

**Symptoms**:
- Evaluation script runs without errors
- All 20 questions return "Empty Response" with 0 sources
- Manual RAG testing works perfectly
- ChromaDB shows 33,757 documents when queried from backend directory
- RAG service logs show "ChromaDB collection 'course_materials' has 0 documents"

**Discovery Process**:
1. Fixed ERROR 10 (ChromaDB ingestion failure) - database now has 33,757 documents
2. Ran evaluation - still got "Empty Response" for all queries
3. Tested retrieval directly - worked fine, retrieved 5 nodes with good scores
4. Tested query engine with LLM - worked fine, generated 812-char response
5. Added logging to RAG service initialization - showed 0 documents in collection
6. Discovered evaluation directory has its own empty `chroma_db/` directory
7. Root cause: Relative path `./chroma_db` resolves differently depending on working directory

**Investigation**:
```bash
# From backend directory - WORKS
cd /root/AIMentorProject/backend
python3 -c "import chromadb; c = chromadb.PersistentClient(path='./chroma_db'); print(c.get_collection('course_materials').count())"
# Output: 33757

# From evaluation directory - FAILS (creates new empty database!)
cd /root/AIMentorProject/backend/evaluation
python3 -c "import chromadb; c = chromadb.PersistentClient(path='./chroma_db'); print(c.get_collection('course_materials').count())"
# Output: 0

# Check if empty chroma_db exists in evaluation dir
ls -la /root/AIMentorProject/backend/evaluation/chroma_db
# Shows empty database directory created by evaluation script
```

**Root Cause**:
The config file used a relative path `./chroma_db` which resolves to different absolute paths depending on the current working directory:
- From `/root/AIMentorProject/backend`: resolves to `/root/AIMentorProject/backend/chroma_db` ✅ (correct, has data)
- From `/root/AIMentorProject/backend/evaluation`: resolves to `/root/AIMentorProject/backend/evaluation/chroma_db` ❌ (wrong, empty)

When ChromaDB's `get_or_create_collection()` runs with the evaluation directory path, it creates a NEW empty database and collection.

**Fix**:
Make ChromaDB path absolute in the config file.

**File: `backend/app/core/config.py`** - Lines 1-8 and 29-32:
```python
# Add Path import at top of file
from pathlib import Path

# ... (in Settings class) ...

# ChromaDB Configuration (file-based, no server needed)
# Use absolute path to ensure it works from any directory (e.g., evaluation/)
chroma_db_path: str = str(Path(__file__).parent.parent.parent / "chroma_db")
chroma_collection_name: str = "course_materials"
```

**Path Resolution**:
- `__file__`: `/root/AIMentorProject/backend/app/core/config.py`
- `.parent`: `/root/AIMentorProject/backend/app/core/`
- `.parent.parent`: `/root/AIMentorProject/backend/app/`
- `.parent.parent.parent`: `/root/AIMentorProject/backend/`
- Final path: `/root/AIMentorProject/backend/chroma_db`

**Verification**:
```bash
cd /root/AIMentorProject/backend/evaluation
source ../venv/bin/activate
python3 run_evaluation.py --mode direct

# Should now show in logs:
# ChromaDB collection 'course_materials' has 33757 documents

# Check results file
python3 -c "import json; data = json.load(open('results/evaluation_TIMESTAMP.json')); print(f'Q1 response length: {len(data[\"responses\"][0][\"response\"])} chars')"
# Should show >200 chars, not 14 ("Empty Response")
```

**Cleanup** (optional):
```bash
# Remove the accidentally created empty database in evaluation dir
rm -rf /root/AIMentorProject/backend/evaluation/chroma_db
```

**Impact**:
CRITICAL - Without this fix, the evaluation framework is completely non-functional when run from any directory other than the backend root. The RAG service connects to an empty database, causing all queries to return "Empty Response".

**Why This Was Hard to Debug**:
- All components (LLM, embeddings, ChromaDB, retrieval) worked individually
- The error only manifested when running from a subdirectory
- No error messages were thrown - the system silently created a new empty database
- Logs showed "0 documents" but didn't indicate the path mismatch

---

## Updated Fresh Instance Setup Summary

When setting up a **completely fresh Runpod instance**, follow these steps in order:

### 1. Clone Repository
```bash
cd /root
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject
```

### 2. Download Model & Course Materials
```bash
# Download Mistral-7B Q5_K_M (~2 minutes)
mkdir -p backend/models
cd backend/models
wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# Download course PDFs (~1 minute)
# CC-licensed computer science books (14 PDFs, ~180MB total)
cd ..
pip3 install gdown
gdown --folder "1kRGaPosd1ZcX6u918NZD5V1Q_S8C2anp" -O course_materials/
if [ -d "course_materials/freeCSbooks" ]; then
    mv course_materials/freeCSbooks/* course_materials/
    rmdir course_materials/freeCSbooks
fi
cd ..
```

### 3. Setup Backend Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# CRITICAL: Reinstall llama-cpp-python with CUDA support
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install "numpy<2.0.0" --force-reinstall

# Verify GPU support
python3 -c "from llama_cpp import llama_supports_gpu_offload; print('CUDA:', llama_supports_gpu_offload())"
```

### 4. Start LLM Server
```bash
source venv/bin/activate
nohup python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instruct \
  --embedding true > llm_server.log 2>&1 &

# Wait for model to load (~30 seconds)
sleep 30
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits  # Should show ~5900 MB
```

### 5. Run Document Ingestion
```bash
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
# Takes ~2-3 minutes, creates 4,193 chunks
```

### 6. Start Backend API
```bash
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
sleep 3
curl http://localhost:8000/  # Should return: {"status":"ok",...}
```

### 7. Setup Frontend
```bash
cd ../frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &
```

### 8. Verify System
```bash
cd backend
source venv/bin/activate
python3 test_agentic_rag.py
# Should see: ✅ ALL TESTS PASSED
```

**Total Time**: ~10-15 minutes (first run), ~5 minutes (subsequent runs if model/PDFs cached)

---

## 🔄 RAG System Improvements - November 5, 2025

### Context: Evaluation and Improvements
After initial system deployment, we conducted a comprehensive baseline evaluation and implemented significant improvements to address two critical issues:

1. **High Hallucination Rate** (35% baseline)
2. **Poor Source Citations** (2.40/5.0 baseline)

### Changes Implemented

#### Configuration Changes (config.py)
```python
# Multi-source retrieval and improved context
top_k_retrieval: int = 3  # ↑ from 1
chunk_size: int = 512  # ↑ from 256
chunk_overlap: int = 50  # ↑ from 25
similarity_threshold: float = 0.4  # ↓ from 0.7

# Response generation improvements
llm_max_tokens: int = 768  # ↑ from 512
stop_sequences: []  # removed ["\n\n"]
```

#### Re-ingestion Required
After configuration changes, documents were re-ingested with larger chunks:
```bash
cd backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
# Creates ~33,757 chunks with 512-token chunk size
```

#### Prompt Engineering (rag_service.py)
Major prompt rewrite with:
- Explicit hallucination constraints ("DO NOT add information from general knowledge")
- Detailed citation format requirements: `[Source: filename, page X]`
- Pedagogical approach for intro CS students
- Completeness guidelines (address ALL parts of questions)
- Technical accuracy instructions (honor distinctions in source material)

### Evaluation Files

#### Baseline Evaluation (Completed & Scored)
- **File**: `backend/evaluation/results/evaluation_20251105_043049.json`
- **CSV**: `backend/evaluation/results/evaluation_20251105_043049_scoring_completed.csv`
- **Metrics**:
  - Overall Score: 3.96/5.0
  - Source Citation: 2.40/5.0 🔴
  - Hallucination Rate: 35% 🔴
  - Retrieval Success: 100% ✅

#### Improved System Evaluation (Pending Scoring)
- **File**: `backend/evaluation/results/evaluation_20251105_084005.json`
- **CSV**: `backend/evaluation/results/evaluation_20251105_084005_scoring.csv`
- **Status**: Awaiting manual scoring for comparison

### 🚨 CRITICAL: Ask User for Scored Evaluation on New Instance

**When starting a fresh Runpod instance**, immediately ask the user:

> "Do you have the scored evaluation CSV for the improved system (evaluation_20251105_084005_scoring.csv)?
> Please provide the Google Sheets link or upload the completed CSV so I can:
> 1. Import the scores
> 2. Generate comparative analysis (baseline vs improved)
> 3. Calculate improvement metrics
> 4. Document final system performance"

**Why this matters**:
- The improved evaluation was run but not manually scored before instance termination
- Without these scores, we cannot validate the improvements made
- All configuration changes (top_k=3, chunk_size=512, etc.) are already implemented
- Need comparison to determine if system is production-ready

### Documentation Created
- `backend/evaluation/BASELINE_ANALYSIS.md` - Detailed baseline metrics analysis
- `backend/evaluation/IMPROVEMENTS_IMPLEMENTED.md` - Comprehensive improvement documentation
- `backend/evaluation/QUICK_COMPARISON.md` - Side-by-side before/after comparison
- `backend/evaluation/IMPROVEMENT_PLAN.md` - 3-phase improvement strategy

### Expected Results (To Be Validated)
- Overall score: 4.2-4.5 (from 3.96)
- Source citations: 4.2-4.6 (from 2.40) - **+80-90% improvement expected**
- Hallucination rate: 3-8% (from 35%) - **-27 to -32 pp expected**

### Files Modified
1. `backend/app/core/config.py` - All configuration parameters
2. `backend/app/services/mistral_llm.py` - Stop sequence removal
3. `backend/app/services/rag_service.py` - Comprehensive prompt rewrite
4. `backend/chroma_db/` - Re-ingested with larger chunks

---

**End of Log**
