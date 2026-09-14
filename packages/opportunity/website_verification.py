"""
Company website and domain verification.

This module verifies an explicitly supplied website candidate against a
company name. It does not guess domains from company names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from packages.opportunity.models import Company


@dataclass(frozen=True)
class WebsiteVerificationResult:
    """Result of verifying a candidate company website."""

    company: Company
    website: str
    verified: bool
    confidence: str
    evidence: tuple[str, ...]


class CompanyWebsiteVerifier:
    """Verify an explicitly supplied website against a company identity."""

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("Website verification timeout must be greater than zero.")

        self.timeout = timeout
        self.client = client

    def verify(
        self,
        company: Company,
        website: str,
    ) -> WebsiteVerificationResult:
        """
        Verify a candidate website for a company.

        The URL must be explicitly supplied. This method never constructs
        a website URL from the company name.
        """
        normalized_url = self._normalize_url(website)

        if normalized_url is None:
            return self._failed_result(
                company,
                website,
                "Candidate website URL is invalid.",
            )

        try:
            html = self._fetch(normalized_url)
        except (httpx.HTTPError, ValueError) as exc:
            return self._failed_result(
                company,
                normalized_url,
                f"Website could not be fetched: {exc.__class__.__name__}.",
            )

        title = self._extract_title(html)
        company_match = self._company_name_matches(
            company.name,
            title,
            html,
        )

        if company_match:
            evidence = (
                "Candidate website was reachable.",
                "Company name is present in the website title or page content.",
            )

            return WebsiteVerificationResult(
                company=Company(
                    name=company.name,
                    website=normalized_url,
                    location=company.location,
                    industry=company.industry,
                    founded_year=company.founded_year,
                    stage=company.stage,
                    size=company.size,
                    signals=company.signals,
                ),
                website=normalized_url,
                verified=True,
                confidence="HIGH",
                evidence=evidence,
            )

        return WebsiteVerificationResult(
            company=Company(
                name=company.name,
                website=normalized_url,
                location=company.location,
                industry=company.industry,
                founded_year=company.founded_year,
                stage=company.stage,
                size=company.size,
                signals=company.signals,
            ),
            website=normalized_url,
            verified=False,
            confidence="LOW",
            evidence=(
                "Candidate website was reachable.",
                "Company name could not be corroborated from the page.",
            ),
        )

    def _fetch(self, website: str) -> str:
        """Fetch website HTML."""
        if self.client is not None:
            response = self.client.get(
                website,
                timeout=self.timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text

        with httpx.Client(follow_redirects=True) as client:
            response = client.get(
                website,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text

    @staticmethod
    def _normalize_url(website: str) -> str | None:
        """Validate and normalize an explicitly supplied URL."""
        candidate = website.strip()

        if not candidate:
            return None

        if not re.match(r"^https?://", candidate, re.IGNORECASE):
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)

        if parsed.scheme not in {"http", "https"}:
            return None

        if not parsed.netloc:
            return None

        return candidate.rstrip("/")

    @staticmethod
    def _extract_title(html: str) -> str:
        """Extract the HTML title."""
        match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            re.IGNORECASE | re.DOTALL,
        )

        if match is None:
            return ""

        return re.sub(r"\s+", " ", match.group(1)).strip()

    @staticmethod
    def _company_name_matches(
        company_name: str,
        title: str,
        html: str,
    ) -> bool:
        """Check whether the company name appears in page evidence."""
        normalized_company = " ".join(company_name.casefold().split())

        if not normalized_company:
            return False

        normalized_title = " ".join(title.casefold().split())

        if normalized_company in normalized_title:
            return True

        text = re.sub(r"<[^>]+>", " ", html)
        normalized_text = " ".join(text.casefold().split())

        return normalized_company in normalized_text

    @staticmethod
    def _failed_result(
        company: Company,
        website: str,
        reason: str,
    ) -> WebsiteVerificationResult:
        """Create a failed verification result."""
        return WebsiteVerificationResult(
            company=company,
            website=website,
            verified=False,
            confidence="NONE",
            evidence=(reason,),
        )
