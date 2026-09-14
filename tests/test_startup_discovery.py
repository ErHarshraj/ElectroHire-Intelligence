from datetime import timezone

import httpx
import pytest

from packages.opportunity.discovery import StartupDiscoveryService
from packages.opportunity.sources.google_news import GoogleNewsStartupSource

RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <item>
      <title>Example Robotics raises funding for autonomous systems</title>
      <link>https://example.com/example-robotics</link>
      <description>
        Example Robotics is developing autonomous hardware.
      </description>
      <pubDate>Mon, 14 Sep 2026 08:30:00 GMT</pubDate>
      <source url="https://example.com">Example News</source>
    </item>
    <item>
      <title>Example Robotics raises funding for autonomous systems</title>
      <link>https://example.com/example-robotics</link>
      <description>
        Duplicate article.
      </description>
      <pubDate>Mon, 14 Sep 2026 08:30:00 GMT</pubDate>
      <source url="https://example.com">Example News</source>
    </item>
    <item>
      <title>New electronics startup launches embedded product</title>
      <link>https://another.example.com/electronics-startup</link>
      <description>
        A new embedded hardware product was announced.
      </description>
      <pubDate>Sun, 13 Sep 2026 10:00:00 GMT</pubDate>
      <source url="https://another.example.com">
        Another News
      </source>
    </item>
  </channel>
</rss>
"""


def make_client(response_text: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            text=response_text,
            request=request,
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_google_news_source_builds_search_url() -> None:
    source = GoogleNewsStartupSource(
        query="India robotics startup",
        language="en-IN",
        country="IN",
    )

    url = source._build_url()

    assert url.startswith(
        "https://news.google.com/rss/search?q="
    )
    assert "hl=en-IN" in url
    assert "gl=IN" in url
    assert "ceid=IN:en" in url


def test_google_news_source_parses_rss_items() -> None:
    client = make_client(RSS_XML)

    source = GoogleNewsStartupSource(
        query="India robotics startup",
        client=client,
    )

    items = source.discover()

    assert len(items) == 3

    first = items[0]

    assert first.title == (
        "Example Robotics raises funding for autonomous systems"
    )
    assert first.url == "https://example.com/example-robotics"
    assert first.summary is not None
    assert "autonomous hardware" in first.summary
    assert first.source_name == "Example News"
    assert first.published_at is not None
    assert first.published_at.tzinfo is not None
    assert first.published_at.astimezone(timezone.utc).hour == 8


def test_google_news_source_skips_items_without_title_or_url() -> None:
    xml = """\
    <rss version="2.0">
      <channel>
        <item>
          <title></title>
          <link>https://example.com/missing-title</link>
        </item>
        <item>
          <title>Missing URL</title>
          <link></link>
        </item>
        <item>
          <title>Valid Item</title>
          <link>https://example.com/valid</link>
        </item>
      </channel>
    </rss>
    """

    client = make_client(xml)

    source = GoogleNewsStartupSource(
        query="India hardware startup",
        client=client,
    )

    items = source.discover()

    assert len(items) == 1
    assert items[0].title == "Valid Item"


def test_google_news_source_handles_invalid_date() -> None:
    xml = """\
    <rss version="2.0">
      <channel>
        <item>
          <title>Hardware startup activity</title>
          <link>https://example.com/activity</link>
          <pubDate>not-a-date</pubDate>
        </item>
      </channel>
    </rss>
    """

    client = make_client(xml)

    source = GoogleNewsStartupSource(
        query="India hardware startup",
        client=client,
    )

    items = source.discover()

    assert len(items) == 1
    assert items[0].published_at is None


def test_google_news_source_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="query must not be empty"):
        GoogleNewsStartupSource(query="   ")


def test_google_news_source_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="timeout must be greater"):
        GoogleNewsStartupSource(timeout=0)


def test_discovery_service_deduplicates_urls() -> None:
    client = make_client(RSS_XML)

    source = GoogleNewsStartupSource(
        query="India robotics startup",
        client=client,
    )

    service = StartupDiscoveryService(source)

    items = service.discover()

    assert len(items) == 2
    assert items[0].url != items[1].url


def test_discovery_service_preserves_source_data() -> None:
    client = make_client(RSS_XML)

    source = GoogleNewsStartupSource(
        query="India robotics startup",
        client=client,
    )

    service = StartupDiscoveryService(source)

    items = service.discover()

    assert all(item.source_name for item in items)
    assert all(item.query == "India robotics startup" for item in items)
