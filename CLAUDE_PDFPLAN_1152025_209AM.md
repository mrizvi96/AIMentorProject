# Automated CS PDF Collection Plan
**Created**: November 5, 2025 2:09 AM
**Goal**: Collect 10+ GB of CC-licensed CS educational materials

---

## Executive Summary

This plan outlines an automated system to collect high-quality computer science educational content (textbooks, lecture notes, technical papers) with **verified open licenses** suitable for AI training and derivative works.

### Target
- **Volume**: 10+ GB of content
- **Count**: ~2,500 documents
- **Types**: Textbooks, lecture notes, research papers, technical reports
- **Licenses**: CC BY, CC BY-SA, CC0, Public Domain only
- **Sources**: DOAB, arXiv, Internet Archive, curated university materials

### Strict License Requirements
**ACCEPT ONLY**:
- Creative Commons Attribution (CC BY)
- Creative Commons Attribution-ShareAlike (CC BY-SA)
- Creative Commons Zero (CC0)
- Public Domain
- MIT License
- Apache 2.0

**REJECT ALL**:
- CC BY-NC (NonCommercial) - Cannot use for commercial AI training
- CC BY-ND (NoDerivatives) - Cannot create derivative works
- CC BY-NC-SA - Combines above restrictions
- Any proprietary or "All Rights Reserved" licenses

---

## Implementation Architecture

### Phase 1: License Validation Framework ✅ COMPLETE

**File**: `backend/scripts/license_validator.py`

**Features**:
- Strict validation with REJECT-by-default philosophy
- Programmatic detection of prohibited terms (NC, ND)
- PDF metadata extraction for post-download verification
- Fuzzy matching for license format variations
- Complete audit trail in JSON format
- Test suite with 12 test cases

**Validation Workflow**:
1. Extract license text from source metadata
2. Normalize (uppercase, remove whitespace/noise)
3. Check prohibited terms → REJECT if any found
4. Check acceptable list → ACCEPT if matched
5. Fuzzy match common variations → ACCEPT if high confidence
6. If uncertain → Flag for MANUAL_REVIEW
7. After download → Verify license in PDF
8. Log all decisions

### Phase 2: Content Discovery & Harvesting ✅ COMPLETE

**File**: `backend/scripts/bulk_harvester.py`

**Harvesters Implemented**:

1. **DOAB Harvester** (Directory of Open Access Books)
   - Uses OAI-PMH protocol
   - DDC code 004 (Computer Science)
   - ~200 books expected
   - ~2 GB estimated

2. **arXiv Harvester** (Computer Science Papers)
   - Uses arXiv API
   - Categories: cs.AI, cs.DS, cs.LG, cs.PL, cs.SE, cs.DB, cs.DC, cs.CR
   - Filters for explicit CC licenses
   - ~2000 papers expected
   - ~5 GB estimated

3. **University Lecture Notes** (Template implemented)
   - MIT OpenCourseWare (filter for CC BY/BY-SA only)
   - Other top universities
   - Manual curation required

**Features**:
- Programmatic license validation before download
- Rate limiting (2 seconds between requests)
- Progress tracking toward 10GB goal
- Resumable downloads
- Metadata JSON generation
- Summary report generation

### Phase 3: Storage & Organization ✅ COMPLETE

**Directory Structure**:
```
cs_materials_bulk/
├── bulk_metadata.json          # Complete metadata
├── download_summary.txt         # Human-readable report
├── validation_log.json          # Audit trail
└── [institution]_[type]_[title].pdf
```

**Metadata Schema**:
```json
{
  "title": "Book/Paper Title",
  "url": "Source URL",
  "source_institution": "DOAB/arXiv/etc",
  "content_type": "textbook/lecture_notes/technical_report",
  "license": "CC BY 4.0",
  "license_verified": true,
  "authors": ["Author 1", "Author 2"],
  "file_size_bytes": 5242880,
  "download_status": "completed",
  "local_path": "/path/to/file.pdf",
  "download_date": "2025-11-05T02:09:00"
}
```

---

## Content Sources Breakdown

### Source 1: DOAB (Priority 1)
**Directory of Open Access Books**

- **Access**: OAI-PMH API
- **Filter**: DDC 004 (Computer Science) + CC licenses
- **License Coverage**: ~60% have CC BY or CC BY-SA
- **Expected Books**: 100-200
- **Expected Size**: 2 GB
- **Quality**: High (peer-reviewed academic textbooks)
- **Status**: ✅ Harvester ready

### Source 2: arXiv (Priority 2)
**arXiv Computer Science Repository**

- **Access**: arXiv API
- **Filter**: CS categories + explicit CC licenses in metadata
- **License Coverage**: Growing (10-20% have CC BY)
- **Expected Papers**: 1000-2000
- **Expected Size**: 5 GB
- **Quality**: High (research papers from top conferences)
- **Status**: ✅ Harvester ready

**Categories**:
- cs.AI - Artificial Intelligence
- cs.DS - Data Structures and Algorithms
- cs.LG - Machine Learning
- cs.PL - Programming Languages
- cs.SE - Software Engineering
- cs.DB - Databases
- cs.DC - Distributed Computing
- cs.CR - Cryptography and Security

### Source 3: Internet Archive (Priority 3)
**Archive.org Technical Books**

- **Access**: Archive.org API
- **Filter**: Subject: Computer Science + CC/Public Domain licenses
- **Expected Items**: 200-500
- **Expected Size**: 2-3 GB
- **Quality**: Mixed (includes older texts, all public domain)
- **Status**: ⏳ Needs implementation

### Source 4: Manual Curation (Priority 4)
**High-Quality Individual Sources**

- **Current Collection**: 14 PDFs, 180MB (from Google Drive)
- **Additional Sources**: Individual verification needed
- **Expected Items**: 50-100 additional
- **Expected Size**: 800 MB
- **Quality**: Very high (carefully curated)
- **Status**: ✅ Ongoing

---

## Projected Results

### By Source
| Source | Items | Size | Status |
|--------|-------|------|--------|
| Current (Google Drive) | 14 | 180 MB | ✅ Complete |
| DOAB Books | 150 | 2 GB | Ready to run |
| arXiv Papers | 2000 | 5 GB | Ready to run |
| Internet Archive | 300 | 2 GB | Needs impl. |
| Manual Additions | 50 | 800 MB | Ongoing |
| **TOTAL** | **~2,514** | **~10 GB** | **70% ready** |

### By Content Type
- **Textbooks**: ~200 (2.5 GB)
- **Research Papers**: ~2,000 (5 GB)
- **Lecture Notes**: ~50 (500 MB)
- **Technical Reports**: ~250 (2 GB)

### By Subject (Estimated)
- Algorithms & Data Structures: 25%
- Machine Learning & AI: 30%
- Programming Languages: 15%
- Software Engineering: 10%
- Systems (OS, Networks, Databases): 15%
- Theory (Computation, Cryptography): 5%

---

## Execution Plan

### Step 1: Install Dependencies
```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
pip install requests beautifulsoup4 PyPDF2
```

### Step 2: Test License Validator
```bash
python3 scripts/license_validator.py
```

**Expected Output**: 12 test cases showing proper ACCEPT/REJECT decisions

### Step 3: Run Bulk Harvester
```bash
# Create output directory
mkdir -p cs_materials_bulk

# Run harvester (will download until 10GB target)
python3 scripts/bulk_harvester.py 2>&1 | tee collection.log
```

**Duration**: 2-6 hours (depending on network speed)

### Step 4: Monitor Progress
```bash
# Check current size
du -sh cs_materials_bulk/

# View summary
cat cs_materials_bulk/download_summary.txt

# Monitor live
tail -f backend/scripts/textbook_collection.log
```

### Step 5: Verify Collection
```bash
# Check metadata
python3 -c "
import json
with open('cs_materials_bulk/bulk_metadata.json') as f:
    data = json.load(f)
    verified = sum(1 for d in data if d.get('license_verified'))
    print(f'Total items: {len(data)}')
    print(f'License verified: {verified}')
"
```

### Step 6: Integrate with RAG System
```bash
# Ingest all new materials into ChromaDB
python3 ingest.py --directory ./cs_materials_bulk/ --overwrite

# Expected: 50,000-100,000 chunks created
# Expected time: 1-2 hours
```

---

## Rate Limiting & Responsible Scraping

### Principles
1. **Respect robots.txt** - Check before scraping any domain
2. **Rate limiting** - Default 2 seconds between requests
3. **Proper identification** - User-Agent identifies as research project
4. **No concurrent requests** - One request at a time per domain
5. **API quotas** - Honor all documented limits

### Specific Limits
- **arXiv**: No official limit, but use 3s delay
- **DOAB**: OAI-PMH standard, use resumption tokens
- **Internet Archive**: 300 requests/minute max
- **General web scraping**: 2s minimum delay

---

## Quality Assurance

### Pre-Download Validation
1. Extract license from metadata
2. Validate against acceptable list
3. REJECT if any prohibited terms found
4. Log decision with reasoning

### Post-Download Validation
1. Extract license from PDF metadata
2. Scan first 10 pages for license statement
3. Verify matches pre-download license
4. Flag discrepancies for manual review

### Random Sampling
- After collection, randomly sample 50 PDFs
- Manual verification of licenses
- Check content quality
- Remove any false positives

---

## Legal & Ethical Compliance

### License Compatibility
✅ **Compatible with AI Training**:
- CC BY - Allows any use with attribution
- CC BY-SA - Allows use with same license sharing
- CC0 - Public domain, no restrictions
- Public Domain - No restrictions

❌ **NOT Compatible**:
- CC BY-NC - Prohibits commercial use (AI training is commercial)
- CC BY-ND - Prohibits derivative works (RAG system creates derivatives)

### Attribution Requirements
- Maintain metadata JSON with author/source info
- Include attribution in generated responses (already implemented)
- Keep source URLs in database

### Audit Trail
- All license decisions logged to `validation_log.json`
- Include original license text, normalized version, decision, reasoning
- Enables compliance auditing

---

## Risk Mitigation

### Risk 1: License Misidentification
**Mitigation**: Two-stage validation (metadata + PDF content)

### Risk 2: License Changes Post-Download
**Mitigation**: Snapshot license at download time, maintain audit trail

### Risk 3: Prohibited Content Slips Through
**Mitigation**: REJECT-by-default philosophy, manual review queue

### Risk 4: Source Throttling/Blocking
**Mitigation**: Respectful rate limiting, proper User-Agent, resume capability

### Risk 5: Low-Quality Content
**Mitigation**: Focus on academic sources (DOAB, arXiv), manual curation

---

## Success Metrics

### Quantitative
- ✅ Total size: ≥ 10 GB
- ✅ All items have verified open licenses
- ✅ Zero CC BY-NC or CC BY-ND content
- ✅ <5% manual review items
- ✅ Download success rate ≥ 95%

### Qualitative
- High-quality academic sources
- Diverse subject coverage
- Mix of textbooks, papers, lecture notes
- Reputable institutions represented

---

## Maintenance Plan

### Weekly
- Check for new content from DOAB (OAI-PMH ListRecords)
- Scan arXiv for new CC BY papers
- Update curated sources list

### Monthly
- Re-validate random sample of licenses
- Check for source URL changes
- Update harvester scripts if APIs change

### Quarterly
- Review validation log for patterns
- Update license validator with new patterns
- Audit collection for quality

---

## Files Created

1. **`backend/scripts/license_validator.py`** (250 lines)
   - Core validation logic
   - PDF license extraction
   - Test suite

2. **`backend/scripts/bulk_harvester.py`** (450 lines)
   - DOAB harvester
   - arXiv harvester
   - Bulk download manager

3. **`backend/scripts/textbook_collector.py`** (350 lines)
   - Original collector framework
   - Extensible architecture

4. **`backend/scripts/cs_textbooks_catalog.json`** (200 lines)
   - License requirements
   - Repository metadata
   - Validation strategies

5. **`backend/scripts/curated_university_sources.json`** (300 lines)
   - University course materials
   - Individual verified sources
   - Implementation strategies

6. **`backend/scripts/README_BULK_COLLECTION.md`** (400 lines)
   - Complete documentation
   - Quick start guide
   - Troubleshooting

7. **`CLAUDE_PDFPLAN_1152025_209AM.md`** (This file)
   - Master plan document
   - Execution instructions

---

## Next Steps After Collection

1. **Verify Collection Quality**
   - Random sample 50 PDFs for license verification
   - Check content quality and relevance

2. **Ingest into RAG System**
   ```bash
   python3 ingest.py --directory ./cs_materials_bulk/
   ```

3. **Test Enhanced System**
   ```bash
   python3 test_agentic_rag.py
   ```

4. **Update Documentation**
   - Add collection statistics to CLAUDE_LOG.md
   - Document new capabilities

5. **Monitor Performance**
   - Query response quality with larger knowledge base
   - Retrieval accuracy metrics
   - End-to-end latency

---

## Expected Outcomes

### Immediate (After Collection)
- 10+ GB of verified CC-licensed CS materials
- ~2,500 documents in unified storage
- Complete metadata and audit trail
- Ready for RAG ingestion

### After Ingestion
- 50,000-100,000 chunks in vector database
- Massive expansion of knowledge base (from 11,642 to ~100,000 chunks)
- Enhanced topic coverage across all CS domains
- Improved answer quality and source diversity

### Long-Term
- Automated weekly updates with new content
- Maintained compliance with open licensing
- Scalable framework for future expansion
- Template for other subject domains

---

**Plan Status**: ✅ READY TO EXECUTE
**Estimated Completion Time**: 4-8 hours
**Resource Requirements**: 15 GB disk space, stable internet
**Prerequisites**: Python packages installed, venv activated
