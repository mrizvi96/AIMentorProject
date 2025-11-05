#!/usr/bin/env python3
"""
Single question evaluation test with verbose logging
"""
import sys
import logging
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging to see everything
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.services.rag_service import RAGService

async def test_single_question():
    """Test a single question with full logging"""
    print("=" * 70)
    print("SINGLE QUESTION EVALUATION TEST")
    print("=" * 70)

    # Initialize RAG service
    print("\n1. Initializing RAG service...")
    rag_service = RAGService()
    rag_service.initialize()
    print("   ✓ RAG service initialized\n")

    # Test question
    question = "What is Python?"
    print(f"2. Testing question: {question}\n")

    # Query RAG service
    print("3. Querying RAG service...")
    result = await rag_service.query(question)

    print("\n4. Results:")
    print(f"   - Response type: {type(result['response'])}")
    print(f"   - Response length: {len(str(result['response']))} chars")
    print(f"   - Sources count: {len(result.get('sources', []))}")
    print(f"\n5. Response content:")
    print(f"   {result['response']}")

    if result.get('sources'):
        print(f"\n6. First source:")
        source = result['sources'][0]
        print(f"   - Text: {source['text'][:100]}...")
        print(f"   - Score: {source['score']}")
        print(f"   - Metadata: {source['metadata'].get('file_name', 'N/A')}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_single_question())
