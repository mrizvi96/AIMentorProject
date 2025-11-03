"""
Evaluation Results Analysis Script

This script analyzes completed evaluation results (after manual scoring)
and generates aggregate metrics, reports, and visualizations.

Usage:
    python analyze_results.py results/evaluation_TIMESTAMP.json
    python analyze_results.py results/evaluation_TIMESTAMP.json --output report.md
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict


def load_evaluation_results(file_path: Path) -> Dict[str, Any]:
    """Load evaluation results from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def calculate_aggregate_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate aggregate metrics from evaluation results"""

    responses = results["responses"]
    total = len(responses)

    # Count how many have been manually scored
    scored_count = sum(1 for r in responses if r["scores"]["answer_relevance"] is not None)

    if scored_count == 0:
        return {
            "error": "No responses have been manually scored yet",
            "total_questions": total,
            "scored_count": 0
        }

    # Initialize metric accumulators
    metrics = {
        "answer_relevance": [],
        "faithfulness": [],
        "clarity": [],
        "conciseness": [],
        "source_citation": []
    }

    # Binary checks
    hallucinations = 0
    retrieval_successes = 0
    binary_checks_completed = 0

    # Category performance
    category_scores = defaultdict(list)
    difficulty_scores = defaultdict(list)

    # Error tracking
    error_count = 0

    for response in responses:
        # Skip unscored responses
        if response["scores"]["answer_relevance"] is None:
            continue

        # Track errors
        if response.get("error"):
            error_count += 1
            continue

        # Collect metric scores
        for metric in metrics.keys():
            score = response["scores"][metric]
            if score is not None:
                metrics[metric].append(score)

        # Binary checks
        if response["binary_checks"]["hallucination_detected"] is not None:
            binary_checks_completed += 1
            if response["binary_checks"]["hallucination_detected"]:
                hallucinations += 1
            if response["binary_checks"]["retrieval_success"]:
                retrieval_successes += 1

        # Category/difficulty breakdown
        category = response["category"]
        difficulty = response["difficulty"]
        overall = response["scores"].get("overall")
        if overall:
            category_scores[category].append(overall)
            difficulty_scores[difficulty].append(overall)

    # Calculate averages
    avg_metrics = {}
    for metric, scores in metrics.items():
        if scores:
            avg_metrics[metric] = {
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "count": len(scores)
            }
        else:
            avg_metrics[metric] = {"mean": 0, "min": 0, "max": 0, "count": 0}

    # Calculate overall score (average of all metrics)
    all_scores = []
    for scores_list in metrics.values():
        all_scores.extend(scores_list)

    overall_mean = sum(all_scores) / len(all_scores) if all_scores else 0

    # Category averages
    category_avgs = {}
    for cat, scores in category_scores.items():
        category_avgs[cat] = sum(scores) / len(scores) if scores else 0

    # Difficulty averages
    difficulty_avgs = {}
    for diff, scores in difficulty_scores.items():
        difficulty_avgs[diff] = sum(scores) / len(scores) if scores else 0

    return {
        "summary": {
            "total_questions": total,
            "scored_count": scored_count,
            "error_count": error_count,
            "overall_score": round(overall_mean, 2),
            "hallucination_rate": round(hallucinations / binary_checks_completed * 100, 1) if binary_checks_completed > 0 else 0,
            "retrieval_success_rate": round(retrieval_successes / binary_checks_completed * 100, 1) if binary_checks_completed > 0 else 0
        },
        "metric_scores": avg_metrics,
        "category_performance": category_avgs,
        "difficulty_performance": difficulty_avgs
    }


def generate_markdown_report(results: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    """Generate a formatted markdown report"""

    timestamp = results["metadata"]["timestamp"]
    mode = results["metadata"]["mode"]

    report = f"""# AI Mentor Evaluation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Evaluation Run:** {timestamp}
**Mode:** {mode}

---

## Executive Summary

"""

    summary = metrics["summary"]
    report += f"""
| Metric | Value |
|--------|-------|
| Total Questions | {summary['total_questions']} |
| Scored Responses | {summary['scored_count']} |
| Error Count | {summary['error_count']} |
| **Overall Score** | **{summary['overall_score']}/5.0** |
| Hallucination Rate | {summary['hallucination_rate']}% |
| Retrieval Success Rate | {summary['retrieval_success_rate']}% |

"""

    # Scoring rubric interpretation
    report += """
### Score Interpretation
- **4.5-5.0**: Excellent - Production ready
- **4.0-4.4**: Good - Minor improvements needed
- **3.5-3.9**: Acceptable - Moderate improvements needed
- **3.0-3.4**: Poor - Significant improvements needed
- **<3.0**: Critical - Major rework required

---

## Detailed Metrics

"""

    # Individual metric scores
    report += "### Individual Metric Performance\n\n"
    report += "| Metric | Mean | Min | Max | Samples |\n"
    report += "|--------|------|-----|-----|----------|\n"

    for metric, scores in metrics["metric_scores"].items():
        metric_name = metric.replace("_", " ").title()
        report += f"| {metric_name} | {scores['mean']:.2f} | {scores['min']} | {scores['max']} | {scores['count']} |\n"

    report += "\n"

    # Category performance
    if metrics["category_performance"]:
        report += "### Performance by Category\n\n"
        report += "| Category | Average Score |\n"
        report += "|----------|---------------|\n"

        for category, score in sorted(metrics["category_performance"].items(), key=lambda x: x[1], reverse=True):
            report += f"| {category} | {score:.2f} |\n"

        report += "\n"

    # Difficulty performance
    if metrics["difficulty_performance"]:
        report += "### Performance by Difficulty\n\n"
        report += "| Difficulty | Average Score |\n"
        report += "|------------|---------------|\n"

        difficulty_order = ["easy", "medium", "hard"]
        for diff in difficulty_order:
            if diff in metrics["difficulty_performance"]:
                score = metrics["difficulty_performance"][diff]
                report += f"| {diff.title()} | {score:.2f} |\n"

        report += "\n"

    # Identify problem areas
    report += """---

## Key Findings

### Strengths
"""

    # Find top 3 metrics
    sorted_metrics = sorted(metrics["metric_scores"].items(), key=lambda x: x[1]["mean"], reverse=True)
    for i, (metric, scores) in enumerate(sorted_metrics[:3], 1):
        metric_name = metric.replace("_", " ").title()
        report += f"{i}. **{metric_name}**: {scores['mean']:.2f}/5.0\n"

    report += "\n### Areas for Improvement\n\n"

    # Find bottom 3 metrics
    for i, (metric, scores) in enumerate(sorted_metrics[-3:], 1):
        metric_name = metric.replace("_", " ").title()
        report += f"{i}. **{metric_name}**: {scores['mean']:.2f}/5.0\n"

    # Add warnings if critical thresholds exceeded
    report += "\n### Alerts\n\n"

    has_alerts = False
    if summary["hallucination_rate"] > 10:
        report += f"- ⚠️ **High hallucination rate** ({summary['hallucination_rate']}%) - Review context grounding\n"
        has_alerts = True

    if summary["retrieval_success_rate"] < 80:
        report += f"- ⚠️ **Low retrieval success** ({summary['retrieval_success_rate']}%) - Check embedding quality\n"
        has_alerts = True

    if summary["overall_score"] < 3.0:
        report += f"- 🚨 **Critical overall score** ({summary['overall_score']}/5.0) - Major improvements needed\n"
        has_alerts = True

    if not has_alerts:
        report += "- ✅ No critical alerts\n"

    report += """

---

## Recommendations

"""

    # Generate recommendations based on metrics
    recommendations = []

    if metrics["metric_scores"]["answer_relevance"]["mean"] < 3.5:
        recommendations.append("1. **Improve retrieval quality**: Consider adjusting chunk size, overlap, or similarity threshold")

    if metrics["metric_scores"]["faithfulness"]["mean"] < 3.5:
        recommendations.append("2. **Strengthen context grounding**: Update system prompt to emphasize using only provided context")

    if metrics["metric_scores"]["clarity"]["mean"] < 3.5:
        recommendations.append("3. **Enhance response clarity**: Refine prompts to encourage simpler explanations and better structure")

    if metrics["metric_scores"]["source_citation"]["mean"] < 3.5:
        recommendations.append("4. **Improve source citations**: Update prompt to explicitly request source references")

    if summary["hallucination_rate"] > 10:
        recommendations.append("5. **Reduce hallucinations**: Add stricter validation in document grading step")

    if not recommendations:
        recommendations.append("1. **Maintain current performance**: System performing well, focus on edge cases")
        recommendations.append("2. **Expand evaluation corpus**: Test with more diverse questions and documents")

    for rec in recommendations:
        report += f"{rec}\n\n"

    report += """---

## Next Steps

1. Review individual responses with low scores
2. Implement recommended improvements
3. Re-run evaluation to measure impact
4. Iterate until target performance achieved

"""

    return report


def main():
    parser = argparse.ArgumentParser(description="Analyze AI Mentor evaluation results")
    parser.add_argument("results_file", help="Path to evaluation results JSON file")
    parser.add_argument("--output", "-o", help="Output markdown report file (default: print to stdout)")
    parser.add_argument("--json", action="store_true", help="Output metrics as JSON instead of markdown")

    args = parser.parse_args()

    # Load results
    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"Error: File not found: {results_path}")
        sys.exit(1)

    print(f"Loading evaluation results from: {results_path}")
    results = load_evaluation_results(results_path)

    # Calculate metrics
    print("Calculating aggregate metrics...")
    metrics = calculate_aggregate_metrics(results)

    if "error" in metrics:
        print(f"\nError: {metrics['error']}")
        print(f"Total questions: {metrics['total_questions']}")
        print(f"Scored: {metrics['scored_count']}")
        print("\nPlease complete manual scoring before running analysis.")
        sys.exit(1)

    # Output results
    if args.json:
        # JSON output
        output = json.dumps(metrics, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"\nMetrics saved to: {args.output}")
        else:
            print(output)
    else:
        # Markdown report
        report = generate_markdown_report(results, metrics)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\nReport saved to: {args.output}")
        else:
            print("\n" + report)

    # Print summary to console
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    summary = metrics["summary"]
    print(f"Overall Score:          {summary['overall_score']}/5.0")
    print(f"Hallucination Rate:     {summary['hallucination_rate']}%")
    print(f"Retrieval Success:      {summary['retrieval_success_rate']}%")
    print(f"Questions Scored:       {summary['scored_count']}/{summary['total_questions']}")
    print("="*60)


if __name__ == "__main__":
    main()
