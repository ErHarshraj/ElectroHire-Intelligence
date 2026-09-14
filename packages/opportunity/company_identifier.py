"""
Company identification from startup discovery evidence.

This module performs conservative company-name extraction from normalized
startup discovery items. It does not attempt to prove that the extracted
name represents a real company.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from packages.opportunity.discovery import StartupNewsItem
from packages.opportunity.models import Company


@dataclass(frozen=True)
class CompanyIdentificationResult:
    """Result of attempting to identify a company from discovery evidence."""

    company: Company | None
    confidence: str
    evidence: tuple[str, ...]


class CompanyIdentifier:
    """Conservatively identify companies from startup news items."""

    _ACTION_PATTERN = re.compile(
        r"""
        ^\s*
        (?P<company>.+?)
        \s+
        (?:
            raises|
            raised|
            secures|
            secured|
            receives|
            received|
            gets|
            got|
            bags|
            launches|
            launched|
            unveils|
            unveiled|
            announces|
            announced|
            expands|
            expanded|
            enters|
            entered|
            develops|
            developed|
            builds|
            built|
            acquires|
            acquired|
            partners|
            partnered
        )
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _NOISE_PREFIXES = (
        "india:",
        "india -",
        "indian startup:",
        "indian startup -",
        "startup:",
        "startup -",
    )

    _NOISE_TERMS = {
        "startup",
        "startups",
        "companies",
        "company",
        "indian startup",
        "india startup",
        "india startups",
    }

    _LEGAL_SUFFIXES = (
        " private limited",
        " pvt ltd",
        " pvt. ltd.",
        " private ltd",
        " limited",
        " ltd",
        " ltd.",
        " inc",
        " inc.",
        " llp",
        " corporation",
        " corp",
        " corp.",
    )

    def identify(
        self,
        item: StartupNewsItem,
    ) -> CompanyIdentificationResult:
        """
        Identify a company from a startup discovery item.

        Returns a low-confidence result when extraction is ambiguous and
        returns no company when a reliable candidate cannot be extracted.
        """
        candidate = self._extract_from_title(item.title)

        if candidate is None:
            return CompanyIdentificationResult(
                company=None,
                confidence="NONE",
                evidence=(
                    "No reliable company name was extracted from the title.",
                ),
            )

        company_name = self._clean_company_name(candidate)

        if not self._is_valid_company_name(company_name):
            return CompanyIdentificationResult(
                company=None,
                confidence="NONE",
                evidence=(
                    "Extracted title fragment did not pass company-name "
                    "validation.",
                ),
            )

        return CompanyIdentificationResult(
            company=Company(name=company_name),
            confidence="MEDIUM",
            evidence=(
                "Company name extracted from the startup-news title.",
            ),
        )

    def _extract_from_title(self, title: str) -> str | None:
        """Extract a candidate company name from a title."""
        normalized_title = self._normalize_title(title)

        if not normalized_title:
            return None

        match = self._ACTION_PATTERN.match(normalized_title)

        if match is None:
            return None

        candidate = match.group("company").strip(" -:|,.")

        if not candidate:
            return None

        return candidate

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize whitespace and common title prefixes."""
        normalized = re.sub(r"\s+", " ", title.strip())

        lowered = normalized.casefold()

        for prefix in CompanyIdentifier._NOISE_PREFIXES:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                lowered = normalized.casefold()

        return normalized

    @classmethod
    def _clean_company_name(cls, candidate: str) -> str:
        """Remove common legal suffixes from a company candidate."""
        cleaned = re.sub(r"\s+", " ", candidate.strip(" -:|,."))

        lowered = cleaned.casefold()

        for suffix in cls._LEGAL_SUFFIXES:
            if lowered.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].rstrip(" ,.-")
                break

        return cleaned

    @classmethod
    def _is_valid_company_name(cls, candidate: str) -> bool:
        """Reject empty, generic, or obviously malformed company names."""
        if not candidate:
            return False

        lowered = candidate.casefold()

        if lowered in cls._NOISE_TERMS:
            return False

        if len(candidate) < 2 or len(candidate) > 100:
            return False

        if "@" in candidate:
            return False

        if "http://" in lowered or "https://" in lowered:
            return False

        if candidate.startswith((".", "/", "-", "_")):
            return False

        words = candidate.split()

        if len(words) > 12:
            return False

        if not any(char.isalpha() for char in candidate):
            return False

        return True
