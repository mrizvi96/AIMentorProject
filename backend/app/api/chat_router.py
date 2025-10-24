"""
Chat API Endpoints
Simple RAG endpoints for Week 1 MVP.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.rag_service import rag_service
from app.services.agentic_rag import get_agentic_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Pydantic models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's question")
    conversation_id: Optional[str] = Field(default="default", description="Conversation ID for tracking")

class Source(BaseModel):
    """Source document information"""
    text: str
    score: float
    metadata: dict

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str
    sources: List[Source]
    question: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat requests using Simple RAG (non-agentic)

    This is the Week 1 MVP endpoint. Will be enhanced with LangGraph in Week 3.
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
