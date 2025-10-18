# 🧪 AI Mentor - Testing Guide

Complete guide to test your AI Mentor system at each stage of deployment.

---

## 🎯 Testing Levels

### Level 1: Quick Smoke Tests (5 minutes)
Verify each service is running

### Level 2: Component Tests (10 minutes)
Test each component individually

### Level 3: End-to-End Tests (15 minutes)
Test complete user workflow

---

## 📋 Prerequisites

Before testing, ensure you've completed deployment:
- ✅ Runpod instance running
- ✅ Repository cloned
- ✅ Model downloaded
- ✅ Textbooks downloaded
- ✅ Services started

---

## Level 1: Quick Smoke Tests

### Test 1: Check Services Are Running

```bash
# Check LLM Server
curl http://localhost:8080/v1/models

# Expected output:
{
  "object": "list",
  "data": [
    {
      "id": "mistral-7b-instruct-v0.2.q5_k_m.gguf",
      "object": "model",
      ...
    }
  ]
}
```

```bash
# Check Backend API
curl http://localhost:8000/

# Expected output:
{
  "status": "ok",
  "message": "AI Mentor API is running",
  "version": "1.0.0"
}
```

```bash
# Check Backend Health (detailed)
curl http://localhost:8000/api/health

# Expected output:
{
  "status": "ok",
  "services": {
    "api": "running",
    "llm": "running",
    "vector_db": "running",
    "rag": "not_configured"
  }
}
```

```bash
# Check Milvus
docker-compose ps

# Expected output: All services showing "healthy"
NAME                COMMAND                  SERVICE             STATUS              PORTS
milvus-etcd         etcd ...                 etcd                running (healthy)   ...
milvus-minio        ...                      minio               running (healthy)   ...
milvus-standalone   ...                      milvus              running (healthy)   ...
```

```bash
# Check Frontend
curl http://localhost:5173/

# Should return HTML (long output)
```

**✅ PASS if:** All services respond without errors

---

### Test 2: Verify Data Ingestion

```bash
cd /root/AIMentorProject/backend
source venv/bin/activate

# Check if PDFs were ingested
python -c "
from pymilvus import connections, utility

connections.connect(host='localhost', port='19530')
collections = utility.list_collections()
print(f'Collections: {collections}')

if 'course_materials' in collections:
    from pymilvus import Collection
    collection = Collection('course_materials')
    print(f'Number of documents: {collection.num_entities}')
else:
    print('No collection found - run ingestion!')
"

# Expected output:
Collections: ['course_materials']
Number of documents: XXX  # Should be > 0
```

**✅ PASS if:** Collection exists and has documents

---

## Level 2: Component Tests

### Test 3: LLM Server Direct Test

```bash
# Test LLM generation directly
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is recursion?",
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Expected: JSON response with generated text
# Should see a response about recursion
```

**✅ PASS if:** LLM generates coherent response

---

### Test 4: Backend RAG Service Test

```bash
# Test chat endpoint (without frontend)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What topics are covered in the course materials?",
    "conversation_id": "test-001"
  }'

# Expected output:
{
  "response": "Based on the course materials... [relevant answer]",
  "sources": [
    {
      "text": "... relevant text snippet ...",
      "score": 0.85,
      "metadata": {
        "file_name": "textbook_1.pdf",
        ...
      }
    }
  ],
  "conversation_id": "test-001"
}
```

**Key things to check:**
- ✅ Response is relevant to question
- ✅ Sources list is not empty
- ✅ Scores are between 0-1
- ✅ Metadata includes file names

**✅ PASS if:** Response is relevant with sources

---

### Test 5: Vector Search Quality Test

```bash
cd /root/AIMentorProject/backend
source venv/bin/activate

# Test if vector search retrieves relevant documents
python << 'EOF'
from app.services.rag_service import rag_service
import asyncio

async def test_retrieval():
    # Initialize service
    rag_service.initialize()

    # Test query
    result = await rag_service.query("Explain binary search trees")

    print("Question:", result['question'])
    print("\nResponse:", result['response'][:200], "...")
    print(f"\nNumber of sources: {len(result['sources'])}")

    for i, source in enumerate(result['sources'], 1):
        print(f"\nSource {i}:")
        print(f"  Score: {source['score']:.2f}")
        print(f"  Text: {source['text'][:100]}...")

asyncio.run(test_retrieval())
EOF
```

**✅ PASS if:**
- Response mentions binary search trees
- At least 1-3 sources returned
- Source scores > 0.5

---

### Test 6: Embedding Quality Test

```bash
cd /root/AIMentorProject/backend
source venv/bin/activate

# Test if embeddings are similar for related queries
python << 'EOF'
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import numpy as np

# Initialize embedding model
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Test queries
query1 = "What is a binary search tree?"
query2 = "Explain BST data structure"
query3 = "How do I cook pasta?"

# Get embeddings
emb1 = embed_model.get_text_embedding(query1)
emb2 = embed_model.get_text_embedding(query2)
emb3 = embed_model.get_text_embedding(query3)

# Calculate cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

sim_1_2 = cosine_similarity(emb1, emb2)
sim_1_3 = cosine_similarity(emb1, emb3)

print(f"Similarity (BST vs BST): {sim_1_2:.4f}")
print(f"Similarity (BST vs Pasta): {sim_1_3:.4f}")
print(f"\n{'PASS' if sim_1_2 > sim_1_3 else 'FAIL'}: Related queries more similar")
EOF
```

**✅ PASS if:** BST vs BST similarity > BST vs Pasta similarity

---

## Level 3: End-to-End Tests

### Test 7: Full User Workflow Test

**Step 1: Open Frontend**
```bash
# Get your Runpod public URL or use SSH tunnel
# Open in browser: http://localhost:5173
```

**Step 2: Ask Test Questions**

**Test Question 1: General Coverage**
```
"What topics are covered in these textbooks?"
```
**Expected:**
- Summary of topics from your 6 textbooks
- Mentions specific CS topics (data structures, algorithms, etc.)
- Shows 1-3 source documents
- Relevance scores visible

---

**Test Question 2: Specific Concept**
```
"Explain how binary search trees work"
```
**Expected:**
- Clear explanation of BST
- Based on textbook content
- Sources from relevant textbook chapters
- Citations shown

---

**Test Question 3: Code-Related**
```
"What are the main sorting algorithms?"
```
**Expected:**
- Lists common sorting algorithms
- May include time complexity if in textbooks
- Sources from algorithms chapters

---

**Test Question 4: Comparison**
```
"What's the difference between arrays and linked lists?"
```
**Expected:**
- Compares both data structures
- Mentions key differences (random access, insertion, etc.)
- Sources from data structures content

---

**Test Question 5: Off-Topic (Should Handle Gracefully)**
```
"How do I bake a cake?"
```
**Expected:**
- Response indicates this is not in the course materials
- OR attempts to answer based on any tangentially related content
- Should not hallucinate computer science facts

---

### Test 8: Source Verification

For each response, verify:

**✅ Check Sources Section:**
- [ ] Shows "Sources (X)" where X > 0
- [ ] Can expand to see source details
- [ ] Each source has:
  - Text snippet preview
  - Relevance score (0-100%)
  - File name from your textbooks

**✅ Check Response Quality:**
- [ ] Relevant to the question
- [ ] Grounded in textbook content
- [ ] Cites specific sources
- [ ] No obvious hallucinations

---

### Test 9: WebSocket Test (Advanced)

```bash
# Install wscat for WebSocket testing
npm install -g wscat

# Connect to WebSocket endpoint
wscat -c ws://localhost:8000/api/ws/chat/test-session

# Once connected, send a message:
{"message": "What is recursion?"}

# Should receive streaming response
```

**✅ PASS if:** Receives response chunks via WebSocket

---

## Level 4: Performance Tests

### Test 10: Response Time Test

```bash
# Test API response time
time curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a hash table?", "conversation_id": "perf-test"}'

# Expected: < 5 seconds for simple queries
```

**Benchmarks:**
- ✅ Excellent: < 3 seconds
- ✅ Good: 3-5 seconds
- ⚠️ Acceptable: 5-10 seconds
- ❌ Slow: > 10 seconds

---

### Test 11: Concurrent Requests Test

```bash
# Test multiple simultaneous requests
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test query $i\", \"conversation_id\": \"concurrent-$i\"}" &
done
wait

# All should complete without errors
```

**✅ PASS if:** All 5 requests complete successfully

---

### Test 12: GPU Utilization Test

```bash
# Monitor GPU while making requests
watch -n 1 nvidia-smi

# In another terminal, make requests
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quicksort algorithm", "conversation_id": "gpu-test"}'

# Check GPU usage spikes during inference
```

**Expected:**
- GPU utilization increases during inference
- Should use < 24GB VRAM (fits in A5000)
- Returns to baseline after completion

---

## 📊 Test Results Template

Copy this to track your testing:

```markdown
# AI Mentor Test Results

**Date:** YYYY-MM-DD
**Runpod Instance:** [Instance ID]
**GPU:** RTX A5000

## Quick Smoke Tests
- [ ] Test 1: All services running
- [ ] Test 2: Data ingestion verified

## Component Tests
- [ ] Test 3: LLM server responds
- [ ] Test 4: Backend RAG works
- [ ] Test 5: Vector search quality
- [ ] Test 6: Embedding quality

## End-to-End Tests
- [ ] Test 7: Full user workflow
- [ ] Test 8: Source verification
- [ ] Test 9: WebSocket (optional)

## Performance Tests
- [ ] Test 10: Response time < 5s
- [ ] Test 11: Concurrent requests
- [ ] Test 12: GPU utilization

## Sample Questions Tested
1. "What topics are covered?" - ✅/❌
2. "Explain binary search trees" - ✅/❌
3. "Main sorting algorithms" - ✅/❌
4. "Arrays vs linked lists" - ✅/❌
5. "Off-topic question" - ✅/❌

## Issues Found
[List any problems]

## Overall Status
✅ PASS / ❌ FAIL

## Notes
[Additional observations]
```

---

## 🚨 Common Issues & Solutions

### Issue: "No sources returned"

**Diagnosis:**
```bash
# Check if ingestion completed
cd backend && source venv/bin/activate
python -c "
from pymilvus import connections, Collection
connections.connect(host='localhost', port='19530')
collection = Collection('course_materials')
print(f'Documents in database: {collection.num_entities}')
"
```

**Solution:**
- If 0 documents: Re-run ingestion
- If > 0 but no sources: Check similarity threshold in config

---

### Issue: "Response is hallucinating"

**Diagnosis:**
- Check if sources are relevant
- Verify retrieval is working

**Solution:**
- Adjust `SIMILARITY_THRESHOLD` in `.env`
- Review system prompt in `rag_service.py`
- May need better textbook content

---

### Issue: "Very slow responses"

**Diagnosis:**
```bash
# Check GPU usage
nvidia-smi

# Check if using CPU instead
cat /tmp/llm_server.log | grep "GPU"
```

**Solution:**
- Ensure `--n_gpu_layers -1` in LLM server
- Restart LLM server
- Check CUDA installation

---

## ✅ Success Criteria

Your system is working correctly if:

✅ **All services respond** (Level 1)
✅ **RAG returns relevant results with sources** (Level 2)
✅ **Frontend chat works end-to-end** (Level 3)
✅ **Responses are grounded in textbooks** (Level 3)
✅ **Response time < 5 seconds** (Level 4)
✅ **GPU is being utilized** (Level 4)

---

## 📝 Next Steps After Testing

### If All Tests Pass ✅
- Start Phase 2: Agentic RAG with LangGraph
- Add self-correction workflow
- Implement query rewriting

### If Some Tests Fail ⚠️
- Review SETUP_STATUS.md for troubleshooting
- Check logs for errors
- Verify all dependencies installed
- Re-run ingestion if data issues

### If Most Tests Fail ❌
- Review RUNPOD_DEPLOYMENT_CHECKLIST.md
- Ensure all steps completed
- Check service logs for errors
- May need to restart services

---

**Happy Testing!** 🎉

Start with Level 1 (Quick Smoke Tests) and work your way up!
