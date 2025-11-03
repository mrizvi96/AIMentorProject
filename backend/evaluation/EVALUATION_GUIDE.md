# AI Mentor Evaluation Guide

This guide explains how to run comprehensive evaluations of the AI Mentor system. The evaluation framework is **corpus-agnostic** and designed to work with any set of PDF documents.

---

## Overview

The evaluation system consists of three main components:

1. **Question Bank** (`question_bank.json`) - Diverse questions testing different capabilities
2. **Evaluation Runner** (`run_evaluation.py`) - Automates querying and result collection
3. **Results Analyzer** (`analyze_results.py`) - Computes metrics and generates reports

---

## Quick Start

### Step 1: Prepare Your Document Corpus

```bash
# Ensure documents are ingested into ChromaDB
cd /root/AIMentorProject/backend
source venv/bin/activate
python3 ingest.py --directory ./course_materials/ --overwrite
```

### Step 2: Run Evaluation

```bash
# Make sure services are running
../service_manager.sh start

# Run evaluation (takes ~5-10 minutes for 20 questions)
cd evaluation
python3 run_evaluation.py --mode direct

# Output: evaluation/results/evaluation_TIMESTAMP.json
```

### Step 3: Manual Scoring

```bash
# Open the results file
nano results/evaluation_TIMESTAMP.json

# For each response, fill in:
# - scores.answer_relevance (0-5)
# - scores.faithfulness (0-5)
# - scores.clarity (0-5)
# - scores.conciseness (0-5)
# - scores.source_citation (0-5)
# - binary_checks.hallucination_detected (true/false)
# - binary_checks.retrieval_success (true/false)
# - notes (optional comments)
```

### Step 4: Analyze Results

```bash
# Generate analysis report
python3 analyze_results.py results/evaluation_TIMESTAMP.json --output report.md

# View summary
cat report.md
```

---

## Detailed Instructions

### Creating a Question Bank

The question bank should test various aspects of the system:

#### Question Categories

1. **factual_recall**: Simple fact-based questions
   - "What is a variable?"
   - "Define recursion"

2. **conceptual_explanation**: Requires deeper understanding
   - "Explain how garbage collection works"
   - "What is the difference between a list and a tuple?"

3. **code_generation**: Requests code examples
   - "Write a function to reverse a string"
   - "Show how to read a file in Python"

4. **comparative_analysis**: Comparing concepts
   - "Compare merge sort and quicksort"
   - "What's the difference between deep copy and shallow copy?"

5. **problem_solving**: Applying concepts
   - "How would you detect a loop in a linked list?"
   - "Design a cache with LRU eviction"

#### Difficulty Levels

- **easy**: Basic definitions and simple concepts
- **medium**: Requires understanding and synthesis
- **hard**: Complex scenarios, edge cases, optimization

#### Question Bank Format

```json
{
  "version": "1.0",
  "description": "Evaluation question bank",
  "questions": [
    {
      "id": "q001",
      "question": "What is a variable in Python?",
      "category": "factual_recall",
      "difficulty": "easy",
      "expected_topics": ["variable", "data", "memory", "assignment"]
    }
  ]
}
```

### Evaluation Modes

#### Direct Mode (Recommended)
- Queries RAG service directly (embedded mode)
- No HTTP server needed
- Faster and more reliable

```bash
python3 run_evaluation.py --mode direct
```

#### HTTP Mode
- Queries through REST API
- Requires backend to be running
- Tests full stack integration

```bash
# Start backend first
cd ..
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Run evaluation
cd evaluation
python3 run_evaluation.py --mode http
```

### Scoring Rubric

Use these guidelines when manually scoring responses:

#### Answer Relevance (0-5)
- **5**: Directly answers the question completely
- **4**: Answers well with minor gaps
- **3**: Partially answers, missing some aspects
- **2**: Tangentially related, mostly off-topic
- **1**: Barely related to the question
- **0**: Completely unrelated

#### Faithfulness (0-5)
- **5**: 100% grounded in provided context, no hallucinations
- **4**: Mostly grounded, minor unsupported details
- **3**: Mix of grounded and unsupported information
- **2**: Significant hallucinations present
- **1**: Mostly hallucinated
- **0**: Entirely fabricated

#### Clarity (0-5)
- **5**: Crystal clear, well-structured, easy to understand
- **4**: Clear with minor ambiguities
- **3**: Understandable but could be clearer
- **2**: Confusing or poorly structured
- **1**: Very difficult to understand
- **0**: Incomprehensible

#### Conciseness (0-5)
- **5**: Perfect length, no unnecessary information
- **4**: Slightly verbose but acceptable
- **3**: Noticeably verbose or too brief
- **2**: Significantly too long or short
- **1**: Extremely verbose or minimal
- **0**: Unusable due to length issues

#### Source Citation (0-5)
- **5**: All claims properly cited with specific sources
- **4**: Most claims cited, minor gaps
- **3**: Some citations, but incomplete
- **2**: Few or vague citations
- **1**: Minimal citation attempts
- **0**: No citations

#### Binary Checks
- **hallucination_detected**: Does the response contain information NOT in the source documents?
- **retrieval_success**: Did the system retrieve relevant documents?

---

## Interpreting Results

### Overall Score Ranges

| Score | Interpretation | Action |
|-------|----------------|--------|
| 4.5-5.0 | Excellent | Production ready, minor refinements only |
| 4.0-4.4 | Good | Minor improvements recommended |
| 3.5-3.9 | Acceptable | Moderate improvements needed |
| 3.0-3.4 | Poor | Significant work required |
| <3.0 | Critical | Major rework necessary |

### Key Metrics to Watch

1. **Hallucination Rate**
   - Target: <5%
   - Warning: 5-10%
   - Critical: >10%

2. **Retrieval Success**
   - Target: >90%
   - Warning: 80-90%
   - Critical: <80%

3. **Answer Relevance**
   - Target: >4.0
   - Indicates if retrieval and prompts are working

4. **Faithfulness**
   - Target: >4.5
   - Critical for educational use (can't mislead students)

---

## Best Practices

### When to Evaluate

1. **After major changes**: Prompt engineering, retrieval tuning, model changes
2. **With new corpus**: When ingesting different types of documents
3. **Before deployment**: Final validation before production
4. **Periodically**: Monthly or quarterly performance checks

### Evaluation Corpus Considerations

⚠️ **IMPORTANT**: The evaluation results are **corpus-dependent**.

- Evaluation on 6 PDFs is a **framework test**, not system validation
- Real evaluation requires a representative corpus similar to production
- Don't tune hyperparameters based on limited corpus results
- Use small corpus evaluations to validate the evaluation process, not the system

### Sample Sizes

- **Minimum**: 20 questions (framework validation)
- **Standard**: 50-100 questions (comprehensive evaluation)
- **Production**: 200+ questions (rigorous testing)

### Question Distribution

Aim for balanced distribution:
- Categories: 20% each (5 categories)
- Difficulty: 40% easy, 40% medium, 20% hard

---

## Troubleshooting

### "No responses have been manually scored"

**Problem**: Running analyze_results.py before scoring
**Solution**: Complete manual scoring in the JSON file first

### "Failed to query RAG service"

**Problem**: Services not running or misconfigured
**Solution**: Check service status with `../service_manager.sh status`

### "Collection does not exist"

**Problem**: Documents not ingested
**Solution**: Run ingestion first: `python3 ingest.py --directory ../course_materials/`

### Low Scores Across All Metrics

**Problem**: System not properly configured or corpus mismatch
**Solution**:
1. Verify documents are ingested correctly
2. Check LLM is responding (test with simple query)
3. Ensure questions are appropriate for the corpus

---

## Automation

### Scheduled Evaluations

Create a cron job for periodic evaluations:

```bash
# Add to crontab (weekly evaluation on Sunday at 2 AM)
0 2 * * 0 cd /root/AIMentorProject/backend/evaluation && /root/AIMentorProject/backend/venv/bin/python3 run_evaluation.py --mode direct
```

### CI/CD Integration

```bash
# In your deployment pipeline
cd backend/evaluation
python3 run_evaluation.py --mode direct
# Parse results and fail deployment if score < threshold
```

---

## Advanced Usage

### Custom Question Banks

Create specialized question banks for specific domains:

```bash
# Create domain-specific bank
cp question_bank.json question_bank_algorithms.json
# Edit to focus on algorithms questions
python3 run_evaluation.py --question-bank question_bank_algorithms.json
```

### Comparing System Versions

```bash
# Evaluate baseline
python3 run_evaluation.py
mv results/evaluation_*.json results/baseline.json

# Make changes to system
# ...

# Evaluate improved version
python3 run_evaluation.py
mv results/evaluation_*.json results/improved.json

# Compare results
python3 analyze_results.py results/baseline.json --json > baseline_metrics.json
python3 analyze_results.py results/improved.json --json > improved_metrics.json
# Manually compare or write comparison script
```

---

## Files and Directory Structure

```
evaluation/
├── README.md                  # Quick reference
├── EVALUATION_GUIDE.md        # This file
├── METRICS.md                 # Detailed metrics definitions
├── question_bank.json         # Question bank (20 questions)
├── run_evaluation.py          # Main evaluation runner
├── analyze_results.py         # Results analysis script
└── results/                   # Evaluation output directory
    ├── evaluation_YYYYMMDD_HHMMSS.json
    └── report_YYYYMMDD_HHMMSS.md
```

---

## Next Steps

1. **Test the framework** with current 6 PDFs to validate the process
2. **Wait for full corpus** before doing real evaluation
3. **Create production question bank** with 100+ questions
4. **Run baseline evaluation** after full ingestion
5. **Iterate on improvements** based on results
6. **Re-evaluate** to measure impact

---

## FAQ

**Q: How long does evaluation take?**
A: ~15-30 seconds per question, so ~5-10 minutes for 20 questions

**Q: Can I run evaluation while system is serving users?**
A: Yes, but may affect response times. Best to run during low-traffic periods.

**Q: How often should I evaluate?**
A: After significant changes, before deployments, and periodically (monthly/quarterly)

**Q: Can I automate the scoring?**
A: Manual scoring is currently required for accuracy. LLM-based auto-scoring is possible but less reliable.

**Q: What if I get different results with same questions?**
A: Some variance is expected due to LLM non-determinism. Look at trends across multiple runs.

---

For questions or issues, refer to the main project documentation or create an issue on GitHub.
