"""
Evaluation Script for AI Mentor RAG System

This script runs the evaluation framework against the question bank,
collects responses from the RAG service, and generates results for manual scoring.

Usage:
    python evaluation/run_evaluation.py

Output:
    evaluation/results/evaluation_TIMESTAMP.json
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import asyncio
import aiohttp
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.services.rag_service import RAGService

# Configuration
QUESTION_BANK_PATH = Path(__file__).parent / "question_bank.json"
RESULTS_DIR = Path(__file__).parent / "results"
API_BASE_URL = "http://localhost:8000/api"


def load_question_bank() -> Dict[str, Any]:
    """Load questions from question_bank.json"""
    with open(QUESTION_BANK_PATH, 'r') as f:
        return json.load(f)


def save_results(results: Dict[str, Any], timestamp: str):
    """Save evaluation results to JSON file"""
    RESULTS_DIR.mkdir(exist_ok=True)
    output_file = RESULTS_DIR / f"evaluation_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, indent=2, fp=f)

    print(f"\n✅ Results saved to: {output_file}")
    return output_file


async def query_rag_http(question: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Query the RAG service via HTTP endpoint"""
    try:
        async with session.post(
            f"{API_BASE_URL}/chat",
            json={"message": question, "conversation_id": "eval"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {
                    "error": f"HTTP {response.status}",
                    "answer": None,
                    "sources": []
                }
    except Exception as e:
        return {
            "error": str(e),
            "answer": None,
            "sources": []
        }


async def query_rag_direct(question: str, rag_service: RAGService) -> Dict[str, Any]:
    """Query the RAG service directly (bypassing HTTP)"""
    try:
        result = await rag_service.query(question)
        # Debug logging
        print(f"  DEBUG - Result keys: {result.keys()}")
        print(f"  DEBUG - Response type: {type(result['response'])}")
        print(f"  DEBUG - Response value: {repr(result['response'][:100])}")
        print(f"  DEBUG - Sources count: {len(result.get('sources', []))}")
        return {
            "answer": result["response"],  # RAG service returns 'response' not 'answer'
            "sources": result.get("sources", []),  # Sources already formatted by RAG service
            "error": None
        }
    except Exception as e:
        print(f"  DEBUG - Exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "answer": None,
            "sources": []
        }


async def run_evaluation_http():
    """Run evaluation using HTTP endpoint (requires backend to be running)"""
    print("🚀 Starting Evaluation (HTTP mode)")
    print("=" * 60)

    # Load question bank
    question_bank = load_question_bank()
    questions = question_bank["questions"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"📋 Loaded {len(questions)} questions")
    print(f"🔗 Using API endpoint: {API_BASE_URL}")
    print()

    # Initialize results structure
    results = {
        "metadata": {
            "timestamp": timestamp,
            "mode": "http",
            "total_questions": len(questions),
            "api_endpoint": API_BASE_URL
        },
        "responses": []
    }

    # Query each question
    async with aiohttp.ClientSession() as session:
        for i, q in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] Processing: {q['id']} - {q['question'][:60]}...")

            response = await query_rag_http(q["question"], session)

            result_entry = {
                "question_id": q["id"],
                "question": q["question"],
                "category": q["category"],
                "difficulty": q["difficulty"],
                "expected_topics": q["expected_topics"],
                "response": response.get("answer"),
                "sources": response.get("sources", []),
                "error": response.get("error"),

                # Placeholders for manual scoring
                "scores": {
                    "answer_relevance": None,  # 0-5
                    "faithfulness": None,       # 0-5
                    "clarity": None,            # 0-5
                    "conciseness": None,        # 0-5
                    "source_citation": None,    # 0-5
                    "overall": None             # Auto-calculated
                },
                "binary_checks": {
                    "hallucination_detected": None,  # true/false
                    "retrieval_success": None        # true/false
                },
                "notes": ""  # Evaluator comments
            }

            results["responses"].append(result_entry)

            # Brief pause to avoid overwhelming the server
            await asyncio.sleep(0.5)

    # Save results
    output_file = save_results(results, timestamp)
    print_evaluation_summary(results, output_file)

    return results


async def run_evaluation_direct():
    """Run evaluation using direct RAG service (no HTTP required)"""
    print("🚀 Starting Evaluation (Direct mode)")
    print("=" * 60)

    # Initialize RAG service
    print("🔧 Initializing RAG service...")
    rag_service = RAGService()
    rag_service.initialize()
    print("✓ RAG service initialized\n")

    # Load question bank
    question_bank = load_question_bank()
    questions = question_bank["questions"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"📋 Loaded {len(questions)} questions\n")

    # Initialize results structure
    results = {
        "metadata": {
            "timestamp": timestamp,
            "mode": "direct",
            "total_questions": len(questions)
        },
        "responses": []
    }

    # Query each question
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Processing: {q['id']} - {q['question'][:60]}...")

        response = await query_rag_direct(q["question"], rag_service)

        result_entry = {
            "question_id": q["id"],
            "question": q["question"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "expected_topics": q["expected_topics"],
            "response": response.get("answer"),
            "sources": response.get("sources", []),
            "error": response.get("error"),

            # Placeholders for manual scoring
            "scores": {
                "answer_relevance": None,  # 0-5
                "faithfulness": None,       # 0-5
                "clarity": None,            # 0-5
                "conciseness": None,        # 0-5
                "source_citation": None,    # 0-5
                "overall": None             # Auto-calculated
            },
            "binary_checks": {
                "hallucination_detected": None,  # true/false
                "retrieval_success": None        # true/false
            },
            "notes": ""  # Evaluator comments
        }

        results["responses"].append(result_entry)

    # Save results
    output_file = save_results(results, timestamp)
    print_evaluation_summary(results, output_file)

    return results


def print_evaluation_summary(results: Dict[str, Any], output_file: Path):
    """Print summary of evaluation run"""
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)

    total = results["metadata"]["total_questions"]
    mode = results["metadata"]["mode"]

    # Count errors
    errors = sum(1 for r in results["responses"] if r.get("error"))
    success = total - errors

    print(f"Mode: {mode.upper()}")
    print(f"Total Questions: {total}")
    print(f"Successful Responses: {success}")
    print(f"Errors: {errors}")

    if errors > 0:
        print("\n⚠️  Errors detected in:")
        for r in results["responses"]:
            if r.get("error"):
                print(f"  - {r['question_id']}: {r['error']}")

    print("\n" + "=" * 60)
    print("📝 NEXT STEPS")
    print("=" * 60)
    print(f"1. Open the results file: {output_file}")
    print(f"2. Manually score each response using the metrics in METRICS.md")
    print(f"3. Fill in the 'scores' and 'binary_checks' fields")
    print(f"4. Add any notes or observations")
    print(f"5. Run analysis script (coming soon) to compute aggregate metrics")
    print("=" * 60 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run AI Mentor evaluation")
    parser.add_argument(
        "--mode",
        choices=["http", "direct"],
        default="direct",
        help="Evaluation mode: 'http' (requires running backend) or 'direct' (embedded)"
    )

    args = parser.parse_args()

    if args.mode == "http":
        # Check if backend is running
        print("⚠️  HTTP mode requires the backend to be running on port 8000")
        print("   Start it with: uvicorn main:app --host 0.0.0.0 --port 8000")
        print()
        asyncio.run(run_evaluation_http())
    else:
        asyncio.run(run_evaluation_direct())


if __name__ == "__main__":
    main()
