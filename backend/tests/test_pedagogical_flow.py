"""
Integration Tests for the Pedagogical State Machine

This test suite verifies the functionality of the core pedagogical tutoring
system by simulating a conversation and asserting the state transitions.

To run:
- Ensure the backend server is running.
- Run from the root of the project: `pytest backend/tests/test_pedagogical_flow.py`
"""

import pytest
import httpx
import time
import random

# --- Configuration ---
BASE_URL = "http://localhost:8000/api/chat/pedagogical"
STATE_URL = f"http://localhost:8000/api/chat/pedagogical/state"
CONVERSATION_ID = f"test-session-{random.randint(1000, 9999)}"

# --- Test Fixture ---

@pytest.fixture(scope="module", autouse=True)
def cleanup_state_after_tests():
    """Fixture to ensure state is cleared after all tests in this module run."""
    yield
    # Teardown: clear the state
    print(f"\nCleaning up state for conversation: {CONVERSATION_ID}")
    try:
        with httpx.Client() as client:
            response = client.delete(f"{STATE_URL}/{CONVERSATION_ID}")
            if response.status_code == 200:
                print("Cleanup successful.")
            elif response.status_code == 404:
                print("State was already clean.")
            else:
                print(f"Warning: Cleanup failed with status {response.status_code}")
    except httpx.ConnectError:
        print("Warning: Could not connect to server for cleanup. It might be offline.")


# --- Helper Functions ---

def send_message(message: str, conv_id: str = CONVERSATION_ID):
    """Sends a message to the pedagogical chat endpoint."""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            BASE_URL,
            json={"message": message, "conversation_id": conv_id}
        )
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        return response.json()

def get_state(conv_id: str = CONVERSATION_ID):
    """Gets the current pedagogical state for a conversation."""
    with httpx.Client() as client:
        response = client.get(f"{STATE_URL}/{conv_id}")
        response.raise_for_status()
        return response.json()

# --- Test Cases ---

def test_01_initial_contact_and_state_creation():
    """
    Test Case 1: Initial contact
    - Sends a first message.
    - Verifies that the state is created.
    - Checks that the initial phase is 'initial'.
    """
    print(f"\n--- Running Test 01: Initial Contact (Conv ID: {CONVERSATION_ID}) ---")

    # 1. Send initial message
    message = "I need help with a data structures problem."
    response = send_message(message)

    # 2. Assertions on the response
    assert response["answer"] is not None
    assert response["current_phase"] == "initial"
    assert response["problem_statement"] is not None

    # 3. Get state directly from the state endpoint
    state = get_state()
    assert state["conversation_id"] == CONVERSATION_ID
    assert state["current_phase"] == "initial"
    assert state["problem_statement"] is not None
    assert state["phase_history"] == ["initial"]
    print("✓ Test 01 Passed: Initial contact created state correctly.")

def test_02_transition_to_explanation():
    """
    Test Case 2: Transition to Explanation
    - Sends a more detailed problem description.
    - Verifies that the phase transitions to 'explanation'.
    """
    print("\n--- Running Test 02: Transition to Explanation ---")
    time.sleep(1) # Give server a moment

    # 1. Send a clear problem statement
    message = "I need to implement a binary search tree in Python, but I'm not sure where to start."
    response = send_message(message)

    # 2. Assertions
    assert response["current_phase"] == "explanation"
    state = get_state()
    assert state["current_phase"] == "explanation"
    assert "initial" in state["phase_history"]
    print("✓ Test 02 Passed: Correctly transitioned to EXPLANATION phase.")

def test_03_transition_to_debugging():
    """
    Test Case 3: Transition to Debugging
    - Sends a message containing keywords like 'error' or 'bug'.
    - Verifies that the phase transitions to 'debugging'.
    """
    print("\n--- Running Test 03: Transition to Debugging ---")
    time.sleep(1)

    # 1. Send a message indicating an error
    message = "I wrote some code for the insert method, but I'm getting a TypeError and it's not working."
    response = send_message(message)

    # 2. Assertions
    assert response["current_phase"] == "debugging"
    state = get_state()
    assert state["current_phase"] == "debugging"
    assert "explanation" in state["phase_history"]
    print("✓ Test 03 Passed: Correctly transitioned to DEBUGGING phase on error.")

def test_04_transition_to_reflection():
    """
    Test Case 4: Transition to Reflection
    - Sends a message indicating the problem is solved.
    - Verifies that the phase transitions to 'reflection'.
    """
    print("\n--- Running Test 04: Transition to Reflection ---")
    time.sleep(1)

    # 1. Send a message indicating the problem is solved
    message = "Ah, I see! The problem was in my node initialization. I fixed it and it works now! Thanks."
    response = send_message(message)

    # 2. Assertions
    assert response["current_phase"] == "reflection"
    state = get_state()
    assert state["current_phase"] == "reflection"
    assert "debugging" in state["phase_history"]
    print("✓ Test 04 Passed: Correctly transitioned to REFLECTION phase on success.")

def test_05_transition_back_to_initial():
    """
    Test Case 5: Resetting the conversation
    - Sends a message indicating a new problem.
    - Verifies that the phase transitions back to 'initial'.
    """
    print("\n--- Running Test 05: Transition back to Initial ---")
    time.sleep(1)

    # 1. Send a message indicating a new problem
    message = "Okay, that's great. Now I'd like to start a new problem about sorting algorithms."
    response = send_message(message)

    # 2. Assertions
    assert response["current_phase"] == "initial"
    state = get_state()
    assert state["current_phase"] == "initial"
    assert "reflection" in state["phase_history"]
    print("✓ Test 05 Passed: Correctly transitioned back to INITIAL for a new problem.")

def test_06_delete_state():
    """
    Test Case 6: Deleting state
    - Calls the DELETE endpoint.
    - Verifies that a subsequent GET request returns a 404.
    """
    print("\n--- Running Test 06: Deleting State ---")

    # 1. Delete the state
    with httpx.Client() as client:
        delete_response = client.delete(f"{STATE_URL}/{CONVERSATION_ID}")
        assert delete_response.status_code == 200

    # 2. Verify that getting the state now fails with a 404
    with httpx.Client() as client:
        get_response = client.get(f"{STATE_URL}/{CONVERSATION_ID}")
        assert get_response.status_code == 404

    print("✓ Test 06 Passed: Correctly deleted conversation state.")
