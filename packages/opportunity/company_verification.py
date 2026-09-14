"""
Company verification from multiple startup discovery records.

This module does not prove that a company legally exists. It evaluates
whether multiple discovery records provide sufficient corroboration for
a company candidate.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.opportunity.company_identifier import CompanyIdentifier
from packages.opportunity.discovery import StartupNewsItem
from packages.opportunity.models import Company


@dataclass(frozen=True)
class CompanyVerificationResult:
    """Result of corroborating a company candidate."""

    company: Company | None
    confidence: str
    article_count: int
    source_count: int
    evidence: tuple[str, ...]


class CompanyVerificationEngine:
    """Corroborate company candidates across discovery records."""

    def __init__(
        self,
        identifier: CompanyIdentifier | None = None,
    ) -> None:
        self.identifier = identifier or CompanyIdentifier()

    def verify(
        self,
        items: list[StartupNewsItem],
    ) -> list[CompanyVerificationResult]:
        """
        Verify company candidates across discovery records.

        Records are grouped by normalized company name. Duplicate article
        URLs are counted only once.
        """
        candidates: dict[str, list[tuple[StartupNewsItem, Company]]] = {}

        for item in items:
            result = self.identifier.identify(item)

            if result.company is None:
                continue

            key = self._normalize_company_name(result.company.name)

            candidates.setdefault(key, []).append(
                (item, result.company)
            )

        results: list[CompanyVerificationResult] = []

        for records in candidates.values():
            results.append(self._build_result(records))

        return sorted(
            results,
            key=lambda result: (
                self._confidence_rank(result.confidence),
                result.article_count,
                result.source_count,
            ),
            reverse=True,
        )

    def _build_result(
        self,
        records: list[tuple[StartupNewsItem, Company]],
    ) -> CompanyVerificationResult:
        """Build a verification result from corroborating records."""
        unique_urls = {item.url for item, _ in records}
        unique_sources = {
            item.source_name.casefold().strip()
            for item, _ in records
            if item.source_name.strip()
        }

        company = records[0][1]
        article_count = len(unique_urls)
        source_count = len(unique_sources)

        if article_count >= 2 and source_count >= 2:
            confidence = "HIGH"
            evidence = (
                "Company identified in multiple distinct articles.",
                "Company evidence comes from multiple distinct sources.",
            )
        elif article_count >= 2:
            confidence = "MEDIUM"
            evidence = (
                "Company identified in multiple distinct articles.",
                "All corroborating articles currently come from one source.",
            )
        else:
            confidence = "LOW"
            evidence = (
                "Company identified from a single discovery article.",
                "Independent corroboration is not yet available.",
            )

        return CompanyVerificationResult(
            company=company,
            confidence=confidence,
            article_count=article_count,
            source_count=source_count,
            evidence=evidence,
        )

    @staticmethod
    def _normalize_company_name(name: str) -> str:
        """Normalize company names for grouping."""
        return " ".join(name.casefold().split())

    @staticmethod
    def _confidence_rank(confidence: str) -> int:
        """Return a sortable confidence rank."""
        return {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
            "NONE": 0,
        }.get(confidence, 0)
