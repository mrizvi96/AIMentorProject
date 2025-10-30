# AI Mentor: Hardening and Evaluation Plan

## 1. Executive Summary

**Current State:** The AI Mentor project is a feature-complete but fragile prototype. It successfully implements an advanced, agentic RAG architecture with WebSocket streaming, as envisioned in the original `plan.txt`. However, this was achieved by taking significant shortcuts, resulting in critical flaws that undermine its stability, portability, and performance.

**Identified Shortcuts & Gaps:**

1.  **Inconsistent and Flawed Configuration:** The backend uses two different embedding models (`all-MiniLM-L6-v2` and `BAAI/bge-small-en-v1.5`), with one being referenced via a hardcoded local path, making setup and replication extremely difficult.
2.  **Sub-optimal RAG Parameters:** The RAG pipeline is configured for speed over quality, retrieving only the single best document chunk (`top_k_retrieval: 1`) from small text chunks (`chunk_size: 256`). This severely limits the context provided to the LLM and is a likely source of poor-quality responses.
3.  **Lack of Observability:** The complex agentic workflow in `agentic_rag.py` has insufficient logging, making it a "black box" that is nearly impossible to debug when errors occur.
4.  **Brittle Agentic Logic:** The LangGraph nodes lack robust error handling. A malformed response from the LLM during a grading or rewriting step could cause the entire workflow to fail unpredictably.
5.  **No Performance Baseline:** The quality of the RAG system is completely unknown. No systematic evaluation has been performed to measure the accuracy, relevance, and faithfulness of the generated answers.

**Path Forward:** This plan outlines a "fix forward" strategy. We will not remove the advanced features. Instead, we will execute a three-phase plan to harden the existing implementation, establish a rigorous evaluation framework, and iteratively refine the system into a production-worthy state.

---

## 2. Phase 1: Foundational RAG & Configuration Cleanup (Immediate Priority)

**Objective:** To fix the broken RAG configuration, establish a consistent and sensible performance baseline, and make the project portable.

### Task 1.1: Unify the Embedding Strategy

**Problem:** The project uses two different embedding models, and one is hardcoded to a local path, breaking portability.

**Plan:**
1.  **Select a Single Model:** Standardize on one embedding model for the entire application. The `BAAI/bge-small-en-v1.5` model specified in `config.py` is a strong choice.
2.  **Update Configuration:** Modify `backend/app/core/config.py`. Change the `embedding_model_name` from the hardcoded path to the Hugging Face model identifier:
    ```python
    # OLD
    # embedding_model_name: str = "./embedding_cache/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    
    # NEW
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    ```
3.  **Update All Services:** Ensure both `rag_service.py` and `agentic_rag.py` use this setting from `config.py`. This will involve removing the hardcoded `all-MiniLM-L6-v2` from `agentic_rag.py`. LlamaIndex will now automatically download and cache the model on first run, ensuring portability.

### Task 1.2: Tune RAG Parameters for Quality

**Problem:** The current RAG parameters (`top_k_retrieval: 1`, `chunk_size: 256`) are severely limiting the quality of the context.

**Plan:**
1.  **Update Configuration:** Modify `backend/app/core/config.py` to use more robust and conventional RAG parameters.
    ```python
    # OLD
    # chunk_size: int = 256
    # top_k_retrieval: int = 1
    
    # NEW
    chunk_size: int = 512
    top_k_retrieval: int = 3
    ```
2.  **Rationale:** Increasing `chunk_size` to 512 provides more meaningful context within each chunk. Increasing `top_k_retrieval` to 3 gives the LLM a much richer set of information to synthesize an answer from, reducing the risk of simplistic or incomplete responses.

### Task 1.3: Re-ingest Knowledge Base

**Problem:** The existing ChromaDB vector store was built with the old, inconsistent settings.

**Plan:**
1.  **Delete Old Database:** Remove the `./backend/chroma_db` directory entirely.
2.  **Run Ingestion Script:** Execute the `ingest.py` script from the `backend` directory.
    ```bash
    python ingest.py
    ```
3.  **Verification:** Confirm that a new `chroma_db` directory is created and populated. This ensures the vector store is now built with a single, high-quality embedding model and a better chunking strategy.

---

## 3. Phase 2: Observability and Hardening

**Objective:** To make the complex agentic workflow debuggable, transparent, and resilient to failure.

### Task 2.1: Implement Structured Logging

**Problem:** The agentic workflow is a "black box." It's impossible to trace the flow of a query or inspect the state at each step.

**Plan:**
1.  **Enhance Logging Configuration:** Ensure the logging in `main.py` uses a structured format that is easy to parse (e.g., JSON).
2.  **Add Detailed Logs to Agent Nodes:** In `backend/app/services/agentic_rag.py`, add detailed logging at the beginning and end of each node function (`_retrieve`, `_grade_documents`, `_rewrite_query`, `_generate`).
    *   **Log Inputs:** Log the relevant parts of the `state` that the node is using.
    *   **Log Outputs:** Log the decision made (for grading) or the data being added back to the `state`.
    *   **Example (in `_grade_documents`):**
        ```python
        logger.info(f"Grading documents for question: {state['question']}")
        # ... grading logic ...
        logger.info(f"Grading decision: {decision}")
        ```

### Task 2.2: Harden Agentic Workflow

**Problem:** The LangGraph nodes assume the LLM will always return perfectly formatted data. A single unexpected output can crash the process.

**Plan:**
1.  **Validate Grader Output:** In the `_grade_documents` node, add logic to parse the LLM's response robustly. Do not just check for `"yes" in decision`. Check if the response is *exactly* "yes" or "no" (after stripping whitespace and converting to lowercase). If the response is anything else, default to a safe behavior (e.g., log a warning and treat it as "yes" to avoid a loop).
2.  **Add `try...except` Blocks:** Wrap the LLM calls within each node (`_grade_documents`, `_rewrite_query`, `_generate`) in `try...except` blocks to catch API errors, timeouts, or other exceptions from the `llama-cpp-python` server. In the case of an error, the node should return a sensible default value and log the failure.
3.  **Harden WebSocket Error Handling:** In `backend/app/api/chat_ws.py`, expand the `except Exception as e:` block to send a more specific, user-friendly error message to the frontend via the WebSocket `error` event type.

---

## 4. Phase 3: Systematic Evaluation and Refinement

**Objective:** To quantitatively measure the performance of the RAG system, identify weaknesses, and use this data to guide iterative improvements.

### Task 3.1: Implement the Evaluation Framework

**Problem:** The quality of the AI mentor is subjective and unknown.

**Plan:**
1.  **Create Question Bank:** As specified in `WEEKS_3-4_EXECUTION_PLAN.md`, create `backend/evaluation/question_bank.json`. Populate it with 20-30 diverse questions based on the ingested documents, including factual, conceptual, and comparative questions.
2.  **Create Evaluation Script:** Create `backend/evaluation/run_evaluation.py`. This script will:
    *   Load the question bank.
    *   Iterate through each question, sending it to the **non-streaming `/api/chat-agentic` endpoint**.
    *   Save the question, the generated answer, the retrieved sources, and the agent's workflow path to a results file (e.g., `evaluation_results.json`).

### Task 3.2: Run Baseline Evaluation and Iteratively Refine

**Plan:**
1.  **Execute Baseline Run:** Run the evaluation script to generate the first set of results with the newly configured, hardened system.
2.  **Manual Scoring:** Create a spreadsheet or markdown table (`ANALYSIS.md`) and manually score each result based on:
    *   **Answer Relevance (1-5):** Does it answer the question?
    *   **Faithfulness (1-5):** Is the answer supported by the sources?
    *   **Conciseness (1-5):** Is it free of waffle?
3.  **Analyze and Refine:** Analyze the scores to identify patterns of failure. Use these insights to perform targeted **prompt engineering** on the prompts in `agentic_rag.py`. For example:
    *   If answers are not faithful, make the `_generate` prompt stricter about adhering to the context.
    *   If the rewrite loop is triggered too often, make the `_grade_documents` prompt more lenient.
4.  **Iterate:** After each significant prompt change, re-run the evaluation and compare the scores to measure the impact of the change. The goal is to achieve a demonstrable improvement in the average scores.
