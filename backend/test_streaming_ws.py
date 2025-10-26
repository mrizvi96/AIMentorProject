#!/usr/bin/env python3
"""
WebSocket Streaming Test Script
Tests the real-time streaming chat functionality via WebSocket
"""
import asyncio
import json
import sys
from websockets import connect


async def test_streaming_chat():
    """Test the WebSocket streaming chat endpoint"""

    # WebSocket URL
    ws_url = "ws://localhost:8000/api/ws/chat"

    # Test question
    test_question = "What is object-oriented programming?"

    print("=" * 80)
    print("WebSocket Streaming Test")
    print("=" * 80)
    print(f"\nConnecting to: {ws_url}")
    print(f"Question: {test_question}\n")

    try:
        async with connect(ws_url) as websocket:
            print("✓ WebSocket connected\n")

            # Send question
            message = {
                "message": test_question,
                "max_retries": 2
            }
            await websocket.send(json.dumps(message))
            print(f"→ Sent question: {test_question}\n")

            # Receive streaming response
            print("-" * 80)
            print("STREAMING RESPONSE:")
            print("-" * 80)

            answer_buffer = ""
            workflow_events = []
            sources = []
            metadata = {}

            while True:
                try:
                    # Receive event
                    response = await websocket.recv()
                    event = json.loads(response)

                    event_type = event.get("type")

                    if event_type == "workflow":
                        # Workflow progress event
                        node = event.get("node", "unknown")
                        message = event.get("message", "")
                        workflow_events.append(node)
                        print(f"\n[WORKFLOW] {message}", flush=True)

                    elif event_type == "token":
                        # Token streaming event
                        token = event.get("content", "")
                        answer_buffer += token
                        print(token, end="", flush=True)

                    elif event_type == "complete":
                        # Completion event
                        print("\n")
                        print("-" * 80)
                        print("COMPLETE")
                        print("-" * 80)

                        sources = event.get("sources", [])
                        metadata = {
                            "workflow_path": event.get("workflow_path", ""),
                            "rewrites_used": event.get("rewrites_used", 0),
                            "was_rewritten": event.get("was_rewritten", False),
                            "num_sources": event.get("num_sources", 0)
                        }

                        print(f"\nWorkflow Path: {metadata['workflow_path']}")
                        print(f"Rewrites Used: {metadata['rewrites_used']}")
                        print(f"Query Rewritten: {metadata['was_rewritten']}")
                        print(f"Sources Retrieved: {metadata['num_sources']}")

                        if sources:
                            print(f"\nSources:")
                            for i, source in enumerate(sources, 1):
                                print(f"\n  Source {i} (score: {source['score']:.3f}):")
                                print(f"  {source['text']}")

                        # All done
                        break

                    elif event_type == "error":
                        # Error event
                        error_msg = event.get("message", "Unknown error")
                        print(f"\n[ERROR] {error_msg}")
                        break

                    else:
                        print(f"\n[UNKNOWN EVENT] {event}")

                except json.JSONDecodeError as e:
                    print(f"\n[JSON ERROR] Failed to parse response: {e}")
                    break

            print("\n" + "=" * 80)
            print("Test Complete")
            print("=" * 80)

            # Summary
            print("\nSummary:")
            print(f"  Answer Length: {len(answer_buffer)} characters")
            print(f"  Workflow Events: {len(workflow_events)}")
            print(f"  Sources: {len(sources)}")

            return True

    except ConnectionRefusedError:
        print("✗ Connection refused - is the backend server running?")
        print("  Start it with: uvicorn main:app --reload")
        return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_questions():
    """Test multiple questions in sequence"""

    questions = [
        "What is inheritance in OOP?",
        "Explain polymorphism with an example.",
        "What is the difference between a class and an object?"
    ]

    ws_url = "ws://localhost:8000/api/ws/chat"

    print("=" * 80)
    print("Multiple Questions Test")
    print("=" * 80)

    try:
        async with connect(ws_url) as websocket:
            print("✓ WebSocket connected\n")

            for i, question in enumerate(questions, 1):
                print(f"\n{'='*80}")
                print(f"Question {i}/{len(questions)}: {question}")
                print('='*80)

                # Send question
                message = {
                    "message": question,
                    "max_retries": 1
                }
                await websocket.send(json.dumps(message))

                # Receive response
                answer_buffer = ""

                while True:
                    response = await websocket.recv()
                    event = json.loads(response)

                    if event.get("type") == "token":
                        token = event.get("content", "")
                        answer_buffer += token
                        print(token, end="", flush=True)
                    elif event.get("type") == "complete":
                        print(f"\n\n✓ Answer received ({len(answer_buffer)} chars)")
                        break
                    elif event.get("type") == "error":
                        print(f"\n✗ Error: {event.get('message')}")
                        break

            print("\n" + "=" * 80)
            print(f"All {len(questions)} questions completed!")
            print("=" * 80)

            return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nWebSocket Streaming Tests\n")

    # Choose test mode
    if len(sys.argv) > 1 and sys.argv[1] == "multi":
        # Multiple questions test
        success = asyncio.run(test_multiple_questions())
    else:
        # Single question test (default)
        success = asyncio.run(test_streaming_chat())

    sys.exit(0 if success else 1)
