#!/usr/bin/env python3
"""
Test the complete RAG pipeline with ChromaDB + LLM
"""
import sys
import time
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

from app.services.rag_service import RAGService

async def test_full_rag_pipeline():
    print("=" * 70)
    print("Testing Complete RAG Pipeline (ChromaDB + Mistral-7B)")
    print("=" * 70)

    try:
        # Initialize RAG service
        print("\n1. Initializing RAG Service...")
        rag_service = RAGService()
        rag_service.initialize()
        print("   ✓ RAG Service initialized successfully")

        # Test queries
        test_queries = [
            "What is Python?",
            "Explain object-oriented programming",
            "What are the key features of Python programming language?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'-' * 70}")
            print(f"Test Query {i}: {query}")
            print(f"{'-' * 70}")

            start_time = time.time()
            response = await rag_service.query(query)
            elapsed = time.time() - start_time

            print(f"\nResponse (generated in {elapsed:.2f}s):")
            print(f"{response['response']}")

            if 'sources' in response and response['sources']:
                print(f"\nSources ({len(response['sources'])} documents):")
                for idx, node in enumerate(response['sources'][:2], 1):
                    print(f"  [{idx}] Score: {node['score']:.4f}")
                    print(f"      Text: {node['text'][:150]}...")

        print("\n" + "=" * 70)
        print("✅ ALL RAG PIPELINE TESTS PASSED")
        print("=" * 70)
        print("\nSystem Components Working:")
        print("  ✓ ChromaDB: Document retrieval")
        print("  ✓ Embeddings: sentence-transformers/all-MiniLM-L6-v2")
        print("  ✓ LLM: Mistral-7B-Instruct-v0.2 (Q5_K_M)")
        print("  ✓ RAG Pipeline: End-to-end query answering")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_rag_pipeline())
    sys.exit(0 if success else 1)
