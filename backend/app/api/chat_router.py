"""
Chat API Endpoints

Provides two RAG (Retrieval-Augmented Generation) endpoints:
1. Simple RAG - Direct retrieval and generation
2. Agentic RAG - Self-correcting with query rewriting and relevance grading
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.rag_service import rag_service
from app.services.agentic_rag import get_agentic_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Pydantic models with enhanced documentation
class ChatRequest(BaseModel):
    """
    Chat request payload

    Represents a user's question to the AI Mentor system.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question or prompt. Must be between 1-2000 characters.",
        examples=["What is a binary search tree?", "Explain dynamic programming"]
    )
    conversation_id: Optional[str] = Field(
        default="default",
        description="Unique identifier for the conversation session. Used for context tracking.",
        examples=["user-123-session-456", "default"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "What are the time complexity trade-offs between quicksort and mergesort?",
                    "conversation_id": "session-abc-123"
                }
            ]
        }
    }

class Source(BaseModel):
    """
    Source document reference

    Represents a document retrieved from the knowledge base that was used to generate the answer.
    """
    text: str = Field(description="Excerpt from the source document relevant to the query")
    score: float = Field(description="Relevance score (0.0-1.0), higher means more relevant", ge=0.0, le=1.0)
    metadata: dict = Field(description="Document metadata (filename, page number, etc.)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "A binary search tree is a node-based data structure where each node has at most two children...",
                    "score": 0.92,
                    "metadata": {"filename": "algorithms_textbook.pdf", "page": 127}
                }
            ]
        }
    }

class ChatResponse(BaseModel):
    """
    Chat response with answer and sources

    Contains the AI-generated answer along with source documents that were used.
    """
    answer: str = Field(description="The AI-generated answer to the user's question")
    sources: List[Source] = Field(description="List of source documents used to generate the answer")
    question: str = Field(description="The original question (or rewritten version if query was rewritten)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "A binary search tree (BST) is a hierarchical data structure where each node contains a key and has at most two children...",
                    "sources": [
                        {
                            "text": "Binary search trees maintain the BST property: left subtree keys < node key < right subtree keys",
                            "score": 0.94,
                            "metadata": {"filename": "data_structures.pdf", "page": 45}
                        }
                    ],
                    "question": "What is a binary search tree?"
                }
            ]
        }
    }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a question using Simple RAG (Direct Retrieval)

    This endpoint implements a straightforward retrieval-augmented generation workflow:
    1. Embeds the user's question
    2. Retrieves relevant documents from the vector database (top-k similarity search)
    3. Generates an answer using the retrieved context

    **Use this endpoint when:**
    - You want fast, direct answers
    - The question is well-formed and specific
    - You don't need self-correction or query refinement

    **Response includes:**
    - Generated answer based on retrieved documents
    - Source documents with relevance scores
    - Original question

    **Example Request:**
    ```json
    {
        "message": "What is the time complexity of quicksort?",
        "conversation_id": "session-123"
    }
    ```

    **Example Response:**
    ```json
    {
        "answer": "Quicksort has an average-case time complexity of O(n log n)...",
        "sources": [...],
        "question": "What is the time complexity of quicksort?"
    }
    ```

    **Error Responses:**
    - `500`: LLM server unavailable or generation failed
    - `422`: Invalid request format or validation error
    """
    try:
        logger.info(f"Chat request from conversation {request.conversation_id}")

        # Get RAG service
        result = await rag_service.query(request.message)

        # Return structured response
        return ChatResponse(answer=result['response'], sources=result['sources'], question=result['question'])

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )

class AgenticChatResponse(ChatResponse):
    """Extended response with agentic metadata"""
    workflow_path: str
    rewrites_used: int
    was_rewritten: bool

@router.post("/chat-agentic", response_model=AgenticChatResponse)
async def chat_agentic(request: ChatRequest):
    """
    Handle chat requests using Agentic RAG (self-correcting)

    This endpoint uses LangGraph to implement:
    - Document relevance grading
    - Query rewriting if retrieval fails
    - Self-correction loop (max 2 retries)
    """
    try:
        logger.info(f"Agentic chat request from conversation {request.conversation_id}")

        # Get agentic RAG service
        rag_service = get_agentic_rag_service()

        # Query with self-correction
        result = rag_service.query(request.message, max_retries=2)

        # Return extended response with metadata
        return AgenticChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            question=result["question"],
            workflow_path=result["workflow_path"],
            rewrites_used=result["rewrites_used"],
            was_rewritten=result["was_rewritten"]
        )

    except Exception as e:
        logger.error(f"Agentic chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )

@router.get("/chat/compare")
async def compare_rag_types(question: str):
    """
    Compare simple RAG vs agentic RAG on the same question
    Useful for evaluation and debugging
    """
    try:

        # Simple RAG
        simple_result = await rag_service.query(question)

        # Agentic RAG
        agentic_rag = get_agentic_rag_service()
        agentic_result = agentic_rag.query(question)

        return {
            "question": question,
            "simple_rag": {
                "answer": simple_result["response"],
                "num_sources": len(simple_result["sources"])
            },
            "agentic_rag": {
                "answer": agentic_result["answer"],
                "num_sources": agentic_result["num_sources"],
                "workflow": agentic_result["workflow_path"],
                "rewrites": agentic_result["rewrites_used"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
