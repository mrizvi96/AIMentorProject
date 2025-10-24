"""
Test script for Agentic RAG service
Tests various scenarios including query rewriting
"""
import sys
sys.path.append('/root/AIMentorProject-1/backend')

from app.services.agentic_rag import get_agentic_rag_service

def test_simple_query():
    """Test with a straightforward query that should retrieve relevant docs"""
    print("\n" + "="*80)
    print("TEST 1: Simple query (should NOT trigger rewrite)")
    print("="*80)

    rag = get_agentic_rag_service()
    result = rag.query("What is a variable in Python?")

    print(f"\nQuestion: {result['question']}")
    print(f"Workflow: {result['workflow_path']}")
    print(f"Rewrites used: {result['rewrites_used']}")
    print(f"Answer preview: {result['answer'][:200]}...")
    print(f"Sources: {result['num_sources']}")

    assert "rewrite" not in result['workflow_path'].lower(), "Should not rewrite simple query"
    assert result['rewrites_used'] == 0, "Should use 0 rewrites"

    print("\n✓ Test 1 passed")

def test_ambiguous_query():
    """Test with an ambiguous query that might trigger rewrite"""
    print("\n" + "="*80)
    print("TEST 2: Ambiguous query (MAY trigger rewrite)")
    print("="*80)

    rag = get_agentic_rag_service()
    result = rag.query("How does it work?")  # Ambiguous "it"

    print(f"\nQuestion: {result['question']}")
    print(f"Workflow: {result['workflow_path']}")
    print(f"Rewrites used: {result['rewrites_used']}")
    print(f"Was rewritten: {result['was_rewritten']}")

    if result['was_rewritten']:
        print(f"Answer preview: {result['answer'][:200]}...")
        print(f"\n✓ Test 2 passed (rewrite triggered as expected)")
    else:
        print(f"\n✓ Test 2 passed (found relevant docs without rewrite)")

def test_max_retries():
    """Test that max_retries prevents infinite loops"""
    print("\n" + "="*80)
    print("TEST 3: Max retries limit")
    print("="*80)

    rag = get_agentic_rag_service()
    result = rag.query("asdfghjkl qwertyuiop", max_retries=1)  # Nonsense query

    print(f"\nQuestion: {result['question']}")
    print(f"Workflow: {result['workflow_path']}")
    print(f"Rewrites used: {result['rewrites_used']}")
    print(f"Max retries: 1")

    assert result['rewrites_used'] <= 1, "Should not exceed max_retries"

    print("\n✓ Test 3 passed (retry limit enforced)")

if __name__ == "__main__":
    print("\n🧪 Starting Agentic RAG Tests...")

    try:
        test_simple_query()
        test_ambiguous_query()
        test_max_retries()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
