"""
WebSocket Chat Router
Provides streaming chat interface via WebSocket for real-time token delivery
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import AsyncGenerator

from ..services.agentic_rag import get_agentic_rag_service_async

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/api/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat

    Protocol:
    - Client sends: JSON {"message": "user question", "max_retries": 2}
    - Server sends: JSON events with type field:
        - {"type": "workflow", "node": "retrieve", "message": "Running retrieve..."}
        - {"type": "token", "content": "word"}
        - {"type": "complete", "answer": "...", "sources": [...], ...}
        - {"type": "error", "message": "error description"}
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                max_retries = message_data.get("max_retries", 2)

                if not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message received"
                    })
                    continue

                logger.info(f"Received question: {user_message[:100]}...")

                # Get agentic RAG service
                rag_service = await get_agentic_rag_service_async()

                # Stream the response
                async for event in rag_service.query_stream(user_message, max_retries):
                    # Send each event to client
                    await websocket.send_json(event)

                logger.info("Response streaming completed")

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Processing failed: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
