# Project Improvement and Documentation Plan

This document outlines identified gaps in the current implementation and proposes documentation to improve project clarity, maintainability, and onboarding.

## 1. Configuration Management

**Gap:** Key parameters like the embedding model name (`all-MiniLM-L6-v2`) and LLM settings are hardcoded in the Python scripts. This makes it difficult to experiment with different models or configurations without modifying the source code.

**Documentation Opportunity:**

*   **Create a `CONFIGURATION.md` file:** This document should detail all the environment variables and configuration settings used in the project. It should be the single source of truth for configuration.
*   **Update `README.md`:** Add a "Configuration" section to the main `README.md` that links to `CONFIGURATION.md` and explains how to set up a `.env` file.
*   **Refactor the code:** Move all hardcoded values to `app/core/config.py` and have them read from environment variables with sensible defaults.

## 2. Error Handling and Resilience

**Gap:** The agentic workflow has "fail-safe" mechanisms that might hide underlying issues. For example, if document grading fails, it defaults to "relevant," which could lead to poor-quality responses. The application startup process also lacks coordination, potentially causing race conditions.

**Documentation Opportunity:**

*   **Create a `TROUBLESHOOTING.md` file:** This document should list potential failure points (like the LLM server being down or document grading failing) and provide steps to diagnose and resolve them.
*   **Add a "System Architecture" section to the `README.md`:** This section should include a diagram showing the service dependencies and startup order. A simple Mermaid diagram would be effective here.
*   **Improve code comments:** Add comments in `agentic_rag.py` to explain the reasoning behind the current error handling and suggest how it could be improved in the future (e.g., by implementing exponential backoff or more sophisticated fallbacks).

## 3. Frontend/Backend Integration

**Gap:** The frontend is not using the WebSocket streaming functionality that has been implemented on the backend. The UI is still using a simple HTTP request-response model.

**Documentation Opportunity:**

*   **Create an `API_GUIDE.md` file:** This document should provide a clear overview of the API, including the REST endpoints and the WebSocket protocol. For the WebSocket, it should detail the expected message formats for both the client and the server.
*   **Update the main `README.md`:** Add a section on "Frontend Development" that explains the current state of the frontend and the task of integrating the WebSocket service.
*   **Add a "TODO" in `frontend/src/routes/+page.svelte`:** A comment in the code itself can serve as a reminder to replace `sendMessageHTTP` with `sendMessageWebSocket`.

## 4. Evaluation Framework

**Gap:** The evaluation framework planned for Weeks 3-4 is completely missing. There is no systematic way to measure the performance of the RAG system.

**Documentation Opportunity:**

*   **Create a `backend/evaluation/README.md` file:** Even before the code is written, a README file can be created to outline the plan for the evaluation framework. This file should describe the purpose of the evaluation, the metrics to be used, and the expected inputs and outputs of the evaluation script. This will make it easier for a developer to pick up this task.

## 5. Onboarding and General Documentation

**Gap:** The project lacks a central, up-to-date `README.md` that explains how to set up, configure, and run the project from scratch. A new developer would struggle to get started.

**Documentation Opportunity:**

*   **Revamp the root `README.md`:** This is the most critical documentation improvement. The new `README.md` should include:
    *   A brief project overview.
    *   Prerequisites (like Docker and Python).
    *   A "Getting Started" section with step-by-step instructions to run the entire application stack (e.g., `docker-compose up -d`, `python ingest.py`, `uvicorn main:app`, `npm run dev`).
    *   Links to the more detailed documentation files (`CONFIGURATION.md`, `API_GUIDE.md`, `TROUBLESHOOTING.md`).
