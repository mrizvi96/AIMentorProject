# AI Mentor Project: Unimplemented Features

Based on a comparison between the project proposal dated 10/22/2025 and the current state of the repository, the following features and components have not yet been implemented.

This document focuses on high-level capabilities and architectural components that were described in the proposal but are not present in the current codebase.

---

## 1. ~~Core Pedagogical Logic and State Machine~~ ✅ **IMPLEMENTED**

*This feature has been fully implemented and is now functional.*

*   **Proposed:** The AI mentor would guide students through a problem-solving process using a multi-state pedagogical framework. The proposal explicitly defines these states:
    *   **Initial State:** Understand the user's problem.
    *   **Explanation State:** Help the student break down the problem.
    *   **Implementation State:** Assist with a specific step.
    *   **Debugging State:** Help the student think through an error.
    *   **Reflection State:** Prompt the student to consider alternative approaches and edge cases.
*   **Current Status:** ✅ **FULLY IMPLEMENTED** - A complete pedagogical state machine using LangGraph has been implemented with all 5 phases. The system uses Socratic questioning methods rather than direct Q&A. Users can toggle between regular Q&A mode and pedagogical tutoring mode in the UI.
*   **Files:**
    * `backend/app/models/pedagogical_state.py` - State model with 5 phases
    * `backend/app/services/pedagogical_graph.py` - Core state machine implementation
    * `backend/app/services/state_manager.py` - State persistence
    * `backend/app/api/chat_router.py` & `chat_ws.py` - API endpoints
    * `backend/tests/test_pedagogical_flow.py` - Complete test suite (6/6 passing)
    * `frontend/src/lib/components/PedagogicalStatus.svelte` - UI components

---

## 2. Detailed Interaction Logging for Analytics

*   **Proposed:** An extensive logging system would capture detailed interaction data for future analysis and the development of personalized learning paths. This included:
    *   User's initial query.
    *   AI's response.
    *   The specific prompt sent to the SLM.
    *   The learner’s **pedagogical state** at the time of the query.
    *   Source materials used for the response.
    *   A user-provided rating of the response's usefulness.
*   **Current Status:** The backend application has standard logging for debugging purposes. However, there is no evidence of the structured, database-oriented logging designed to capture the specific data points listed above for analytical purposes.

---

## 3. User Feedback Mechanism

*   **Proposed:** Students would have an opportunity to rate the usefulness of a response, and this rating would be logged.
*   **Current Status:** The frontend UI does not contain any buttons, star ratings, or other controls for a user to provide feedback on the AI's answer. The backend does not have an endpoint to receive or store this feedback.

---

## 4. Multi-Session Management and Conversation History

*   **Proposed:** The application would support multiple, distinct chat sessions, and users would be able to view their past conversations.
*   **Current Status:**
    *   The frontend is a single-page application that appears to support only one continuous chat session.
    *   There is no UI for switching between different sessions or viewing a list of past conversations.
    *   While the backend API `ChatRequest` model includes a `conversation_id`, the corresponding frontend management features are not implemented.

---

## 5. Real-Time Streaming Chat Interface

*   **Proposed:** The project would feature "real-time, responsive chat features."
*   **Current Status:** The backend has a WebSocket router (`chat_ws.py`) and endpoint, indicating that a real-time communication channel was planned or partially built. However, the primary frontend logic (`+page.svelte`) uses a standard HTTP request (`sendMessageHTTP`) to communicate with the backend. This results in a request-response interaction rather than a real-time, streaming one.

---

## 6. Formal System Evaluation

*   **Proposed:** The system was to be evaluated using a pre-written question bank (Task #4, Week 12).
*   **Current Status:** The repository contains a `student_questions.json` file and a `/api/chat/compare` endpoint, which are excellent building blocks for an evaluation. However, there are no automated evaluation scripts, and the `RAG_TEST_RESULTS.md` file is empty, indicating that a formal, documented evaluation has not yet been conducted or recorded.
