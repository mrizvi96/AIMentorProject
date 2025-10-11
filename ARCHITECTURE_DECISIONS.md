# Architecture Decisions

This document clarifies the key architectural decisions for the AI Mentor project and the rationale behind them.

## Hardware & Environment (COMMITTED)

**Runpod GPU Instance:**
- **GPU**: NVIDIA RTX A5000 (24GB VRAM)
- **Container**: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
  - CUDA 12.8.1
  - PyTorch 2.8.0
  - Ubuntu 24.04
  - Python 3.12 pre-installed

**Rationale:**
- RTX A5000 provides excellent performance/cost ratio for 7B-13B models
- 24GB VRAM allows full GPU offloading with substantial headroom (14GB+) for:
  - Multiple concurrent requests
  - Larger context windows (up to 8192+ tokens)
  - Future model upgrades (13B Q4/Q5)
- PyTorch container includes all necessary CUDA libraries pre-configured
- Ubuntu 24.04 LTS provides stability and long-term support

## Development Workflow (COMMITTED)

**VS Code Remote-SSH:**
- Local laptop (8GB RAM) runs VS Code as thin client
- All development happens on Runpod instance via SSH
- Benefits:
  - Laptop resource constraints irrelevant for backend work
  - Direct GPU access for testing and debugging
  - Low-latency interaction with running services
  - Git operations on same machine as code

**Rationale:**
- Avoids network latency issues of local dev → remote deployment cycle
- Single source of truth (all code on Runpod)
- Easier debugging of GPU-related issues
- Simpler SSH tunnel management for port forwarding

## Vector Database: Milvus (COMMITTED)

**Choice**: Milvus Standalone (Docker) over ChromaDB or FAISS

**Rationale for Production-Oriented Decision:**

### Scalability
- **Milvus**: Designed for billions of vectors
  - Distributed architecture ready (standalone → cluster migration path)
  - Handles production workloads (10K+ QPS)
  - Horizontal scaling when needed

- **ChromaDB**: Optimized for <10M vectors
  - Primarily in-memory or single-file persistence
  - Great for prototyping, not production scale

- **FAISS**: Library, not a database
  - No built-in persistence layer
  - No query language or REST API
  - Requires custom infrastructure

### Features & Functionality

**Milvus Advantages:**
1. **Multiple Index Types**:
   - IVF_FLAT, IVF_PQ, HNSW, ANNOY, etc.
   - Can optimize for speed vs. accuracy based on use case
   - Dynamic index switching without data migration

2. **Advanced Filtering**:
   - Scalar filtering (filter by metadata before vector search)
   - Hybrid search (combine vector similarity + keyword search)
   - Time-travel queries (query historical states)

3. **Production Features**:
   - RBAC (role-based access control)
   - Monitoring and observability (Prometheus/Grafana integration)
   - Backup and recovery tools
   - Load balancing and query routing

4. **Integration Ecosystem**:
   - Native LlamaIndex integration (`MilvusVectorStore`)
   - LangChain support
   - REST and gRPC APIs
   - Official Python SDK (`pymilvus`)

### Operational Considerations

**Docker Compose Stack:**
```
Services:
- etcd: Metadata storage (distributed coordination)
- MinIO: Object storage (large vector data)
- Milvus Standalone: Query and index engine
```

**Why This Complexity is Worth It:**

1. **Data Persistence & Reliability**:
   - etcd provides consistent metadata storage
   - MinIO ensures durable object storage
   - Clean separation of concerns (compute vs. storage)

2. **Migration Path**:
   - Standalone → Cluster is straightforward
   - Same APIs, just different deployment
   - No code changes needed

3. **Resource Efficiency**:
   - RTX A5000 has resources to spare
   - Docker overhead is minimal (~500MB RAM total for stack)
   - Most VRAM consumed by LLM, not database

4. **Educational Value**:
   - Learn production-grade vector database
   - Experience with distributed systems concepts
   - Transferable skills to real-world projects

### Trade-offs Acknowledged

**Cons:**
- More complex setup than ChromaDB (3 services vs. 1 file)
- Requires Docker knowledge
- Longer troubleshooting time if issues arise

**Mitigations:**
- Week 1-4 (Phase 1) uses ChromaDB for rapid MVP
- Week 6 (Phase 2) migrates to Milvus after validating core RAG logic
- Detailed health checks and verification steps in revised plan
- Fallback: stay with ChromaDB if Milvus causes delays

## Phased Approach Justification

### Phase 1 (Weeks 1-4): Simple RAG with ChromaDB
**Goal**: Prove core functionality fast

- Use simplest possible vector store (ChromaDB)
- HTTP REST APIs only (no WebSockets)
- Basic RAG without agentic loops
- **Deliverable**: Working chat interface that answers questions

**Why Start Simple:**
- Reduces risk of complete failure
- Allows prompt engineering and testing early
- Validates PDF ingestion pipeline
- Proves LLM server works on RTX A5000

### Phase 2 (Weeks 5-7): Production Features
**Goal**: Add sophistication for real-world use

- Migrate to Milvus for scalability
- Implement agentic RAG (LangGraph)
- Add WebSocket streaming for UX
- **Deliverable**: Production-ready system

**Why Defer Complexity:**
- LangGraph has learning curve (3-5 days)
- Milvus troubleshooting can consume time
- WebSocket debugging requires working backend first
- Already have working system to fall back on

### Phase 3 (Weeks 8-10): Polish & Deploy
**Goal**: Make it bulletproof

- Evaluation and metrics
- Performance tuning
- Docker containerization
- Documentation

## Alternative Architectures Considered

### Option A: All-In-One Simple Stack
**Stack**: FastAPI + FAISS + Simple prompting
**Pros**: Fastest to build
**Cons**: Not production-ready, doesn't meet project goals
**Verdict**: Too simple, doesn't demonstrate sophistication

### Option B: Full Cloud (OpenAI + Pinecone)
**Stack**: OpenAI API + Pinecone vector DB
**Pros**: Zero infrastructure, fastest MVP
**Cons**: Costs $$ per query, no learning value, not self-hosted
**Verdict**: Against project requirement for local LLM

### Option C: Minimal Local (Ollama + ChromaDB)
**Stack**: Ollama for LLM + ChromaDB + FastAPI
**Pros**: Simpler than llama.cpp, easier setup
**Cons**: Less control, less flexible
**Verdict**: Good alternative, but less educational

### Option D: Chosen Architecture (llama.cpp + Milvus + LangGraph)
**Stack**: Decoupled llama.cpp + Milvus + Agentic RAG
**Pros**:
- Full control over inference
- Production-scale vector DB
- Sophisticated agent workflows
- Modular and extensible

**Cons**:
- Highest complexity
- Longest learning curve
- Most setup/debugging time

**Verdict**: Best balance of learning value + production readiness

## Key Design Principles

### 1. Decoupling
**Principle**: Each major component is independently replaceable

- **LLM Server** (llama.cpp): Exposes OpenAI-compatible API
  - Can swap for Ollama, vLLM, or actual OpenAI
  - Just change `api_base` URL

- **Vector Store** (Milvus): Used via LlamaIndex abstraction
  - Can swap for Pinecone, Weaviate, Qdrant
  - Just change vector store adapter

- **Frontend** (Svelte): Talks to generic REST/WebSocket API
  - Backend framework agnostic
  - Can migrate to React, Vue, or mobile app

### 2. Observability
**Principle**: System health must be transparent

- Health check endpoints for each service
- Logging at INFO level minimum
- Performance metrics captured (response times)
- Error handling with clear messages

### 3. Incremental Complexity
**Principle**: Build simple first, enhance later

- Phase 1: Simple RAG (prove it works)
- Phase 2: Agentic RAG (make it smart)
- Phase 3: Production polish (make it bulletproof)

### 4. Pragmatic Over Perfect
**Principle**: Shipping beats optimization

- Use sentence-transformers embeddings (fast, good enough)
- Don't over-engineer prompt templates initially
- Defer caching, rate limiting, auth until Phase 3
- Buffer weeks allow refinement after core functionality

## Risk Management

### High Risk: LangGraph Complexity
**Impact**: Could consume entire Week 5
**Mitigation**:
- Study docs + examples first (Day 1-2)
- Build incrementally (one node at a time)
- Keep simple RAG endpoint as fallback
- If blocked after 3 days, skip agentic features

### Medium Risk: Milvus Setup Issues
**Impact**: Week 6 could overrun
**Mitigation**:
- Use ChromaDB in Phase 1 (working system to fall back on)
- Comprehensive health checks in docker-compose
- Document common issues and solutions
- If blocked, declare ChromaDB as final vector store

### Medium Risk: GPU Memory Management
**Impact**: OOM errors, slow inference
**Mitigation**:
- Monitor VRAM with `nvidia-smi`
- RTX A5000 has ample headroom (14GB+ free)
- Can reduce context window (4096 → 2048)
- Can use Q4 quantization if needed

### Low Risk: Frontend Development
**Impact**: UI polish takes longer than expected
**Mitigation**:
- SvelteKit has great docs
- UI is not core innovation
- Can use basic styling, defer polish to Phase 3

## Success Criteria

### Phase 1 MVP Success:
✓ User can ask questions via web UI
✓ System returns contextually relevant answers
✓ Answers cite source documents
✓ Average response time < 15 seconds
✓ System recovers from service restarts

### Phase 2 Enhancement Success:
✓ Agentic RAG improves answer quality (measured via evaluation)
✓ Streaming provides real-time UX
✓ Milvus handles same workload as ChromaDB
✓ System is stable under load

### Phase 3 Production Success:
✓ Full Docker Compose deployment works
✓ Comprehensive documentation exists
✓ Evaluation shows 80%+ quality scores
✓ Known limitations are documented

## Conclusion

This architecture balances:
- **Learning**: Exposure to production-grade tools (Milvus, LangGraph)
- **Pragmatism**: Phased approach reduces risk of complete failure
- **Quality**: Sophisticated enough to be impressive
- **Completability**: 10-week timeline with built-in buffers

The RTX A5000 + Milvus + LangGraph stack is ambitious but achievable. The phased delivery ensures we have a working MVP early, then enhance incrementally. If Phase 2 proves too complex, Phase 1 alone is a respectable deliverable.
