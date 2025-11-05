#!/usr/bin/env python3
"""
Import manually scored CSV back into evaluation JSON and compute metrics
"""
import json
import csv
import sys
from pathlib import Path
from datetime import datetime


def import_scores_from_csv(csv_file: Path, json_file: Path) -> dict:
    """Import scores from CSV and update JSON evaluation file"""

    # Load original JSON
    with open(json_file) as f:
        data = json.load(f)

    # Load scores from CSV
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        scores_by_id = {}

        for row in reader:
            q_id = row['ID']

            # Parse scores (handle empty strings)
            try:
                scores_by_id[q_id] = {
                    'answer_relevance': float(row['Answer_Relevance_0-5']) if row['Answer_Relevance_0-5'] else None,
                    'faithfulness': float(row['Faithfulness_0-5']) if row['Faithfulness_0-5'] else None,
                    'clarity': float(row['Clarity_0-5']) if row['Clarity_0-5'] else None,
                    'conciseness': float(row['Conciseness_0-5']) if row['Conciseness_0-5'] else None,
                    'source_citation': float(row['Source_Citation_0-5']) if row['Source_Citation_0-5'] else None,
                    'hallucination_detected': row['Hallucination_Detected_Y/N'].upper() == 'Y' if row['Hallucination_Detected_Y/N'] else None,
                    'retrieval_success': row['Retrieval_Success_Y/N'].upper() == 'Y' if row['Retrieval_Success_Y/N'] else None,
                    'notes': row['Notes']
                }
            except (ValueError, KeyError) as e:
                print(f"Warning: Error parsing scores for {q_id}: {e}")
                continue

    # Update JSON with scores
    scored_count = 0
    for response in data['responses']:
        q_id = response['question_id']
        if q_id in scores_by_id:
            scores = scores_by_id[q_id]

            # Update scores
            response['scores']['answer_relevance'] = scores['answer_relevance']
            response['scores']['faithfulness'] = scores['faithfulness']
            response['scores']['clarity'] = scores['clarity']
            response['scores']['conciseness'] = scores['conciseness']
            response['scores']['source_citation'] = scores['source_citation']

            # Calculate overall score (average of non-None scores)
            score_values = [v for v in [
                scores['answer_relevance'],
                scores['faithfulness'],
                scores['clarity'],
                scores['conciseness'],
                scores['source_citation']
            ] if v is not None]

            if score_values:
                response['scores']['overall'] = round(sum(score_values) / len(score_values), 2)
                scored_count += 1

            # Update binary checks
            response['binary_checks']['hallucination_detected'] = scores['hallucination_detected']
            response['binary_checks']['retrieval_success'] = scores['retrieval_success']

            # Update notes
            response['notes'] = scores['notes']

    print(f"✅ Imported scores for {scored_count}/{len(data['responses'])} questions")
    return data


def compute_aggregate_metrics(data: dict) -> dict:
    """Compute aggregate metrics from scored evaluation data"""

    responses = data['responses']
    scored_responses = [r for r in responses if r['scores']['overall'] is not None]

    if not scored_responses:
        print("⚠️  No responses have been manually scored yet")
        return {}

    metrics = {
        'summary': {
            'total_questions': len(responses),
            'scored_questions': len(scored_responses),
            'scoring_completion': f"{len(scored_responses)/len(responses)*100:.1f}%"
        },
        'average_scores': {},
        'by_category': {},
        'by_difficulty': {},
        'binary_metrics': {}
    }

    # Average scores across all questions
    score_types = ['answer_relevance', 'faithfulness', 'clarity', 'conciseness', 'source_citation', 'overall']
    for score_type in score_types:
        values = [r['scores'][score_type] for r in scored_responses if r['scores'][score_type] is not None]
        if values:
            metrics['average_scores'][score_type] = round(sum(values) / len(values), 2)

    # Scores by category
    categories = set(r['category'] for r in scored_responses)
    for category in categories:
        cat_responses = [r for r in scored_responses if r['category'] == category]
        cat_scores = [r['scores']['overall'] for r in cat_responses if r['scores']['overall'] is not None]
        if cat_scores:
            metrics['by_category'][category] = {
                'count': len(cat_responses),
                'avg_score': round(sum(cat_scores) / len(cat_scores), 2)
            }

    # Scores by difficulty
    difficulties = set(r['difficulty'] for r in scored_responses)
    for difficulty in difficulties:
        diff_responses = [r for r in scored_responses if r['difficulty'] == difficulty]
        diff_scores = [r['scores']['overall'] for r in diff_responses if r['scores']['overall'] is not None]
        if diff_scores:
            metrics['by_difficulty'][difficulty] = {
                'count': len(diff_responses),
                'avg_score': round(sum(diff_scores) / len(diff_scores), 2)
            }

    # Binary metrics
    hallucination_responses = [r for r in scored_responses if r['binary_checks']['hallucination_detected'] is not None]
    if hallucination_responses:
        hallucinations = sum(1 for r in hallucination_responses if r['binary_checks']['hallucination_detected'])
        metrics['binary_metrics']['hallucination_rate'] = f"{hallucinations/len(hallucination_responses)*100:.1f}%"
        metrics['binary_metrics']['hallucination_count'] = f"{hallucinations}/{len(hallucination_responses)}"

    retrieval_responses = [r for r in scored_responses if r['binary_checks']['retrieval_success'] is not None]
    if retrieval_responses:
        successes = sum(1 for r in retrieval_responses if r['binary_checks']['retrieval_success'])
        metrics['binary_metrics']['retrieval_success_rate'] = f"{successes/len(retrieval_responses)*100:.1f}%"
        metrics['binary_metrics']['retrieval_success_count'] = f"{successes}/{len(retrieval_responses)}"

    return metrics


def print_metrics(metrics: dict):
    """Pretty print metrics"""
    print("\n" + "="*70)
    print("📊 EVALUATION METRICS")
    print("="*70)

    if not metrics:
        return

    print("\n📈 Summary")
    for key, value in metrics['summary'].items():
        print(f"  {key}: {value}")

    print("\n📊 Average Scores (0-5 scale)")
    for key, value in metrics['average_scores'].items():
        print(f"  {key}: {value}")

    if metrics['by_category']:
        print("\n📂 Scores by Category")
        for category, data in metrics['by_category'].items():
            print(f"  {category}: {data['avg_score']} ({data['count']} questions)")

    if metrics['by_difficulty']:
        print("\n🎯 Scores by Difficulty")
        for difficulty, data in metrics['by_difficulty'].items():
            print(f"  {difficulty}: {data['avg_score']} ({data['count']} questions)")

    if metrics['binary_metrics']:
        print("\n🔍 Binary Metrics")
        for key, value in metrics['binary_metrics'].items():
            print(f"  {key}: {value}")

    print("\n" + "="*70)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 import_scores.py <csv_file>")
        print("Example: python3 import_scores.py results/evaluation_20251105_043049_scoring.csv")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    # Determine corresponding JSON file
    json_file = csv_file.parent / csv_file.name.replace('_scoring.csv', '.json')
    if not json_file.exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)

    print(f"Importing scores from: {csv_file}")
    print(f"Updating JSON file: {json_file}")

    # Import scores
    data = import_scores_from_csv(csv_file, json_file)

    # Compute metrics
    metrics = compute_aggregate_metrics(data)

    # Save updated JSON
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Updated JSON file with scores: {json_file}")

    # Print metrics
    print_metrics(metrics)

    # Save metrics to separate file
    metrics_file = csv_file.parent / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n💾 Saved metrics to: {metrics_file}")


if __name__ == "__main__":
    main()
