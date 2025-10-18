"""
Chat API Router
Provides REST and WebSocket endpoints for chat interactions
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import json

from ..services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    conversation_id: Optional[str] = "default"


class SourceDocument(BaseModel):
    """Source document reference"""
    text: str
    score: float
    metadata: Dict


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    sources: List[SourceDocument]
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI mentor response

    This is a simple REST endpoint (non-streaming).
    WebSocket streaming will be added in Phase 2.
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Ensure RAG service is initialized
        if not rag_service._initialized:
            logger.info("RAG service not initialized, initializing now...")
            rag_service.initialize()

        # Query the RAG system
        result = await rag_service.query(request.message)

        # Format response
        response = ChatResponse(
            response=result['response'],
            sources=[
                SourceDocument(
                    text=src['text'],
                    score=src['score'],
                    metadata=src['metadata']
                )
                for src in result['sources']
            ],
            conversation_id=request.conversation_id
        )

        return response

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stats")
async def get_stats():
    """Get RAG service statistics"""
    return rag_service.get_stats()


# WebSocket endpoint for streaming (Phase 2)
@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for streaming chat responses

    Note: Full streaming implementation will be added in Phase 2
    with LangGraph agentic workflow.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established: {conversation_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            logger.info(f"WebSocket received: {message.get('message', '')[:50]}...")

            # Ensure RAG service is initialized
            if not rag_service._initialized:
                rag_service.initialize()

            # Query RAG system
            result = await rag_service.query(message['message'])

            # Send response back to client
            await websocket.send_json({
                'type': 'response',
                'response': result['response'],
                'sources': result['sources']
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
