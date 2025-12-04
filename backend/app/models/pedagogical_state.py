"""
Pedagogical State Model for AI Mentor Tutoring System

This module defines the data structures for tracking the pedagogical state
of a tutoring conversation, including the current tutoring phase and context.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class TutoringPhase(Enum):
    """The different phases of the tutoring process"""
    INITIAL = "initial"
    EXPLANATION = "explanation"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    REFLECTION = "reflection"


class PedagogicalState(BaseModel):
    """
    Tracks the state of a pedagogical tutoring conversation.

    This state persists across messages within a conversation to maintain
    tutoring context and guide the student through problem-solving phases.
    """
    conversation_id: str = Field(default="default", description="Unique identifier for the conversation")
    current_phase: TutoringPhase = Field(
        default=TutoringPhase.INITIAL,
        description="Current tutoring phase"
    )
    problem_statement: Optional[str] = Field(
        default=None,
        description="The problem the student is trying to solve"
    )
    last_user_message: Optional[str] = Field(
        default=None,
        description="The last message from the user"
    )
    last_ai_response: Optional[str] = Field(
        default=None,
        description="The last response from the AI"
    )
    phase_history: List[str] = Field(
        default_factory=list,
        description="History of phases visited in order"
    )

    def get_phase_summary(self) -> str:
        """Get a human-readable summary of the current phase"""
        phase_descriptions = {
            TutoringPhase.INITIAL: "Understanding your problem",
            TutoringPhase.EXPLANATION: "Breaking down the problem",
            TutoringPhase.IMPLEMENTATION: "Working on the solution",
            TutoringPhase.DEBUGGING: "Fixing issues",
            TutoringPhase.REFLECTION: "Reviewing and learning"
        }
        return phase_descriptions.get(self.current_phase, "Unknown phase")

    def transition_to_phase(self, new_phase: TutoringPhase) -> None:
        """Record a phase transition"""
        if self.current_phase != new_phase:
            self.phase_history.append(self.current_phase.value)
            self.current_phase = new_phase