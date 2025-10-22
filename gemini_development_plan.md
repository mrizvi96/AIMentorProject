# Gemini's Incremental Development Plan for the AI Mentor Project

## Introduction

This document outlines a strategic plan for the continued development of the AI Mentor project. It builds upon the existing foundation, including the work from the "SIX_WEEK_EXECUTION_PLAN.md" and the "WEEKS_1-2_SUMMARY.md". The focus of this plan is to promote a modular, scalable, and incremental development process, ensuring a robust and maintainable final product.

## Guiding Principles

*   **Modularity:** Each component of the system (e.g., data ingestion, RAG service, API, frontend) should be self-contained and easily replaceable or upgradeable.
*   **Scalability:** The architecture should be able to handle growth in terms of data volume, user traffic, and computational demand.
*   **Incremental Development:** Features will be developed and integrated in small, manageable, and testable steps.
*   **Test-Driven Development (TDD):** Writing tests before or alongside new features to ensure correctness and prevent regressions.

## Phase 1: Solidify the Foundation

**Goal:** Ensure the existing simple RAG pipeline is robust, configurable, and has a basic level of automated testing.

**Tasks:**

1.  **Configuration Management:**
    *   **Problem:** Hardcoded values (like model names, collection names, ports) are scattered throughout the code.
    *   **Solution:** Centralize all configuration in `backend/app/core/config.py` using Pydantic's `BaseSettings` to load from environment variables. This will make the application easier to configure for different environments (development, testing, production).
    *   **File to create/modify:** `backend/app/core/config.py`

2.  **Robust Error Handling and Logging:**
    *   **Problem:** The current error handling is basic. More specific exceptions and more structured logging are needed for easier debugging.
    *   **Solution:** Implement custom exception classes for different error scenarios (e.g., `LLMConnectionError`, `VectorDBError`). Use a structured logging library (like `structlog`) to produce machine-readable logs.

3.  **Unit and Integration Testing:**
    *   **Problem:** The current plan lacks a formal testing strategy.
    *   **Solution:** Introduce `pytest` for backend testing.
        *   **Unit Tests:** Test individual functions and classes in isolation (e.g., test the `ChatRequest` model).
        *   **Integration Tests:** Test the interaction between components (e.g., test the `/api/chat` endpoint by mocking the RAG service).
    *   **Files to create:** `backend/tests/unit/` and `backend/tests/integration/`.

4.  **Basic CI/CD Pipeline:**
    *   **Problem:** Manual testing is slow and error-prone.
    *   **Solution:** Create a simple GitHub Actions workflow that automatically runs `pytest` on every push to the `main` branch. This will provide rapid feedback on code changes.
    *   **File to create:** `.github/workflows/backend-ci.yml`

## Phase 2: Enhance the RAG Pipeline (Agentic Capabilities)

**Goal:** Implement the planned agentic workflow using LangGraph, while maintaining a modular architecture.

**Tasks:**

1.  **Modular RAG Service:**
    *   **Problem:** The `SimpleRAGService` is a good start, but integrating the agentic workflow directly could make it monolithic.
    *   **Solution:** Refactor the RAG service. Create a base `RAGService` interface and implement `SimpleRAGService` and `AgenticRAGService` as separate classes that adhere to this interface. This will allow for easy switching between the two.

2.  **Develop LangGraph Agent:**
    *   **Problem:** The agentic logic needs to be implemented.
    *   **Solution:** Implement the LangGraph agent as described in the "SIX_WEEK_EXECUTION_PLAN.md". This includes the agent state, nodes for retrieval, grading, rewriting, and generation.

3.  **API for Agentic RAG:**
    *   **Problem:** A new endpoint is needed for the agentic RAG.
    *   **Solution:** Create a new API endpoint (e.g., `/api/chat/agentic`) for the agentic RAG. This keeps the simple RAG available for comparison and testing.

4.  **Frontend Enhancements for Agentic Workflow:**
    *   **Problem:** The frontend needs to visualize the agent's process.
    *   **Solution:** Update the Svelte frontend to display the agent's current state (e.g., "Rewriting question...", "Grading documents..."). This can be achieved by extending the API response to include the workflow path.

## Phase 3: Evaluation and User Experience

**Goal:** Systematically evaluate the RAG system's performance and improve the overall user experience.

**Tasks:**

1.  **Evaluation Framework:**
    *   **Problem:** No systematic way to measure the quality of the RAG system.
    *   **Solution:**
        *   Create a small, representative evaluation dataset of question-answer pairs.
        *   Develop a Python script to run these questions through the RAG system and compare the generated answers to the ground truth.
        *   Use metrics like RAGAs (Retrieval-Augmented Generation Assessment) to evaluate retrieval and generation quality.

2.  **Conversation History:**
    *   **Problem:** The current chat is stateless.
    *   **Solution:** Implement conversation history. The backend should store and retrieve conversation history, and the RAG system should use it to understand the context of the user's questions.

3.  **Frontend Polish:**
    *   **Problem:** The frontend is basic.
    *   **Solution:**
        *   Implement Markdown rendering for the AI's responses to allow for better formatting (e.g., lists, bold text).
        *   Add syntax highlighting for code snippets in the responses.
        *   Improve the overall styling and layout.

## Phase 4: Scalability and Deployment

**Goal:** Prepare the application for a more production-like environment and ensure it can scale.

**Tasks:**

1.  **Containerization:**
    *   **Problem:** The current setup relies on manual steps and scripts.
    *   **Solution:** Create `Dockerfile`s for the backend and frontend applications. Update the `docker-compose.yml` to run the entire application stack (backend, frontend, Milvus, LLM server) with a single command.

2.  **Scalable LLM Serving:**
    *   **Problem:** The `llama-cpp-python` server is good for development, but may not be sufficient for higher loads.
    *   **Solution:** Explore and benchmark more advanced inference servers like vLLM or Text Generation Inference (TGI). The modular design of the RAG service should make it easy to swap out the LLM component.

3.  **Monitoring and Health Checks:**
    *   **Problem:** No visibility into the health and performance of the services.
    *   **Solution:**
        *   Expand the `/api/health` endpoint to provide a more comprehensive status of all services.
        *   Introduce a monitoring tool like Prometheus to collect metrics from the backend and other services.

4.  **Refined Deployment Process:**
    *   **Problem:** The deployment process is manual.
    *   **Solution:** Create a deployment script or extend the GitHub Actions workflow to automate the deployment of the containerized application to a target environment.

## Conclusion

This plan provides a roadmap for the continued development of the AI Mentor project. By focusing on modularity, scalability, and incremental development, we can build a robust, maintainable, and high-quality application. The emphasis on testing and evaluation from an early stage will ensure that the project stays on track and meets its goals.
