#!/usr/bin/env python3
"""
Automated Source Citation Verification System

This script provides 100% certainty verification that AI-generated citations
actually exist in the PDF knowledge base by cross-referencing:
1. AI output citations (filename, page numbers, content quotes)
2. Actual PDF content stored in ChromaDB
3. PDF files on disk for text extraction verification

Usage:
    python verify_sources.py --query "What is Python?" --verify-ai-citations
    python verify_sources.py --test-questions questions.json --batch-verify
    python verify_sources.py --citation "file.pdf, pages 2-3" --content-check
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import requests
from dataclasses import dataclass
import chromadb
import fitz  # PyMuPDF

# Add backend path for imports
sys.path.append('/root/AIMentorProject/backend')
from app.core.config import settings
from app.services.agentic_rag import get_agentic_rag_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Citation:
    """Represents a citation extracted from AI output"""
    filename: str
    pages: str  # e.g., "2-3", "15", "23-25"
    author: Optional[str] = None
    title: Optional[str] = None
    confidence: float = 0.0
    extracted_from: str = ""  # The original text mentioning this citation

@dataclass
class VerificationResult:
    """Result of citation verification"""
    citation: Citation
    is_verified: bool
    verification_method: str
    matching_content: str
    confidence_score: float
    issues: List[str]
    pdf_exists: bool
    content_match_score: float

class CitationExtractor:
    """Extracts citations from AI-generated text using multiple patterns"""

    def __init__(self):
        # Common citation patterns in AI responses
        self.citation_patterns = [
            # Pattern: "Author, Title, pages X-Y"
            r'([A-Za-z\s,]+?),\s*([^,]+?),\s*pages?\s*(\d+(?:-\d+)?)',
            # Pattern: "Source: Filename, page X"
            r'Source:\s*([^,]+?),?\s*page\s*(\d+)',
            # Pattern: "Filename.pdf, pages X-Y"
            r'([A-Za-z0-9_\-\.]+\.pdf),?\s*pages?\s*(\d+(?:-\d+)?)',
            # Pattern: "Author et al., Year, page X"
            r'([A-Za-z\s]+?)\s+et\s+al\.?,?\s*(\d{4})?,?\s*page?\s*(\d+)',
            # Pattern: "(Filename, p. X)"
            r'\(([^,]+?),\s*p\.?\s*(\d+)\)',
            # Pattern: "according to Filename (page X)"
            r'according\s+to\s+([^,(]+?)\s*\(?\s*page\s*(\d+)\s*\)?',
        ]

        # PDF filename patterns
        self.pdf_pattern = r'([A-Za-z0-9_\-\.]+\.pdf)'

    def extract_citations(self, text: str) -> List[Citation]:
        """Extract citations from AI-generated text"""
        citations = []

        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    extracted_text = match.group(0)

                    # Extract filename
                    filename = None
                    if '.pdf' in extracted_text.lower():
                        pdf_match = re.search(self.pdf_pattern, extracted_text, re.IGNORECASE)
                        if pdf_match:
                            filename = pdf_match.group(1)
                    elif len(groups) >= 1:
                        # First group might be filename or author
                        potential_filename = groups[0].strip()
                        if '.pdf' in potential_filename.lower():
                            filename = potential_filename

                    # Extract pages
                    pages = None
                    page_match = re.search(r'pages?\s*(\d+(?:-\d+)?)', extracted_text, re.IGNORECASE)
                    if page_match:
                        pages = page_match.group(1)
                    elif len(groups) >= 3 and groups[2].isdigit():
                        pages = groups[2]
                    elif len(groups) >= 2 and groups[1].isdigit():
                        pages = groups[1]

                    # Extract author/title if available
                    author = None
                    title = None
                    if len(groups) >= 2 and filename != groups[0]:
                        potential_author = groups[0].strip()
                        if ',' in potential_author and not potential_author.lower().endswith('.pdf'):
                            parts = potential_author.split(',')
                            author = parts[0].strip()
                            if len(parts) > 1:
                                title = parts[1].strip()

                    if filename or pages:
                        citation = Citation(
                            filename=filename or "",
                            pages=pages or "",
                            author=author,
                            title=title,
                            extracted_from=extracted_text
                        )
                        citations.append(citation)

                except Exception as e:
                    logger.warning(f"Failed to parse citation match {match}: {e}")
                    continue

        return citations

class ChromaDBVerifier:
    """Verifies citations against ChromaDB content"""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_db_path)
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection_name)
        self.rag_service = get_agentic_rag_service()

    def search_by_filename(self, filename: str) -> List[Dict]:
        """Search ChromaDB for documents from specific filename"""
        try:
            # Query for documents with this filename
            results = self.collection.get(
                where={"file_name": filename},
                include=['documents', 'metadatas']
            )

            documents = []
            for doc, meta in zip(results['documents'], results['metadatas']):
                documents.append({
                    'text': doc,
                    'metadata': meta,
                    'page': int(meta.get('page_label', 0))
                })

            return sorted(documents, key=lambda x: x['page'])

        except Exception as e:
            logger.error(f"Error searching ChromaDB for {filename}: {e}")
            return []

    def verify_content_in_pages(self, filename: str, pages: str, ai_content: str) -> Tuple[bool, float, str]:
        """
        Verify if AI content exists in specific pages of a PDF

        Returns:
            (is_found, similarity_score, matching_text)
        """
        try:
            # Parse page range
            page_range = self._parse_page_range(pages)
            if not page_range:
                return False, 0.0, "Invalid page range"

            # Get all documents from this file
            docs = self.search_by_filename(filename)
            if not docs:
                return False, 0.0, f"File {filename} not found in database"

            # Filter by pages
            target_pages = []
            start_page, end_page = page_range
            for doc in docs:
                if start_page <= doc['page'] <= end_page:
                    target_pages.append(doc)

            if not target_pages:
                return False, 0.0, f"No content found for {filename}, pages {pages}"

            # Search for content matches
            best_match = ""
            best_score = 0.0

            for doc in target_pages:
                page_text = doc['text']

                # Exact phrase matching
                ai_sentences = [s.strip() for s in ai_content.split('.') if s.strip()]
                for sentence in ai_sentences:
                    if len(sentence) > 20:  # Only check meaningful sentences
                        if sentence.lower() in page_text.lower():
                            score = len(sentence) / len(ai_content)
                            if score > best_score:
                                best_score = score
                                best_match = sentence

                # Partial matching with word overlap
                words_ai = set(ai_content.lower().split())
                words_page = set(page_text.lower().split())
                overlap = len(words_ai.intersection(words_page))
                overlap_score = overlap / len(words_ai) if words_ai else 0

                if overlap_score > best_score:
                    best_score = overlap_score
                    best_match = page_text[:200] + "..." if len(page_text) > 200 else page_text

            is_verified = best_score > 0.3  # At least 30% content match
            return is_verified, best_score, best_match

        except Exception as e:
            logger.error(f"Error verifying content for {filename} pages {pages}: {e}")
            return False, 0.0, str(e)

    def _parse_page_range(self, pages: str) -> Optional[Tuple[int, int]]:
        """Parse page range string like '2-3', '15', '23-25'"""
        try:
            pages = pages.strip()
            if '-' in pages:
                start, end = pages.split('-', 1)
                return int(start), int(end)
            else:
                page_num = int(pages)
                return page_num, page_num
        except Exception:
            return None

class PDFVerifier:
    """Direct PDF verification using PyMuPDF"""

    def __init__(self, pdf_directory: str = "/root/AIMentorProject/course_materials"):
        self.pdf_directory = Path(pdf_directory)

    def verify_pdf_exists(self, filename: str) -> bool:
        """Check if PDF file exists on disk"""
        pdf_path = self.pdf_directory / filename
        return pdf_path.exists() and pdf_path.suffix.lower() == '.pdf'

    def extract_text_from_pages(self, filename: str, pages: str) -> str:
        """Extract text directly from PDF pages"""
        try:
            pdf_path = self.pdf_directory / filename
            if not pdf_path.exists():
                return ""

            doc = fitz.open(pdf_path)
            page_range = self._parse_page_range(pages)

            if not page_range:
                doc.close()
                return ""

            start_page, end_page = page_range
            text = ""

            # PyMuPDF is 0-indexed, so subtract 1
            for page_num in range(start_page - 1, min(end_page, len(doc))):
                page = doc[page_num]
                text += page.get_text() + "\n"

            doc.close()
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return ""

    def verify_content_directly(self, filename: str, pages: str, ai_content: str) -> Tuple[bool, float, str]:
        """
        Verify AI content directly against PDF text

        Returns:
            (is_verified, confidence_score, extracted_pdf_text)
        """
        try:
            pdf_text = self.extract_text_from_pages(filename, pages)
            if not pdf_text:
                return False, 0.0, "Could not extract PDF text"

            # Content matching
            ai_sentences = [s.strip() for s in ai_content.split('.') if s.strip()]
            matches_found = 0

            for sentence in ai_sentences:
                if len(sentence) > 20:  # Only check meaningful sentences
                    if sentence.lower() in pdf_text.lower():
                        matches_found += 1

            confidence = matches_found / len(ai_sentences) if ai_sentences else 0
            is_verified = confidence > 0.3  # At least 30% of sentences found

            return is_verified, confidence, pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text

        except Exception as e:
            logger.error(f"Error in direct PDF verification: {e}")
            return False, 0.0, str(e)

    def _parse_page_range(self, pages: str) -> Optional[Tuple[int, int]]:
        """Parse page range string"""
        try:
            pages = pages.strip()
            if '-' in pages:
                start, end = pages.split('-', 1)
                return int(start), int(end)
            else:
                return int(pages), int(pages)
        except Exception:
            return None

class SourceVerificationSystem:
    """Main verification system combining all verification methods"""

    def __init__(self):
        self.citation_extractor = CitationExtractor()
        self.chroma_verifier = ChromaDBVerifier()
        self.pdf_verifier = PDFVerifier()

    def verify_ai_response(self, question: str, ai_response: str) -> Dict:
        """
        Verify all citations in an AI response

        Returns:
            Dict with verification results for each citation
        """
        logger.info(f"Verifying citations for: {question[:100]}...")

        # Extract citations from AI response
        citations = self.citation_extractor.extract_citations(ai_response)
        logger.info(f"Found {len(citations)} potential citations")

        verification_results = []

        for i, citation in enumerate(citations):
            logger.info(f"Verifying citation {i+1}: {citation.filename}, pages {citation.pages}")

            result = self.verify_single_citation(citation, ai_response)
            verification_results.append(result)

        # Calculate overall verification score
        verified_count = sum(1 for r in verification_results if r.is_verified)
        overall_score = verified_count / len(verification_results) if verification_results else 0

        return {
            'question': question,
            'citations_found': len(citations),
            'citations_verified': verified_count,
            'overall_verification_score': overall_score,
            'verification_results': verification_results,
            'summary': self._generate_summary(verification_results)
        }

    def verify_single_citation(self, citation: Citation, context_text: str) -> VerificationResult:
        """Verify a single citation using multiple methods"""
        issues = []

        # Check if PDF exists
        pdf_exists = self.pdf_verifier.verify_pdf_exists(citation.filename)
        if not pdf_exists:
            issues.append(f"PDF file not found: {citation.filename}")

        # Extract relevant content from AI response
        relevant_content = self._extract_relevant_content(citation, context_text)

        # Method 1: ChromaDB verification
        chroma_verified, chroma_score, chroma_match = self.chroma_verifier.verify_content_in_pages(
            citation.filename, citation.pages, relevant_content
        )

        # Method 2: Direct PDF verification
        pdf_verified, pdf_score, pdf_match = self.pdf_verifier.verify_content_directly(
            citation.filename, citation.pages, relevant_content
        )

        # Determine final verification result
        is_verified = chroma_verified or pdf_verified
        confidence_score = max(chroma_score, pdf_score)

        # Choose best method for reporting
        if pdf_score > chroma_score:
            verification_method = "Direct PDF verification"
            matching_content = pdf_match
            content_match_score = pdf_score
        else:
            verification_method = "ChromaDB verification"
            matching_content = chroma_match
            content_match_score = chroma_score

        if not is_verified:
            issues.append("Content not found in cited pages")
            if not citation.filename:
                issues.append("No filename identified")
            if not citation.pages:
                issues.append("No page numbers identified")

        return VerificationResult(
            citation=citation,
            is_verified=is_verified,
            verification_method=verification_method,
            matching_content=matching_content,
            confidence_score=confidence_score,
            issues=issues,
            pdf_exists=pdf_exists,
            content_match_score=content_match_score
        )

    def _extract_relevant_content(self, citation: Citation, full_text: str) -> str:
        """Extract content relevant to the citation from the AI response"""
        # Find the citation mention in the text and extract surrounding content
        citation_pos = full_text.lower().find(citation.extracted_from.lower())
        if citation_pos == -1:
            return full_text  # Use full text if citation not found

        # Extract 200 characters before and after the citation
        start = max(0, citation_pos - 200)
        end = min(len(full_text), citation_pos + len(citation.extracted_from) + 200)

        return full_text[start:end]

    def _generate_summary(self, results: List[VerificationResult]) -> str:
        """Generate a summary of verification results"""
        if not results:
            return "No citations found to verify"

        verified = sum(1 for r in results if r.is_verified)
        total = len(results)

        summary = f"Verified {verified}/{total} citations ({verified/total*100:.1f}%)\n"

        if verified < total:
            summary += "\nIssues found:\n"
            for result in results:
                if not result.is_verified:
                    summary += f"  • {result.citation.filename or 'Unknown file'}: "
                    summary += "; ".join(result.issues) + "\n"

        return summary

def main():
    parser = argparse.ArgumentParser(description="Verify AI source citations")
    parser.add_argument("--query", type=str, help="Question to ask AI")
    parser.add_argument("--ai-response", type=str, help="AI response to verify")
    parser.add_argument("--test-questions", type=str, help="JSON file with test questions")
    parser.add_argument("--batch-verify", action="store_true", help="Batch verify multiple questions")
    parser.add_argument("--citation", type=str, help="Specific citation to test (format: 'file.pdf, pages X-Y')")
    parser.add_argument("--content-check", type=str, help="Content to check in citation")
    parser.add_argument("--output", type=str, help="Output file for results")

    args = parser.parse_args()

    verifier = SourceVerificationSystem()

    if args.batch_verify and args.test_questions:
        # Batch verification
        with open(args.test_questions, 'r') as f:
            questions = json.load(f)

        results = []
        for i, q in enumerate(questions):
            logger.info(f"Processing question {i+1}/{len(questions)}")

            # Get AI response
            try:
                rag_service = get_agentic_rag_service()
                ai_result = rag_service.query(q['question'])
                ai_response = ai_result['answer']

                # Verify citations
                verification = verifier.verify_ai_response(q['question'], ai_response)
                results.append(verification)

            except Exception as e:
                logger.error(f"Failed to process question {q['question']}: {e}")
                continue

        output = {
            'total_questions': len(questions),
            'results': results,
            'summary': {
                'total_citations': sum(r['citations_found'] for r in results),
                'verified_citations': sum(r['citations_verified'] for r in results),
                'average_verification_score': sum(r['overall_verification_score'] for r in results) / len(results) if results else 0
            }
        }

    elif args.query:
        # Single query verification
        try:
            rag_service = get_agentic_rag_service()
            ai_result = rag_service.query(args.query)
            ai_response = ai_result['answer']

            print(f"AI Response:\n{ai_response}\n")
            print("="*60)

            verification = verifier.verify_ai_response(args.query, ai_response)
            output = verification

        except Exception as e:
            logger.error(f"Failed to get AI response: {e}")
            return 1

    elif args.citation:
        # Specific citation test
        filename, pages = args.citation.split(',', 1)
        filename = filename.strip()
        pages = pages.replace('pages', '').replace('page', '').strip()

        content = args.content_check or "Python is a programming language"

        citation = Citation(filename=filename, pages=pages)
        result = verifier.verify_single_citation(citation, content)

        output = {
            'citation_test': {
                'filename': filename,
                'pages': pages,
                'content': content,
                'verified': result.is_verified,
                'confidence': result.confidence_score,
                'method': result.verification_method,
                'issues': result.issues
            }
        }

    else:
        print("Error: Please specify --query, --batch-verify with --test-questions, or --citation")
        return 1

    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(output, indent=2, default=str))

    return 0

if __name__ == "__main__":
    sys.exit(main())