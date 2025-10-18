# AI Mentor - Intelligent Computer Science Tutor

An agentic RAG (Retrieval-Augmented Generation) system designed to provide intelligent tutoring for computer science students. Built with FastAPI, SvelteKit, and powered by local LLM inference.

## 🚀 Quick Start (Runpod)

Every new Runpod instance, run:

```bash
# 1. Clone repository
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject

# 2. Download Mistral model (one time, ~5 minutes)
mkdir -p /workspace/models
cd /workspace/models
wget -O Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
cd ~/AIMentorProject

# 3. Start all services
./START_SERVICES.sh

# 4. In separate terminals, start the servers:
# Terminal 1: LLM Server
./start_llm_server.sh

# Terminal 2: Backend API
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Frontend
cd frontend
npm run dev -- --host 0.0.0.0
```

**Access the application:**
- Frontend UI: http://localhost:5173
- Backend API: http://localhost:8000/docs
- LLM Server: http://localhost:8080/v1

## 📋 Prerequisites

- **Runpod Instance:** RTX A5000 (24GB VRAM) recommended
- **Base Image:** `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- **Python:** 3.10+
- **Node.js:** 20+
- **Docker:** For Milvus vector database

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (SvelteKit)                          │
│  - Modern chat interface                       │
│  - Real-time message streaming                 │
│  - Source document viewer                      │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────────────┐
│  Backend (FastAPI)                             │
│  - RAG orchestration                           │
│  - Chat API endpoints                          │
│  - Document ingestion pipeline                 │
└──────┬──────────────────────────┬───────────────┘
       │                          │
       │ Query/Embed              │ Retrieve
       ▼                          ▼
┌──────────────┐          ┌──────────────────┐
│ LLM Server   │          │ Milvus Vector DB │
│ (llama.cpp)  │          │ - Document chunks │
│ Mistral-7B   │          │ - Embeddings      │
└──────────────┘          └──────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Mistral-7B-Instruct-v0.2 (Q5_K_M quantization) |
| **Inference** | llama.cpp (OpenAI-compatible API) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Vector DB** | Milvus 2.3.10 (Docker) |
| **Backend** | FastAPI + LlamaIndex + Python 3.10+ |
| **Frontend** | SvelteKit + TypeScript |
| **GPU** | CUDA 12.8.1 (RTX A5000, 24GB VRAM) |

## 📁 Project Structure

```
AIMentorProject/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── chat_router.py  # Chat endpoints (REST + WebSocket)
│   │   ├── core/
│   │   │   └── config.py       # Configuration management
│   │   └── services/
│   │       └── rag_service.py  # RAG orchestration logic
│   ├── main.py                 # FastAPI application entry
│   ├── ingest.py               # PDF ingestion CLI
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variables template
├── frontend/                   # SvelteKit frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/     # Svelte components
│   │   │   ├── stores.ts       # State management
│   │   │   └── api.ts          # Backend API client
│   │   └── routes/
│   │       └── +page.svelte    # Main chat page
│   └── package.json            # Node dependencies
├── course_materials/           # Upload PDFs here
├── docker-compose.yml          # Milvus infrastructure
├── start_llm_server.sh         # LLM server startup script
├── START_SERVICES.sh           # Automated setup script
└── SETUP_STATUS.md             # Detailed setup guide
```

## 🔧 Detailed Setup

### 1. Environment Setup

```bash
# Install system dependencies (if needed)
sudo apt-get update && sudo apt-get install -y \
  python3-venv python3-pip \
  nodejs npm \
  docker.io docker-compose \
  git curl wget

# Start Docker daemon
sudo systemctl start docker
```

### 2. Clone and Configure

```bash
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject

# Create .env file (optional, defaults work)
cp backend/.env.example backend/.env
```

### 3. Download Model

```bash
# Create models directory
mkdir -p /workspace/models

# Download Mistral-7B (4.8GB, ~5-10 minutes)
wget -O /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# Verify download
ls -lh /workspace/models/
# Should show ~4.8GB file
```

### 4. Start Services

**Option A: Automated (Recommended)**
```bash
./START_SERVICES.sh
```

**Option B: Manual**
```bash
# Start Milvus
docker-compose up -d

# Setup Python environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 5. Upload Course Materials

Upload your scholarly PDFs to `course_materials/`:

```bash
# Via SCP from local machine
scp /path/to/textbook.pdf root@RUNPOD_IP:/root/AIMentorProject/course_materials/

# Or using VS Code Remote-SSH:
# Right-click on course_materials/ → Upload
```

### 6. Ingest Documents

```bash
cd backend
source venv/bin/activate
python ingest.py --directory ../course_materials

# Optional: Overwrite existing collection
python ingest.py --directory ../course_materials --overwrite
```

### 7. Start Servers

**Terminal 1 - LLM Server:**
```bash
./start_llm_server.sh
```

**Terminal 2 - Backend API:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

## 🧪 Testing

### Health Checks

```bash
# Check LLM server
curl http://localhost:8080/v1/models

# Check backend
curl http://localhost:8000/

# Check Milvus
docker-compose ps
```

### Test Query

```bash
# Via API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is recursion?", "conversation_id": "test"}'

# Via UI
# Open http://localhost:5173 and ask a question
```

## 📊 API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/health` | Detailed service status |
| POST | `/api/chat` | Send chat message (non-streaming) |
| GET | `/api/chat/stats` | RAG service statistics |
| WS | `/api/ws/chat/{id}` | WebSocket streaming (Phase 2) |

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎯 Configuration

Edit `backend/.env` to customize:

```bash
# LLM Configuration
LLM_BASE_URL=http://localhost:8080/v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512

# Milvus Configuration
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=course_materials

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=3
SIMILARITY_THRESHOLD=0.7
```

## 🐛 Troubleshooting

### Model not found
```bash
ls -lh /workspace/models/
# Should show Mistral-7B-Instruct-v0.2.Q5_K_M.gguf (~4.8GB)
```

### Milvus connection failed
```bash
docker-compose ps
# All services should show "healthy"

docker-compose logs milvus
# Check for errors
```

### LLM server won't start
```bash
# Reinstall with CUDA support
pip uninstall llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install --no-cache-dir "llama-cpp-python[server]"
```

### Out of GPU memory
```bash
# Check GPU usage
nvidia-smi

# Reduce context window in .env
LLM_MAX_TOKENS=256
```

### CORS errors in browser
- Verify backend is running on port 8000
- Check `main.py` CORS configuration
- Clear browser cache

## 📈 Development Status

**Phase 1 (Weeks 1-2): Simple RAG MVP** - ✅ 75% Complete

- ✅ Backend API with RAG service
- ✅ Frontend chat interface
- ✅ Milvus vector database integration
- ✅ PDF ingestion pipeline
- ✅ LLM inference setup
- ⏳ End-to-end testing (pending course materials)

**Phase 2 (Weeks 3-4): Agentic RAG** - 🔜 Next

- LangGraph workflow implementation
- Self-correcting retrieve → grade → rewrite → generate loop
- WebSocket streaming for real-time responses
- Query rewriting for better retrieval

**Phase 3 (Weeks 5-6): Production** - 📅 Planned

- Systematic evaluation (20-question test bank)
- Prompt engineering refinement
- Full containerization (Docker)
- Operational runbook and monitoring

## 🤝 Contributing

This is a capstone project. For questions or suggestions:
- Open an issue on GitHub
- Contact: mohammad.rizvi@csuglobal.edu

## 📄 License

Educational project - CSU Global Capstone

## 🙏 Acknowledgments

- **LlamaIndex** - RAG orchestration framework
- **Milvus** - Vector database
- **llama.cpp** - Efficient LLM inference
- **Mistral AI** - Base language model
- **SvelteKit** - Frontend framework

---

**Generated with Claude Code** - AI-assisted development for educational AI systems
