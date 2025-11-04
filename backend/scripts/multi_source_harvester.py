#!/usr/bin/env python3
"""
Multi-Source CS Content Harvester

Strategy: Use known repositories of CC-licensed books + manual curation
This ensures high quality and verifiable licenses.

Sources:
1. Green Tea Press (Allen Downey) - Multiple CC BY-SA books
2. OpenDSA - CC BY-SA
3. Runestone Academy textbooks - Mix of licenses (filter needed)
4. Free programming books from GitHub awesome list
5. University open textbooks
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
    size_mb_estimate: float = 5.0  # Default estimate


# Curated collection of verified CC-licensed CS books
CURATED_BOOKS = [
    # Allen Downey (Green Tea Press) - All CC BY-SA or CC BY-NC-SA
    Book(
        title="Think Python 2nd Edition",
        url="https://greenteapress.com/thinkpython2/thinkpython2.pdf",
        source="Green Tea Press",
        license="CC BY-NC 3.0",  # Will be rejected - NonCommercial
        authors=["Allen B. Downey"],
        size_mb_estimate=3.0
    ),
    Book(
        title="Think Java 2nd Edition",
        url="https://greenteapress.com/thinkjava7/thinkjava2.pdf",
        source="Green Tea Press",
        license="CC BY-NC-SA 4.0",  # Will be rejected - NonCommercial
        authors=["Allen B. Downey", "Chris Mayfield"],
        size_mb_estimate=4.0
    ),
    Book(
        title="Think Bayes 2nd Edition",
        url="https://allendowney.github.io/ThinkBayes2/ThinkBayes2.pdf",
        source="Green Tea Press",
        license="CC BY-NC-SA 4.0",  # Will be rejected
        authors=["Allen B. Downey"],
        size_mb_estimate=5.0
    ),

    # Open Data Structures
    Book(
        title="Open Data Structures (Python Edition)",
        url="http://opendatastructures.org/ods-python.pdf",
        source="opendatastructures.org",
        license="CC BY 2.5",
        authors=["Pat Morin"],
        size_mb_estimate=1.5
    ),
    Book(
        title="Open Data Structures (Java Edition)",
        url="http://opendatastructures.org/ods-java.pdf",
        source="opendatastructures.org",
        license="CC BY 2.5",
        authors=["Pat Morin"],
        size_mb_estimate=1.5
    ),
    Book(
        title="Open Data Structures (C++ Edition)",
        url="http://opendatastructures.org/ods-cpp.pdf",
        source="opendatastructures.org",
        license="CC BY 2.5",
        authors=["Pat Morin"],
        size_mb_estimate=1.5
    ),

    # Structure and Interpretation of Computer Programs
    Book(
        title="SICP - JavaScript Edition",
        url="https://sourceacademy.org/sicpjs.pdf",
        source="MIT Press / Source Academy",
        license="CC BY-SA 4.0",
        authors=["Harold Abelson", "Gerald Jay Sussman"],
        size_mb_estimate=5.0
    ),

    # Mathematics for Computer Science
    Book(
        title="Mathematics for Computer Science",
        url="https://courses.csail.mit.edu/6.042/spring18/mcs.pdf",
        source="MIT OpenCourseWare",
        license="CC BY-SA 3.0",
        authors=["Eric Lehman", "F. Thomson Leighton", "Albert R. Meyer"],
        size_mb_estimate=6.0
    ),

    # Algorithms textbooks
    Book(
        title="Algorithms by Jeff Erickson",
        url="http://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf",
        source="University of Illinois",
        license="CC BY 4.0",
        authors=["Jeff Erickson"],
        size_mb_estimate=8.0
    ),

    # OpenStax - College-level textbooks (all CC BY)
    Book(
        title="Python Programming",
        url="https://assets.openstax.org/oscms-prodcms/media/documents/PythonProgramming-WEB.pdf",
        source="OpenStax",
        license="CC BY 4.0",
        authors=["OpenStax"],
        size_mb_estimate=15.0
    ),

    # Computer Systems: A Programmer's Perspective (check license first)
    # Skipping - not open license

    # Operating Systems: Three Easy Pieces
    Book(
        title="Operating Systems: Three Easy Pieces",
        url="https://pages.cs.wisc.edu/~remzi/OSTEP/ostep-1.01.pdf",
        source="University of Wisconsin",
        license="CC BY-NC-SA 4.0",  # Will be rejected - NonCommercial
        authors=["Remzi H. Arpaci-Dusseau", "Andrea C. Arpaci-Dusseau"],
        size_mb_estimate=2.5
    ),

    # Dive Into Python 3
    Book(
        title="Dive Into Python 3",
        url="https://diveintopython3.problemsolving.io/d/diveintopython3.pdf",
        source="Mark Pilgrim",
        license="CC BY-SA 3.0",
        authors=["Mark Pilgrim"],
        size_mb_estimate=2.0
    ),

    # The Linux Command Line
    Book(
        title="The Linux Command Line",
        url="https://sourceforge.net/projects/linuxcommand/files/TLCL/19.01/TLCL-19.01.pdf/download",
        source="LinuxCommand.org",
        license="CC BY-NC-ND 4.0",  # Will be rejected - NC and ND
        authors=["William E. Shotts, Jr."],
        size_mb_estimate=2.5
    ),

    # Automate the Boring Stuff with Python
    Book(
        title="Automate the Boring Stuff with Python",
        url="https://automatetheboringstuff.com/2e/Automate_the_Boring_Stuff_with_Python_2e.pdf",
        source="No Starch Press",
        license="CC BY-NC-SA 3.0",  # Will be rejected - NonCommercial
        authors=["Al Sweigart"],
        size_mb_estimate=7.0
    ),

    # Introduction to Theoretical Computer Science
    Book(
        title="Introduction to Theoretical Computer Science",
        url="https://files.boazbarak.org/introtcs/lnotes_book.pdf",
        source="Boaz Barak",
        license="CC BY-SA 4.0",
        authors=["Boaz Barak"],
        size_mb_estimate=10.0
    ),

    # Crafting Interpreters
    Book(
        title="Crafting Interpreters",
        url="https://github.com/munificent/craftinginterpreters/releases/download/1.0.3/book.pdf",
        source="Robert Nystrom",
        license="CC BY-NC-ND 4.0",  # Will be rejected - NC and ND
        authors=["Robert Nystrom"],
        size_mb_estimate=4.0
    ),
]


class CuratedBookDownloader:
    """Download books from curated list with license validation"""

    def __init__(self, output_dir: str = './cs_materials_bulk'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validator = StrictLicenseValidator()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Educational-Content-Harvester/1.0 (Research Project)'
        })

        self.total_downloaded = 0
        self.total_bytes = 0
        self.target_bytes = 10 * 1024 * 1024 * 1024  # 10 GB
        self.failed = []
        self.downloaded_books = []

    def download_all(self, books: List[Book], rate_limit: float = 2.0):
        """Download all books with validated licenses"""

        logger.info("="*70)
        logger.info("CURATED CS TEXTBOOK COLLECTION")
        logger.info(f"Target: {self.target_bytes / 1024 / 1024 / 1024:.1f} GB")
        logger.info("="*70)

        # First pass: validate licenses
        logger.info("\n=== Phase 1: License Validation ===\n")
        approved_books = []
        rejected_books = []

        for book in books:
            validation = self.validator.validate(book.license, source=book.source)

            if validation.decision == LicenseDecision.ACCEPT:
                approved_books.append(book)
                logger.info(f"✓ APPROVED: {book.title} ({book.license})")
            else:
                rejected_books.append(book)
                logger.info(f"✗ REJECTED: {book.title} ({book.license}) - {validation.reason}")

        logger.info(f"\nApproved: {len(approved_books)} books")
        logger.info(f"Rejected: {len(rejected_books)} books")

        if len(approved_books) == 0:
            logger.error("No books passed license validation!")
            return

        # Second pass: download approved books
        logger.info("\n=== Phase 2: Downloading Approved Books ===\n")

        for i, book in enumerate(approved_books, 1):
            if self.total_bytes >= self.target_bytes:
                logger.info(f"\n✓ TARGET REACHED: {self.total_bytes / 1024 / 1024 / 1024:.2f} GB")
                break

            logger.info(f"\n[{i}/{len(approved_books)}] {book.title}")
            logger.info(f"  Authors: {', '.join(book.authors)}")
            logger.info(f"  Source: {book.source}")
            logger.info(f"  License: {book.license}")
            logger.info(f"  URL: {book.url}")

            success = self._download_book(book)

            if success:
                self.total_downloaded += 1
                self.downloaded_books.append(book)
            else:
                self.failed.append(book)

            # Rate limiting
            time.sleep(rate_limit)

        # Summary
        self._print_summary(approved_books, rejected_books)

    def _download_book(self, book: Book) -> bool:
        """Download a single book"""
        try:
            # Download with streaming
            response = self.session.get(book.url, stream=True, timeout=120, allow_redirects=True)
            response.raise_for_status()

            # Generate filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', book.title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            filename = f"{book.source}_{safe_title}.pdf"
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
            logger.info(f"  Total: {self.total_bytes / 1024 / 1024 / 1024:.2f} GB / {self.target_bytes / 1024 / 1024 / 1024:.1f} GB")
            logger.info(f"  Progress: {(self.total_bytes / self.target_bytes) * 100:.1f}%")

            return True

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            return False

    def _print_summary(self, approved_books: List[Book], rejected_books: List[Book]):
        """Print download summary"""

        report = f"""
{'='*70}
DOWNLOAD SUMMARY
{'='*70}
Generated: {datetime.now().isoformat()}

License Validation:
  Total books in catalog: {len(CURATED_BOOKS)}
  Approved (CC BY, CC BY-SA, CC0, PD): {len(approved_books)}
  Rejected (NC, ND, or other): {len(rejected_books)}

Downloads:
  Successfully downloaded: {self.total_downloaded}
  Failed: {len(self.failed)}
  Total size: {self.total_bytes / 1024 / 1024 / 1024:.2f} GB
  Target: {self.target_bytes / 1024 / 1024 / 1024:.1f} GB
  Progress: {(self.total_bytes / self.target_bytes) * 100:.1f}%

Downloaded Books:
"""

        for book in self.downloaded_books:
            report += f"  ✓ {book.title} ({book.license})\n"

        if self.failed:
            report += f"\nFailed Downloads:\n"
            for book in self.failed:
                report += f"  ✗ {book.title}\n"

        report += f"\n{'='*70}\n"

        # Save to file
        report_file = self.output_dir / 'curated_collection_summary.txt'
        with open(report_file, 'w') as f:
            f.write(report)

        # Also save metadata
        metadata = {
            'collection_date': datetime.now().isoformat(),
            'total_books': len(CURATED_BOOKS),
            'approved': len(approved_books),
            'rejected': len(rejected_books),
            'downloaded': self.total_downloaded,
            'failed': len(self.failed),
            'total_size_bytes': self.total_bytes,
            'books': [asdict(b) for b in self.downloaded_books]
        }

        metadata_file = self.output_dir / 'curated_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(report)
        logger.info(f"Summary saved to: {report_file}")
        logger.info(f"Metadata saved to: {metadata_file}")


def main():
    """Main execution"""
    downloader = CuratedBookDownloader(output_dir='./cs_materials_bulk')
    downloader.download_all(CURATED_BOOKS, rate_limit=2.0)

    logger.info("\n✓ Collection complete!")
    logger.info(f"Downloaded {downloader.total_downloaded} books ({downloader.total_bytes / 1024 / 1024 / 1024:.2f} GB)")

    if downloader.total_bytes < downloader.target_bytes:
        remaining = (downloader.target_bytes - downloader.total_bytes) / 1024 / 1024 / 1024
        logger.warning(f"\n⚠ Only reached {downloader.total_bytes / 1024 / 1024 / 1024:.2f} GB of {downloader.target_bytes / 1024 / 1024 / 1024:.1f} GB target")
        logger.warning(f"Need {remaining:.2f} GB more to reach 10GB goal")
        logger.warning("Consider:")
        logger.warning("  1. Adding more curated books to CURATED_BOOKS list")
        logger.warning("  2. Including larger textbooks and reference materials")
        logger.warning("  3. Adding technical reports and papers")


if __name__ == '__main__':
    main()
