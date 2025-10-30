# Evaluation Metrics for AI Mentor RAG System

## Overview

This document defines the metrics used to evaluate the quality and effectiveness of the AI Mentor's responses. The evaluation framework measures both the technical performance and pedagogical quality of the system.

---

## Core Metrics

### 1. Answer Relevance (0-5 scale)

**Definition**: How well does the answer address the specific question asked?

**Scoring Criteria:**
- **5 - Excellent**: Answer directly addresses all aspects of the question with comprehensive coverage
- **4 - Good**: Answer addresses the main question thoroughly but may miss minor details
- **3 - Adequate**: Answer addresses the core question but lacks depth or completeness
- **2 - Partial**: Answer is tangentially related but misses key aspects of the question
- **1 - Poor**: Answer barely relates to the question
- **0 - Irrelevant**: Answer is completely off-topic or unrelated

**Example Questions to Ask:**
- Does the response directly answer what was asked?
- Are all parts of multi-part questions addressed?
- Is the level of detail appropriate for the question?

---

### 2. Faithfulness / Grounding (0-5 scale)

**Definition**: How well is the answer grounded in the retrieved source documents? Does it avoid hallucination?

**Scoring Criteria:**
- **5 - Excellent**: All claims are directly supported by source documents with accurate citations
- **4 - Good**: Most claims are supported; minor interpretations are reasonable extrapolations
- **3 - Adequate**: Core claims are supported but some details lack clear source attribution
- **2 - Partial**: Mix of grounded and unsupported claims; some hallucination present
- **1 - Poor**: Mostly unsupported claims; significant hallucination
- **0 - Fabricated**: Entirely made up with no grounding in source documents

**Example Questions to Ask:**
- Can each claim be traced back to a source document?
- Are citations provided and accurate?
- Does the answer introduce information not present in the sources?

---

### 3. Clarity / Pedagogical Quality (0-5 scale)

**Definition**: How clear, understandable, and pedagogically effective is the explanation?

**Scoring Criteria:**
- **5 - Excellent**: Crystal clear explanation with examples, analogies, and appropriate structure
- **4 - Good**: Clear and well-organized with good use of examples
- **3 - Adequate**: Understandable but could be clearer; basic explanation without much depth
- **2 - Partial**: Somewhat confusing; lacks structure or clear progression of ideas
- **1 - Poor**: Confusing, disorganized, or uses unexplained jargon
- **0 - Incomprehensible**: Cannot be understood or is completely incoherent

**Example Questions to Ask:**
- Would a student understand this explanation?
- Are examples or analogies used effectively?
- Is the language appropriate for the target audience?
- Is the explanation well-structured and logical?

---

### 4. Conciseness (0-5 scale)

**Definition**: Is the answer appropriately concise without being too verbose or too brief?

**Scoring Criteria:**
- **5 - Excellent**: Perfect balance; comprehensive yet concise
- **4 - Good**: Slightly verbose or slightly brief, but still effective
- **3 - Adequate**: Somewhat verbose or lacks detail, but acceptable
- **2 - Partial**: Too long-winded or too brief; affects comprehension
- **1 - Poor**: Extremely verbose or extremely terse; hard to use
- **0 - Unusable**: Completely inappropriate length (book-length or one-word)

**Example Questions to Ask:**
- Does the answer respect the user's time?
- Is information repeated unnecessarily?
- Are key details missing due to excessive brevity?

---

### 5. Source Citation Quality (0-5 scale)

**Definition**: Are sources properly cited and helpful to the user?

**Scoring Criteria:**
- **5 - Excellent**: All sources cited with specific references (file name, page, section)
- **4 - Good**: Sources cited with most identifying information
- **3 - Adequate**: Sources mentioned but with limited detail
- **2 - Partial**: Vague source attribution (e.g., "according to the textbook")
- **1 - Poor**: Sources claimed but not actually cited
- **0 - None**: No source attribution at all

**Example Questions to Ask:**
- Can the user find the original source easily?
- Are specific pages or sections referenced?
- Do the citations match the actual source documents?

---

## Binary Checks

### Hallucination Check (Yes/No)

**Definition**: Does the response contain any information that is not supported by the source documents?

**Criteria:**
- **No Hallucination (Pass)**: All factual claims can be traced to source documents
- **Hallucination Detected (Fail)**: Response includes fabricated information, made-up examples, or incorrect facts not present in sources

**Examples of Hallucination:**
- Made-up code examples not in the textbooks
- Incorrect version numbers or dates
- Fictional anecdotes or historical references
- Technical details that contradict the sources

---

### Retrieval Success (Yes/No)

**Definition**: Did the system successfully retrieve relevant documents for this question?

**Criteria:**
- **Success (Pass)**: At least one retrieved document contains information relevant to the question
- **Failure (Fail)**: No retrieved documents are relevant to the question

---

## Aggregate Metrics

### Overall Score

**Calculation**:
```
Overall Score = (Answer Relevance + Faithfulness + Clarity + Conciseness + Source Citation) / 5
```

**Interpretation:**
- **4.5 - 5.0**: Excellent response
- **3.5 - 4.4**: Good response
- **2.5 - 3.4**: Adequate response
- **1.5 - 2.4**: Poor response
- **0.0 - 1.4**: Unacceptable response

### Pass Rate

**Calculation**:
```
Pass Rate = (Number of responses with Overall Score >= 3.0) / Total responses
```

**Target**: >= 80% pass rate for production readiness

---

## Evaluation Process

### Manual Evaluation (Phase 1)

For initial evaluation, a human evaluator will:
1. Read each question
2. Review the AI Mentor's response
3. Check the retrieved source documents
4. Score each metric independently
5. Note any hallucinations or issues
6. Record findings in evaluation results file

### Semi-Automated Evaluation (Phase 2 - Future)

- Use LLM-as-judge for initial scoring
- Human review for validation
- Automated hallucination detection
- Batch processing of question bank

---

## Reporting

Each evaluation run should produce:
1. **Summary Report**: Overall scores, pass rate, average by category
2. **Detailed Results**: Individual scores for each question
3. **Failure Analysis**: List of low-scoring responses with reasons
4. **Recommendations**: Specific improvements needed (prompt engineering, retrieval tuning, etc.)

---

## Revision History

- **v1.0 (2025-10-30)**: Initial metrics definition
  - 5 core metrics defined
  - 2 binary checks added
  - Aggregate scoring established
