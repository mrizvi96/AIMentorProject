#!/usr/bin/env python3
"""
Strict License Validation Module

This module ensures ONLY Creative Commons Attribution (CC BY),
CC BY-SA, CC0, and Public Domain content is collected.

REJECTS:
- CC BY-NC (NonCommercial)
- CC BY-ND (NoDerivatives)
- CC BY-NC-SA
- CC BY-NC-ND
- All Rights Reserved
- Any proprietary licenses
"""

import re
import logging
from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LicenseDecision(Enum):
    """License validation decision"""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass
class ValidationResult:
    """Result of license validation"""
    decision: LicenseDecision
    normalized_license: str
    reason: str
    confidence: float  # 0.0 to 1.0


class StrictLicenseValidator:
    """
    Strict validator that ONLY accepts truly open licenses.

    Philosophy: When in doubt, reject. Better to miss content than
    include improperly licensed material.
    """

    # Exact acceptable licenses (case-insensitive)
    ACCEPTABLE_EXACT = {
        'CC BY',
        'CC BY 2.0',
        'CC BY 2.5',
        'CC BY 3.0',
        'CC BY 4.0',
        'CC-BY',
        'CC-BY 4.0',
        'CC BY-SA',
        'CC BY-SA 2.0',
        'CC BY-SA 2.5',
        'CC BY-SA 3.0',
        'CC BY-SA 4.0',
        'CC-BY-SA',
        'CC-BY-SA 4.0',
        'CC0',
        'CC0 1.0',
        'PUBLIC DOMAIN',
        'PD',
        'MIT LICENSE',
        'MIT',
        'APACHE 2.0',
        'APACHE LICENSE 2.0',
        'BSD LICENSE',
        'BSD 3-CLAUSE'
    }

    # Prohibited terms - if ANY of these appear, REJECT
    PROHIBITED_TERMS = {
        'NC',           # NonCommercial
        'ND',           # NoDerivatives
        'NONCOMMERCIAL',
        'NON-COMMERCIAL',
        'NODERIVATIVES',
        'NO-DERIVATIVES',
        'NO DERIVATIVES',
        'ALL RIGHTS RESERVED',
        'COPYRIGHT ©',  # If accompanied by restrictions
        'PROPRIETARY',
        'RESTRICTED',
        'EDUCATIONAL USE ONLY',
        'PERSONAL USE ONLY',
        'NON-TRANSFERABLE'
    }

    def __init__(self):
        self.validation_log = []

    def validate(self, license_text: str, source: str = "") -> ValidationResult:
        """
        Validate a license string.

        Args:
            license_text: License text to validate
            source: Source of the license (for logging)

        Returns:
            ValidationResult with decision and reasoning
        """

        if not license_text or len(license_text.strip()) == 0:
            return ValidationResult(
                decision=LicenseDecision.REJECT,
                normalized_license="",
                reason="Empty or missing license",
                confidence=1.0
            )

        # Normalize
        normalized = self._normalize_license(license_text)

        # Log for audit
        log_entry = {
            'source': source,
            'original': license_text,
            'normalized': normalized
        }

        # Step 1: Check for prohibited terms (highest priority)
        prohibited_found = self._check_prohibited(normalized)
        if prohibited_found:
            result = ValidationResult(
                decision=LicenseDecision.REJECT,
                normalized_license=normalized,
                reason=f"Contains prohibited restriction: {prohibited_found}",
                confidence=1.0
            )
            log_entry['decision'] = 'REJECT'
            log_entry['reason'] = result.reason
            self.validation_log.append(log_entry)
            logger.warning(f"REJECTED: {license_text} - {result.reason}")
            return result

        # Step 2: Check against acceptable list
        if self._is_acceptable(normalized):
            result = ValidationResult(
                decision=LicenseDecision.ACCEPT,
                normalized_license=normalized,
                reason="Matches approved license list",
                confidence=1.0
            )
            log_entry['decision'] = 'ACCEPT'
            log_entry['reason'] = result.reason
            self.validation_log.append(log_entry)
            logger.info(f"ACCEPTED: {license_text}")
            return result

        # Step 3: Try fuzzy matching with caution
        fuzzy_match, confidence = self._fuzzy_match(normalized)
        if fuzzy_match and confidence > 0.8:
            # High confidence fuzzy match
            result = ValidationResult(
                decision=LicenseDecision.ACCEPT,
                normalized_license=normalized,
                reason=f"Fuzzy matched to: {fuzzy_match}",
                confidence=confidence
            )
            log_entry['decision'] = 'ACCEPT'
            log_entry['reason'] = result.reason
            log_entry['confidence'] = confidence
            self.validation_log.append(log_entry)
            logger.info(f"ACCEPTED (fuzzy): {license_text} -> {fuzzy_match}")
            return result

        # Step 4: If uncertain, flag for manual review
        result = ValidationResult(
            decision=LicenseDecision.MANUAL_REVIEW,
            normalized_license=normalized,
            reason="License format not recognized - requires manual verification",
            confidence=0.0
        )
        log_entry['decision'] = 'MANUAL_REVIEW'
        log_entry['reason'] = result.reason
        self.validation_log.append(log_entry)
        logger.warning(f"MANUAL REVIEW NEEDED: {license_text}")
        return result

    def _normalize_license(self, license_text: str) -> str:
        """Normalize license text for comparison"""
        # Convert to uppercase
        normalized = license_text.upper().strip()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove common noise
        normalized = normalized.replace('LICENSE', '').replace('LICENCE', '')
        normalized = normalized.replace('VERSION', '').strip()

        # Remove URLs
        normalized = re.sub(r'HTTP[S]?://\S+', '', normalized)

        return normalized.strip()

    def _check_prohibited(self, normalized: str) -> Optional[str]:
        """Check for prohibited terms. Returns first match if found."""
        for prohibited in self.PROHIBITED_TERMS:
            if prohibited in normalized:
                # Extra check: Make sure it's not part of a word
                # e.g., "FUNCTION" contains "NC"
                pattern = r'\b' + re.escape(prohibited) + r'\b'
                if re.search(pattern, normalized):
                    return prohibited
        return None

    def _is_acceptable(self, normalized: str) -> bool:
        """Check if license is in acceptable list"""
        # Direct match
        if normalized in self.ACCEPTABLE_EXACT:
            return True

        # Check if it starts with an acceptable license
        # (to handle version variations)
        for acceptable in self.ACCEPTABLE_EXACT:
            if normalized.startswith(acceptable + ' '):
                return True

        return False

    def _fuzzy_match(self, normalized: str) -> Tuple[Optional[str], float]:
        """
        Attempt fuzzy matching for common variations.

        Returns:
            (matched_license, confidence_score)
        """

        # Pattern: CC BY (with optional version number)
        if re.match(r'^CC\s*BY\s*(?:\d+\.\d+)?$', normalized):
            return ('CC BY', 0.9)

        # Pattern: CC BY-SA (with optional version)
        if re.match(r'^CC\s*BY-SA\s*(?:\d+\.\d+)?$', normalized):
            return ('CC BY-SA', 0.9)

        # Pattern: CC0
        if re.match(r'^CC\s*0\s*(?:1\.0)?$', normalized):
            return ('CC0', 0.95)

        # Pattern: Public Domain variations
        if re.match(r'^PUBLIC\s*DOMAIN', normalized):
            return ('PUBLIC DOMAIN', 0.9)

        # Pattern: Creative Commons Attribution
        if 'CREATIVE COMMONS ATTRIBUTION' in normalized and 'SHARE' in normalized:
            return ('CC BY-SA', 0.7)
        elif 'CREATIVE COMMONS ATTRIBUTION' in normalized:
            return ('CC BY', 0.7)

        return (None, 0.0)

    def export_validation_log(self, filepath: str):
        """Export validation log for auditing"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.validation_log, f, indent=2)
        logger.info(f"Validation log exported to {filepath}")


class PDFLicenseExtractor:
    """Extract license information from PDF files"""

    def __init__(self):
        self.validator = StrictLicenseValidator()

    def extract_from_pdf(self, pdf_path: str) -> ValidationResult:
        """
        Extract and validate license from PDF.

        Checks:
        1. PDF metadata
        2. First 10 pages for license text
        3. Copyright page
        """
        import PyPDF2

        try:
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)

                # Check metadata
                if pdf.metadata:
                    for key in ['License', 'Rights', 'Copyright', 'Subject']:
                        if key in pdf.metadata:
                            value = pdf.metadata[key]
                            if value:
                                result = self.validator.validate(
                                    value,
                                    source=f"PDF Metadata:{key}"
                                )
                                if result.decision == LicenseDecision.ACCEPT:
                                    return result

                # Check first 10 pages
                for i in range(min(10, len(pdf.pages))):
                    text = pdf.pages[i].extract_text()

                    # Look for license statements
                    license_patterns = [
                        r'(CC BY(?:-SA)?\s*\d+\.\d+)',
                        r'(Creative Commons Attribution(?:-ShareAlike)?)',
                        r'(Public Domain)',
                        r'(CC0)',
                        r'(MIT License)',
                        r'(Apache License)'
                    ]

                    for pattern in license_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            result = self.validator.validate(
                                match,
                                source=f"PDF Page {i+1}"
                            )
                            if result.decision == LicenseDecision.ACCEPT:
                                return result

        except Exception as e:
            logger.error(f"Error extracting license from {pdf_path}: {e}")

        # If nothing found, reject
        return ValidationResult(
            decision=LicenseDecision.REJECT,
            normalized_license="",
            reason="No verifiable license found in PDF",
            confidence=1.0
        )


def test_validator():
    """Test the validator with various inputs"""
    validator = StrictLicenseValidator()

    test_cases = [
        ("CC BY 4.0", LicenseDecision.ACCEPT),
        ("CC BY-SA 3.0", LicenseDecision.ACCEPT),
        ("CC BY-NC 4.0", LicenseDecision.REJECT),  # NonCommercial
        ("CC BY-ND 2.0", LicenseDecision.REJECT),  # NoDerivatives
        ("CC BY-NC-SA 4.0", LicenseDecision.REJECT),  # NC
        ("Public Domain", LicenseDecision.ACCEPT),
        ("CC0", LicenseDecision.ACCEPT),
        ("MIT License", LicenseDecision.ACCEPT),
        ("All Rights Reserved", LicenseDecision.REJECT),
        ("Copyright © 2024", LicenseDecision.REJECT),
        ("Creative Commons Attribution 4.0", LicenseDecision.ACCEPT),
        ("", LicenseDecision.REJECT),
    ]

    print("License Validator Test Results")
    print("=" * 60)

    for license_text, expected in test_cases:
        result = validator.validate(license_text, source="test")
        status = "✓" if result.decision == expected else "✗"
        print(f"{status} '{license_text}' -> {result.decision.value} ({result.reason})")

    print("\n" + "=" * 60)
    print(f"Validation log: {len(validator.validation_log)} entries")


if __name__ == '__main__':
    test_validator()
