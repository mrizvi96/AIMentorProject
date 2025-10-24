"""
Test streaming functionality locally
"""
import asyncio
import sys
sys.path.append('/root/AIMentorProject-1/backend')

from app.services.agentic_rag import get_agentic_rag_service_async

async def test_streaming():
    print("\n" + "="*80)
    print("Testing Agentic RAG Streaming")
    print("="*80)

    rag = await get_agentic_rag_service_async()
    question = "What is a variable in Python?"

    print(f"\nQuestion: {question}")
    print("\nStreaming response:\n")

    full_answer = ""

    async for chunk in rag.query_stream(question):
        chunk_type = chunk.get("type")

        if chunk_type == "workflow":
            node = chunk.get("node")
            status = chunk.get("status")
            print(f"[{node.upper()}] {status}")

        elif chunk_type == "token":
            content = chunk.get("content")
            print(content, end="", flush=True)
            full_answer += content

        elif chunk_type == "metadata":
            event = chunk.get("event")
            print(f"\n[METADATA] {event}: {chunk}")

        elif chunk_type == "complete":
            print("\n\n[COMPLETE]")
            break

        elif chunk_type == "error":
            print(f"\n[ERROR] {chunk.get('error')}")
            break

    print(f"\n\nFull answer ({len(full_answer)} chars):")
    print(full_answer)
    print("\n✓ Streaming test complete")

if __name__ == "__main__":
    asyncio.run(test_streaming())
