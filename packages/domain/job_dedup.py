"""Conservative cross-source job deduplication helpers."""

from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from packages.domain.job import Job

_TRACKING_QUERY_PREFIXES = ("utm_",)
_TRACKING_QUERY_NAMES = {
    "fbclid",
    "gclid",
    "ref",
    "source",
    "src",
}


def normalize_text(value: str | None) -> str:
    """Normalize human-readable job fields for stable comparisons."""
    if not value:
        return ""

    return " ".join(unescape(value).casefold().split())


def normalize_job_url(url: str) -> str:
    """Normalize a job URL while preserving meaningful query parameters."""
    parts = urlsplit(url.strip())

    if not parts.scheme or not parts.netloc:
        return url.strip().rstrip("/")

    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.casefold() not in _TRACKING_QUERY_NAMES
        and not key.casefold().startswith(_TRACKING_QUERY_PREFIXES)
    ]
    query_items.sort()

    return urlunsplit(
        (
            parts.scheme.casefold(),
            parts.netloc.casefold(),
            parts.path.rstrip("/") or "/",
            urlencode(query_items),
            "",
        )
    )


def url_dedup_key(job: Job) -> str:
    """Return the strongest deduplication key: the canonical application URL."""
    return f"url:{normalize_job_url(str(job.source_url))}"


def metadata_dedup_key(job: Job) -> str | None:
    """Return a conservative company/title/location fingerprint when available."""
    company = normalize_text(job.company)
    title = normalize_text(job.title)
    location = normalize_text(job.location)

    if not company or not title or not location:
        return None

    return f"meta:{company}|{title}|{location}"


def dedup_keys(job: Job) -> tuple[str, ...]:
    """Return deduplication keys from strongest to weaker evidence."""
    keys = [url_dedup_key(job)]
    metadata_key = metadata_dedup_key(job)

    if metadata_key is not None:
        keys.append(metadata_key)

    return tuple(keys)
