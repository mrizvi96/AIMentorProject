#!/usr/bin/env python3
"""
Standalone test script for pedagogical flow (no pytest dependency)
"""

import httpx
import time
import random
import sys

# --- Configuration ---
BASE_URL = "http://localhost:8000/api/chat/pedagogical"
STATE_URL = "http://localhost:8000/api/chat/pedagogical/state"
CONVERSATION_ID = f"test-session-{random.randint(1000, 9999)}"

def send_message(message: str, conv_id: str = CONVERSATION_ID):
    """Sends a message to the pedagogical chat endpoint."""
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                BASE_URL,
                json={"message": message, "conversation_id": conv_id}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def get_state(conv_id: str = CONVERSATION_ID):
    """Gets the current pedagogical state for a conversation."""
    try:
        with httpx.Client() as client:
            response = client.get(f"{STATE_URL}/{conv_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error getting state: {e}")
        return None

def cleanup_state(conv_id: str = CONVERSATION_ID):
    """Clean up state after tests"""
    try:
        with httpx.Client() as client:
            response = client.delete(f"{STATE_URL}/{conv_id}")
            return response.status_code == 200
    except:
        return False

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

    if not response:
        print("✗ Test 01 Failed: No response from server")
        return False

    # 2. Assertions on the response
    if response["answer"] is None:
        print("✗ Test 01 Failed: No answer in response")
        return False

    if response["current_phase"] != "initial":
        print(f"✗ Test 01 Failed: Expected phase 'initial', got '{response['current_phase']}'")
        return False

    if response["problem_statement"] is None:
        print("✗ Test 01 Failed: No problem statement in response")
        return False

    # 3. Get state directly from the state endpoint
    state = get_state()
    if not state:
        print("✗ Test 01 Failed: No state found")
        return False

    if state["conversation_id"] != CONVERSATION_ID:
        print(f"✗ Test 01 Failed: Wrong conversation ID: {state['conversation_id']}")
        return False

    if state["current_phase"] != "initial":
        print(f"✗ Test 01 Failed: State has wrong phase: {state['current_phase']}")
        return False

    if state["problem_statement"] is None:
        print("✗ Test 01 Failed: State has no problem statement")
        return False

    if state["phase_history"] != ["initial"]:
        print(f"✗ Test 01 Failed: Wrong phase history: {state['phase_history']}")
        return False

    print("✓ Test 01 Passed: Initial contact created state correctly.")
    return True

def test_02_transition_to_explanation():
    """
    Test Case 2: Transition to Explanation
    - Sends a more detailed problem description.
    - Verifies that the phase transitions to 'explanation'.
    """
    print("\n--- Running Test 02: Transition to Explanation ---")
    time.sleep(1)  # Give server a moment

    # 1. Send a clear problem statement
    message = "I need to implement a binary search tree in Python, but I'm not sure where to start."
    response = send_message(message)

    if not response:
        print("✗ Test 02 Failed: No response from server")
        return False

    # 2. Assertions
    if response["current_phase"] != "explanation":
        print(f"✗ Test 02 Failed: Expected phase 'explanation', got '{response['current_phase']}'")
        return False

    state = get_state()
    if not state:
        print("✗ Test 02 Failed: No state found")
        return False

    if state["current_phase"] != "explanation":
        print(f"✗ Test 02 Failed: State has wrong phase: {state['current_phase']}")
        return False

    if "initial" not in state["phase_history"]:
        print("✗ Test 02 Failed: 'initial' not in phase history")
        return False

    print("✓ Test 02 Passed: Correctly transitioned to EXPLANATION phase.")
    return True

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

    if not response:
        print("✗ Test 03 Failed: No response from server")
        return False

    # 2. Assertions
    if response["current_phase"] != "debugging":
        print(f"✗ Test 03 Failed: Expected phase 'debugging', got '{response['current_phase']}'")
        return False

    state = get_state()
    if not state:
        print("✗ Test 03 Failed: No state found")
        return False

    if state["current_phase"] != "debugging":
        print(f"✗ Test 03 Failed: State has wrong phase: {state['current_phase']}")
        return False

    if "explanation" not in state["phase_history"]:
        print("✗ Test 03 Failed: 'explanation' not in phase history")
        return False

    print("✓ Test 03 Passed: Correctly transitioned to DEBUGGING phase on error.")
    return True

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

    if not response:
        print("✗ Test 04 Failed: No response from server")
        return False

    # 2. Assertions
    if response["current_phase"] != "reflection":
        print(f"✗ Test 04 Failed: Expected phase 'reflection', got '{response['current_phase']}'")
        return False

    state = get_state()
    if not state:
        print("✗ Test 04 Failed: No state found")
        return False

    if state["current_phase"] != "reflection":
        print(f"✗ Test 04 Failed: State has wrong phase: {state['current_phase']}")
        return False

    if "debugging" not in state["phase_history"]:
        print("✗ Test 04 Failed: 'debugging' not in phase history")
        return False

    print("✓ Test 04 Passed: Correctly transitioned to REFLECTION phase on success.")
    return True

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

    if not response:
        print("✗ Test 05 Failed: No response from server")
        return False

    # 2. Assertions
    if response["current_phase"] != "initial":
        print(f"✗ Test 05 Failed: Expected phase 'initial', got '{response['current_phase']}'")
        return False

    state = get_state()
    if not state:
        print("✗ Test 05 Failed: No state found")
        return False

    if state["current_phase"] != "initial":
        print(f"✗ Test 05 Failed: State has wrong phase: {state['current_phase']}")
        return False

    if "reflection" not in state["phase_history"]:
        print("✗ Test 05 Failed: 'reflection' not in phase history")
        return False

    print("✓ Test 05 Passed: Correctly transitioned back to INITIAL for a new problem.")
    return True

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
        if delete_response.status_code != 200:
            print(f"✗ Test 06 Failed: Delete failed with status {delete_response.status_code}")
            return False

    # 2. Verify that getting the state now fails with a 404
    with httpx.Client() as client:
        get_response = client.get(f"{STATE_URL}/{CONVERSATION_ID}")
        if get_response.status_code != 404:
            print(f"✗ Test 06 Failed: Expected 404 after delete, got {get_response.status_code}")
            return False

    print("✓ Test 06 Passed: Correctly deleted conversation state.")
    return True

def run_all_tests():
    """Run all test cases"""
    tests = [
        test_01_initial_contact_and_state_creation,
        test_02_transition_to_explanation,
        test_03_transition_to_debugging,
        test_04_transition_to_reflection,
        test_05_transition_back_to_initial,
        test_06_delete_state
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            failed += 1

    # Summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    print(f"{'='*50}")

    return failed == 0

if __name__ == "__main__":
    # Ensure cleanup at the end
    try:
        success = run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted")
        success = False
    finally:
        # Always try to cleanup
        print(f"\nCleaning up state for conversation: {CONVERSATION_ID}")
        if cleanup_state():
            print("Cleanup successful.")
        else:
            print("Cleanup failed or was not needed.")

    sys.exit(0 if success else 1)