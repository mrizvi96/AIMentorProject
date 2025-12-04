"""
Pedagogical Graph for AI Mentor Tutoring System

This module implements a LangGraph-based state machine for pedagogical tutoring,
with nodes representing different tutoring phases and an intelligent router
that determines the next phase based on user input.
"""

import logging
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

from ..models.pedagogical_state import PedagogicalState, TutoringPhase
from ..services.agentic_rag import get_agentic_rag_service


class PedagogicalGraphState(TypedDict):
    """State for the pedagogical graph workflow"""
    pedagogical_state: PedagogicalState
    user_message: str
    generation: str

logger = logging.getLogger(__name__)


def initial_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initial phase: Understand the user's problem and set up tutoring context.

    This node focuses on clarifying the problem statement and understanding
    what the student is trying to accomplish.
    """
    pedagogical_state = state['pedagogical_state']
    user_message = state['user_message']

    prompt = f"""A student says: '{user_message}'

Help them clarify their problem. Ask what they're trying to solve and any relevant details.

Be supportive and encouraging. Ask 1-2 clarifying questions. Do NOT provide solutions.

Start naturally without mentioning you are an example."""

    # Use existing RAG service for context if needed
    rag_service = get_agentic_rag_service()
    response = rag_service.llm.complete(prompt)

    # Update the problem statement if it seems clear from the message
    problem_statement = pedagogical_state.problem_statement
    if not problem_statement and len(user_message.strip()) > 20:
        # Simple heuristic: if the message is substantial and there's no problem statement yet
        # use it as a tentative problem statement
        problem_statement = user_message.strip()

    return {
        "generation": response.text,
        "pedagogical_state": pedagogical_state.model_copy(update={
            "last_user_message": user_message,
            "last_ai_response": response.text,
            "problem_statement": problem_statement,
            "phase_history": pedagogical_state.phase_history + ["initial"],
            "current_phase": TutoringPhase.INITIAL
        })
    }


def explanation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explanation phase: Help the student break down the problem.

    This node guides the student through creating a high-level plan
    and understanding the problem components.
    """
    pedagogical_state = state['pedagogical_state']
    user_message = state['user_message']

    prompt = f"""You are an expert Computer Science tutor helping a student break down their problem.

Problem statement: '{pedagogical_state.problem_statement or user_message}'
User's current message: '{user_message}'

Your goal in this EXPLANATION phase is to:
1. Help them create a high-level, step-by-step plan in plain English
2. Identify key concepts they need to understand
3. Suggest how to approach the problem systematically
4. Break complex problems into manageable sub-problems

Do NOT write code. Focus on planning and understanding.
Ask guiding questions to help them think through the approach.

Respond in a supportive tone and guide them step-by-step."""

    rag_service = get_agentic_rag_service()
    response = rag_service.llm.complete(prompt)

    return {
        "generation": response.text,
        "pedagogical_state": pedagogical_state.model_copy(update={
            "last_user_message": user_message,
            "last_ai_response": response.text,
            "phase_history": pedagogical_state.phase_history + ["explanation"],
            "current_phase": TutoringPhase.EXPLANATION
        })
    }


def implementation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implementation phase: Assist with a specific implementation step.

    This node helps the student work through a specific part of their solution.
    """
    pedagogical_state = state['pedagogical_state']
    user_message = state['user_message']

    prompt = f"""You are an expert Computer Science tutor helping a student implement their solution.

Problem statement: '{pedagogical_state.problem_statement or "Not specified yet"}'
User's current implementation step/question: '{user_message}'

Your goal in this IMPLEMENTATION phase is to:
1. Help them think through the specific step they're working on
2. Encourage them to consider different approaches before coding
3. Guide them through writing pseudocode or thinking about logic
4. Help them verify their approach makes sense

Encourage them to think through the approach first before writing code.
If they show code, focus on the logic and approach rather than syntax.

Respond with guidance and questions to help them implement this specific step."""

    rag_service = get_agentic_rag_service()
    response = rag_service.llm.complete(prompt)

    return {
        "generation": response.text,
        "pedagogical_state": pedagogical_state.model_copy(update={
            "last_user_message": user_message,
            "last_ai_response": response.text,
            "phase_history": pedagogical_state.phase_history + ["implementation"],
            "current_phase": TutoringPhase.IMPLEMENTATION
        })
    }


def debugging_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Debugging phase: Help the student think through an error.

    This node guides students through systematic debugging rather than
    giving them the direct solution.
    """
    pedagogical_state = state['pedagogical_state']
    user_message = state['user_message']

    # Direct response to avoid LLM confusion
    # Extract just the problem part, removing leading acknowledgments
    problem_part = user_message
    if user_message.lower().startswith(("yes.", "yeah.", "ok.", "okay.", "sure.")):
        problem_part = user_message.split('.', 1)[1].strip() if '.' in user_message else user_message

    return {
        "generation": f"""That sounds frustrating! Can you tell me more about what you're trying to do?

You mentioned: {problem_part}

What does the error or issue mean? Can you show me the relevant part of your code?""",
        "pedagogical_state": pedagogical_state.model_copy(update={
            "last_user_message": user_message,
            "last_ai_response": f"That sounds frustrating! Can you tell me more about what you're trying to do?\n\nYou mentioned: {problem_part}\n\nWhat does the error or issue mean? Can you show me the relevant part of your code?",
            "phase_history": pedagogical_state.phase_history + ["debugging"],
            "current_phase": TutoringPhase.DEBUGGING
        })
    }


def reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reflection phase: Prompt the student to consider alternatives and next steps.

    This node encourages metacognitive thinking and helps students learn
    from their problem-solving process.
    """
    pedagogical_state = state['pedagogical_state']
    user_message = state['user_message']

    prompt = f"""You are an expert Computer Science tutor helping a student reflect on their work.

Problem statement: '{pedagogical_state.problem_statement or "Not specified yet"}'
User's latest work/achievement: '{user_message}'

Your goal in this REFLECTION phase is to:
1. Help them think about what they learned
2. Consider alternative approaches or improvements
3. Identify key takeaways from the problem
4. Guide them to think about how this connects to other concepts

Ask metacognitive questions like:
- What was the most challenging part?
- What would you do differently next time?
- How does this problem connect to what you've learned before?
- What new insights did you gain?

Encourage deeper thinking about their learning process."""

    rag_service = get_agentic_rag_service()
    response = rag_service.llm.complete(prompt)

    return {
        "generation": response.text,
        "pedagogical_state": pedagogical_state.model_copy(update={
            "last_user_message": user_message,
            "last_ai_response": response.text,
            "phase_history": pedagogical_state.phase_history + ["reflection"],
            "current_phase": TutoringPhase.REFLECTION
        })
    }


def route_phase(state: Dict[str, Any]) -> str:
    """
    The router node - decides which phase to go to next.

    This is the "brains" of the pedagogical system, using LLM analysis
    to determine the most appropriate next phase based on user input.
    """
    pedagogical_state = state['pedagogical_state']
    user_message = state['user_message']

    prompt = f"""You are an intelligent routing system for a Computer Science tutoring AI.

Current tutoring phase: '{pedagogical_state.current_phase.value}'
User's message: '{user_message}'
Problem being worked on: '{pedagogical_state.problem_statement or "Not yet established"}'

Your task is to determine which tutoring phase should come next.
The available phases are: INITIAL, EXPLANATION, IMPLEMENTATION, DEBUGGING, REFLECTION.

Routing rules:
- If the user is starting a new problem or the problem statement is unclear → INITIAL
- If the user needs help understanding or breaking down the problem → EXPLANATION
- If the user is ready to work on implementation details or specific steps → IMPLEMENTATION
- If the user has an error, bug, or something isn't working → DEBUGGING
- If the user completed a step and should reflect or consider alternatives → REFLECTION

Consider the user's intent and context. Choose the phase that best serves their current need.

Respond with ONLY the name of the phase (INITIAL, EXPLANATION, IMPLEMENTATION, DEBUGGING, or REFLECTION)."""

    rag_service = get_agentic_rag_service()
    try:
        response = rag_service.llm.complete(prompt)
        next_phase = response.text.strip().upper()
    except Exception as e:
        logger.error(f"Error in phase routing LLM call: {e}")
        # Default to staying in current phase if there's an error
        next_phase = pedagogical_state.current_phase.value.upper()

    # Validate the response
    valid_phases = ["INITIAL", "EXPLANATION", "IMPLEMENTATION", "DEBUGGING", "REFLECTION"]
    if next_phase not in valid_phases:
        # If LLM gives invalid response, use simple rule-based fallback
        current_phase = pedagogical_state.current_phase.value.upper()

        # Simple fallback logic with priority for confusion over implementation
        if any(keyword in user_message.lower() for keyword in ["error", "bug", "doesn't work", "wrong", "exception", "infinite loop", "loop", "stuck", "terminate"]):
            next_phase = "DEBUGGING"
        elif any(keyword in user_message.lower() for keyword in ["done", "finished", "completed", "what's next", "works", "solved"]):
            next_phase = "REFLECTION"
        elif pedagogical_state.problem_statement is None and len(pedagogical_state.phase_history) == 0:
            # First message in new conversation - always go to INITIAL
            next_phase = "INITIAL"
        # Check for confusion before implementation - confusion takes priority
        elif any(keyword in user_message.lower() for keyword in ["not sure", "don't know", "confused", "lost", "help", "don't understand"]):
            next_phase = "EXPLANATION"
        elif any(keyword in user_message.lower() for keyword in ["implement", "code", "method", "function", "write"]):
            next_phase = "IMPLEMENTATION"
        elif any(keyword in user_message.lower() for keyword in ["explain", "understand", "break down"]):
            next_phase = "EXPLANATION"
        elif any(keyword in user_message.lower() for keyword in ["start", "new problem", "different", "another"]):
            next_phase = "INITIAL"
        else:
            next_phase = current_phase

    logger.info(f"Router: {pedagogical_state.current_phase.value} -> {next_phase}")
    return next_phase


def create_pedagogical_graph():
    """
    Build the pedagogical tutoring graph using LangGraph.

    Returns:
        Compiled LangGraph workflow ready for execution
    """
    # Create the workflow
    workflow = StateGraph(PedagogicalGraphState)

    # Add nodes for each phase
    workflow.add_node("INITIAL", initial_node)
    workflow.add_node("EXPLANATION", explanation_node)
    workflow.add_node("IMPLEMENTATION", implementation_node)
    workflow.add_node("DEBUGGING", debugging_node)
    workflow.add_node("REFLECTION", reflection_node)

    # The entry point is the starting phase.
    workflow.set_entry_point("INITIAL")

    # Each phase node should end after execution - no automatic transitions
    # The API will invoke the appropriate node based on the current phase
    workflow.add_edge("INITIAL", END)
    workflow.add_edge("EXPLANATION", END)
    workflow.add_edge("IMPLEMENTATION", END)
    workflow.add_edge("DEBUGGING", END)
    workflow.add_edge("REFLECTION", END)

    # Compile the graph
    return workflow.compile()


# Global graph instance for the application
pedagogical_graph = create_pedagogical_graph()