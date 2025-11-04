#!/usr/bin/env python3
"""
Practical CS Content Harvester - Focus on high-yield CC-licensed sources

Strategy:
1. Internet Archive: Large collection of CC/Public Domain CS books
2. OpenStax: High-quality CC BY textbooks
3. Open Textbook Library: Curated open textbooks
4. Project Gutenberg: Public domain technical books
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from license_validator import StrictLicenseValidator, ValidationResult, LicenseDecision

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContentSource:
    """Represents a content source"""
    title: str
    url: str
    source_institution: str
    content_type: str
    license: str
    license_verified: bool
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    file_size_bytes: Optional[int] = None
    download_status: str = "pending"
    local_path: Optional[str] = None
    download_date: Optional[str] = None


class InternetArchiveHarvester:
    """
    Harvest from Internet Archive - huge collection of public domain
    and CC-licensed materials.
    """

    def __init__(self):
        self.validator = StrictLicenseValidator()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Educational-Content-Harvester/1.0 (Research Project)'
        })
        self.api_base = "https://archive.org/advancedsearch.php"

    def harvest_cs_books(self, max_items: int = 500) -> List[ContentSource]:
        """
        Harvest CS books from Internet Archive.

        Focus on:
        - Subject: Computer Science OR Computers
        - License: Creative Commons OR Public Domain
        """
        sources = []

        try:
            # Search query for CS books with open licenses
            query = '(subject:"computer science" OR subject:"computers" OR subject:"programming") AND (licenseurl:"creativecommons.org" OR licenseurl:"publicdomain")'

            params = {
                'q': query,
                'fl[]': ['identifier', 'title', 'creator', 'licenseurl', 'downloads', 'format'],
                'rows': max_items,
                'page': 1,
                'output': 'json',
                'sort[]': 'downloads desc'  # Most popular first
            }

            logger.info(f"Querying Internet Archive: {query[:80]}...")
            response = self.session.get(self.api_base, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            docs = data.get('response', {}).get('docs', [])

            logger.info(f"Found {len(docs)} potential items from Internet Archive")

            for doc in docs:
                identifier = doc.get('identifier')
                title = doc.get('title', 'Unknown')
                creators = doc.get('creator', [])
                if isinstance(creators, str):
                    creators = [creators]

                license_url = doc.get('licenseurl', '')
                formats = doc.get('format', [])

                # Check if PDF is available
                if 'PDF' not in formats and 'Text PDF' not in formats:
                    continue

                # Extract license from URL
                license_text = self._extract_license_from_url(license_url)

                # Validate license
                validation = self.validator.validate(license_text, source='Internet Archive')

                if validation.decision == LicenseDecision.ACCEPT:
                    # Construct download URL
                    pdf_url = f"https://archive.org/download/{identifier}/{identifier}.pdf"

                    source = ContentSource(
                        title=title if isinstance(title, str) else title[0],
                        url=pdf_url,
                        source_institution='Internet Archive',
                        content_type='textbook',
                        license=license_text,
                        license_verified=True,
                        authors=creators
                    )
                    sources.append(source)
                    logger.info(f"✓ Found: {title[:60]}")

                # Rate limiting
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error harvesting Internet Archive: {e}")

        return sources

    def _extract_license_from_url(self, license_url: str) -> str:
        """Extract license type from Creative Commons URL"""
        if not license_url:
            return "Public Domain"

        # Parse CC license from URL
        # e.g., https://creativecommons.org/licenses/by-sa/4.0/
        match = re.search(r'creativecommons\.org/licenses/([^/]+)/([^/]+)', license_url)
        if match:
            license_type = match.group(1).upper()
            version = match.group(2)
            return f"CC {license_type} {version}"

        if 'publicdomain' in license_url.lower():
            return "Public Domain"

        return license_url


class OpenTextbookLibraryHarvester:
    """
    Harvest from Open Textbook Library (University of Minnesota)
    Curated collection of peer-reviewed open textbooks
    """

    def __init__(self):
        self.validator = StrictLicenseValidator()
        self.session = requests.Session()
        self.base_url = "https://open.umn.edu/opentextbooks"

    def harvest_cs_books(self) -> List[ContentSource]:
        """
        Harvest CS textbooks from Open Textbook Library

        Note: This requires scraping their website or using their API if available
        For now, we'll return manually curated known-good sources
        """
        sources = []

        # Known CC BY or CC BY-SA books from Open Textbook Library
        known_books = [
            {
                'title': 'Think Python 2e',
                'url': 'https://greenteapress.com/thinkpython2/thinkpython2.pdf',
                'license': 'CC BY-NC 3.0',  # Will be rejected
                'authors': ['Allen Downey']
            },
            {
                'title': 'Open Data Structures',
                'url': 'http://opendatastructures.org/ods-python.pdf',
                'license': 'CC BY 2.5',
                'authors': ['Pat Morin']
            }
        ]

        for book in known_books:
            validation = self.validator.validate(book['license'], source='Open Textbook Library')

            if validation.decision == LicenseDecision.ACCEPT:
                source = ContentSource(
                    title=book['title'],
                    url=book['url'],
                    source_institution='Open Textbook Library',
                    content_type='textbook',
                    license=book['license'],
                    license_verified=True,
                    authors=book.get('authors', [])
                )
                sources.append(source)
                logger.info(f"✓ Added: {book['title']}")

        return sources


class BulkDownloader:
    """Downloads content sources with progress tracking and size limits"""

    def __init__(self, output_dir: str = './cs_materials_bulk'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.output_dir / 'bulk_metadata.json'
        self.total_downloaded_bytes = 0
        self.target_bytes = 10 * 1024 * 1024 * 1024  # 10 GB
        self.successful_downloads = 0
        self.failed_downloads = 0

    def download_batch(self, sources: List[ContentSource], rate_limit_seconds: float = 2.0):
        """Download a batch of content sources"""

        logger.info(f"\n{'='*70}")
        logger.info(f"Starting batch download of {len(sources)} sources")
        logger.info(f"Target: {self.target_bytes / 1024 / 1024 / 1024:.1f} GB")
        logger.info(f"{'='*70}\n")

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Educational-Content-Harvester/1.0 (Research Project)'
        })

        for i, source in enumerate(sources, 1):
            if self.total_downloaded_bytes >= self.target_bytes:
                logger.info(f"\n{'='*70}")
                logger.info(f"✓ TARGET REACHED: {self.total_downloaded_bytes / 1024 / 1024 / 1024:.2f} GB")
                logger.info(f"{'='*70}\n")
                break

            logger.info(f"\n[{i}/{len(sources)}] Downloading: {source.title[:70]}")
            logger.info(f"  Source: {source.source_institution}")
            logger.info(f"  License: {source.license}")
            logger.info(f"  URL: {source.url}")

            try:
                # Download with streaming
                response = session.get(source.url, stream=True, timeout=120)
                response.raise_for_status()

                # Generate safe filename
                filename = self._generate_filename(source)
                filepath = self.output_dir / filename

                # Get total size
                total_size = int(response.headers.get('content-length', 0))

                # Download with progress
                downloaded = 0
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Progress every 1MB
                            if downloaded % (1024 * 1024) < 8192 and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                size_mb = downloaded / 1024 / 1024
                                print(f"  Progress: {progress:.1f}% ({size_mb:.1f} MB)", end='\r', flush=True)

                print()  # New line after progress

                # Update source
                actual_size = filepath.stat().st_size
                source.local_path = str(filepath)
                source.file_size_bytes = actual_size
                source.download_status = "completed"
                source.download_date = datetime.now().isoformat()

                self.total_downloaded_bytes += actual_size
                self.successful_downloads += 1

                logger.info(f"  ✓ Downloaded: {actual_size / 1024 / 1024:.2f} MB")
                logger.info(f"  Total so far: {self.total_downloaded_bytes / 1024 / 1024 / 1024:.2f} GB / {self.target_bytes / 1024 / 1024 / 1024:.1f} GB")
                logger.info(f"  Progress: {(self.total_downloaded_bytes / self.target_bytes) * 100:.1f}%")

            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                source.download_status = "failed"
                self.failed_downloads += 1

            # Save metadata after each download
            self.save_metadata(sources)

            # Rate limiting
            time.sleep(rate_limit_seconds)

        # Generate summary
        self._generate_summary_report(sources)

    def _generate_filename(self, source: ContentSource) -> str:
        """Generate safe filename from source"""
        # Sanitize title
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', source.title)
        safe_title = safe_title[:100]  # Limit length

        # Remove extra spaces
        safe_title = re.sub(r'\s+', '_', safe_title)

        filename = f"{source.source_institution}_{safe_title}.pdf"
        return filename

    def save_metadata(self, sources: List[ContentSource]):
        """Save metadata JSON"""
        with open(self.metadata_file, 'w') as f:
            json.dump([asdict(s) for s in sources], f, indent=2)

    def _generate_summary_report(self, sources: List[ContentSource]):
        """Generate download summary"""
        completed = [s for s in sources if s.download_status == "completed"]
        failed = [s for s in sources if s.download_status == "failed"]

        report = f"""
{'='*70}
Bulk Download Summary
{'='*70}
Generated: {datetime.now().isoformat()}

Statistics:
  Total sources discovered: {len(sources)}
  Successfully downloaded: {len(completed)}
  Failed: {len(failed)}
  Total size: {self.total_downloaded_bytes / 1024 / 1024 / 1024:.2f} GB
  Target size: {self.target_bytes / 1024 / 1024 / 1024:.1f} GB
  Progress: {(self.total_downloaded_bytes / self.target_bytes) * 100:.1f}%

By Institution:
"""

        # Group by institution
        by_institution = {}
        by_institution_size = {}
        for s in completed:
            by_institution[s.source_institution] = by_institution.get(s.source_institution, 0) + 1
            by_institution_size[s.source_institution] = by_institution_size.get(s.source_institution, 0) + s.file_size_bytes

        for inst, count in sorted(by_institution.items()):
            size_gb = by_institution_size[inst] / 1024 / 1024 / 1024
            report += f"  {inst}: {count} items ({size_gb:.2f} GB)\n"

        report += "\nBy License:\n"
        by_license = {}
        for s in completed:
            by_license[s.license] = by_license.get(s.license, 0) + 1

        for lic, count in sorted(by_license.items()):
            report += f"  {lic}: {count}\n"

        if failed:
            report += f"\nFailed Downloads ({len(failed)}):\n"
            for s in failed[:10]:  # Show first 10
                report += f"  - {s.title[:60]}\n"

        report += f"\n{'='*70}\n"

        # Save report
        report_file = self.output_dir / 'download_summary.txt'
        with open(report_file, 'w') as f:
            f.write(report)

        print(report)


def main():
    """Main execution"""

    # Initialize harvesters
    ia_harvester = InternetArchiveHarvester()
    otl_harvester = OpenTextbookLibraryHarvester()

    # Collect sources
    all_sources = []

    logger.info("="*70)
    logger.info("PRACTICAL CS CONTENT HARVESTER")
    logger.info("Target: 10 GB of CC-licensed materials")
    logger.info("="*70)

    logger.info("\n=== Phase 1: Discovering Content ===\n")

    # Internet Archive (priority 1 - largest source)
    logger.info("Harvesting from Internet Archive...")
    ia_sources = ia_harvester.harvest_cs_books(max_items=500)
    all_sources.extend(ia_sources)
    logger.info(f"Found {len(ia_sources)} items from Internet Archive")

    # Open Textbook Library
    logger.info("\nHarvesting from Open Textbook Library...")
    otl_sources = otl_harvester.harvest_cs_books()
    all_sources.extend(otl_sources)
    logger.info(f"Found {len(otl_sources)} items from Open Textbook Library")

    logger.info(f"\nTotal sources discovered: {len(all_sources)}")

    if len(all_sources) == 0:
        logger.error("No sources found! Check API endpoints and queries.")
        return

    # Download
    logger.info("\n=== Phase 2: Downloading Content ===\n")
    downloader = BulkDownloader(output_dir='./cs_materials_bulk')
    downloader.download_batch(all_sources, rate_limit_seconds=2.0)

    logger.info("\n✓ Collection complete!")
    logger.info(f"Check results in: {downloader.output_dir}")


if __name__ == '__main__':
    main()
