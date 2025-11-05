#!/usr/bin/env python3
"""
Automated Quality Checker for RAG Responses

Validates responses against quality criteria without manual scoring.
Useful for quick validation during development and monitoring in production.
"""
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class QualityCheck:
    """Result of a quality check"""
    name: str
    passed: bool
    severity: str  # 'critical', 'warning', 'info'
    message: str
    score: float = 0.0  # 0-1, for weighted scoring


def check_sources_section(response: str) -> QualityCheck:
    """Check if response has a Sources section"""
    has_sources = 'sources:' in response.lower()

    return QualityCheck(
        name="Sources Section Present",
        passed=has_sources,
        severity='critical' if not has_sources else 'info',
        message="Response includes 'Sources:' section" if has_sources else "Missing 'Sources:' section",
        score=1.0 if has_sources else 0.0
    )


def check_citation_format(response: str) -> QualityCheck:
    """Check for proper citation format"""
    # Check for old format (bad)
    has_old_format = 'page_label:' in response

    # Check for new format (good)
    has_new_format = bool(re.search(r'page \d+', response, re.IGNORECASE))

    if has_old_format:
        return QualityCheck(
            name="Citation Format",
            passed=False,
            severity='warning',
            message="Uses old 'page_label:' format - should use 'page X'",
            score=0.0
        )

    if has_new_format:
        return QualityCheck(
            name="Citation Format",
            passed=True,
            severity='info',
            message="Uses correct 'page X' format",
            score=1.0
        )

    return QualityCheck(
        name="Citation Format",
        passed=False,
        severity='info',
        message="No page numbers found in response",
        score=0.5
    )


def check_response_length(response: str, min_length: int = 300) -> QualityCheck:
    """Check if response is sufficiently detailed"""
    length = len(response)
    passed = length >= min_length

    return QualityCheck(
        name="Response Length",
        passed=passed,
        severity='info',
        message=f"Response length: {length} chars" + (" (adequate)" if passed else " (too brief)"),
        score=min(1.0, length / min_length)
    )


def check_multi_source_usage(sources: List[Dict]) -> QualityCheck:
    """Check if multiple sources were retrieved"""
    count = len(sources)
    passed = count >= 3

    return QualityCheck(
        name="Multi-Source Retrieval",
        passed=passed,
        severity='info',
        message=f"Retrieved {count} sources" + (" (good)" if passed else " (limited)"),
        score=min(1.0, count / 3)
    )


def check_empty_response(response: str) -> QualityCheck:
    """Check for empty or trivial responses"""
    is_empty = len(response.strip()) < 50

    return QualityCheck(
        name="Non-Empty Response",
        passed=not is_empty,
        severity='critical' if is_empty else 'info',
        message="Response is adequate" if not is_empty else "Response is empty or too short",
        score=0.0 if is_empty else 1.0
    )


def check_hallucination_indicators(response: str, sources: List[Dict]) -> QualityCheck:
    """Check for common hallucination patterns"""
    indicators = []

    # Check if response mentions specific numbers/dates not in sources
    response_numbers = re.findall(r'\b(?:19|20)\d{2}\b', response)  # Years
    source_text = ' '.join([s.get('text', '') for s in sources])

    for number in response_numbers:
        if number not in source_text:
            indicators.append(f"Year '{number}' not found in sources")

    # Check for common hedging phrases that might indicate hallucination
    confident_claims = [
        "it is well known",
        "everyone knows",
        "obviously",
        "clearly",
        "without a doubt"
    ]

    for claim in confident_claims:
        if claim in response.lower():
            indicators.append(f"Overconfident claim: '{claim}'")

    # Check if response admits lack of information
    admits_limitation = any(phrase in response.lower() for phrase in [
        "not contain enough information",
        "insufficient information",
        "cannot determine from the context",
        "does not specify"
    ])

    passed = len(indicators) == 0 or admits_limitation

    return QualityCheck(
        name="Hallucination Indicators",
        passed=passed,
        severity='warning' if indicators and not admits_limitation else 'info',
        message=f"Found {len(indicators)} potential issues: {', '.join(indicators[:2])}" if indicators and not admits_limitation else "No obvious hallucination indicators",
        score=1.0 if passed else 0.5
    )


def check_question_completeness(question: str, response: str) -> QualityCheck:
    """Check if response addresses all parts of multi-part questions"""
    # Detect multi-part questions
    multi_part_indicators = ['compare and contrast', 'when would you', 'why is', 'how does', 'explain how', 'and']

    is_multi_part = any(indicator in question.lower() for indicator in multi_part_indicators)

    if not is_multi_part:
        return QualityCheck(
            name="Question Completeness",
            passed=True,
            severity='info',
            message="Single-part question",
            score=1.0
        )

    # Check for comparison completeness
    if 'compare' in question.lower():
        has_similarities = any(word in response.lower() for word in ['similar', 'both', 'like', 'same'])
        has_differences = any(word in response.lower() for word in ['different', 'unlike', 'whereas', 'however', 'contrast'])

        if has_similarities and has_differences:
            return QualityCheck(
                name="Comparison Completeness",
                passed=True,
                severity='info',
                message="Addresses both similarities and differences",
                score=1.0
            )
        else:
            return QualityCheck(
                name="Comparison Completeness",
                passed=False,
                severity='warning',
                message="May not fully address both similarities and differences",
                score=0.5
            )

    # Check for "when to use" completeness
    if 'when would you' in question.lower() or 'when to use' in question.lower():
        has_use_case = any(word in response.lower() for word in ['suitable for', 'use when', 'appropriate for', 'ideal for'])

        if has_use_case:
            return QualityCheck(
                name="Use Case Completeness",
                passed=True,
                severity='info',
                message="Provides use case guidance",
                score=1.0
            )
        else:
            return QualityCheck(
                name="Use Case Completeness",
                passed=False,
                severity='warning',
                message="May not address 'when to use' aspect",
                score=0.5
            )

    # Check for "why" explanation completeness
    if question.lower().startswith('why'):
        has_reasoning = any(word in response.lower() for word in ['because', 'due to', 'reason', 'since', 'therefore'])

        if has_reasoning:
            return QualityCheck(
                name="Why Explanation",
                passed=True,
                severity='info',
                message="Provides reasoning",
                score=1.0
            )
        else:
            return QualityCheck(
                name="Why Explanation",
                passed=False,
                severity='warning',
                message="May not fully explain 'why'",
                score=0.5
            )

    return QualityCheck(
        name="Question Completeness",
        passed=True,
        severity='info',
        message="Multi-part question addressed",
        score=1.0
    )


def check_source_relevance(sources: List[Dict], threshold: float = 0.4) -> QualityCheck:
    """Check if retrieved sources are relevant enough"""
    if not sources:
        return QualityCheck(
            name="Source Relevance",
            passed=False,
            severity='critical',
            message="No sources retrieved",
            score=0.0
        )

    avg_score = sum(s.get('score', 0) for s in sources) / len(sources)
    passed = avg_score >= threshold

    return QualityCheck(
        name="Source Relevance",
        passed=passed,
        severity='warning' if not passed else 'info',
        message=f"Average relevance: {avg_score:.3f}" + (" (good)" if passed else " (low)"),
        score=min(1.0, avg_score / threshold)
    )


def run_quality_checks(response_data: Dict) -> Tuple[List[QualityCheck], float]:
    """Run all quality checks on a response"""
    checks = []

    question = response_data.get('question', '')
    response = response_data.get('response', '')
    sources = response_data.get('sources', [])

    # Run checks
    checks.append(check_empty_response(response))
    checks.append(check_sources_section(response))
    checks.append(check_citation_format(response))
    checks.append(check_response_length(response))
    checks.append(check_multi_source_usage(sources))
    checks.append(check_hallucination_indicators(response, sources))
    checks.append(check_question_completeness(question, response))
    checks.append(check_source_relevance(sources))

    # Calculate overall quality score
    total_score = sum(check.score for check in checks)
    max_score = len(checks)
    quality_score = (total_score / max_score) if max_score > 0 else 0.0

    return checks, quality_score


def analyze_evaluation_file(file_path: Path):
    """Analyze an entire evaluation file"""
    with open(file_path) as f:
        data = json.load(f)

    responses = data.get('responses', [])

    print("=" * 80)
    print(f"QUALITY ANALYSIS: {file_path.name}")
    print("=" * 80)
    print(f"\nTotal responses: {len(responses)}\n")

    all_checks_summary = {
        'critical_failures': 0,
        'warnings': 0,
        'total_checks': 0,
        'passed_checks': 0
    }

    response_scores = []

    for i, response_data in enumerate(responses, 1):
        checks, quality_score = run_quality_checks(response_data)
        response_scores.append((response_data['question_id'], quality_score))

        # Count issues
        for check in checks:
            all_checks_summary['total_checks'] += 1
            if check.passed:
                all_checks_summary['passed_checks'] += 1
            if not check.passed and check.severity == 'critical':
                all_checks_summary['critical_failures'] += 1
            if not check.passed and check.severity == 'warning':
                all_checks_summary['warnings'] += 1

        # Print per-response summary
        critical = [c for c in checks if not c.passed and c.severity == 'critical']
        warnings = [c for c in checks if not c.passed and c.severity == 'warning']

        status = "✅" if not critical and not warnings else ("⚠️" if not critical else "🔴")

        print(f"{status} {response_data['question_id']}: Quality {quality_score:.2f} | ", end='')

        if critical:
            print(f"CRITICAL: {', '.join(c.name for c in critical)} | ", end='')
        if warnings:
            print(f"Warnings: {', '.join(c.name for c in warnings)} | ", end='')

        if not critical and not warnings:
            print("All checks passed", end='')

        print()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    avg_quality = sum(score for _, score in response_scores) / len(response_scores) if response_scores else 0
    print(f"\nAverage Quality Score: {avg_quality:.2f}")
    print(f"Checks Passed: {all_checks_summary['passed_checks']}/{all_checks_summary['total_checks']} ({all_checks_summary['passed_checks']/all_checks_summary['total_checks']*100:.1f}%)")
    print(f"Critical Failures: {all_checks_summary['critical_failures']}")
    print(f"Warnings: {all_checks_summary['warnings']}")

    # Top 5 lowest quality responses
    print("\n📉 Lowest Quality Responses:")
    sorted_scores = sorted(response_scores, key=lambda x: x[1])
    for q_id, score in sorted_scores[:5]:
        print(f"  {q_id}: {score:.2f}")

    # Top 5 highest quality responses
    print("\n📈 Highest Quality Responses:")
    sorted_scores = sorted(response_scores, key=lambda x: x[1], reverse=True)
    for q_id, score in sorted_scores[:5]:
        print(f"  {q_id}: {score:.2f}")

    print("\n" + "=" * 80)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 quality_checker.py <evaluation_json_file>")
        print("Example: python3 quality_checker.py results/evaluation_20251105_084005.json")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    analyze_evaluation_file(file_path)


if __name__ == "__main__":
    main()
