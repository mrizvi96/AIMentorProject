# AI Mentor: Weeks 3-4 Execution Plan

## WEEK 3: REAL-TIME STREAMING WITH WEBSOCKETS

**Goal:** Enhance user experience by providing real-time, token-by-token streaming for answers and broadcasting workflow state changes.
**Effort:** 25-30 hours
**Success Criteria:** The frontend chat updates in real-time, showing both the agent's internal state (e.g., "Rewriting question...") and the final answer as it's being generated.

---

### Day 1-2: Backend WebSocket Implementation (10-12 hours)

#### **Task 3.1: Create WebSocket Endpoint** (2-3 hours)

- In `backend/app/api/`, create a new file `chat_ws.py`.
- Implement a FastAPI `WebSocket` endpoint at `/api/ws/chat`.
- This endpoint will handle the lifecycle of a WebSocket connection: accepting connections, receiving a user's question, and streaming back responses.

#### **Task 3.2: Implement Graph-Level Streaming in `agentic_rag.py`** (6-8 hours)

- In `backend/app/services/agentic_rag.py`, create a new `async` method `query_stream()`.
- This method will use `self.graph.astream()` to iterate through the LangGraph state updates. **This is the correct approach learned from the Week 2 bug.**
- For each state update, yield a JSON object indicating the event type (e.g., `{"type": "workflow", "event": "retrieve"}`).
- When the `generate` node is reached, instead of returning the full text, use a streaming-capable LLM call (`llm.stream_chat()`) and yield each token as a `{"type": "token", "content": "..."}` event.
- Ensure the `_generate` node itself remains non-streaming (`llm.complete()`) for the core graph logic, and the streaming for the final answer is handled within the `query_stream` method after the final state is reached.

#### **Task 3.3: Update `main.py`** (30 min)

- Import the new router from `chat_ws.py`.
- Include the WebSocket router in the FastAPI app.

---

### Day 3-4: Frontend WebSocket Integration (10-12 hours)

#### **Task 3.4: Create WebSocket Service** (3-4 hours)

- In `frontend/src/lib/`, create a new file `websocket.ts`.
- This service will manage the WebSocket connection, including `connect`, `disconnect`, `sendMessage`, and message listeners (`onopen`, `onmessage`, `onclose`, `onerror`).
- It should expose Svelte stores or callbacks to broadcast received messages to the UI.

#### **Task 3.5: Update Chat UI (`+page.svelte`)** (5-6 hours)

- Refactor the main page to use the new `websocket.ts` service instead of the HTTP-based `api.ts`.
- When the user sends a message, call the WebSocket service.
- Listen for incoming messages and update the UI dynamically.
- **UX Improvement:** Display status messages based on workflow events (e.g., "Retrieving relevant documents...", "Grading documents...", "Your question is being rewritten for clarity...").
- Append tokens to the assistant's message bubble in real-time to create a typing effect.

---

### Day 5: Testing and Refinement (4-6 hours)

#### **Task 3.6: Create Streaming Test Script** (2-3 hours)

- In `backend/`, create `test_streaming_ws.py`.
- Use a Python WebSocket client library (like `websockets`) to connect to the `/api/ws/chat` endpoint.
- Send a sample question and assert that the script receives a sequence of both workflow and token events, ending with a "complete" message.

#### **Task 3.7: End-to-End Testing** (2-3 hours)

- Manually test the entire flow from the Svelte UI.
- Verify that the UI correctly displays status updates and streams the final answer.
- Test with questions that are likely to trigger the rewrite loop to ensure those events are also broadcast correctly.

---

## WEEK 4: EVALUATION & PROMPT REFINEMENT

**Goal:** Systematically evaluate the RAG system's performance, identify weaknesses, and refine prompts for better accuracy and reliability.
**Effort:** 25-30 hours
**Success Criteria:** A completed evaluation report with quantitative and qualitative findings, and demonstrable improvements in answer quality after prompt refinement.

---

### Day 1-2: Evaluation Framework Setup (8-10 hours)

#### **Task 4.1: Create Evaluation Question Bank** (2-3 hours)

- Create a new directory `backend/evaluation`.
- Inside, create `question_bank.json`.
- Populate it with 20-30 diverse questions. Include:
    - Simple, direct questions.
    - Vague or ambiguous questions designed to trigger the rewrite loop.
    - Questions whose answers are not in the source documents.
    - Complex questions requiring synthesis from multiple sources.

#### **Task 4.2: Define Evaluation Metrics** (1-2 hours)

- Create `backend/evaluation/METRICS.md`.
- Define the scoring criteria for manual evaluation:
    - **Answer Relevance (1-5):** How well does the answer address the user's question?
    - **Faithfulness (1-5):** Is the answer fully supported by the cited sources?
    - **Conciseness (1-5):** Is the answer free of redundant or irrelevant information?

#### **Task 4.3: Create Evaluation Script** (5-6 hours)

- Create `backend/evaluation/run_evaluation.py`.
- The script should:
    1. Load the `question_bank.json`.
    2. Iterate through each question.
    3. Execute a query against the **agentic RAG service** (non-streaming endpoint).
    4. For each result, save the question, answer, sources, workflow path, and response time to `evaluation_results.json`.

---

### Day 3-4: Analysis and Prompt Engineering (10-12 hours)

#### **Task 4.4: Run Evaluation and Analyze Results** (4-5 hours)

- Run the `run_evaluation.py` script.
- Create a spreadsheet or markdown table (`backend/evaluation/ANALYSIS.md`).
- Manually score each generated answer based on the defined metrics (Relevance, Faithfulness, Conciseness).
- Identify patterns:
    - Where does the agent fail to rewrite effectively?
    - When does it hallucinate information not in the context?
    - Are the generated answers too verbose?
    - Does the grading step incorrectly classify documents?

#### **Task 4.5: Refine Prompts** (6-7 hours)

- Based on the analysis, iteratively refine the system prompts in `backend/app/services/agentic_rag.py`:
    - **`_grade_documents` prompt:** Make the instructions for "yes" or "no" more explicit.
    - **`_rewrite_query` prompt:** Provide better examples or clearer instructions on how to reformulate.
    - **`_generate` prompt:** Add constraints to improve conciseness or enforce stricter adherence to the context.
- After each significant prompt change, re-run the evaluation on a subset of the question bank to measure the impact.

---

### Day 5: Final Evaluation and Documentation (4-6 hours)

#### **Task 4.6: Final Evaluation Run** (2-3 hours)

- With the refined prompts, perform one final, full run of the evaluation script.
- Update the `ANALYSIS.md` with the new scores and a comparison against the baseline.

#### **Task 4.7: Document Findings** (2-3 hours)

- Write a summary in `ANALYSIS.md` that covers:
    - The initial baseline performance.
    - The weaknesses identified.
    - The specific prompt changes made.
    - The final performance scores, demonstrating the improvements.
    - Recommendations for future prompt engineering work.
