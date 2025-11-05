#!/usr/bin/env python3
"""
Comparative Analysis Script

Compares baseline vs improved evaluation metrics once scores are available.
Generates detailed comparison report showing improvements and regressions.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def load_evaluation(file_path: Path) -> Dict[str, Any]:
    """Load evaluation JSON file"""
    with open(file_path) as f:
        return json.load(f)


def calculate_metrics(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate aggregate metrics from evaluation"""
    responses = evaluation['responses']

    # Filter scored responses
    scored = [r for r in responses if r['scores'].get('overall') is not None]

    if not scored:
        return {
            'error': 'No scored responses found',
            'total_questions': len(responses),
            'scored_count': 0
        }

    metrics = {
        'summary': {
            'total_questions': len(responses),
            'scored_count': len(scored)
        },
        'average_scores': {},
        'by_category': defaultdict(list),
        'by_difficulty': defaultdict(list),
        'binary_metrics': {}
    }

    # Calculate average scores
    score_types = ['answer_relevance', 'faithfulness', 'clarity', 'conciseness', 'source_citation', 'overall']
    for score_type in score_types:
        values = [r['scores'][score_type] for r in scored if r['scores'].get(score_type) is not None]
        if values:
            metrics['average_scores'][score_type] = {
                'mean': round(sum(values) / len(values), 2),
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'count': len(values)
            }

    # By category
    for response in scored:
        category = response['category']
        overall = response['scores'].get('overall')
        if overall:
            metrics['by_category'][category].append(overall)

    # By difficulty
    for response in scored:
        difficulty = response['difficulty']
        overall = response['scores'].get('overall')
        if overall:
            metrics['by_difficulty'][difficulty].append(overall)

    # Calculate category averages
    for category, scores in metrics['by_category'].items():
        metrics['by_category'][category] = {
            'mean': round(sum(scores) / len(scores), 2),
            'count': len(scores)
        }

    # Calculate difficulty averages
    for difficulty, scores in metrics['by_difficulty'].items():
        metrics['by_difficulty'][difficulty] = {
            'mean': round(sum(scores) / len(scores), 2),
            'count': len(scores)
        }

    # Binary metrics
    hallucinations = [r for r in scored if r['binary_checks'].get('hallucination_detected')]
    retrieval_success = [r for r in scored if r['binary_checks'].get('retrieval_success')]

    metrics['binary_metrics']['hallucination_rate'] = round(len(hallucinations) / len(scored) * 100, 1) if scored else 0
    metrics['binary_metrics']['hallucination_count'] = f"{len(hallucinations)}/{len(scored)}"
    metrics['binary_metrics']['retrieval_success_rate'] = round(len(retrieval_success) / len(scored) * 100, 1) if scored else 0
    metrics['binary_metrics']['retrieval_success_count'] = f"{len(retrieval_success)}/{len(scored)}"

    return metrics


def generate_comparison_report(baseline: Dict, improved: Dict, baseline_metrics: Dict, improved_metrics: Dict) -> str:
    """Generate markdown comparison report"""

    report = """# Comparative Evaluation Analysis: Baseline vs Improved

**Date**: {date}
**Baseline**: {baseline_file}
**Improved**: {improved_file}

---

## Executive Summary

""".format(
        date="TBD",
        baseline_file="evaluation_20251105_043049.json",
        improved_file="evaluation_20251105_084005.json"
    )

    # Overall comparison
    baseline_overall = baseline_metrics['average_scores'].get('overall', {}).get('mean', 0)
    improved_overall = improved_metrics['average_scores'].get('overall', {}).get('mean', 0)
    overall_change = improved_overall - baseline_overall
    overall_pct = (overall_change / baseline_overall * 100) if baseline_overall > 0 else 0

    report += f"""### Overall Performance

| Metric | Baseline | Improved | Change | % Change |
|--------|----------|----------|--------|----------|
| **Overall Score** | **{baseline_overall:.2f}** | **{improved_overall:.2f}** | **{overall_change:+.2f}** | **{overall_pct:+.1f}%** |

"""

    # Detailed metrics comparison
    report += """---

## Detailed Metrics Comparison

### Individual Metric Scores

| Metric | Baseline | Improved | Change | % Change | Status |
|--------|----------|----------|--------|----------|--------|
"""

    score_names = {
        'answer_relevance': 'Answer Relevance',
        'faithfulness': 'Faithfulness',
        'clarity': 'Clarity',
        'conciseness': 'Conciseness',
        'source_citation': 'Source Citation'
    }

    for key, name in score_names.items():
        baseline_val = baseline_metrics['average_scores'].get(key, {}).get('mean', 0)
        improved_val = improved_metrics['average_scores'].get(key, {}).get('mean', 0)
        change = improved_val - baseline_val
        pct_change = (change / baseline_val * 100) if baseline_val > 0 else 0

        # Determine status
        if change > 0.2:
            status = "✅ Improved"
        elif change < -0.2:
            status = "⚠️ Regression"
        else:
            status = "➡️ Stable"

        report += f"| {name} | {baseline_val:.2f} | {improved_val:.2f} | {change:+.2f} | {pct_change:+.1f}% | {status} |\n"

    report += "\n"

    # Binary metrics
    report += """### Binary Metrics

| Metric | Baseline | Improved | Change | Status |
|--------|----------|----------|--------|--------|
"""

    baseline_hall = baseline_metrics['binary_metrics'].get('hallucination_rate', 0)
    improved_hall = improved_metrics['binary_metrics'].get('hallucination_rate', 0)
    hall_change = improved_hall - baseline_hall
    hall_status = "✅ Reduced" if hall_change < -5 else ("⚠️ Increased" if hall_change > 5 else "➡️ Stable")

    baseline_retr = baseline_metrics['binary_metrics'].get('retrieval_success_rate', 0)
    improved_retr = improved_metrics['binary_metrics'].get('retrieval_success_rate', 0)
    retr_change = improved_retr - baseline_retr
    retr_status = "✅ Improved" if retr_change > 5 else ("⚠️ Reduced" if retr_change < -5 else "➡️ Stable")

    report += f"| Hallucination Rate | {baseline_hall:.1f}% | {improved_hall:.1f}% | {hall_change:+.1f} pp | {hall_status} |\n"
    report += f"| Retrieval Success | {baseline_retr:.1f}% | {improved_retr:.1f}% | {retr_change:+.1f} pp | {retr_status} |\n"

    report += "\n---\n\n## Performance by Category\n\n| Category | Baseline | Improved | Change | Status |\n|----------|----------|----------|--------|--------|\n"

    # Category comparison
    all_categories = set(baseline_metrics['by_category'].keys()) | set(improved_metrics['by_category'].keys())
    for category in sorted(all_categories):
        baseline_cat = baseline_metrics['by_category'].get(category, {}).get('mean', 0)
        improved_cat = improved_metrics['by_category'].get(category, {}).get('mean', 0)
        cat_change = improved_cat - baseline_cat
        cat_status = "✅" if cat_change > 0.2 else ("⚠️" if cat_change < -0.2 else "➡️")

        report += f"| {category.replace('_', ' ').title()} | {baseline_cat:.2f} | {improved_cat:.2f} | {cat_change:+.2f} | {cat_status} |\n"

    report += "\n---\n\n## Performance by Difficulty\n\n| Difficulty | Baseline | Improved | Change | Status |\n|------------|----------|----------|--------|--------|\n"

    # Difficulty comparison
    for difficulty in ['easy', 'medium', 'hard']:
        baseline_diff = baseline_metrics['by_difficulty'].get(difficulty, {}).get('mean', 0)
        improved_diff = improved_metrics['by_difficulty'].get(difficulty, {}).get('mean', 0)
        diff_change = improved_diff - baseline_diff
        diff_status = "✅" if diff_change > 0.2 else ("⚠️" if diff_change < -0.2 else "➡️")

        report += f"| {difficulty.title()} | {baseline_diff:.2f} | {improved_diff:.2f} | {diff_change:+.2f} | {diff_status} |\n"

    # Key findings
    report += "\n---\n\n## Key Findings\n\n### Major Improvements ✅\n\n"

    improvements = []

    # Check each metric for improvements
    for key, name in score_names.items():
        baseline_val = baseline_metrics['average_scores'].get(key, {}).get('mean', 0)
        improved_val = improved_metrics['average_scores'].get(key, {}).get('mean', 0)
        change = improved_val - baseline_val
        pct_change = (change / baseline_val * 100) if baseline_val > 0 else 0

        if change > 0.3:
            improvements.append(f"- **{name}**: {baseline_val:.2f} → {improved_val:.2f} (+{pct_change:.1f}%)")

    # Hallucination improvement
    if hall_change < -10:
        improvements.append(f"- **Hallucination Rate Reduction**: {baseline_hall:.1f}% → {improved_hall:.1f}% ({hall_change:.1f} pp)")

    if improvements:
        report += "\n".join(improvements)
    else:
        report += "No major improvements (>0.3 points) detected.\n"

    report += "\n\n### Regressions ⚠️\n\n"

    regressions = []
    for key, name in score_names.items():
        baseline_val = baseline_metrics['average_scores'].get(key, {}).get('mean', 0)
        improved_val = improved_metrics['average_scores'].get(key, {}).get('mean', 0)
        change = improved_val - baseline_val
        pct_change = (change / baseline_val * 100) if baseline_val > 0 else 0

        if change < -0.3:
            regressions.append(f"- **{name}**: {baseline_val:.2f} → {improved_val:.2f} ({pct_change:.1f}%)")

    if regressions:
        report += "\n".join(regressions)
    else:
        report += "No significant regressions detected.\n"

    # Recommendations
    report += "\n---\n\n## Recommendations\n\n"

    if improved_overall >= 4.0 and improved_hall <= 10:
        report += "### ✅ Production Ready\n\nThe improved system meets production criteria:\n"
        report += f"- Overall score > 4.0: ✅ ({improved_overall:.2f})\n"
        report += f"- Hallucination rate < 10%: ✅ ({improved_hall:.1f}%)\n"
        report += "\n**Recommendation**: Deploy to production with monitoring.\n"
    elif improved_overall >= 3.8:
        report += "### ⚠️ Near Production Ready\n\nThe system shows significant improvement but may need minor iteration.\n"
        report += "\n**Recommendation**: Address remaining issues before production deployment.\n"
    else:
        report += "### 🔴 Requires Further Improvement\n\nThe system needs additional work before production deployment.\n"
        report += "\n**Recommendation**: Implement additional improvements and re-evaluate.\n"

    report += "\n---\n\n**Analysis Complete**\n"

    return report


def main():
    """Main comparison function"""
    if len(sys.argv) != 3:
        print("Usage: python3 compare_evaluations.py <baseline_json> <improved_json>")
        print("Example: python3 compare_evaluations.py results/evaluation_20251105_043049.json results/evaluation_20251105_084005.json")
        sys.exit(1)

    baseline_file = Path(sys.argv[1])
    improved_file = Path(sys.argv[2])

    if not baseline_file.exists():
        print(f"Error: Baseline file not found: {baseline_file}")
        sys.exit(1)

    if not improved_file.exists():
        print(f"Error: Improved file not found: {improved_file}")
        sys.exit(1)

    print("Loading evaluations...")
    baseline = load_evaluation(baseline_file)
    improved = load_evaluation(improved_file)

    print("Calculating metrics...")
    baseline_metrics = calculate_metrics(baseline)
    improved_metrics = calculate_metrics(improved)

    if 'error' in baseline_metrics:
        print(f"Error with baseline: {baseline_metrics['error']}")
        sys.exit(1)

    if 'error' in improved_metrics:
        print(f"Error with improved: {improved_metrics['error']}")
        sys.exit(1)

    print("Generating comparison report...")
    report = generate_comparison_report(baseline, improved, baseline_metrics, improved_metrics)

    # Save report
    output_file = Path("results/COMPARATIVE_ANALYSIS.md")
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"\n✅ Comparison report saved to: {output_file}")

    # Print summary
    baseline_overall = baseline_metrics['average_scores']['overall']['mean']
    improved_overall = improved_metrics['average_scores']['overall']['mean']
    overall_change = improved_overall - baseline_overall

    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print(f"Overall Score:  {baseline_overall:.2f} → {improved_overall:.2f} ({overall_change:+.2f})")
    print(f"Hallucination:  {baseline_metrics['binary_metrics']['hallucination_rate']:.1f}% → {improved_metrics['binary_metrics']['hallucination_rate']:.1f}%")
    print(f"Source Citation: {baseline_metrics['average_scores']['source_citation']['mean']:.2f} → {improved_metrics['average_scores']['source_citation']['mean']:.2f}")
    print("="*70)


if __name__ == "__main__":
    main()
