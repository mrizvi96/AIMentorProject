# Agentic RAG Guide

## Architecture

The agentic RAG workflow is implemented using LangGraph. The workflow is a state machine with the following nodes:

- `retrieve`: Retrieves documents from the vector store.
- `grade_documents`: Grades the relevance of the retrieved documents.
- `rewrite_query`: Rewrites the query if the documents are not relevant.
- `generate`: Generates the final answer.

The workflow is as follows:

1. The `retrieve` node is the entry point.
2. After `retrieve`, the `grade_documents` node is called.
3. Based on the grade, the workflow either goes to the `generate` node or the `rewrite_query` node.
4. If the workflow goes to the `rewrite_query` node, it then goes back to the `retrieve` node.
5. The `generate` node is the exit point.

## API Endpoints

- `POST /api/chat-agentic`: This endpoint takes a `ChatRequest` and returns an `AgenticChatResponse`.
- `GET /api/chat/compare`: This endpoint takes a `question` and compares the simple and agentic RAG systems.

## How to Use

To use the agentic RAG system, send a POST request to the `/api/chat-agentic` endpoint with a `ChatRequest` body.

To compare the simple and agentic RAG systems, send a GET request to the `/api/chat/compare` endpoint with a `question` query parameter.
