#!/usr/bin/env python3
"""
Expanded Academic CS Content Harvester

Focus: High-quality, peer-reviewed materials with verified CC BY/BY-SA/CC0 licenses
Strategy: Known academic publishers, university presses, and open textbook initiatives
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

import requests

from license_validator import StrictLicenseValidator, LicenseDecision

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Book:
    """Represents a book to download"""
    title: str
    url: str
    source: str
    license: str
    authors: List[str]
    peer_reviewed: bool = True
    size_mb_estimate: float = 5.0


# Expanded collection of verified CC-licensed CS books
# Focus on peer-reviewed, academic sources
ACADEMIC_BOOKS = [
    # ==================== ALGORITHMS & DATA STRUCTURES ====================
    Book(
        title="Algorithms by Jeff Erickson",
        url="http://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf",
        source="University of Illinois",
        license="CC BY 4.0",
        authors=["Jeff Erickson"],
        peer_reviewed=True,
        size_mb_estimate=24.0
    ),
    Book(
        title="Open Data Structures (Python)",
        url="http://opendatastructures.org/ods-python.pdf",
        source="opendatastructures.org",
        license="CC BY 2.5",
        authors=["Pat Morin"],
        peer_reviewed=True,
        size_mb_estimate=1.5
    ),
    Book(
        title="Open Data Structures (Java)",
        url="http://opendatastructures.org/ods-java.pdf",
        source="opendatastructures.org",
        license="CC BY 2.5",
        authors=["Pat Morin"],
        peer_reviewed=True,
        size_mb_estimate=1.5
    ),
    Book(
        title="Open Data Structures (C++)",
        url="http://opendatastructures.org/ods-cpp.pdf",
        source="opendatastructures.org",
        license="CC BY 2.5",
        authors=["Pat Morin"],
        peer_reviewed=True,
        size_mb_estimate=1.5
    ),

    # ==================== THEORETICAL CS ====================
    Book(
        title="Introduction to Theoretical Computer Science",
        url="https://files.boazbarak.org/introtcs/lnotes_book.pdf",
        source="Boaz Barak",
        license="CC BY-SA 4.0",
        authors=["Boaz Barak"],
        peer_reviewed=True,
        size_mb_estimate=21.0
    ),
    Book(
        title="Mathematics for Computer Science",
        url="https://courses.csail.mit.edu/6.042/spring18/mcs.pdf",
        source="MIT OpenCourseWare",
        license="CC BY-SA 3.0",
        authors=["Eric Lehman", "F. Thomson Leighton", "Albert R. Meyer"],
        peer_reviewed=True,
        size_mb_estimate=13.0
    ),

    # ==================== PROGRAMMING LANGUAGES ====================
    Book(
        title="Programming Languages: Application and Interpretation",
        url="http://cs.brown.edu/courses/cs173/2012/book/book.pdf",
        source="Brown University",
        license="CC BY-SA 3.0",
        authors=["Shriram Krishnamurthi"],
        peer_reviewed=True,
        size_mb_estimate=3.0
    ),

    # ==================== MACHINE LEARNING & AI ====================
    Book(
        title="Dive into Deep Learning",
        url="https://d2l.ai/d2l-en.pdf",
        source="d2l.ai",
        license="CC BY-SA 4.0",
        authors=["Aston Zhang", "Zachary C. Lipton", "Mu Li", "Alexander J. Smola"],
        peer_reviewed=True,
        size_mb_estimate=15.0
    ),
    Book(
        title="Neural Networks and Deep Learning",
        url="http://neuralnetworksanddeeplearning.com/chap1.html",  # Web-based, check for PDF
        source="Michael Nielsen",
        license="CC BY-NC 3.0",  # Will be rejected - NonCommercial
        authors=["Michael Nielsen"],
        peer_reviewed=True,
        size_mb_estimate=5.0
    ),

    # ==================== COMPUTER ARCHITECTURE ====================
    Book(
        title="Computer Organization and Design RISC-V Edition (Open Chapters)",
        url="https://www.elsevier.com/__data/assets/pdf_file/0009/1017013/Computer-Organization-and-Design-RISC-V-Chapter-1.pdf",
        source="Morgan Kaufmann / Elsevier",
        license="Unknown",  # Need to verify
        authors=["David Patterson", "John Hennessy"],
        peer_reviewed=True,
        size_mb_estimate=2.0
    ),

    # ==================== SOFTWARE ENGINEERING ====================
    Book(
        title="Software Engineering at Google",
        url="https://abseil.io/resources/swe-book/html/toc.html",  # HTML version, PDF may exist
        source="O'Reilly / Google",
        license="CC BY-NC-ND 4.0",  # Will be rejected - NC and ND
        authors=["Titus Winters", "Tom Manshreck", "Hyrum Wright"],
        peer_reviewed=True,
        size_mb_estimate=10.0
    ),

    # ==================== DATABASES ====================
    Book(
        title="Foundations of Databases",
        url="http://webdam.inria.fr/Alice/pdfs/all.pdf",
        source="INRIA",
        license="Unknown",  # Check if available
        authors=["Serge Abiteboul", "Richard Hull", "Victor Vianu"],
        peer_reviewed=True,
        size_mb_estimate=8.0
    ),

    # ==================== OPERATING SYSTEMS ====================
    Book(
        title="Operating Systems: From 0 to 1",
        url="https://github.com/tuhdo/os01/raw/master/Operating_Systems_From_0_to_1.pdf",
        source="GitHub / Tu Do",
        license="Unknown",  # Check repository
        authors=["Tu Do"],
        peer_reviewed=False,
        size_mb_estimate=3.0
    ),

    # ==================== CRYPTOGRAPHY ====================
    Book(
        title="A Graduate Course in Applied Cryptography",
        url="http://toc.cryptobook.us/book.pdf",
        source="Stanford / Dan Boneh",
        license="CC BY-NC-ND 4.0",  # Will be rejected
        authors=["Dan Boneh", "Victor Shoup"],
        peer_reviewed=True,
        size_mb_estimate=10.0
    ),

    # ==================== COMPUTER NETWORKS ====================
    Book(
        title="Computer Networks: A Systems Approach",
        url="https://book.systemsapproach.org/",  # Check for PDF version
        source="Systems Approach",
        license="CC BY 4.0",
        authors=["Larry Peterson", "Bruce Davie"],
        peer_reviewed=True,
        size_mb_estimate=8.0
    ),

    # ==================== PARALLEL COMPUTING ====================
    Book(
        title="Introduction to Parallel Computing",
        url="https://hpc.llnl.gov/documentation/tutorials/introduction-parallel-computing-tutorial",
        source="Lawrence Livermore National Laboratory",
        license="Public Domain",  # US Government work
        authors=["Blaise Barney"],
        peer_reviewed=True,
        size_mb_estimate=2.0
    ),

    # ==================== COMPILER DESIGN ====================
    Book(
        title="Introduction to Compilers and Language Design",
        url="https://www3.nd.edu/~dthain/compilerbook/compilerbook.pdf",
        source="University of Notre Dame",
        license="CC BY 4.0",
        authors=["Douglas Thain"],
        peer_reviewed=True,
        size_mb_estimate=5.0
    ),

    # ==================== COMPUTER GRAPHICS ====================
    Book(
        title="Computer Graphics from Scratch",
        url="https://gabrielgambetta.com/computer-graphics-from-scratch/",
        source="Gabriel Gambetta",
        license="CC BY-NC-SA 4.0",  # Will be rejected
        authors=["Gabriel Gambetta"],
        peer_reviewed=False,
        size_mb_estimate=3.0
    ),

    # ==================== FORMAL METHODS ====================
    Book(
        title="Logic and Proof",
        url="https://leanprover.github.io/logic_and_proof/logic_and_proof.pdf",
        source="Carnegie Mellon University",
        license="CC BY 4.0",
        authors=["Jeremy Avigad", "Robert Y. Lewis", "Floris van Doorn"],
        peer_reviewed=True,
        size_mb_estimate=2.0
    ),

    # ==================== INFORMATION THEORY ====================
    Book(
        title="Information Theory, Inference, and Learning Algorithms",
        url="http://www.inference.org.uk/itprnn/book.pdf",
        source="Cambridge University",
        license="Unknown",  # Check
        authors=["David MacKay"],
        peer_reviewed=True,
        size_mb_estimate=15.0
    ),

    # ==================== WEB DEVELOPMENT ====================
    Book(
        title="Eloquent JavaScript (3rd Edition)",
        url="https://eloquentjavascript.net/Eloquent_JavaScript.pdf",
        source="Marijn Haverbeke",
        license="CC BY-NC 3.0",  # Will be rejected
        authors=["Marijn Haverbeke"],
        peer_reviewed=False,
        size_mb_estimate=2.0
    ),

    # ==================== DISTRIBUTED SYSTEMS ====================
    Book(
        title="Distributed Systems for Fun and Profit",
        url="http://book.mixu.net/distsys/single-page.html",  # HTML, check for PDF
        source="Mikito Takada",
        license="CC BY-NC 2.0",  # Will be rejected
        authors=["Mikito Takada"],
        peer_reviewed=False,
        size_mb_estimate=1.0
    ),

    # ==================== QUANTUM COMPUTING ====================
    Book(
        title="Quantum Computing: Lecture Notes",
        url="https://homepages.cwi.nl/~rdewolf/qcnotes.pdf",
        source="CWI Amsterdam",
        license="CC BY-NC-SA 4.0",  # Will be rejected
        authors=["Ronald de Wolf"],
        peer_reviewed=True,
        size_mb_estimate=3.0
    ),
]


class AcademicDownloader:
    """Download academic books with license validation"""

    def __init__(self, output_dir: str = './course_materials'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validator = StrictLicenseValidator()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Academic-Content-Harvester/1.0'
        })

        self.total_downloaded = 0
        self.total_bytes = 0
        self.failed = []
        self.downloaded_books = []

    def download_all(self, books: List[Book], rate_limit: float = 3.0):
        """Download all books with validated licenses"""

        logger.info("="*70)
        logger.info("EXPANDED ACADEMIC CS TEXTBOOK COLLECTION")
        logger.info("Focus: Peer-reviewed, high-quality materials")
        logger.info("="*70)

        # Phase 1: License validation
        logger.info("\n=== Phase 1: License Validation ===\n")
        approved_books = []
        rejected_books = []
        manual_review = []

        for book in books:
            validation = self.validator.validate(book.license, source=book.source)

            if validation.decision == LicenseDecision.ACCEPT:
                approved_books.append(book)
                review_status = "⭐ PEER-REVIEWED" if book.peer_reviewed else ""
                logger.info(f"✓ APPROVED: {book.title} ({book.license}) {review_status}")
            elif validation.decision == LicenseDecision.MANUAL_REVIEW:
                manual_review.append(book)
                logger.info(f"⚠ MANUAL REVIEW: {book.title} ({book.license})")
            else:
                rejected_books.append(book)
                logger.info(f"✗ REJECTED: {book.title} ({book.license}) - {validation.reason}")

        logger.info(f"\n✓ Approved: {len(approved_books)} books")
        logger.info(f"✗ Rejected: {len(rejected_books)} books")
        logger.info(f"⚠ Manual review: {len(manual_review)} books")

        peer_reviewed_count = sum(1 for b in approved_books if b.peer_reviewed)
        logger.info(f"⭐ Peer-reviewed: {peer_reviewed_count}/{len(approved_books)} approved books")

        if len(approved_books) == 0:
            logger.error("No books passed license validation!")
            return

        # Phase 2: Download
        logger.info("\n=== Phase 2: Downloading Approved Books ===\n")

        for i, book in enumerate(approved_books, 1):
            logger.info(f"\n[{i}/{len(approved_books)}] {book.title}")
            logger.info(f"  Authors: {', '.join(book.authors)}")
            logger.info(f"  Source: {book.source}")
            logger.info(f"  License: {book.license}")
            logger.info(f"  Peer-reviewed: {'Yes ⭐' if book.peer_reviewed else 'No'}")
            logger.info(f"  URL: {book.url}")

            # Check if already exists
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', book.title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            filename = f"{book.source}_{safe_title}.pdf"
            filepath = self.output_dir / filename

            if filepath.exists():
                existing_size = filepath.stat().st_size
                logger.info(f"  ⏭ Already exists ({existing_size / 1024 / 1024:.2f} MB), skipping")
                self.total_bytes += existing_size
                self.total_downloaded += 1
                self.downloaded_books.append(book)
                continue

            success = self._download_book(book)

            if success:
                self.total_downloaded += 1
                self.downloaded_books.append(book)
            else:
                self.failed.append(book)

            # Rate limiting (be respectful)
            time.sleep(rate_limit)

        # Summary
        self._print_summary(approved_books, rejected_books, manual_review)

    def _download_book(self, book: Book) -> bool:
        """Download a single book"""
        try:
            # Handle HTML-only sources
            if not book.url.endswith('.pdf'):
                logger.warning(f"  ⚠ URL is not a direct PDF link, skipping: {book.url}")
                return False

            # Download with streaming
            response = self.session.get(book.url, stream=True, timeout=180, allow_redirects=True)
            response.raise_for_status()

            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and 'application/octet-stream' not in content_type.lower():
                logger.warning(f"  ⚠ Response is not a PDF (Content-Type: {content_type}), skipping")
                return False

            # Generate filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', book.title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            filename = f"{book.source}_{safe_title}.pdf"
            filename = re.sub(r'[/\\]', '_', filename)  # Remove any remaining slashes
            filepath = self.output_dir / filename

            # Get size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Download
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Progress
                        if downloaded % (1024 * 1024) < 8192 and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"  Progress: {progress:.1f}%", end='\r', flush=True)

            print()  # Newline

            # Get actual size
            actual_size = filepath.stat().st_size
            self.total_bytes += actual_size

            logger.info(f"  ✓ Downloaded: {actual_size / 1024 / 1024:.2f} MB")
            logger.info(f"  Total: {self.total_bytes / 1024 / 1024:.2f} MB")

            return True

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            return False

    def _print_summary(self, approved_books: List[Book], rejected_books: List[Book], manual_review: List[Book]):
        """Print download summary"""

        peer_reviewed_downloaded = sum(1 for b in self.downloaded_books if b.peer_reviewed)

        report = f"""
{'='*70}
EXPANDED ACADEMIC COLLECTION SUMMARY
{'='*70}
Generated: {datetime.now().isoformat()}

License Validation:
  Total books in catalog: {len(ACADEMIC_BOOKS)}
  ✓ Approved (CC BY, CC BY-SA, CC0, PD): {len(approved_books)}
  ✗ Rejected (NC, ND, or other): {len(rejected_books)}
  ⚠ Manual review needed: {len(manual_review)}

Downloads:
  Successfully downloaded: {self.total_downloaded}
  ⭐ Peer-reviewed: {peer_reviewed_downloaded}/{self.total_downloaded}
  Failed: {len(self.failed)}
  Total size: {self.total_bytes / 1024 / 1024:.2f} MB

Downloaded Books:
"""

        for book in self.downloaded_books:
            peer_review_mark = "⭐" if book.peer_reviewed else ""
            report += f"  ✓ {book.title} ({book.license}) {peer_review_mark}\n"

        if self.failed:
            report += f"\nFailed Downloads:\n"
            for book in self.failed:
                report += f"  ✗ {book.title} - Check URL or format\n"

        if manual_review:
            report += f"\nManual Review Needed:\n"
            for book in manual_review:
                report += f"  ⚠ {book.title} ({book.license}) - Verify license manually\n"

        report += f"\n{'='*70}\n"

        # Save to file
        report_file = self.output_dir / 'expanded_collection_summary.txt'
        with open(report_file, 'w') as f:
            f.write(report)

        # Also save metadata
        metadata = {
            'collection_date': datetime.now().isoformat(),
            'total_books': len(ACADEMIC_BOOKS),
            'approved': len(approved_books),
            'rejected': len(rejected_books),
            'manual_review': len(manual_review),
            'downloaded': self.total_downloaded,
            'peer_reviewed_downloaded': peer_reviewed_downloaded,
            'failed': len(self.failed),
            'total_size_bytes': self.total_bytes,
            'books': [asdict(b) for b in self.downloaded_books]
        }

        metadata_file = self.output_dir / 'expanded_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(report)
        logger.info(f"Summary saved to: {report_file}")
        logger.info(f"Metadata saved to: {metadata_file}")


def main():
    """Main execution"""
    downloader = AcademicDownloader(output_dir='./course_materials')
    downloader.download_all(ACADEMIC_BOOKS, rate_limit=3.0)

    logger.info("\n✓ Collection complete!")
    logger.info(f"Downloaded {downloader.total_downloaded} books ({downloader.total_bytes / 1024 / 1024:.2f} MB)")
    logger.info(f"Peer-reviewed: {sum(1 for b in downloader.downloaded_books if b.peer_reviewed)}")


if __name__ == '__main__':
    main()
