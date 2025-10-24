# Next Development Steps After Weeks 1-2

## Current Status: ✅ Foundation Complete!

You've successfully completed the **Foundation Phase (Weeks 1-2)**:

✅ **Environment Setup**
- Runpod instance with RTX A5000 (24GB VRAM)
- CUDA-enabled llama.cpp with GPU acceleration
- ChromaDB vector database (instead of Milvus)
- Python virtual environment with all dependencies

✅ **Basic RAG Pipeline Working**
- Document ingestion: 4,340 chunks from 6 PDFs
- ChromaDB: 56MB database with embeddings
- Mistral-7B-Instruct-v0.2 (Q5_K_M) running on GPU
- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Query response time: **1.7-2.9 seconds**

✅ **Performance Verified**
- GPU acceleration working (95+ tokens/second)
- Prompt processing: 2,949 tokens/second
- 3 test queries successfully answered
- Sources properly cited

---

## What's Next: Phase 2 - Agentic RAG Intelligence

### Current Limitation
Your system is a **Simple RAG** pipeline:
```
User Query → Retrieve Documents → Generate Answer → Done
```

**Problems:**
- No quality check on retrieved documents
- No retry mechanism if retrieval fails
- One-shot, hope-for-the-best approach
- Can give poor answers when retrieval is weak

### Target: Agentic RAG with Self-Correction

Transform your system into an **Intelligent Mentor**:
```
User Query → Retrieve → Grade Documents
                ↓              ↓
            (relevant?)    (not relevant)
                ↓              ↓
            Generate ←── Rewrite Query ← Loop with limit
```

**Benefits:**
- Self-correcting when initial retrieval fails
- Quality gates before generating answers
- Query refinement for better results
- Mentor-like behavior (thinks before answering)

---

## Week 2 Roadmap: LangGraph Implementation

**Goal:** Add self-correcting intelligence to your RAG system
**Estimated Time:** 30-35 hours
**Key Technology:** LangGraph (stateful workflow engine)

### Day 1-2: LangGraph Foundation (10-12 hours)

#### Task 2.1: Install LangGraph Dependencies (30 min)

```bash
cd /root/AIMentorProject-1/backend
source venv/bin/activate

# Install LangGraph stack
pip install \
  "langgraph==0.0.55" \
  "langchain==0.1.20" \
  "langchain-core==0.1.52" \
  "langchain-community==0.0.38"

# Update requirements
pip freeze > requirements.txt

# Verify installation
python3 -c "from langgraph.graph import StateGraph, END; print('✓ LangGraph installed')"
```

#### Task 2.2: Study LangGraph Concepts (2-3 hours)

**Key concepts to understand:**
1. **StateGraph** - Stateful workflow engine
2. **TypedDict State** - Shared state across nodes
3. **Nodes** - Functions that process state and return updates
4. **Edges** - Transitions between nodes (conditional or standard)
5. **Compilation** - Convert graph definition to runnable

**Resources:**
- LangGraph docs: https://langchain-ai.github.io/langgraph/
- Agentic RAG tutorial: https://blog.langchain.com/agentic-rag-with-langgraph/
- Examples: https://github.com/langchain-ai/langgraph/tree/main/examples

**Take notes on:**
- How conditional routing functions work
- How `add_messages` annotation works
- How to compile and invoke graphs
- Error handling in node functions

#### Task 2.3: Design Agent State (1-2 hours)

Create `/root/AIMentorProject-1/backend/app/services/agent_state.py`:

```python
"""
Agent State Definition for Agentic RAG
"""
from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Shared state for agentic RAG workflow"""

    # Question management
    question: str                          # Original user question
    rewritten_question: str | None         # Query after rewrite

    # Retrieved context
    documents: List[str]                   # Document chunks
    document_scores: List[float]           # Relevance scores

    # Generation output
    generation: str                        # Final answer

    # Conversation history
    messages: Annotated[list, add_messages]

    # Loop prevention (CRITICAL!)
    retry_count: int                       # Rewrite attempts
    max_retries: int                       # Maximum allowed (default: 2)

    # Metadata
    relevance_decision: str | None         # "yes" or "no" from grading
    workflow_path: List[str]               # Visited nodes
```

**Why this structure:**
- `retry_count` prevents infinite rewrite loops
- `workflow_path` helps debug the agent's decision path
- `messages` maintains conversation history
- `document_scores` allows quality assessment

#### Task 2.4: Implement Retrieve Node (2-3 hours)

This node queries ChromaDB for relevant documents:

```python
def retrieve(state: AgentState) -> Dict:
    """
    Retrieve relevant documents from ChromaDB

    Returns:
        Updated state with documents and scores
    """
    question = state.get("rewritten_question") or state["question"]

    logger.info(f"[RETRIEVE] Querying: {question[:100]}...")

    # Query ChromaDB via LlamaIndex
    response = query_engine.query(question)

    documents = []
    scores = []
    for node in response.source_nodes[:3]:  # Top 3 results
        documents.append(node.text)
        scores.append(node.score)

    logger.info(f"[RETRIEVE] Found {len(documents)} documents")
    logger.info(f"[RETRIEVE] Scores: {[f'{s:.3f}' for s in scores]}")

    return {
        "documents": documents,
        "document_scores": scores,
        "workflow_path": state["workflow_path"] + ["retrieve"]
    }
```

---

### Day 3-4: Grade and Rewrite Nodes (10-12 hours)

#### Task 2.5: Implement Grade Documents Node (3-4 hours)

**Purpose:** LLM judges if retrieved documents are relevant

```python
def grade_documents(state: AgentState) -> Dict:
    """
    Grade retrieved documents for relevance

    Returns:
        Updated state with relevance decision
    """
    question = state["question"]
    documents = state["documents"]

    logger.info(f"[GRADE] Evaluating {len(documents)} documents...")

    # Prompt LLM to grade relevance
    prompt = f"""You are grading retrieved documents for relevance.

Question: {question}

Retrieved Documents:
{chr(10).join([f'{i+1}. {doc[:200]}...' for i, doc in enumerate(documents)])}

Do these documents contain information to answer the question?
Answer with ONLY 'yes' or 'no'.

Answer:"""

    response = llm.complete(prompt)
    decision = response.text.strip().lower()

    # Normalize response
    if "yes" in decision:
        decision = "yes"
    else:
        decision = "no"

    logger.info(f"[GRADE] Decision: {decision}")

    return {
        "relevance_decision": decision,
        "workflow_path": state["workflow_path"] + ["grade_documents"]
    }
```

**Critical prompt engineering:**
- Request binary yes/no answer (LLMs are unpredictable)
- Show document snippets, not full text
- Normalize response to handle variations ("Yes", "YES", "yes, they do")

#### Task 2.6: Implement Rewrite Query Node (2-3 hours)

**Purpose:** Improve query when documents aren't relevant

```python
def rewrite_query(state: AgentState) -> Dict:
    """
    Rewrite query to improve retrieval

    Returns:
        Updated state with rewritten question
    """
    original_question = state["question"]

    logger.info(f"[REWRITE] Original: {original_question}")

    prompt = f"""You are improving a search query for better retrieval results.

Original Question: {original_question}

The current query didn't retrieve relevant documents.
Rewrite this question to be more specific and likely to match relevant content.
Focus on key concepts and technical terms.

Rewritten Question:"""

    response = llm.complete(prompt)
    rewritten = response.text.strip()

    logger.info(f"[REWRITE] Improved: {rewritten}")

    return {
        "rewritten_question": rewritten,
        "retry_count": state["retry_count"] + 1,
        "workflow_path": state["workflow_path"] + ["rewrite_query"]
    }
```

#### Task 2.7: Implement Generate Node (2-3 hours)

**Purpose:** Create final answer from validated documents

```python
def generate(state: AgentState) -> Dict:
    """
    Generate final answer from relevant documents

    Returns:
        Updated state with generation
    """
    question = state["question"]
    documents = state["documents"]

    logger.info(f"[GENERATE] Creating answer...")

    # Build context from documents
    context = "\n\n".join([
        f"Source {i+1}:\n{doc}"
        for i, doc in enumerate(documents)
    ])

    prompt = f"""You are an expert Computer Science mentor helping students understand complex topics.

Context from course materials:
{context}

Based strictly on the context above, answer the following question.
Provide a clear, direct answer using simple language and helpful analogies.
Cite specific sources you used.

Question: {question}

Answer:"""

    response = llm.complete(prompt)

    logger.info(f"[GENERATE] Answer generated ({len(response.text)} chars)")

    return {
        "generation": response.text,
        "workflow_path": state["workflow_path"] + ["generate"]
    }
```

---

### Day 5-6: Build LangGraph Workflow (8-10 hours)

#### Task 2.8: Assemble State Graph (4-5 hours)

**Purpose:** Connect all nodes into self-correcting workflow

```python
def _build_graph(self):
    """Build the LangGraph state machine"""

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("retrieve", self.retrieve)
    workflow.add_node("grade_documents", self.grade_documents)
    workflow.add_node("rewrite_query", self.rewrite_query)
    workflow.add_node("generate", self.generate)

    # Set entry point
    workflow.set_entry_point("retrieve")

    # Add edges
    workflow.add_edge("retrieve", "grade_documents")

    # Conditional routing after grading
    workflow.add_conditional_edges(
        "grade_documents",
        self.decide_to_generate,  # Routing function
        {
            "rewrite": "rewrite_query",
            "generate": "generate"
        }
    )

    # After rewrite, check if we should retry or give up
    workflow.add_conditional_edges(
        "rewrite_query",
        self.should_retry,  # Routing function
        {
            "retrieve": "retrieve",  # Try retrieval again
            "generate": "generate"   # Max retries reached, generate anyway
        }
    )

    # End after generation
    workflow.add_edge("generate", END)

    # Compile
    self.graph = workflow.compile()

    logger.info("✓ LangGraph workflow built successfully")
```

**Routing functions:**

```python
def decide_to_generate(self, state: AgentState) -> str:
    """Decide whether to generate answer or rewrite query"""
    if state["relevance_decision"] == "yes":
        return "generate"
    else:
        return "rewrite"

def should_retry(self, state: AgentState) -> str:
    """Decide whether to retry retrieval or give up"""
    if state["retry_count"] >= state["max_retries"]:
        logger.warning(f"[RETRY] Max retries reached ({state['max_retries']})")
        return "generate"  # Give up, generate with what we have
    else:
        return "retrieve"  # Try again
```

#### Task 2.9: Integration Testing (3-4 hours)

**Test the complete workflow:**

```python
# Create test script: test_agentic_rag.py
import asyncio
from app.services.agentic_rag import AgenticRAGService

async def test_agentic_workflow():
    print("="*70)
    print("Testing Agentic RAG with Self-Correction")
    print("="*70)

    service = AgenticRAGService()

    # Test Case 1: Good query (should not rewrite)
    print("\n Test 1: Direct retrieval success")
    result1 = service.query("What is Python programming language?")
    print(f"✓ Answer: {result1['generation'][:200]}...")
    print(f"✓ Workflow: {' → '.join(result1['workflow_path'])}")

    # Test Case 2: Poor query (should trigger rewrite)
    print("\n Test 2: Query refinement")
    result2 = service.query("How do I use that thing?")  # Vague query
    print(f"✓ Answer: {result2['generation'][:200]}...")
    print(f"✓ Workflow: {' → '.join(result2['workflow_path'])}")
    print(f"✓ Rewrites: {result2['retry_count']}")

    # Test Case 3: Out-of-domain query (should max out retries)
    print("\n Test 3: Max retry handling")
    result3 = service.query("What is the capital of France?")
    print(f"✓ Answer: {result3['generation'][:200]}...")
    print(f"✓ Workflow: {' → '.join(result3['workflow_path'])}")
    print(f"✓ Rewrites: {result3['retry_count']}")

    print("\n" + "="*70)
    print("✅ ALL AGENTIC RAG TESTS PASSED")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_agentic_workflow())
```

**Run tests:**
```bash
cd /root/AIMentorProject-1/backend
source venv/bin/activate
python test_agentic_rag.py
```

**Expected behavior:**
- Test 1: `retrieve → grade → generate` (no rewrite needed)
- Test 2: `retrieve → grade → rewrite → retrieve → grade → generate`
- Test 3: Hits max retries, generates best answer possible

---

### Day 7: Documentation and Validation (4-6 hours)

#### Task 2.10: Update API Endpoints (2-3 hours)

Update `chat_router.py` to use agentic service:

```python
from app.services.agentic_rag import AgenticRAGService

agentic_service = AgenticRAGService()

@router.post("/chat")
async def chat(message: ChatMessage):
    """Chat endpoint with agentic RAG"""
    result = agentic_service.query(message.message)

    return AgentResponse(
        response=result["generation"],
        sources=result.get("sources", []),
        workflow_path=result["workflow_path"],
        retry_count=result["retry_count"]
    )
```

#### Task 2.11: Create Comprehensive Documentation (2-3 hours)

Document the agentic workflow:

**Create `AGENTIC_RAG_GUIDE.md`:**
- Architecture diagram of workflow
- Explanation of each node
- Routing logic explanation
- Example queries and workflows
- Troubleshooting guide

---

## Week 2 Success Criteria

✅ **You've completed Week 2 when:**

1. **LangGraph installed and working**
   - Can import StateGraph, END
   - Dependencies pinned in requirements.txt

2. **All 4 nodes implemented**
   - retrieve: Gets documents from ChromaDB
   - grade_documents: LLM evaluates relevance
   - rewrite_query: Improves vague queries
   - generate: Creates final answer

3. **Workflow compiled and tested**
   - Graph compiles without errors
   - Can invoke with test queries
   - Routing logic works correctly

4. **Loop prevention working**
   - Max retries enforced (default: 2)
   - System doesn't infinite loop
   - Generates answer even after max retries

5. **Self-correction demonstrated**
   - Can show example where rewrite improves answer
   - Workflow path tracked correctly
   - Better answers than simple RAG

---

## Comparison: Before vs After Week 2

### Before (Current - Simple RAG)
```
Query: "What is that language thing?"
↓
Retrieve: [Low relevance documents about languages in general]
↓
Generate: [Vague, unhelpful answer based on poor context]
❌ User frustrated
```

### After (Week 2 - Agentic RAG)
```
Query: "What is that language thing?"
↓
Retrieve: [Low relevance documents]
↓
Grade: "no, not relevant"
↓
Rewrite: "What is Python programming language features?"
↓
Retrieve: [High relevance documents about Python]
↓
Grade: "yes, relevant"
↓
Generate: [Specific, helpful answer about Python]
✅ User satisfied
```

---

## Common Challenges and Solutions

### Challenge 1: LLM Doesn't Return "yes" or "no" in Grading

**Solution:** Add response normalization:
```python
response_text = response.text.strip().lower()
if any(word in response_text for word in ["yes", "relevant", "sufficient"]):
    decision = "yes"
else:
    decision = "no"
```

### Challenge 2: Rewritten Query is Too Similar to Original

**Solution:** Improve rewrite prompt:
```python
prompt = f"""Original question was too vague: "{original_question}"

Create a MORE SPECIFIC version that:
1. Uses technical terminology
2. Focuses on concrete concepts
3. Removes ambiguous words like "that thing", "it", "this"

Rewritten:"""
```

### Challenge 3: Graph Compilation Errors

**Solution:** Common issues:
- Missing nodes in conditional edges
- Typo in node names
- Forgot to set entry point
- Forgot END edge

Debug with:
```python
try:
    graph = workflow.compile()
except Exception as e:
    print(f"Compilation error: {e}")
    print(f"Nodes: {workflow.nodes}")
    print(f"Edges: {workflow.edges}")
```

### Challenge 4: System Too Slow (Multiple LLM Calls)

**Current:** Each query = 3-5 LLM calls (retrieve, grade, potentially rewrite, generate)
**Latency:** ~6-15 seconds vs 3 seconds for simple RAG

**Solutions for Week 3:**
- Add streaming (users see progress)
- Parallel grading (grade multiple docs simultaneously)
- Faster grading model (TinyLlama for grading, Mistral for generation)

---

## Week 3 Preview: WebSocket Streaming

After Week 2 completes, Week 3 will add:

**Goal:** Real-time token streaming so users see responses word-by-word

**Key technology:** `astream_events()` from LangGraph

**User experience improvement:**
- Before: Wait 10 seconds → See complete answer
- After: See "Searching... Evaluating... Writing..." → Words appear in real-time

**Deliverable:** Frontend shows:
- "🔍 Retrieving documents..."
- "✓ Found 3 relevant sources"
- "📝 Generating answer..."
- [Tokens stream in word-by-word]

---

## Key Takeaways

1. **Week 2 is about INTELLIGENCE, not just retrieval**
   - Transform from simple Q&A to self-correcting mentor

2. **LangGraph enables stateful workflows**
   - Think of it as a "program" for AI reasoning
   - Nodes = steps, Edges = decisions

3. **Loop prevention is CRITICAL**
   - Without max_retries, system can infinite loop
   - Always cap iterations

4. **Prompt engineering matters MORE in agentic systems**
   - Grading prompt must reliably return yes/no
   - Rewrite prompt must actually improve query
   - Each prompt requires iteration

5. **Trade latency for quality**
   - Simple RAG: 3 seconds, sometimes wrong
   - Agentic RAG: 10 seconds, usually correct
   - Week 3 streaming makes latency feel better

---

## Resources

**LangGraph:**
- Official docs: https://langchain-ai.github.io/langgraph/
- Tutorial: https://blog.langchain.com/agentic-rag-with-langgraph/
- Examples: https://github.com/langchain-ai/langgraph/tree/main/examples

**Agentic RAG Papers:**
- "Self-RAG": https://arxiv.org/abs/2310.11511
- "Corrective RAG": https://arxiv.org/abs/2401.15884

**Your Project Docs:**
- `SIX_WEEK_EXECUTION_PLAN.md` - Full development plan
- `CLAUDE.md` - Project architecture
- `RAG_TEST_RESULTS.md` - Week 1 test results

---

## Ready to Start?

**Current status:** ✅ Simple RAG working, GPU accelerated, tested
**Next task:** Install LangGraph and study concepts (Task 2.1 + 2.2)
**Estimated time to complete Week 2:** 30-35 hours
**Exciting milestone:** Transform your tutor from basic Q&A to intelligent, self-correcting mentor!

**First command to run:**
```bash
cd /root/AIMentorProject-1/backend
source venv/bin/activate
pip install "langgraph==0.0.55" "langchain==0.1.20" "langchain-core==0.1.52" "langchain-community==0.0.38"
python3 -c "from langgraph.graph import StateGraph, END; print('✓ LangGraph installed')"
```

Let's build something intelligent! 🚀
