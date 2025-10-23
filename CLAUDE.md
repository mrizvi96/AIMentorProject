# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚀 Quick Start

**New to this project?** Start with [RUNPOD_MILVUS_LITE_GUIDE.md](./RUNPOD_MILVUS_LITE_GUIDE.md) for complete Runpod deployment guide using Milvus Lite.

**TL;DR:** Run `./runpod_simple_startup.sh` to download model and start all services (~35 min first run, ~5 min subsequent runs).

---

## Project Overview

AI Mentor is a modular, scalable educational platform for computer science students. It uses an agentic RAG (Retrieval-Augmented Generation) system powered by a local LLM to provide intelligent tutoring. The system runs on a remote Runpod GPU instance with RTX A5000 (24GB VRAM).

**Hardware Environment:**
- GPU: NVIDIA RTX A5000 (24GB VRAM)
- Container: runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
- CUDA: 12.8.1
- PyTorch: 2.8.0
- OS: Ubuntu 24.04

**Key Technologies:**
- Backend: FastAPI + Python (llama.cpp, LlamaIndex, LangGraph, Milvus Lite, PyMuPDF)
- Frontend: SvelteKit + TypeScript
- Database: Milvus Lite (file-based vector database, no Docker needed)
- LLM: Local quantized models via llama.cpp (e.g., Mistral-7B-Instruct Q5_K_M)

## Architecture

### Core System Design

**Agentic RAG Workflow (LangGraph):**
The system implements a self-correcting, stateful agent that goes beyond simple retrieval:

1. **retrieve** node: Queries Milvus vector store for relevant documents
2. **grade_documents** node: LLM evaluates relevance of retrieved context
3. **rewrite_query** node: Rephrases query if context is poor, loops back to retrieve
4. **generate** node: Synthesizes final answer from validated context

This cyclical architecture (retrieve → grade → rewrite → retrieve → generate) enables the AI to self-correct when initial retrieval fails.

**Deployment Architecture:**
- All compute-intensive operations (LLM inference, embeddings, database) run on Runpod RTX A5000 instance
- Base container: runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404 (CUDA 12.8.1, PyTorch 2.8.0, Ubuntu 24.04)
- Local machine serves as thin development client (VS Code Remote-SSH)
- llama.cpp runs as standalone OpenAI-compatible API server (decoupled from FastAPI)
- Milvus Lite runs embedded (file-based database in `backend/milvus_data/`, no Docker needed)

### Backend Structure

```
backend/
├── main.py                    # FastAPI app entry point with health check
├── app/
│   ├── api/                   # API endpoint routers
│   │   └── chat_router.py     # /chat POST and /ws/chat WebSocket endpoints
│   ├── core/                  # Configuration, settings, environment variables
│   ├── services/              # Business logic
│   │   └── agent_graph.py     # LangGraph agent definition and workflow
```

**Key Components:**
- `agent_graph.py`: Contains `AgentState` (TypedDict with question, documents, generation, messages) and the compiled LangGraph workflow
- `chat_router.py`: Implements both REST and WebSocket endpoints for streaming responses
- CORS configured to allow requests from Svelte dev server (http://localhost:5173)

### Frontend Structure

```
frontend/
├── src/
│   ├── routes/
│   │   └── +page.svelte       # Main chat interface
│   ├── lib/
│   │   ├── components/
│   │   │   ├── MessageList.svelte
│   │   │   ├── Message.svelte
│   │   │   ├── ChatInput.svelte
│   │   │   └── SourceViewer.svelte
│   │   ├── stores.ts          # Svelte writable stores for state
│   │   └── api.ts             # ChatService class for WebSocket management
```

**State Management:**
- Uses native Svelte writable stores (no external state library needed)
- WebSocket service streams tokens from backend, updating stores reactively

## Development Commands

### Streamlined Runpod Startup (Recommended)

**For complete setup instructions, see [RUNPOD_QUICK_START.md](./RUNPOD_QUICK_START.md)**

**Quick Start (after one-time preparation):**
```bash
# Clone repository on Runpod instance
git clone https://github.com/YOUR_USERNAME/AIMentorProject.git
cd AIMentorProject

# Run automated startup script (starts all services)
./runpod_startup.sh
```

This single command starts:
- Milvus vector database (Docker)
- LLM inference server (Docker, with model pre-loaded)
- Backend FastAPI server (tmux session)

**Time: ~3-5 minutes** (vs 30-60 minutes manual setup)

---

### Backend (Run on Runpod GPU Instance) - Manual Setup

**Environment Setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install "fastapi[all]" "uvicorn[standard]" "python-dotenv" "pymilvus" "llama-index" "langgraph" "llama-cpp-python[server]" "PyMuPDF"
```

**Start Services:**
```bash
# 1. Start Milvus vector database (from project root)
docker-compose up -d

# 2. Start llama.cpp inference server (port 8080)
./start_llm.sh
# Or manually:
python3 -m llama_cpp.server \
  --model ./models/mistral-7b-instruct-v0.2.q5_k_m.gguf \
  --n_gpu_layers -1 \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080 \
  --chat_format mistral-instral

# 3. Start FastAPI backend (port 8000)
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Data Ingestion:**
```bash
# Ingest PDF documents into Milvus vector store
python ingest.py --directory ./course_materials/
```

**Check Services:**
```bash
# Verify Milvus containers
docker-compose ps

# Test LLM server
curl http://localhost:8080/v1/models

# Test FastAPI health
curl http://localhost:8000/
```

### Frontend (Run on Local Machine)

**Setup:**
```bash
cd frontend
npm create svelte@latest .  # Select "Skeleton project" with TypeScript
npm install
```

**Development:**
```bash
# Start dev server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Linting:**
```bash
npm run lint
```

## Data Ingestion Pipeline

The system ingests educational materials (PDFs) through a structured pipeline:

1. **Parsing**: PyMuPDF extracts text from PDFs
2. **Chunking**: SentenceSplitter creates 512-token chunks with 50-token overlap
3. **Embedding**: OpenAIEmbedding client (pointed at llama.cpp) generates vectors
4. **Storage**: Embeddings stored in Milvus via LlamaIndex's MilvusVectorStore

**Configuration Parameters:**
- Chunk size: 512 tokens
- Overlap: 50 tokens (preserves context across boundaries)
- Milvus connection: localhost:19530
- LLM embedding endpoint: http://localhost:8080/v1

## API Contract

### REST Endpoints

**POST /api/chat**
- Request: `ChatMessage(message: str, conversation_id: str)`
- Response: `AgentResponse(response: str, sources: List[str])`
- Non-streamed, complete response

**POST /api/documents**
- Request: `fastapi.UploadFile` (PDF)
- Response: `Status(status: str, message: str)`
- Uploads document to staging area

**POST /api/ingest**
- Request: None
- Response: `Status(status: str, message: str)`
- Triggers ingestion of staged documents

### WebSocket

**WS /ws/chat/{conversation_id}**
- Bidirectional streaming chat
- Client sends: `str` (user message)
- Server sends: `str` (streamed tokens from generate node)
- Real-time token-by-token response rendering

## LLM Model Configuration

**Model Selection Criteria:**
- 7B parameter instruction-tuned model (Mistral-7B-Instruct-v0.2 or Llama-3)
- Q5_K_M quantization (balance of quality and size)
- Fits in RTX A5000 24GB VRAM with all layers on GPU

**llama.cpp Server Parameters:**
- `--n_gpu_layers -1`: Offload all layers to GPU (RTX A5000 supports full offload for 7B models)
- `--n_ctx 4096`: Context window size
- `--host 0.0.0.0 --port 8080`: Network accessibility
- `--chat_format mistral-instruct`: Template for instruction format

**RTX A5000 Specifications:**
- 24GB GDDR6 VRAM
- 8192 CUDA cores
- Ampere architecture (compute capability 8.6)
- Supports full GPU offloading for models up to ~13B parameters (with quantization)

**Constraints:**
- GPU memory ceiling: 24GB VRAM limits model size and context window
- Larger models (13B+) or extended contexts require careful memory management
- RTX A5000 recommended models: 7B Q5/Q6, 13B Q4/Q5, or 34B Q3/Q4 (latter may have reduced context)

## Key Architectural Decisions

### Decoupled LLM Server
llama.cpp runs as a standalone OpenAI-compatible server, not embedded in FastAPI. This allows:
- Hot-swapping LLM backends (Ollama, vLLM) by changing base_url
- Independent scaling and updates
- Clean separation of concerns

### Agentic Over Simple RAG
The LangGraph workflow adds latency (multiple LLM calls) but provides:
- Self-correction when retrieval fails
- Quality gating through document grading
- Query refinement for better results
- More robust responses for complex queries

### Monorepo Structure
Both backend and frontend in single repository:
- Simplified dependency management
- Single source of truth under Git
- Streamlined build process

### Svelte for Frontend
Compile-time framework optimization:
- Smaller bundle sizes (compiles to vanilla JS)
- Superior runtime performance
- Critical for responsive educational UI

## System Prompt Engineering

The `generate` node uses a specialized system prompt to shape AI persona:

"You are an expert Computer Science mentor. Your role is to help students understand complex topics. Explain concepts clearly and concisely. When a student asks a question, first provide a direct answer, then offer a simple analogy or example to aid understanding. Base your answers strictly on the provided context documents. Cite the sources you used by referencing their filenames at the end of your response."

**Prompt Refinement Guidelines:**
- Emphasize pedagogical tone (mentor, not just answering)
- Enforce grounding in retrieved context (reduce hallucination)
- Request source citations
- Encourage analogies and examples

## Docker Configuration

**docker-compose.yml Services:**
- `etcd`: Metadata storage for Milvus
- `minio`: Object storage for Milvus
- `milvus-standalone`: Vector database (ports 19530 gRPC, 9091 HTTP)
- Data persisted in `./volumes/` directories

**Containerization Strategy:**
- Backend Dockerfile: Python base, install requirements.txt, run Uvicorn
- Frontend Dockerfile: Multi-stage build (Node.js build → Nginx serve)
- llama.cpp service: Custom or pre-built image in docker-compose

**Deployment Command:**
```bash
docker-compose up -d  # Start entire stack
```

## Testing and Evaluation

**Evaluation Protocol:**
- 20-question test bank covering: factual recall, conceptual explanation, comparative analysis, code generation
- Scoring criteria (1-5 scale): answer correctness, context relevance, clarity/coherence
- Binary hallucination check: does response contain unsupported information?

**Performance Metrics to Monitor:**
- Retrieval accuracy (are correct documents retrieved?)
- End-to-end latency (query submission → first token)
- Context relevance scores from grade_documents node

**Bottlenecks to Watch:**
- Data ingestion throughput for large document corpora
- Agentic workflow latency (multiple LLM calls per query)
- GPU memory constraints with larger models

## Future Enhancement Roadmap

**Phase 2: Pedagogical Features**
- Socratic scaffolding: Guide students with hints rather than direct answers
- Metacognitive feedback: Code review with style/efficiency suggestions

**Phase 3: Personalization**
- Persistent user profiles in PostgreSQL
- Multi-modal input (image analysis with LLaVA)
- Knowledge graph integration (Neo4j/Memgraph for complex reasoning)

**Phase 4: Platform Integration**
- LMS plugins (Moodle, Canvas, Blackboard)
- Collaborative learning environments

## Important Notes

- CORS must allow `http://localhost:5173` for local dev
- Environment variables for API keys should be in `.env` (gitignored)
- Pin dependency versions in `requirements.txt` and `package.json` to avoid breaking changes
- WebSocket connections require proper disconnect handling
- Always use absolute paths when configuring file locations
- The system is designed for self-hosted deployment (no external API calls)