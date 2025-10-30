# AI Mentor Evaluation Framework

## Overview

This directory contains the evaluation framework for measuring and improving the AI Mentor RAG system's performance.

## Structure

```
evaluation/
├── README.md                 # This file
├── METRICS.md               # Evaluation metrics definitions
├── question_bank.json       # Test questions
├── run_evaluation.py        # Evaluation script
└── results/                 # Evaluation results (created on first run)
    └── evaluation_YYYYMMDD_HHMMSS.json
```

## Quick Start

### 1. Run Evaluation

```bash
# From backend directory
cd /workspace/AIMentorProject/backend

# Activate virtual environment
source venv/bin/activate

# Run evaluation (direct mode - no HTTP server needed)
python evaluation/run_evaluation.py --mode direct

# Or, if backend is already running:
python evaluation/run_evaluation.py --mode http
```

### 2. Review Results

The script will create a results file in `evaluation/results/` with all responses collected.

### 3. Manual Scoring

Open the results JSON file and fill in the scores for each response:

```json
{
  "scores": {
    "answer_relevance": 4,     // 0-5 scale
    "faithfulness": 5,          // 0-5 scale
    "clarity": 4,               // 0-5 scale
    "conciseness": 3,           // 0-5 scale
    "source_citation": 4        // 0-5 scale
  },
  "binary_checks": {
    "hallucination_detected": false,
    "retrieval_success": true
  },
  "notes": "Good explanation but slightly verbose"
}
```

Refer to `METRICS.md` for detailed scoring criteria.

### 4. Analyze Results

Calculate aggregate metrics:
- Overall score per question
- Pass rate (% with score >= 3.0)
- Average scores by category
- Identify improvement areas

## Question Bank

The question bank (`question_bank.json`) contains 20 diverse questions across 5 categories:

1. **Factual Recall** (easy): Basic definitions and concepts
2. **Conceptual Understanding** (medium): Explanations of how things work
3. **Code Analysis** (medium): Understanding code snippets
4. **Problem Solving** (medium-hard): How to approach a task
5. **Comparative Analysis** (hard): Compare and contrast concepts

### Adding New Questions

Edit `question_bank.json`:

```json
{
  "id": "Q021",
  "category": "factual_recall",
  "difficulty": "easy",
  "question": "What is a boolean in programming?",
  "expected_topics": ["true", "false", "binary", "logical"],
  "should_cite_sources": true
}
```

## Evaluation Metrics

See `METRICS.md` for complete definitions. Summary:

| Metric | Scale | Description |
|--------|-------|-------------|
| Answer Relevance | 0-5 | Does it answer the question? |
| Faithfulness | 0-5 | Is it grounded in sources? |
| Clarity | 0-5 | Is it understandable? |
| Conciseness | 0-5 | Appropriate length? |
| Source Citation | 0-5 | Are sources properly cited? |

**Binary Checks:**
- Hallucination: Yes/No
- Retrieval Success: Yes/No

## Typical Workflow

1. **Initial Baseline**: Run evaluation on current system
2. **Identify Issues**: Review low-scoring responses
3. **Make Improvements**:
   - Adjust prompts in `agentic_rag.py` or `rag_service.py`
   - Tune retrieval parameters
   - Improve chunking strategy
4. **Re-evaluate**: Run evaluation again
5. **Compare**: Measure improvement quantitatively

## Best Practices

- **Consistent Scoring**: Use same evaluator for comparison
- **Document Changes**: Note what you changed before re-evaluating
- **Track Trends**: Keep all evaluation results for historical analysis
- **Focus on Failures**: Pay special attention to scores below 3.0
- **Category Analysis**: Look for patterns by question category/difficulty

## Example Results Analysis

After scoring, you might find:

```
Overall Pass Rate: 85% (17/20 questions scored >= 3.0)

By Category:
- Factual Recall: 100% pass (5/5)
- Conceptual Understanding: 80% pass (4/5)
- Code Analysis: 75% pass (3/4)
- Problem Solving: 67% pass (2/3)
- Comparative Analysis: 100% pass (3/3)

Areas for Improvement:
- Problem Solving questions: need better step-by-step guidance
- Q009 (lowest score 2.2): Answer was too terse, lacked explanation
```

## Future Enhancements

- [ ] Automated LLM-as-judge scoring
- [ ] Visualization dashboard for results
- [ ] Regression testing against past results
- [ ] Integration with CI/CD pipeline
- [ ] A/B testing different prompts

---

**Created**: October 30, 2025
**Last Updated**: October 30, 2025
