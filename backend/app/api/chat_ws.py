"""
WebSocket Chat Router
Provides streaming chat interface via WebSocket for real-time token delivery

Two endpoints available:
1. /api/ws/chat - Agentic RAG with self-correction
2. /api/ws/chat-pedagogical - Phase-based tutoring with Socratic guidance
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import AsyncGenerator

from ..services.agentic_rag import get_agentic_rag_service_async
from ..services.state_manager import state_manager
from ..services.pedagogical_graph import pedagogical_graph

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


@router.websocket("/api/ws/chat-pedagogical/{conversation_id}")
async def websocket_pedagogical_chat_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for pedagogical tutoring with phase tracking

    Protocol:
    - Client sends: JSON {"message": "user message"}
    - Server sends: JSON events with type field:
        - {"type": "phase_change", "phase": "explanation", "message": "Breaking down the problem"}
        - {"type": "workflow", "node": "EXPLANATION", "message": "Running explanation phase..."}
        - {"type": "token", "content": "word"}
        - {"type": "complete", "answer": "...", "current_phase": "explanation", ...}
        - {"type": "error", "message": "error description"}

    Features:
    - Tracks tutoring phase across messages
    - Provides phase change notifications
    - Maintains conversation state
    - Socratic guidance instead of direct answers
    """
    await websocket.accept()
    logger.info(f"Pedagogical WebSocket connection established for conversation {conversation_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")

                if not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message received"
                    })
                    continue

                logger.info(f"Pedagogical message: {user_message[:100]}... (conversation: {conversation_id})")

                # Get current state for this conversation
                pedagogical_state = state_manager.get_or_create_state(conversation_id)
                previous_phase = pedagogical_state.current_phase.value

                # Send phase change notification if phase will change
                if len(pedagogical_state.phase_history) == 0:
                    # First message, show initial phase
                    await websocket.send_json({
                        "type": "phase_change",
                        "phase": "initial",
                        "message": "Understanding your problem"
                    })

                # Prepare state for graph
                graph_state = {
                    "pedagogical_state": pedagogical_state,
                    "user_message": user_message,
                    "generation": ""
                }

                # Import node functions and route_phase function
                from ..services.pedagogical_graph import (
                    initial_node, explanation_node, implementation_node,
                    debugging_node, reflection_node, route_phase
                )

                # Use route_phase to determine which node to execute
                target_phase = route_phase(graph_state)

                phase_node_map = {
                    "INITIAL": initial_node,
                    "EXPLANATION": explanation_node,
                    "IMPLEMENTATION": implementation_node,
                    "DEBUGGING": debugging_node,
                    "REFLECTION": reflection_node
                }

                # Execute the appropriate node
                node_function = phase_node_map.get(target_phase, initial_node)
                result = node_function(graph_state)
                updated_state = result["pedagogical_state"]

                # Update state with results
                state_manager.update_state(
                    conversation_id,
                    current_phase=updated_state.current_phase,
                    problem_statement=updated_state.problem_statement,
                    last_user_message=updated_state.last_user_message,
                    last_ai_response=updated_state.last_ai_response,
                    phase_history=updated_state.phase_history
                )

                # Notify about phase change if it occurred
                if previous_phase != updated_state.current_phase.value:
                    await websocket.send_json({
                        "type": "phase_change",
                        "phase": updated_state.current_phase.value,
                        "message": updated_state.get_phase_summary()
                    })

                # Send workflow step notification
                if updated_state.phase_history:
                    last_phase = updated_state.phase_history[-1]
                    await websocket.send_json({
                        "type": "workflow",
                        "node": last_phase.upper(),
                        "message": f"Completed {last_phase} phase"
                    })

                # Stream the response tokens
                answer_text = result["generation"]

                # For now, send the complete answer as a single token
                # In the future, we could implement actual token streaming from LLM
                await websocket.send_json({
                    "type": "token",
                    "content": answer_text
                })

                # Send completion event with full context
                await websocket.send_json({
                    "type": "complete",
                    "answer": answer_text,
                    "current_phase": updated_state.current_phase.value,
                    "phase_summary": updated_state.get_phase_summary(),
                    "phase_history": updated_state.phase_history,
                    "problem_statement": updated_state.problem_statement,
                    "question": user_message
                })

                logger.info(f"Pedagogical response sent for conversation {conversation_id}")

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing pedagogical message: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Processing failed: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info(f"Pedagogical WebSocket connection closed by client (conversation: {conversation_id})")
    except Exception as e:
        logger.error(f"Pedagogical WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
