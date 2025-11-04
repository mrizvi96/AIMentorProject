#!/usr/bin/env python3
"""
Additional High-Quality CS Sources with Direct PDF Links
Focus: Finding more peer-reviewed materials with verified licenses
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import List
from dataclasses import dataclass, asdict
from datetime import datetime

import requests

from license_validator import StrictLicenseValidator, LicenseDecision

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Book:
    title: str
    url: str
    source: str
    license: str
    authors: List[str]
    peer_reviewed: bool = True
    size_mb_estimate: float = 5.0


# Additional verified sources with direct PDF links
ADDITIONAL_BOOKS = [
    # Computer Networks - Fixed URL
    Book(
        title="Computer Networks: A Systems Approach (Full Book)",
        url="https://github.com/SystemsApproach/book/releases/download/v6.2/book.pdf",
        source="Systems Approach",
        license="CC BY 4.0",
        authors=["Larry Peterson", "Bruce Davie"],
        peer_reviewed=True,
        size_mb_estimate=8.0
    ),

    # Logic and Proof - Fixed URL
    Book(
        title="Logic and Proof",
        url="https://leanprover.github.io/logic_and_proof/logic_and_proof.pdf",  # Try alternate
        source="Carnegie Mellon University",
        license="CC BY 4.0",
        authors=["Jeremy Avigad", "Robert Y. Lewis", "Floris van Doorn"],
        peer_reviewed=True,
        size_mb_estimate=2.0
    ),

    # OpenIntro Statistics (useful for data science/ML)
    Book(
        title="OpenIntro Statistics (4th Edition)",
        url="https://github.com/OpenIntroStat/openintro-statistics/releases/download/os4_tablet/os4.pdf",
        source="OpenIntro",
        license="CC BY-SA 3.0",
        authors=["David Diez", "Mine Çetinkaya-Rundel", "Christopher Barr"],
        peer_reviewed=True,
        size_mb_estimate=12.0
    ),

    # Information Theory
    Book(
        title="Information Theory, Inference, and Learning Algorithms",
        url="http://www.inference.org.uk/itprnn/book.pdf",
        source="David MacKay / Cambridge",
        license="Unknown",  # Check PDF itself
        authors=["David MacKay"],
        peer_reviewed=True,
        size_mb_estimate=15.0
    ),

    # Probabilistic Programming & Bayesian Methods
    Book(
        title="Probabilistic Programming & Bayesian Methods for Hackers",
        url="https://github.com/CamDavidsonPilon/Probabilistic-Programming-and-Bayesian-Methods-for-Hackers/raw/master/Probabilistic_Programming_and_Bayesian_Methods_for_Hackers.pdf",
        source="Cam Davidson-Pilon",
        license="MIT License",
        authors=["Cameron Davidson-Pilon"],
        peer_reviewed=False,
        size_mb_estimate=8.0
    ),

    # Software Foundations (Coq textbook)
    Book(
        title="Software Foundations - Logical Foundations",
        url="https://softwarefoundations.cis.upenn.edu/lf-current/lf.pdf",
        source="University of Pennsylvania",
        license="CC BY-SA 4.0",
        authors=["Benjamin Pierce", "et al"],
        peer_reviewed=True,
        size_mb_estimate=3.0
    ),

    # Software Foundations - Programming Language Foundations
    Book(
        title="Software Foundations - Programming Language Foundations",
        url="https://softwarefoundations.cis.upenn.edu/plf-current/plf.pdf",
        source="University of Pennsylvania",
        license="CC BY-SA 4.0",
        authors=["Benjamin Pierce", "et al"],
        peer_reviewed=True,
        size_mb_estimate=3.0
    ),

    # Computational and Inferential Thinking
    Book(
        title="Computational and Inferential Thinking",
        url="https://inferentialthinking.com/chapters/Computational_and_Inferential_Thinking.pdf",
        source="UC Berkeley",
        license="CC BY-NC-ND 4.0",  # Will be rejected - NC and ND
        authors=["Ani Adhikari", "John DeNero"],
        peer_reviewed=True,
        size_mb_estimate=10.0
    ),

    # Introduction to Computer Networks
    Book(
        title="An Introduction to Computer Networks",
        url="http://intronetworks.cs.luc.edu/current2/ComputerNetworks.pdf",
        source="Loyola University Chicago",
        license="CC BY-NC-ND 4.0",  # Will be rejected
        authors=["Peter Dordal"],
        peer_reviewed=True,
        size_mb_estimate=12.0
    ),

    # Category Theory for Programmers
    Book(
        title="Category Theory for Programmers",
        url="https://github.com/hmemcpy/milewski-ctfp-pdf/releases/download/v1.3.0/category-theory-for-programmers.pdf",
        source="Bartosz Milewski",
        license="CC BY-SA 4.0",
        authors=["Bartosz Milewski"],
        peer_reviewed=False,
        size_mb_estimate=5.0
    ),

    # Homotopy Type Theory
    Book(
        title="Homotopy Type Theory: Univalent Foundations of Mathematics",
        url="https://homotopytypetheory.org/book/hott-uf-agda-0-1.pdf",  # Check if still available
        source="Homotopy Type Theory",
        license="CC BY-SA 3.0",
        authors=["Univalent Foundations Program"],
        peer_reviewed=True,
        size_mb_estimate=3.0
    ),

    # Introduction to High-Performance Scientific Computing
    Book(
        title="Introduction to High-Performance Scientific Computing",
        url="https://web.corral.tacc.utexas.edu/CompEdu/pdf/istc/EijkhoutIntroToHPC.pdf",
        source="TACC / Victor Eijkhout",
        license="CC BY 3.0",
        authors=["Victor Eijkhout"],
        peer_reviewed=True,
        size_mb_estimate=15.0
    ),

    # The Art of Unix Programming (if available)
    Book(
        title="Think OS: A Brief Introduction to Operating Systems",
        url="https://greenteapress.com/thinkos/thinkos.pdf",
        source="Green Tea Press",
        license="CC BY-NC 3.0",  # Will be rejected
        authors=["Allen B. Downey"],
        peer_reviewed=False,
        size_mb_estimate=2.0
    ),

    # Real World OCaml
    Book(
        title="Real World OCaml (2nd Edition)",
        url="https://dev.realworldocaml.org/book.pdf",
        source="Jane Street / O'Reilly",
        license="CC BY-NC-ND 4.0",  # Will be rejected
        authors=["Yaron Minsky", "Anil Madhavapeddy", "Jason Hickey"],
        peer_reviewed=True,
        size_mb_estimate=5.0
    ),

    # Introduction to Probability for Data Science
    Book(
        title="Introduction to Probability for Data Science",
        url="https://probability4datascience.com/book.pdf",
        source="Stanley H. Chan",
        license="CC BY-NC-SA 4.0",  # Will be rejected
        authors=["Stanley H. Chan"],
        peer_reviewed=True,
        size_mb_estimate=8.0
    ),
]


class AdditionalDownloader:
    """Download additional books"""

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
        logger.info("ADDITIONAL ACADEMIC SOURCES")
        logger.info("="*70)

        # Phase 1: License validation
        logger.info("\n=== License Validation ===\n")
        approved_books = []
        rejected_books = []

        for book in books:
            validation = self.validator.validate(book.license, source=book.source)

            if validation.decision == LicenseDecision.ACCEPT:
                approved_books.append(book)
                logger.info(f"✓ {book.title} ({book.license})")
            else:
                rejected_books.append(book)
                logger.info(f"✗ {book.title} ({book.license}) - {validation.reason}")

        logger.info(f"\n✓ Approved: {len(approved_books)}")
        logger.info(f"✗ Rejected: {len(rejected_books)}")

        if len(approved_books) == 0:
            logger.warning("No additional books passed validation")
            return

        # Phase 2: Download
        logger.info("\n=== Downloading ===\n")

        for i, book in enumerate(approved_books, 1):
            logger.info(f"\n[{i}/{len(approved_books)}] {book.title}")
            logger.info(f"  URL: {book.url}")

            # Check if already exists
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', book.title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            filename = f"{book.source}_{safe_title}.pdf"
            filename = re.sub(r'[/\\]', '_', filename)
            filepath = self.output_dir / filename

            if filepath.exists():
                size = filepath.stat().st_size
                logger.info(f"  ⏭ Already exists ({size / 1024 / 1024:.2f} MB)")
                self.total_bytes += size
                self.total_downloaded += 1
                self.downloaded_books.append(book)
                continue

            success = self._download_book(book, filepath)

            if success:
                self.total_downloaded += 1
                self.downloaded_books.append(book)
            else:
                self.failed.append(book)

            time.sleep(rate_limit)

        # Summary
        logger.info(f"\n{'='*70}")
        logger.info(f"Downloaded: {self.total_downloaded} books ({self.total_bytes / 1024 / 1024:.2f} MB)")
        logger.info(f"Failed: {len(self.failed)}")
        logger.info(f"{'='*70}")

    def _download_book(self, book: Book, filepath: Path) -> bool:
        """Download a single book"""
        try:
            response = self.session.get(book.url, stream=True, timeout=180, allow_redirects=True)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and 'application/octet-stream' not in content_type.lower():
                logger.warning(f"  ⚠ Not a PDF (Content-Type: {content_type})")
                return False

            # Download
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if downloaded % (1024 * 1024) < 8192 and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"  Progress: {progress:.1f}%", end='\r', flush=True)

            print()

            actual_size = filepath.stat().st_size
            self.total_bytes += actual_size

            logger.info(f"  ✓ Downloaded: {actual_size / 1024 / 1024:.2f} MB")
            return True

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            return False


def main():
    """Main execution"""
    downloader = AdditionalDownloader(output_dir='./course_materials')
    downloader.download_all(ADDITIONAL_BOOKS, rate_limit=3.0)


if __name__ == '__main__':
    main()
