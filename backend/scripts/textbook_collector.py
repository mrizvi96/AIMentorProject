#!/usr/bin/env python3
"""
Automated CC-Licensed Computer Science Textbook Collector

This script automates the discovery, verification, and download of
Creative Commons licensed computer science textbooks from multiple sources.

Supported Licenses:
- Creative Commons Attribution (CC BY)
- Creative Commons Attribution-ShareAlike (CC BY-SA)
- Public Domain (CC0)
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import PyPDF2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('textbook_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Textbook:
    """Represents a textbook with metadata"""
    title: str
    url: str
    license: str
    source: str
    authors: Optional[List[str]] = None
    subject: Optional[str] = None
    year: Optional[int] = None
    file_size: Optional[int] = None
    local_path: Optional[str] = None
    verified: bool = False
    download_date: Optional[str] = None


class LicenseVerifier:
    """Verifies that textbooks have acceptable Creative Commons licenses"""

    ACCEPTABLE_LICENSES = [
        'CC BY',
        'CC BY 4.0',
        'CC BY 3.0',
        'CC BY 2.0',
        'CC BY-SA',
        'CC BY-SA 4.0',
        'CC BY-SA 3.0',
        'CC BY-SA 2.0',
        'CC0',
        'Public Domain',
        'CC-BY',
        'CC-BY-SA',
    ]

    @classmethod
    def is_acceptable(cls, license_text: str) -> bool:
        """Check if license is acceptable for our use case"""
        if not license_text:
            return False

        license_upper = license_text.upper().strip()

        for acceptable in cls.ACCEPTABLE_LICENSES:
            if acceptable.upper() in license_upper:
                # Exclude NC (Non-Commercial) and ND (No Derivatives)
                if 'NC' in license_upper or 'ND' in license_upper:
                    logger.warning(f"License '{license_text}' contains NC or ND restrictions")
                    return False
                return True

        return False

    @classmethod
    def extract_from_pdf(cls, pdf_path: str) -> Optional[str]:
        """Extract license information from PDF metadata"""
        try:
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)

                # Check metadata
                if pdf.metadata:
                    for key in ['License', 'Rights', 'Copyright']:
                        if key in pdf.metadata:
                            return pdf.metadata[key]

                # Check first few pages for license text
                for i in range(min(5, len(pdf.pages))):
                    text = pdf.pages[i].extract_text()
                    if 'creative commons' in text.lower() or 'cc by' in text.lower():
                        # Extract license using regex
                        match = re.search(r'CC\s*BY(?:-SA)?(?:\s*\d\.\d)?', text, re.IGNORECASE)
                        if match:
                            return match.group(0)

        except Exception as e:
            logger.error(f"Error extracting license from PDF {pdf_path}: {e}")

        return None


class TextbookSource:
    """Base class for textbook sources"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Educational-Textbook-Collector/1.0 (Research Project)'
        })

    def discover(self) -> List[Textbook]:
        """Discover textbooks from this source"""
        raise NotImplementedError

    def download(self, textbook: Textbook, output_dir: Path) -> bool:
        """Download a textbook"""
        try:
            logger.info(f"Downloading: {textbook.title} from {textbook.url}")

            response = self.session.get(textbook.url, timeout=60, stream=True)
            response.raise_for_status()

            # Generate filename
            filename = self._sanitize_filename(textbook.title) + '.pdf'
            output_path = output_dir / filename

            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"  Progress: {progress:.1f}%")

            textbook.local_path = str(output_path)
            textbook.file_size = output_path.stat().st_size
            textbook.download_date = datetime.now().isoformat()

            logger.info(f"✓ Downloaded: {filename} ({textbook.file_size / 1024 / 1024:.2f} MB)")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to download {textbook.title}: {e}")
            return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe filesystem storage"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        return filename[:200]


class OpenTextbookLibrarySource(TextbookSource):
    """Source for Open Textbook Library"""

    def __init__(self):
        super().__init__('Open Textbook Library', 'https://open.umn.edu/opentextbooks')

    def discover(self) -> List[Textbook]:
        """Discover CS textbooks from Open Textbook Library"""
        textbooks = []

        # Computer Science subject page
        cs_url = f"{self.base_url}/subjects/computer-science"

        try:
            response = self.session.get(cs_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse textbook listings
            # (Implementation would depend on actual HTML structure)
            # This is a template - actual parsing logic would go here

            logger.info(f"Discovered textbooks from {self.name}")

        except Exception as e:
            logger.error(f"Error discovering from {self.name}: {e}")

        return textbooks


class TextbookCollector:
    """Main orchestrator for textbook collection"""

    def __init__(self, output_dir: str = './cc_textbooks'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.output_dir / 'metadata.json'
        self.textbooks: List[Textbook] = []

        # Initialize sources
        self.sources: List[TextbookSource] = [
            # Add more sources here
        ]

    def load_metadata(self):
        """Load existing metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                self.textbooks = [Textbook(**item) for item in data]
            logger.info(f"Loaded {len(self.textbooks)} existing textbooks from metadata")

    def save_metadata(self):
        """Save metadata to JSON"""
        with open(self.metadata_file, 'w') as f:
            json.dump([asdict(tb) for tb in self.textbooks], f, indent=2)
        logger.info(f"Saved metadata for {len(self.textbooks)} textbooks")

    def discover_all(self):
        """Discover textbooks from all sources"""
        logger.info("Starting discovery from all sources...")

        for source in self.sources:
            logger.info(f"\nDiscovering from: {source.name}")
            discovered = source.discover()

            # Filter by license
            acceptable = [
                tb for tb in discovered
                if LicenseVerifier.is_acceptable(tb.license)
            ]

            logger.info(f"  Found: {len(discovered)} total, {len(acceptable)} with acceptable licenses")
            self.textbooks.extend(acceptable)

        logger.info(f"\n✓ Total textbooks discovered: {len(self.textbooks)}")

    def download_all(self, max_downloads: Optional[int] = None, rate_limit_delay: float = 2.0):
        """Download all textbooks with rate limiting"""
        logger.info("\nStarting downloads...")

        to_download = [tb for tb in self.textbooks if not tb.local_path]

        if max_downloads:
            to_download = to_download[:max_downloads]

        logger.info(f"Downloading {len(to_download)} textbooks")

        for i, textbook in enumerate(to_download, 1):
            logger.info(f"\n[{i}/{len(to_download)}] Processing: {textbook.title}")

            # Find appropriate source
            source = self._find_source(textbook.source)
            if not source:
                logger.warning(f"No source found for {textbook.source}")
                continue

            # Download
            success = source.download(textbook, self.output_dir)

            if success:
                # Verify license in downloaded PDF
                extracted_license = LicenseVerifier.extract_from_pdf(textbook.local_path)
                if extracted_license:
                    textbook.verified = LicenseVerifier.is_acceptable(extracted_license)
                    logger.info(f"  License verified: {extracted_license}")

            # Save metadata after each download
            self.save_metadata()

            # Rate limiting
            time.sleep(rate_limit_delay)

        logger.info(f"\n✓ Download complete: {len([tb for tb in self.textbooks if tb.local_path])} files")

    def _find_source(self, source_name: str) -> Optional[TextbookSource]:
        """Find source by name"""
        for source in self.sources:
            if source.name == source_name:
                return source
        return None

    def generate_report(self) -> str:
        """Generate a summary report"""
        total = len(self.textbooks)
        downloaded = len([tb for tb in self.textbooks if tb.local_path])
        verified = len([tb for tb in self.textbooks if tb.verified])

        total_size = sum(tb.file_size or 0 for tb in self.textbooks if tb.file_size)

        report = f"""
Textbook Collection Report
Generated: {datetime.now().isoformat()}
{'=' * 60}

Statistics:
  Total textbooks: {total}
  Downloaded: {downloaded}
  License verified: {verified}
  Total size: {total_size / 1024 / 1024 / 1024:.2f} GB

By Source:
"""

        # Group by source
        by_source: Dict[str, int] = {}
        for tb in self.textbooks:
            by_source[tb.source] = by_source.get(tb.source, 0) + 1

        for source, count in sorted(by_source.items()):
            report += f"  {source}: {count}\n"

        report += f"\nBy License:\n"
        by_license: Dict[str, int] = {}
        for tb in self.textbooks:
            by_license[tb.license] = by_license.get(tb.license, 0) + 1

        for license, count in sorted(by_license.items()):
            report += f"  {license}: {count}\n"

        return report


def main():
    """Main entry point"""
    collector = TextbookCollector(output_dir='./cc_textbooks')

    # Load existing metadata
    collector.load_metadata()

    # Discover new textbooks
    collector.discover_all()

    # Download (limit to 10 for testing)
    collector.download_all(max_downloads=10, rate_limit_delay=3.0)

    # Generate report
    report = collector.generate_report()
    print(report)

    # Save report
    with open(collector.output_dir / 'collection_report.txt', 'w') as f:
        f.write(report)


if __name__ == '__main__':
    main()
