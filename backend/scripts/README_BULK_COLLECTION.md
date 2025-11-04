# Automated CS Content Collection System

## Goal
Collect **10+ GB** of high-quality computer science educational materials (textbooks, lecture notes, papers) with **verified open licenses** (CC BY, CC BY-SA, CC0, Public Domain).

## Architecture

### Components

1. **License Validator** (`license_validator.py`)
   - Strict validation of licenses
   - REJECTS NC (NonCommercial) and ND (NoDerivatives)
   - Extracts licenses from PDF metadata
   - Maintains audit trail

2. **Bulk Harvester** (`bulk_harvester.py`)
   - Discovers content from multiple sources
   - Downloads with rate limiting
   - Tracks progress toward 10GB goal
   - Generates summary reports

3. **Curated Sources** (`curated_university_sources.json`, `cs_textbooks_catalog.json`)
   - Pre-verified open sources
   - University course materials
   - Implementation strategies

## Quick Start

### 1. Install Dependencies
```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
pip install requests beautifulsoup4 PyPDF2
```

### 2. Test License Validator
```bash
python3 scripts/license_validator.py
```

Expected output:
```
✓ 'CC BY 4.0' -> ACCEPT
✓ 'CC BY-NC 4.0' -> REJECT (NonCommercial)
✓ 'Public Domain' -> ACCEPT
...
```

### 3. Run Bulk Harvester
```bash
python3 scripts/bulk_harvester.py
```

This will:
- Discover content from DOAB, arXiv, etc.
- Validate licenses
- Download until 10GB target reached
- Save to `./cs_materials_bulk/`
- Generate `bulk_metadata.json` and `download_summary.txt`

## Content Sources

### Priority 1: DOAB (Directory of Open Access Books)
- **API**: OAI-PMH
- **License Coverage**: ~60% CC BY/BY-SA
- **Expected Content**: 100-200 CS textbooks
- **Expected Size**: 2GB
- **Implementation Status**: ✓ Ready

### Priority 2: arXiv Computer Science
- **API**: arXiv API
- **License Coverage**: Growing CC BY adoption (est. 10-20%)
- **Expected Content**: 1000-5000 papers
- **Expected Size**: 5GB
- **Implementation Status**: ✓ Ready
- **Categories**: cs.AI, cs.DS, cs.LG, cs.PL, cs.SE, cs.DB, cs.DC, cs.CR

### Priority 3: Internet Archive
- **API**: Archive.org API
- **License Coverage**: Mixed, needs filtering
- **Expected Content**: 200-500 items
- **Expected Size**: 2-3GB
- **Implementation Status**: Needs implementation

### Priority 4: Manual Curation
- Individual high-quality sources
- Already collected: 14 PDFs (180MB) in current dataset
- Can expand with targeted additions

## License Validation Strategy

### Acceptable Licenses
- Creative Commons Attribution (CC BY) - any version
- Creative Commons Attribution-ShareAlike (CC BY-SA) - any version
- Creative Commons Zero (CC0 / Public Domain)
- MIT License
- Apache 2.0

### Rejected (Prohibited)
- CC BY-NC (NonCommercial) - Cannot use for this project
- CC BY-ND (NoDerivatives) - Cannot create derivative works
- CC BY-NC-SA - Combination of above
- All Rights Reserved
- Any proprietary licenses

### Validation Process
1. Extract license from source metadata
2. Normalize text (uppercase, remove noise)
3. Check for prohibited terms (NC, ND) - **REJECT if found**
4. Check against acceptable list - **ACCEPT if matched**
5. Download PDF
6. Verify license in PDF metadata/content
7. Log all decisions for audit trail

## Storage Structure

```
cs_materials_bulk/
├── bulk_metadata.json          # Complete metadata for all sources
├── download_summary.txt         # Human-readable summary
├── validation_log.json          # Audit trail of license decisions
└── [institution]_[type]_[title].pdf  # Downloaded PDFs
```

Example filenames:
- `DOAB_textbook_Algorithms_Advanced_Topics.pdf`
- `arXiv_technical_report_Deep_Learning_Survey.pdf`
- `MIT_lecture_notes_Introduction_to_Algorithms.pdf`

## Monitoring Progress

### Check Current Size
```bash
du -sh cs_materials_bulk/
```

### View Summary
```bash
cat cs_materials_bulk/download_summary.txt
```

### Monitor Live Download
```bash
tail -f backend/scripts/textbook_collection.log
```

## Scaling to 10GB

### Current Status
- **Phase 1** (Completed): 14 PDFs, 180MB from Google Drive folder
- **Phase 2** (In Progress): Automated bulk collection

### Projected Breakdown
| Source | Expected Items | Expected Size | Status |
|--------|---------------|---------------|--------|
| Current collection | 14 | 180 MB | ✓ |
| DOAB books | 150 | 2 GB | Ready |
| arXiv papers | 2000 | 5 GB | Ready |
| Internet Archive | 300 | 2 GB | Needs impl. |
| Manual additions | 50 | 800 MB | Ongoing |
| **TOTAL** | **~2500** | **~10 GB** | |

## Rate Limiting & Ethics

### Responsible Scraping
- Default delay: 2 seconds between requests
- Respect robots.txt
- User-Agent identifies as research project
- No concurrent requests to same domain
- Honor API rate limits

### API Quotas
- arXiv: No official limit, but be respectful (use delays)
- DOAB: OAI-PMH standard, use resumption tokens
- Internet Archive: 300 requests/minute limit

## Next Steps

1. **Implement Internet Archive harvester**
   - Add to `bulk_harvester.py`
   - Use Archive.org API
   - Filter by subject + license

2. **Run full collection**
   ```bash
   python3 scripts/bulk_harvester.py 2>&1 | tee collection.log
   ```

3. **Verify collected content**
   - Random sample PDF license checks
   - Quality assessment
   - Remove any false positives

4. **Integrate with ingestion pipeline**
   - Point `ingest.py` to `cs_materials_bulk/`
   - Process all PDFs into ChromaDB
   - Update CLAUDE_LOG.md

5. **Monitor and maintain**
   - Periodically check sources for new content
   - Update curated lists
   - Re-validate licenses (they can change)

## Troubleshooting

### Issue: License extraction fails from PDF
- **Cause**: PDF has no metadata or license is embedded in image
- **Solution**: Manual review required, skip if uncertain

### Issue: Download speed is slow
- **Cause**: Rate limiting or network throttling
- **Solution**: Acceptable - prioritizes being respectful to sources

### Issue: "Manual review" decisions pile up
- **Cause**: Ambiguous license text
- **Solution**: Review `validation_log.json`, make manual decisions, update validator patterns

### Issue: Hit 10GB before expected number of items
- **Cause**: PDFs larger than estimated
- **Solution**: This is fine - quality over quantity

## Legal & Ethical Notes

- All content must have verified open licenses
- When in doubt, REJECT (conservative approach)
- Keep audit trail of all license decisions
- Do not use CC BY-NC content (violates NonCommercial terms for derivative AI training)
- Respect source attribution requirements
- Maintain metadata with proper author/source credits

## References

- [Creative Commons Licenses](https://creativecommons.org/licenses/)
- [DOAB OAI-PMH Documentation](https://www.doabooks.org/en/librarians/oai-pmh)
- [arXiv API Documentation](https://arxiv.org/help/api/)
- [Open Textbook Library](https://open.umn.edu/opentextbooks/)
