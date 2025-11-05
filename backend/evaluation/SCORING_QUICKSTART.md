# Evaluation Scoring Quick Start Guide

## 📝 Overview

You now have a CSV file ready for manual scoring: `results/evaluation_20251105_043049_scoring.csv`

This file contains all 20 evaluation questions, their responses, and empty columns for you to fill in scores.

## 🚀 Quick Start

### 1. Open the CSV File

```bash
# Option 1: Download to your local machine and open in Excel/Google Sheets
# The file is at: /root/AIMentorProject/backend/evaluation/results/evaluation_20251105_043049_scoring.csv

# Option 2: Edit directly on the server with a text editor
nano results/evaluation_20251105_043049_scoring.csv
```

### 2. Score Each Question

For each row (question), fill in the following columns:

| Column | Values | Description |
|--------|--------|-------------|
| **Answer_Relevance_0-5** | 0-5 | How well does the answer address the question? |
| **Faithfulness_0-5** | 0-5 | Is the answer grounded in source documents? |
| **Clarity_0-5** | 0-5 | Is the answer clear and well-structured? |
| **Conciseness_0-5** | 0-5 | Is the answer appropriately concise? |
| **Source_Citation_0-5** | 0-5 | Are sources properly cited? |
| **Hallucination_Detected_Y/N** | Y or N | Does the response contain unsupported information? |
| **Retrieval_Success_Y/N** | Y or N | Did the system retrieve relevant documents? |
| **Notes** | Text | Any observations (optional) |

### 3. Import Scores Back

Once you've finished scoring, run the import script:

```bash
cd /root/AIMentorProject/backend/evaluation
source ../venv/bin/activate
python3 import_scores.py results/evaluation_20251105_043049_scoring.csv
```

This will:
- ✅ Update the original JSON file with your scores
- ✅ Calculate aggregate metrics automatically
- ✅ Generate a metrics summary report
- ✅ Save metrics to a timestamped JSON file

## 📊 Scoring Rubric Reference

### Answer Relevance (0-5)
- **5**: Directly answers the question completely
- **4**: Answers well with minor gaps
- **3**: Partially answers, missing some aspects
- **2**: Tangentially related, mostly off-topic
- **1**: Barely related to the question
- **0**: Completely unrelated

### Faithfulness (0-5)
- **5**: 100% grounded in provided context, no hallucinations
- **4**: Mostly grounded, minor unsupported details
- **3**: Mix of grounded and unsupported information
- **2**: Significant hallucinations present
- **1**: Mostly hallucinated
- **0**: Entirely fabricated

### Clarity (0-5)
- **5**: Crystal clear, well-structured, easy to understand
- **4**: Clear with minor ambiguities
- **3**: Understandable but could be clearer
- **2**: Confusing or poorly structured
- **1**: Very difficult to understand
- **0**: Incomprehensible

### Conciseness (0-5)
- **5**: Perfect length, no unnecessary information
- **4**: Slightly verbose but acceptable
- **3**: Noticeably verbose or too brief
- **2**: Significantly too long or short
- **1**: Extremely verbose or minimal
- **0**: Unusable due to length issues

### Source Citation (0-5)
- **5**: All claims properly cited with specific sources
- **4**: Most claims cited, minor gaps
- **3**: Some citations, but incomplete
- **2**: Few or vague citations
- **1**: Minimal citation attempts
- **0**: No citations

### Binary Checks

**Hallucination Detected (Y/N)**
- Y: Response contains information NOT found in source documents
- N: All information is grounded in provided sources

**Retrieval Success (Y/N)**
- Y: The system retrieved relevant documents for the question
- N: Retrieved documents were not relevant or none were retrieved

## 💡 Tips for Efficient Scoring

1. **Score in Batches**: Score all questions for one metric at a time (e.g., all Answer Relevance scores first)
2. **Use Context**: Compare responses within the same category or difficulty to calibrate your scores
3. **Be Consistent**: Establish your scoring criteria early and apply them consistently
4. **Take Notes**: Use the Notes column to capture important observations that inform your scoring
5. **Check Sources**: The "Sources" column shows how many source documents were retrieved (useful for assessing retrieval success)

## 📈 What Happens After Scoring

Once you import the scores, you'll get:

### Automatic Calculations
- Overall score for each question (average of 5 metrics)
- Average scores across all questions
- Scores broken down by category and difficulty
- Hallucination rate
- Retrieval success rate

### Example Output
```
📊 EVALUATION METRICS
================================

📈 Summary
  total_questions: 20
  scored_questions: 20
  scoring_completion: 100.0%

📊 Average Scores (0-5 scale)
  answer_relevance: 4.2
  faithfulness: 4.5
  clarity: 4.3
  conciseness: 4.0
  source_citation: 3.8
  overall: 4.16

📂 Scores by Category
  factual_recall: 4.5 (5 questions)
  conceptual_understanding: 4.2 (6 questions)
  ...

🔍 Binary Metrics
  hallucination_rate: 5.0%
  retrieval_success_rate: 95.0%
```

## 🔄 Iteration Workflow

1. **Baseline Evaluation** ← You are here!
   - Score the current system performance
   - Identify weaknesses and improvement opportunities

2. **Analysis & Planning**
   - Analyze metrics to prioritize improvements
   - Plan system tuning (prompts, retrieval params, etc.)

3. **Implement Improvements**
   - Make changes based on analysis

4. **Comparative Evaluation**
   - Run evaluation again
   - Compare new scores to baseline
   - Measure impact of changes

## 📁 Files Generated

- `evaluation_20251105_043049_scoring.csv` - CSV for manual scoring (YOU EDIT THIS)
- `evaluation_20251105_043049.json` - Original + updated JSON with scores
- `metrics_TIMESTAMP.json` - Computed aggregate metrics

## ❓ Questions?

Refer to the full guide: [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)

---

**Ready to score?** Open the CSV file and start filling in the score columns! 🎯
