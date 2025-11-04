#!/usr/bin/env python3
"""
Bulk CS Content Harvester - Target: 10GB+ of CC-licensed materials

Focuses on:
1. University lecture notes (MIT, Stanford, Berkeley, CMU, etc.)
2. Open textbooks
3. Technical reports
4. Course materials from top CS programs

All content must have CC BY, CC BY-SA, CC0, or Public Domain licenses.
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

logger = logging.getLogger(__name__)


@dataclass
class ContentSource:
    """Represents a content source (textbook, lecture notes, etc.)"""
    title: str
    url: str
    source_institution: str
    content_type: str  # 'textbook', 'lecture_notes', 'technical_report'
    license: str
    license_verified: bool
    authors: Optional[List[str]] = None
    course_code: Optional[str] = None
    year: Optional[int] = None
    file_size_bytes: Optional[int] = None
    download_status: str = "pending"  # pending, downloading, completed, failed
    local_path: Optional[str] = None
    download_date: Optional[str] = None


class UniversityLectureNotesHarvester:
    """
    Harvest lecture notes from top CS universities that allow reuse.

    Target Universities:
    - MIT OpenCourseWare (CC BY-NC-SA - check individual courses)
    - Stanford CS Course Materials
    - UC Berkeley CS
    - Carnegie Mellon University
    - University of Washington
    - Cornell University
    """

    def __init__(self):
        self.validator = StrictLicenseValidator()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Educational-Content-Harvester/1.0 (Research Project)'
        })

    def harvest_mit_ocw(self) -> List[ContentSource]:
        """
        Harvest from MIT OpenCourseWare.

        NOTE: Most MIT OCW is CC BY-NC-SA (NonCommercial).
        However, some newer courses are CC BY-SA or CC BY.
        We must check each course individually.
        """
        sources = []

        # MIT OCW computer science courses
        mit_cs_base = "https://ocw.mit.edu/search/"

        try:
            # Search for computer science courses
            params = {
                'q': 'computer science',
                'f': 'https://ocw.mit.edu/course-lists/computer-science/'
            }

            # NOTE: This is a template. Actual implementation would:
            # 1. Query MIT OCW API or scrape course listings
            # 2. For each course, check license
            # 3. Download PDF materials from courses with acceptable licenses
            # 4. Skip CC BY-NC-SA content (most of MIT OCW)

            logger.info("Checking MIT OCW for CC BY or CC BY-SA courses...")

            # Example courses known to be CC BY-SA (would be populated from API/scraping):
            known_acceptable_courses = [
                {
                    'course_num': '6.0001',
                    'title': 'Introduction to Computer Science and Programming in Python',
                    'license': 'CC BY-NC-SA 4.0',  # REJECT
                    'materials_url': 'https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/'
                }
            ]

            for course in known_acceptable_courses:
                validation = self.validator.validate(course['license'], source='MIT OCW')
                if validation.decision == LicenseDecision.ACCEPT:
                    # Would download course materials here
                    logger.info(f"Found acceptable MIT course: {course['course_num']}")
                else:
                    logger.info(f"Skipping MIT course {course['course_num']}: {validation.reason}")

        except Exception as e:
            logger.error(f"Error harvesting MIT OCW: {e}")

        return sources

    def harvest_arxiv_cs(self, max_papers: int = 100) -> List[ContentSource]:
        """
        Harvest CS papers from arXiv with CC licenses.

        arXiv has API: http://export.arxiv.org/api/query
        Most papers are arXiv.org perpetual license, but some are CC BY.
        """
        sources = []

        arxiv_api = "http://export.arxiv.org/api/query"

        try:
            # Categories for Computer Science
            cs_categories = [
                'cs.AI',  # Artificial Intelligence
                'cs.DS',  # Data Structures and Algorithms
                'cs.LG',  # Machine Learning
                'cs.PL',  # Programming Languages
                'cs.SE',  # Software Engineering
                'cs.DB',  # Databases
                'cs.DC',  # Distributed Computing
                'cs.CR',  # Cryptography
            ]

            for category in cs_categories:
                params = {
                    'search_query': f'cat:{category}',
                    'start': 0,
                    'max_results': max_papers,
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }

                response = self.session.get(arxiv_api, params=params, timeout=30)
                response.raise_for_status()

                # Parse XML response
                from xml.etree import ElementTree as ET
                root = ET.fromstring(response.content)

                # Namespace for arXiv API
                ns = {'atom': 'http://www.w3.org/2005/Atom',
                      'arxiv': 'http://arxiv.org/schemas/atom'}

                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text.strip()
                    pdf_link = None

                    # Find PDF link
                    for link in entry.findall('atom:link', ns):
                        if link.get('title') == 'pdf':
                            pdf_link = link.get('href')
                            break

                    # Check license (if specified)
                    rights = entry.find('atom:rights', ns)
                    license_text = rights.text if rights is not None else "arXiv.org perpetual non-exclusive license"

                    validation = self.validator.validate(license_text, source='arXiv')

                    if validation.decision == LicenseDecision.ACCEPT and pdf_link:
                        source = ContentSource(
                            title=title,
                            url=pdf_link,
                            source_institution='arXiv',
                            content_type='technical_report',
                            license=license_text,
                            license_verified=True
                        )
                        sources.append(source)

                        logger.info(f"Found arXiv paper: {title[:50]}...")

                # Rate limiting
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error harvesting arXiv: {e}")

        return sources


class DOABHarvester:
    """
    Harvest from Directory of Open Access Books (DOAB).

    Uses OAI-PMH protocol to programmatically access metadata.
    """

    def __init__(self):
        self.validator = StrictLicenseValidator()
        self.oai_endpoint = "https://directory.doabooks.org/oai/request"
        self.session = requests.Session()

    def harvest_cs_books(self, max_books: int = 200) -> List[ContentSource]:
        """
        Harvest CS books from DOAB using OAI-PMH.

        Computer Science DDC code: 004
        """
        sources = []

        try:
            # OAI-PMH ListRecords request
            params = {
                'verb': 'ListRecords',
                'metadataPrefix': 'oai_dc',
                'set': 'ddc:004'  # Computer Science
            }

            response = self.session.get(self.oai_endpoint, params=params, timeout=30)
            response.raise_for_status()

            # Parse XML
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)

            ns = {
                'oai': 'http://www.openarchives.org/OAI/2.0/',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }

            for record in root.findall('.//oai:record', ns):
                metadata = record.find('.//oai:metadata', ns)
                if metadata is None:
                    continue

                # Extract Dublin Core metadata
                title = metadata.find('.//dc:title', ns)
                rights = metadata.find('.//dc:rights', ns)
                identifier = metadata.findall('.//dc:identifier', ns)

                if title is not None and rights is not None:
                    title_text = title.text
                    license_text = rights.text

                    # Validate license
                    validation = self.validator.validate(license_text, source='DOAB')

                    if validation.decision == LicenseDecision.ACCEPT:
                        # Find PDF URL in identifiers
                        pdf_url = None
                        for ident in identifier:
                            if ident.text and ident.text.endswith('.pdf'):
                                pdf_url = ident.text
                                break

                        if pdf_url:
                            source = ContentSource(
                                title=title_text,
                                url=pdf_url,
                                source_institution='DOAB',
                                content_type='textbook',
                                license=license_text,
                                license_verified=True
                            )
                            sources.append(source)
                            logger.info(f"Found DOAB book: {title_text[:50]}...")

            # Handle resumption token for pagination
            resumption_token = root.find('.//oai:resumptionToken', ns)
            if resumption_token is not None and resumption_token.text and len(sources) < max_books:
                # Implement pagination logic here
                pass

        except Exception as e:
            logger.error(f"Error harvesting DOAB: {e}")

        return sources


class BulkDownloader:
    """
    Downloads content sources with progress tracking and size limits.

    Target: 10GB of content
    """

    def __init__(self, output_dir: str = './cs_materials_bulk'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.output_dir / 'bulk_metadata.json'
        self.total_downloaded_bytes = 0
        self.target_bytes = 10 * 1024 * 1024 * 1024  # 10 GB

    def download_batch(self, sources: List[ContentSource], rate_limit_seconds: float = 2.0):
        """
        Download a batch of content sources.

        Args:
            sources: List of ContentSource objects
            rate_limit_seconds: Delay between downloads
        """

        logger.info(f"\nStarting batch download of {len(sources)} sources")
        logger.info(f"Target: {self.target_bytes / 1024 / 1024 / 1024:.1f} GB")

        session = requests.Session()

        for i, source in enumerate(sources, 1):
            if self.total_downloaded_bytes >= self.target_bytes:
                logger.info(f"\n✓ Target size reached: {self.total_downloaded_bytes / 1024 / 1024 / 1024:.2f} GB")
                break

            logger.info(f"\n[{i}/{len(sources)}] Downloading: {source.title[:60]}")
            logger.info(f"  URL: {source.url}")
            logger.info(f"  License: {source.license}")

            try:
                # Download
                response = session.get(source.url, stream=True, timeout=120)
                response.raise_for_status()

                # Generate safe filename
                filename = self._generate_filename(source)
                filepath = self.output_dir / filename

                # Download with progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Progress every 1MB
                            if downloaded % (1024 * 1024) == 0 and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"  Progress: {progress:.1f}% ({downloaded / 1024 / 1024:.1f} MB)", end='\r')

                # Update source
                source.local_path = str(filepath)
                source.file_size_bytes = filepath.stat().st_size
                source.download_status = "completed"
                source.download_date = datetime.now().isoformat()

                self.total_downloaded_bytes += source.file_size_bytes

                logger.info(f"  ✓ Downloaded: {source.file_size_bytes / 1024 / 1024:.2f} MB")
                logger.info(f"  Total so far: {self.total_downloaded_bytes / 1024 / 1024 / 1024:.2f} GB")

            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                source.download_status = "failed"

            # Save metadata after each download
            self.save_metadata(sources)

            # Rate limiting
            time.sleep(rate_limit_seconds)

        self._generate_summary_report(sources)

    def _generate_filename(self, source: ContentSource) -> str:
        """Generate safe filename from source"""
        # Use institution, content type, and sanitized title
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', source.title)
        safe_title = safe_title[:150]  # Limit length

        filename = f"{source.source_institution}_{source.content_type}_{safe_title}.pdf"
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
Bulk Download Summary
{'=' * 70}
Generated: {datetime.now().isoformat()}

Statistics:
  Total sources: {len(sources)}
  Successfully downloaded: {len(completed)}
  Failed: {len(failed)}
  Total size: {self.total_downloaded_bytes / 1024 / 1024 / 1024:.2f} GB

By Institution:
"""

        # Group by institution
        by_institution = {}
        for s in completed:
            by_institution[s.source_institution] = by_institution.get(s.source_institution, 0) + 1

        for inst, count in sorted(by_institution.items()):
            report += f"  {inst}: {count}\n"

        report += "\nBy Content Type:\n"
        by_type = {}
        for s in completed:
            by_type[s.content_type] = by_type.get(s.content_type, 0) + 1

        for ctype, count in sorted(by_type.items()):
            report += f"  {ctype}: {count}\n"

        # Save report
        report_file = self.output_dir / 'download_summary.txt'
        with open(report_file, 'w') as f:
            f.write(report)

        print(report)


def main():
    """Main execution"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize harvesters
    lecture_harvester = UniversityLectureNotesHarvester()
    doab_harvester = DOABHarvester()

    # Collect sources
    all_sources = []

    logger.info("=== Phase 1: Discovering Content ===\n")

    # Harvest from DOAB (textbooks)
    logger.info("Harvesting from DOAB...")
    doab_sources = doab_harvester.harvest_cs_books(max_books=200)
    all_sources.extend(doab_sources)
    logger.info(f"Found {len(doab_sources)} books from DOAB")

    # Harvest from arXiv (papers)
    logger.info("\nHarvesting from arXiv...")
    arxiv_sources = lecture_harvester.harvest_arxiv_cs(max_papers=100)
    all_sources.extend(arxiv_sources)
    logger.info(f"Found {len(arxiv_sources)} papers from arXiv")

    logger.info(f"\nTotal sources discovered: {len(all_sources)}")

    # Download
    logger.info("\n=== Phase 2: Downloading Content ===\n")
    downloader = BulkDownloader(output_dir='./cs_materials_bulk')
    downloader.download_batch(all_sources, rate_limit_seconds=2.0)


if __name__ == '__main__':
    main()
