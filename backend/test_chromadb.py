#!/usr/bin/env python3
"""
Quick test script to verify ChromaDB setup and query functionality
"""
import chromadb
from app.core.config import settings

def test_chromadb():
    print("=" * 60)
    print("Testing ChromaDB Connection and Query")
    print("=" * 60)

    # Connect to ChromaDB
    print(f"\n1. Connecting to ChromaDB at: {settings.chroma_db_path}")
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    print("   ✓ Connected successfully")

    # Get collection
    print(f"\n2. Loading collection: {settings.chroma_collection_name}")
    collection = client.get_collection(name=settings.chroma_collection_name)
    print("   ✓ Collection loaded")

    # Get collection stats
    count = collection.count()
    print(f"\n3. Collection Statistics:")
    print(f"   - Total documents: {count}")

    # Test query
    print(f"\n4. Testing sample query...")
    test_query = "What is Python?"
    results = collection.query(
        query_texts=[test_query],
        n_results=3
    )

    print(f"   Query: '{test_query}'")
    print(f"   Results found: {len(results['ids'][0])}")

    if results['documents'] and len(results['documents'][0]) > 0:
        print(f"\n5. Top Result Preview:")
        print(f"   {results['documents'][0][0][:200]}...")
        print("\n   ✓ ChromaDB is working correctly!")
    else:
        print("\n   ⚠ No results found (collection might be empty)")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_chromadb()
