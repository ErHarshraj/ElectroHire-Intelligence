"""
Discover candidate company websites from source pages.

This module only discovers candidate URLs.
It does not decide whether a URL is the official company website.

Verification is handled separately by CompanyWebsiteVerifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx


@dataclass(frozen=True)
class WebsiteCandidate:
    company_name: str
    website: str
    evidence: tuple[str, ...] = ()


class CompanyWebsiteDiscovery:
    """
    Discovers possible company websites from an article/source page.

    The discovery layer intentionally does not guess domains.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout: float = 15.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self._client = client
        self._timeout = timeout

    def discover_from_page(
        self,
        company_name: str,
        page_url: str,
    ) -> list[WebsiteCandidate]:
        if not company_name.strip():
            return []

        if not page_url.strip():
            return []

        response = self._get(page_url)

        if response.status_code >= 400:
            return []

        html = response.text

        candidates: list[WebsiteCandidate] = []
        seen: set[str] = set()

        for href, text in self._extract_links(html):
            absolute_url = urljoin(page_url, href)

            if not self._is_http_url(absolute_url):
                continue

            if self._is_same_domain(absolute_url, page_url):
                continue

            if self._is_excluded_domain(absolute_url):
                continue

            normalized = self._normalize_url(absolute_url)

            if normalized in seen:
                continue

            if not self._looks_relevant(
                company_name=company_name,
                link_text=text,
                url=normalized,
            ):
                continue

            seen.add(normalized)

            evidence = (
                f"Found company-related link on source page: {page_url}",
            )

            if text.strip():
                evidence += (
                    f' Link text: "{text.strip()}"',
                )

            candidates.append(
                WebsiteCandidate(
                    company_name=company_name,
                    website=normalized,
                    evidence=evidence,
                )
            )

        return candidates

    def _get(self, url: str) -> httpx.Response:
        if self._client is not None:
            return self._client.get(
                url,
                timeout=self._timeout,
                follow_redirects=True,
            )

        with httpx.Client(
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            return client.get(url)

    @staticmethod
    def _extract_links(html: str) -> list[tuple[str, str]]:
        """
        Lightweight anchor extraction.

        This intentionally avoids adding another HTML dependency.
        """

        import re

        pattern = re.compile(
            r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )

        links: list[tuple[str, str]] = []

        for match in pattern.finditer(html):
            href = match.group(1).strip()
            text = re.sub(r"<[^>]+>", " ", match.group(2))
            text = " ".join(text.split())

            links.append((href, text))

        return links

    @staticmethod
    def _is_http_url(url: str) -> bool:
        parsed = urlparse(url)

        return parsed.scheme in {"http", "https"} and bool(
            parsed.netloc
        )

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)

        return (
            f"{parsed.scheme}://{parsed.netloc}"
            f"{parsed.path.rstrip('/')}"
        )

    @staticmethod
    def _is_same_domain(
        candidate_url: str,
        source_url: str,
    ) -> bool:
        candidate = urlparse(candidate_url).netloc.lower()
        source = urlparse(source_url).netloc.lower()

        return candidate == source

    @staticmethod
    def _is_excluded_domain(url: str) -> bool:
        domain = urlparse(url).netloc.lower()

        excluded_domains = {
            "facebook.com",
            "www.facebook.com",
            "instagram.com",
            "www.instagram.com",
            "linkedin.com",
            "www.linkedin.com",
            "twitter.com",
            "www.twitter.com",
            "x.com",
            "www.x.com",
            "youtube.com",
            "www.youtube.com",
            "google.com",
            "www.google.com",
            "news.google.com",
        }

        return domain in excluded_domains

    @staticmethod
    def _looks_relevant(
        company_name: str,
        link_text: str,
        url: str,
    ) -> bool:
        company_tokens = {
            token.lower()
            for token in company_name.split()
            if len(token) >= 3
        }

        if not company_tokens:
            return False

        searchable = (
            f"{link_text} "
            f"{urlparse(url).netloc} "
            f"{urlparse(url).path}"
        ).lower()

        return any(
            token in searchable
            for token in company_tokens
        )
