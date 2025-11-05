# CSV Update - Source Transparency Added

## Changes Made

The scoring CSV has been updated to include **source document transparency**, making it much easier to evaluate whether the system retrieved relevant documents and whether responses are grounded in those sources.

## New Columns Added

| Column | Description | Example |
|--------|-------------|---------|
| **Source_Documents** | Shows which PDF file(s) were retrieved | `UDAYAN_DAS_Introduction_to_Python_Programming_-_WEB.pdf` |
| **Source_Scores** | Shows similarity scores for retrieved documents | `0.478` (higher = more relevant) |

## Before vs After

### Before
```
ID, Category, Difficulty, Question, Response, Sources, Answer_Relevance_0-5, ...
Q001, factual_recall, easy, "What is Python?", "...", 1, ___, ...
```
❌ You could see "1 source" but not WHICH document

### After  
```
ID, Category, Difficulty, Question, Response, Source_Count, Source_Documents, Source_Scores, Answer_Relevance_0-5, ...
Q001, factual_recall, easy, "What is Python?", "...", 1, "UDAYAN_DAS_Introduction_to_Python_Programming_-_WEB.pdf", "0.478", ___, ...
```
✅ You can see EXACTLY which PDF was used and how relevant it was!

## Why This Matters for Scoring

### 1. **Retrieval Success (Y/N)**
You can now objectively determine if the retrieved document is relevant to the question:
- Look at `Source_Documents` column
- Ask: "Is this PDF the right one for answering this question?"
- Score in `Retrieval_Success_Y/N` column

### 2. **Faithfulness (0-5)**
You can verify if the response is grounded in the source:
- Note which document was retrieved
- Check if the response content could come from that specific PDF
- If response contains info NOT in that PDF → lower faithfulness score

### 3. **Source Citation (0-5)**
You can assess citation quality:
- Compare what the response cites vs. what was actually retrieved
- Check if page numbers/file paths in response match `Source_Documents`

## Retrieval Analysis Summary

Based on the evaluation:

- **12 different PDFs** were used across 20 questions (57% corpus coverage)
- Most frequently retrieved: `UDAYAN_DAS_Introduction_to_Python_Programming_-_WEB.pdf` (20% of questions)
- **Similarity scores** ranged from 0.375 to 0.665 (avg: 0.512)
- All questions retrieved **exactly 1 source** (top_k_retrieval = 1 in config)

## Scoring Tips with New Columns

### Assessing Retrieval Success

**Example - Good Retrieval:**
- Question: "What is Python?"
- Retrieved: `UDAYAN_DAS_Introduction_to_Python_Programming_-_WEB.pdf`
- Score: 0.478
- Assessment: ✅ Correct document, relevant content → Retrieval_Success = Y

**Example - Poor Retrieval:**
- Question: "Explain quantum computing"
- Retrieved: `Introduction_to_Python_Programming.pdf`  
- Assessment: ❌ Wrong domain → Retrieval_Success = N

### Assessing Faithfulness

Now you can:
1. Note which PDF was retrieved
2. Ask: "Could this response have been generated from that specific PDF?"
3. If the response includes information that seems outside the scope of that document → potential hallucination

### Example Workflow

For Question Q001:
1. **See retrieval**: "UDAYAN_DAS_Introduction_to_Python_Programming_-_WEB.pdf" (score: 0.478)
2. **Read response**: "Python is a programming language. Its name comes from Monty Python..."
3. **Evaluate**:
   - Retrieval Success: Y (correct document for Python question)
   - Faithfulness: Check if naming origin is in that PDF
   - Source Citation: Response mentions page 41, can verify

## File Location

**Updated CSV**: `/root/AIMentorProject/backend/evaluation/results/evaluation_20251105_043049_scoring.csv`

The import script (`import_scores.py`) has been tested and works correctly with the new columns.

---

✅ **You now have complete transparency into what the RAG system retrieved for each question!**
