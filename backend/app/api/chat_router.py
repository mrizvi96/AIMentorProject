"""
Chat API Endpoints

Provides three types of chat endpoints:
1. Simple RAG - Direct retrieval and generation
2. Agentic RAG - Self-correcting with query rewriting and relevance grading
3. Pedagogical RAG - Phase-based tutoring with Socratic guidance
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.rag_service import rag_service
from app.services.agentic_rag import get_agentic_rag_service
from app.services.state_manager import state_manager
from app.services.pedagogical_graph import pedagogical_graph
from app.models.pedagogical_state import TutoringPhase

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

class PedagogicalChatResponse(BaseModel):
    """
    Pedagogical chat response with phase information

    Contains the AI-generated response along with tutoring phase context.
    """
    answer: str = Field(description="The AI-generated response with Socratic guidance")
    current_phase: str = Field(description="Current tutoring phase the conversation is in")
    phase_summary: str = Field(description="Human-readable description of the current phase")
    phase_history: List[str] = Field(description="History of phases visited in this conversation")
    problem_statement: Optional[str] = Field(description="The problem being worked on, if established")
    question: str = Field(description="The original user message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "Let's break this down step by step. First, can you tell me what you've tried so far?",
                    "current_phase": "explanation",
                    "phase_summary": "Breaking down the problem",
                    "phase_history": ["initial", "explanation"],
                    "problem_statement": "How to implement binary search tree",
                    "question": "I need help implementing a BST"
                }
            ]
        }
    }

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


@router.post("/chat/pedagogical", response_model=PedagogicalChatResponse)
async def chat_pedagogical(request: ChatRequest):
    """
    Process a question using Pedagogical RAG (Phase-based tutoring)

    This endpoint uses a phase-based state machine to provide Socratic tutoring:
    - INITIAL: Understand the problem
    - EXPLANATION: Break down the problem
    - IMPLEMENTATION: Work on solution steps
    - DEBUGGING: Fix issues systematically
    - REFLECTION: Review and learn

    **Use this endpoint when:**
    - You want guided learning instead of direct answers
    - You're working through a complex problem step by step
    - You need help with debugging or understanding concepts
    - You want to develop problem-solving skills

    **Response includes:**
    - Socratic guidance instead of direct answers
    - Current tutoring phase
    - Phase history
    - Problem statement (if established)

    **Example Request:**
    ```json
    {
        "message": "I'm stuck implementing a binary search tree",
        "conversation_id": "session-123"
    }
    ```

    **Example Response:**
    ```json
    {
        "answer": "Let's think through this step by step. Can you tell me what you've tried so far?",
        "current_phase": "debugging",
        "phase_summary": "Fixing issues",
        "phase_history": ["initial", "explanation", "implementation", "debugging"],
        "problem_statement": "Implementing binary search tree",
        "question": "I'm stuck implementing a BST"
    }
    ```
    """
    try:
        logger.info(f"Pedagogical chat request from conversation {request.conversation_id}")

        # Get or create state for this conversation
        pedagogical_state = state_manager.get_or_create_state(request.conversation_id)

        # Create a simple mapping of phase to node function
        from ..services.pedagogical_graph import (
            initial_node, explanation_node, implementation_node,
            debugging_node, reflection_node, PedagogicalGraphState, route_phase
        )

        # Prepare state for graph
        graph_state = {
            "pedagogical_state": pedagogical_state,
            "user_message": request.message,
            "generation": ""
        }

        # Use route_phase to determine which node to execute based on user message
        # This ensures we route to the correct phase for new messages
        target_phase = route_phase(graph_state)

        phase_node_map = {
            "INITIAL": initial_node,
            "EXPLANATION": explanation_node,
            "IMPLEMENTATION": implementation_node,
            "DEBUGGING": debugging_node,
            "REFLECTION": reflection_node
        }

        # Execute the appropriate node based on routing decision
        node_function = phase_node_map.get(target_phase, initial_node)
        result = node_function(graph_state)

        # Validate response completeness
        response_text = result["generation"]

        # Check if response is too short or incomplete
        if len(response_text.strip()) < 20:
            logger.warning(f"Short pedagogical response detected: {response_text[:100]}")
            # For debugging: log the routing info
            logger.info(f"Routed to phase: {target_phase}, User message: {request.message[:100]}")

        # Common incomplete responses to detect and potentially retry
        incomplete_patterns = [
            "Remember, the goal is",
            "Good luck",
            "Your task is",
            "Question 1:",
            "Answer:",
            "Response:"
        ]

        if any(pattern in response_text for pattern in incomplete_patterns):
            logger.warning(f"Likely incomplete response pattern detected: {response_text[:100]}")

        # Update state with results
        updated_state = result["pedagogical_state"]
        state_manager.update_state(
            request.conversation_id,
            current_phase=updated_state.current_phase,
            problem_statement=updated_state.problem_statement,
            last_user_message=updated_state.last_user_message,
            last_ai_response=updated_state.last_ai_response,
            phase_history=updated_state.phase_history
        )

        # Return pedagogical response
        return PedagogicalChatResponse(
            answer=result["generation"],
            current_phase=updated_state.current_phase.value,
            phase_summary=updated_state.get_phase_summary(),
            phase_history=updated_state.phase_history,
            problem_statement=updated_state.problem_statement,
            question=request.message
        )

    except Exception as e:
        logger.error(f"Pedagogical chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process pedagogical request: {str(e)}"
        )


@router.get("/chat/pedagogical/state/{conversation_id}")
async def get_pedagogical_state(conversation_id: str):
    """
    Get the current pedagogical state for a conversation
    Useful for debugging or UI state management
    """
    try:
        state = state_manager.get_state(conversation_id)
        if not state:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "conversation_id": state.conversation_id,
            "current_phase": state.current_phase.value,
            "phase_summary": state.get_phase_summary(),
            "phase_history": state.phase_history,
            "problem_statement": state.problem_statement,
            "last_user_message": state.last_user_message,
            "last_ai_response": state.last_ai_response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get pedagogical state error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/pedagogical/state/{conversation_id}")
async def clear_pedagogical_state(conversation_id: str):
    """
    Clear the pedagogical state for a conversation
    Useful for starting fresh on a new problem
    """
    try:
        success = state_manager.delete_state(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"message": "Pedagogical state cleared successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear pedagogical state error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
