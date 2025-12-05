"""
Agent State Definition for Agentic RAG
"""
from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Shared state for agentic RAG workflow"""

    # Question management
    question: str                          # Original user question
    rewritten_question: str | None         # Query after rewrite

    # Retrieved context
    documents: List[str]                   # Document chunks
    document_scores: List[float]           # Relevance scores

    # Generation output
    generation: str                        # Final answer

    # Conversation history
    messages: Annotated[list, add_messages]

    # Loop prevention (CRITICAL!)
    retry_count: int                       # Rewrite attempts
    max_retries: int                       # Maximum allowed (default: 2)

    # Metadata
    relevance_decision: str | None         # "yes" or "no" from grading
    workflow_path: List[str]               # Visited nodes
    document_metadata: List[dict]          # Document metadata (filenames, page numbers, etc.)
    slm_prompt: str | None                 # The actual prompt sent to SLM (for analytics)