"""
State Manager for Pedagogical Tutoring System

This module provides simple in-memory state management for tracking
pedagogical tutoring sessions across multiple conversations.
"""

from typing import Dict
from ..models.pedagogical_state import PedagogicalState


class StateManager:
    """
    Simple in-memory manager for pedagogical tutoring states.

    This stores PedagogicalState objects by conversation ID, allowing
    the tutoring context to persist across multiple messages within
    the same conversation.
    """

    def __init__(self):
        """Initialize the state manager with an empty state dictionary."""
        self.states: Dict[str, PedagogicalState] = {}

    def get_or_create_state(self, conversation_id: str) -> PedagogicalState:
        """
        Get existing state for a conversation or create a new one.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            PedagogicalState: The state for the conversation
        """
        if conversation_id not in self.states:
            self.states[conversation_id] = PedagogicalState(
                conversation_id=conversation_id
            )
        return self.states[conversation_id]

    def update_state(self, conversation_id: str, **kwargs) -> PedagogicalState:
        """
        Update specific fields of a conversation's state.

        Args:
            conversation_id: Unique identifier for the conversation
            **kwargs: Fields to update (e.g., current_phase, problem_statement)

        Returns:
            PedagogicalState: The updated state
        """
        state = self.get_or_create_state(conversation_id)
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                # Log warning for unknown fields
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Attempted to update unknown field: {key}")
        return state

    def get_state(self, conversation_id: str) -> PedagogicalState:
        """
        Get the state for a conversation (returns None if not found).

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            PedagogicalState or None: The state for the conversation
        """
        return self.states.get(conversation_id)

    def delete_state(self, conversation_id: str) -> bool:
        """
        Delete the state for a conversation.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            bool: True if state was deleted, False if not found
        """
        if conversation_id in self.states:
            del self.states[conversation_id]
            return True
        return False

    def get_all_states(self) -> Dict[str, PedagogicalState]:
        """
        Get all stored states.

        Returns:
            Dict[str, PedagogicalState]: All stored states by conversation ID
        """
        return self.states.copy()

    def clear_all_states(self) -> None:
        """Clear all stored states (useful for testing or reset)."""
        self.states.clear()

    def get_conversation_count(self) -> int:
        """
        Get the number of active conversations.

        Returns:
            int: Number of stored states
        """
        return len(self.states)


# Global singleton instance for the application
state_manager = StateManager()