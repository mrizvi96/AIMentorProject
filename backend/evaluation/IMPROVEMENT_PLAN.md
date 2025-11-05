# RAG System Improvement Plan

**Date**: November 5, 2025
**Status**: Planning Phase - Based on Baseline Evaluation
**Goal**: Optimize RAG system performance through evidence-based tuning

---

## Executive Summary

This plan outlines specific improvements to the AI Mentor RAG system based on analysis of the baseline evaluation (20 questions, 100% response rate). The improvements are prioritized by expected impact and implementation difficulty.

---

## Current System State

### ✅ What's Working Well

1. **Core Functionality**: 100% success rate (20/20 questions answered)
2. **Infrastructure**: All services stable and operational
3. **Data Pipeline**: 33,757 chunks from 21 PDFs successfully ingested
4. **Source Grounding**: All responses cite sources with page numbers

### ⚠️ Areas for Improvement

Based on evaluation data analysis:

| Issue | Evidence | Impact |
|-------|----------|--------|
| **Limited retrieval context** | Only 1 source per query | May miss relevant information |
| **Moderate similarity scores** | Avg: 0.512 (range: 0.375-0.665) | Suggests potential for better matches |
| **Low corpus coverage** | Only 57% (12/21 PDFs) used | Underutilizing available knowledge |
| **Inconsistent response length** | 150-1275 chars (Q2: 1275 chars) | User experience inconsistency |
| **Small chunk size** | 256 tokens | May fragment context unnecessarily |

### 📊 Current Configuration

```python
# Retrieval
top_k_retrieval = 1          # Only 1 source retrieved
similarity_threshold = 0.7    # High threshold (may filter too much)
chunk_size = 256             # Small chunks
chunk_overlap = 25           # ~10% overlap

# Generation
temperature = 0.7            # Moderate creativity
max_tokens = 512            # May be limiting longer explanations
stop_sequences = ["\n\n"]   # May truncate prematurely
```

---

## Improvement Priorities

### 🚀 Phase 1: Quick Wins (< 30 minutes)

**Target**: Improve retrieval quality and response consistency

#### 1.1 Increase Retrieval Context (HIGHEST PRIORITY)

**Rationale**: Single source limits context breadth. Multiple perspectives improve answer quality.

**Changes**:
```python
# config.py
top_k_retrieval: int = 3  # Up from 1
```

**Expected Impact**:
- ✅ Richer context for generation
- ✅ Better handling of multi-faceted questions
- ✅ Improved source citation diversity
- ⚠️ Slightly higher latency (~200ms)

**Test Questions**: Q6 (binary search), Q11 (arrays vs linked lists), Q18 (interpreted vs compiled)

---

#### 1.2 Optimize Stop Sequences

**Rationale**: Current `["\n\n"]` may truncate responses prematurely, especially for multi-paragraph explanations.

**Changes**:
```python
# mistral_llm.py - line 37
"stop": kwargs.get("stop", [])  # Remove double newline stop
```

**Expected Impact**:
- ✅ More complete explanations
- ✅ Better multi-paragraph responses
- ⚠️ May need max_tokens adjustment to prevent verbosity

---

#### 1.3 Adjust Max Tokens

**Rationale**: Current 512 may be too restrictive for detailed explanations (Q2 hit limits at 1275 chars).

**Changes**:
```python
# config.py
llm_max_tokens: int = 768  # Up from 512
```

**Expected Impact**:
- ✅ Allows fuller explanations for complex topics
- ✅ Reduces truncation issues
- ⚠️ Slightly higher cost/latency

---

### 🔧 Phase 2: Medium-Term Improvements (1-2 hours)

#### 2.1 Increase Chunk Size

**Rationale**: 256 tokens is small and may fragment conceptual context. Educational content benefits from larger chunks.

**Changes**:
```python
# config.py
chunk_size: int = 512  # Up from 256
chunk_overlap: int = 50  # Maintain ~10% overlap
```

**Note**: Requires re-ingestion of all documents (~5 minutes).

**Expected Impact**:
- ✅ Better context preservation
- ✅ Reduced chunk fragmentation
- ✅ Potentially higher similarity scores
- ⚠️ Fewer total chunks (~17K instead of 33K)

**Implementation**:
```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
# Update config.py first
python3 ingest.py --directory ./course_materials/ --overwrite
```

---

#### 2.2 Prompt Engineering for Consistency

**Rationale**: Current prompt doesn't constrain response length, leading to 150-1275 char variability.

**Current Prompt** (rag_service.py:92-107):
```
You are an expert Computer Science mentor helping students understand complex topics.

Context information from course materials:
{context_str}

Based strictly on the context above, answer the following question...

Instructions:
1. Provide a clear, direct answer
2. Use simple language and analogies when helpful
3. Cite specific parts of the context you used
4. If unsure, acknowledge limitations

Answer:
```

**Improved Prompt**:
```
You are an expert Computer Science mentor helping students learn programming concepts.

Context information from course materials:
{context_str}

Question: {query_str}

Provide a clear, concise answer (2-4 paragraphs) that:
1. Directly addresses the question in the first paragraph
2. Explains key concepts with simple analogies
3. Cites specific page numbers from the context (e.g., "page 41")
4. Uses 200-400 words total

Base your answer ONLY on the provided context. If the context lacks information, state this explicitly.

Answer:
```

**Expected Impact**:
- ✅ More consistent response lengths
- ✅ Better structure (intro → explanation → citation)
- ✅ Clearer user expectations

---

#### 2.3 Lower Similarity Threshold

**Rationale**: Current 0.7 threshold is high. Avg score is 0.512, meaning some relevant docs might be filtered.

**Changes**:
```python
# config.py
similarity_threshold: float = 0.4  # Down from 0.7
```

**Expected Impact**:
- ✅ More lenient retrieval (useful for edge cases)
- ⚠️ May include marginally relevant chunks
- ℹ️ With top_k=3, only affects borderline cases

---

### 🔬 Phase 3: Experimental (2+ hours)

#### 3.1 Query Expansion

**Rationale**: Single-term queries may miss relevant docs. Expand with synonyms/related terms.

**Implementation**: Add query preprocessing in rag_service.py

**Expected Impact**:
- ✅ Better retrieval for ambiguous queries
- ⚠️ Adds complexity
- ⚠️ Requires careful tuning

**Priority**: LOW (test after Phase 1-2 improvements)

---

#### 3.2 Reranking Strategy

**Rationale**: Embeddings alone may not capture semantic relevance. Rerank with cross-encoder.

**Implementation**: Add reranker between retrieval and generation

**Expected Impact**:
- ✅ Higher quality top_k selection
- ⚠️ Adds latency (~300ms per query)
- ⚠️ Requires additional model

**Priority**: LOW (evaluate if Phase 1-2 insufficient)

---

## Testing Strategy

### Comparative Evaluation Protocol

For each configuration change:

1. **Run Evaluation**:
   ```bash
   python3 run_evaluation.py --mode direct
   ```

2. **Generate New CSV**:
   ```bash
   # CSV will be auto-generated with timestamp
   ```

3. **Manual Scoring**: Score new results using same rubric

4. **Compare Metrics**:
   - Overall score: Target > 4.0
   - Faithfulness: Target > 4.5 (critical for education)
   - Answer Relevance: Target > 4.2
   - Source Citation: Target > 4.0
   - Hallucination rate: Target < 5%
   - Retrieval success: Target > 90%

5. **Statistical Significance**: Need ≥ 0.2 improvement to be meaningful

---

## Implementation Roadmap

### Week 1: Phase 1 (Quick Wins)

**Day 1** (Today):
- [x] Create improvement plan
- [ ] Implement top_k=3
- [ ] Remove stop sequences
- [ ] Increase max_tokens to 768
- [ ] Run comparative evaluation
- [ ] Score and compare results

**Expected Completion**: 2-3 hours
**Risk**: LOW
**Rollback**: Easy (revert config.py)

---

### Week 1: Phase 2 (Medium-Term)

**Day 2-3**:
- [ ] Re-ingest with chunk_size=512
- [ ] Update prompt template
- [ ] Lower similarity threshold to 0.4
- [ ] Run comparative evaluation
- [ ] Score and compare results

**Expected Completion**: 4-6 hours
**Risk**: MEDIUM (re-ingestion required)
**Rollback**: Moderate (need to re-ingest with old config)

---

### Week 2: Phase 3 (Experimental)

**Only if Phase 1-2 results are insufficient**:
- Query expansion
- Reranking
- Alternative embedding models

---

## Success Criteria

### Minimum Acceptable Performance (MVP)

| Metric | Baseline | Target | Stretch |
|--------|----------|--------|---------|
| Overall Score | TBD | > 4.0 | > 4.5 |
| Faithfulness | TBD | > 4.5 | > 4.8 |
| Answer Relevance | TBD | > 4.2 | > 4.5 |
| Hallucination Rate | TBD | < 5% | < 2% |
| Retrieval Success | TBD | > 90% | > 95% |

**Note**: Baseline scores will be determined after manual scoring is complete.

---

## Risk Assessment

### Low Risk Changes
- ✅ top_k_retrieval: 1 → 3 (easy rollback)
- ✅ max_tokens: 512 → 768 (easy rollback)
- ✅ stop_sequences: ["\n\n"] → [] (easy rollback)

### Medium Risk Changes
- ⚠️ chunk_size: 256 → 512 (requires re-ingestion)
- ⚠️ Prompt template changes (affects all responses)

### High Risk Changes
- ⛔ Query expansion (may degrade precision)
- ⛔ Reranking (adds latency, complexity)

---

## Rollback Plan

If changes degrade performance:

1. **Immediate Rollback** (< 5 min):
   ```bash
   git checkout app/core/config.py
   git checkout app/services/rag_service.py
   # Restart backend
   ```

2. **Database Rollback** (if re-ingested):
   ```bash
   # Restore from backup or re-run with old config
   python3 ingest.py --directory ./course_materials/ --overwrite
   ```

---

## Next Actions

### Immediate (While User Scores Baseline)

1. ✅ Create this improvement plan
2. ⏳ Implement Phase 1 changes
3. ⏳ Run comparative evaluation
4. ⏳ Prepare side-by-side comparison for user

### After User Completes Scoring

1. Review baseline scores together
2. Validate improvement priorities
3. Review comparative evaluation results
4. Decide on Phase 2 implementation

---

## Appendix: Configuration Change Summary

### Phase 1: Quick Wins

```python
# app/core/config.py
top_k_retrieval: int = 3           # Changed from 1
llm_max_tokens: int = 768          # Changed from 512

# app/services/mistral_llm.py (line 37)
"stop": kwargs.get("stop", [])     # Changed from ["\n\n"]
```

### Phase 2: Medium-Term

```python
# app/core/config.py
chunk_size: int = 512              # Changed from 256
chunk_overlap: int = 50            # Changed from 25
similarity_threshold: float = 0.4  # Changed from 0.7

# app/services/rag_service.py
# Updated prompt template (lines 92-107)
```

---

**Document Status**: Ready for Implementation
**Next Update**: After Phase 1 comparative evaluation
