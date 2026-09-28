"""Tests for the 5-site web crawler (Task 4.1).

Coverage:
- Off-allowlist URLs are dropped.
- Unchanged content produces zero writes on a second run (content_hash change detection).
- Extraction removes known boilerplate (navigation, footer, sidebar, comments).
- robots.txt disallow is honoured.
- Sitemap XML parsing extracts URLs.
"""

from __future__ import annotations

import pytest

from ingestion.crawler import (
    Crawler,
    HTMLContentExtractor,
    canonicalize_url,
    is_approved_url,
    parse_sitemap_xml,
)
from storage.memory import MemoryStorage


@pytest.mark.asyncio
async def test_off_allowlist_urls_dropped():
    storage = MemoryStorage()
    crawler = Crawler(storage=storage)

    # 1. Unapproved external domains
    unapproved_urls = [
        "https://random-blog.com/artikel",
        "https://evil.org/phishing",
        "https://wikipedia.org/wiki/Jesus",
    ]
    for url in unapproved_urls:
        assert not is_approved_url(url)
        article, changed = await crawler.ingest_html(url, "<html><body>Hello</body></html>")
        assert article is None
        assert not changed

    # Verify zero articles saved
    assert len(await storage.list_articles()) == 0

    # 2. Approved domains
    approved = [
        "https://isadanislam.org/keselamatan",
        "https://isadanalquran.com/artikel-1",
        "https://isadanalfatihah.com/rahmat",
        "https://isaislamdankaumwanita.com/ibu",
        "https://takutneraka.com/jalan-lurus",
    ]
    for url in approved:
        assert is_approved_url(url)


@pytest.mark.asyncio
async def test_unchanged_content_produces_zero_writes():
    storage = MemoryStorage()
    crawler = Crawler(storage=storage)
    url = "https://isadanislam.org/kasih-allah"
    html = """
    <!DOCTYPE html>
    <html>
      <head><title>Kasih Allah yang Abadi - Isa dan Islam</title></head>
      <body>
        <main>
          <h1>Kasih Allah yang Abadi</h1>
          <p>Kasih Allah melampaui segala pemahaman manusia dan menjangkau hati yang terluka.</p>
        </main>
      </body>
    </html>
    """

    # First crawl -> New article written
    art1, changed1 = await crawler.ingest_html(url, html)
    assert art1 is not None
    assert changed1 is True
    assert art1.title == "Kasih Allah yang Abadi"
    assert "Kasih Allah melampaui" in art1.summary

    # Second crawl with identical content -> Change detection skips writes
    art2, changed2 = await crawler.ingest_html(url, html)
    assert art2 is not None
    assert changed2 is False
    assert art2.id == art1.id
    assert art2.content_hash == art1.content_hash

    # Third crawl with modified content -> Detected as changed
    modified_html = html.replace("hati yang terluka", "setiap insan yang percaya")
    art3, changed3 = await crawler.ingest_html(url, modified_html)
    assert art3 is not None
    assert changed3 is True
    assert art3.content_hash != art1.content_hash


def test_extraction_removes_known_boilerplate():
    html = """
    <!DOCTYPE html>
    <html>
      <head><title>Jalan Keselamatan | Isa dan Al-Quran</title></head>
      <body>
        <header>
          <nav>
            <a href="/">Beranda</a>
            <a href="/tentang">Tentang Kami</a>
          </nav>
        </header>

        <div class="sidebar widget-area">
          <h3>Artikel Populer</h3>
          <ul><li>Sidebar Link</li></ul>
        </div>

        <article class="main-content">
          <h1>Jalan Menuju Keselamatan</h1>
          <p>Banyak orang mencari kepastian tentang kehidupan setelah kematian.</p>
          <p>Kitab Suci memberikan petunjuk yang terang mengenai pengampunan dosa.</p>
        </article>

        <div id="comments" class="comments-area">
          <p>Komentar pembaca: Sangat bermanfaat!</p>
        </div>

        <footer>
          <p>&copy; 2026 Isa dan Al-Quran. Hak cipta dilindungi.</p>
        </footer>
      </body>
    </html>
    """
    extractor = HTMLContentExtractor()
    extractor.feed(html)
    title, body = extractor.get_result()

    assert title == "Jalan Keselamatan"
    # Main content is present
    assert "Banyak orang mencari kepastian tentang kehidupan setelah kematian." in body
    assert "Kitab Suci memberikan petunjuk yang terang mengenai pengampunan dosa." in body

    # Boilerplate is completely stripped
    assert "Beranda" not in body
    assert "Tentang Kami" not in body
    assert "Artikel Populer" not in body
    assert "Sidebar Link" not in body
    assert "Komentar pembaca" not in body
    assert "Hak cipta dilindungi" not in body


@pytest.mark.asyncio
async def test_robots_txt_disallow_honoured():
    storage = MemoryStorage()
    crawler = Crawler(storage=storage)

    # Seed robots.txt blocking /secret/
    crawler.robots_cache.set_robots_txt(
        "isadanislam.org",
        """
        User-agent: *
        Disallow: /secret/
        Allow: /
        """,
    )

    allowed_url = "https://isadanislam.org/artikel"
    blocked_url = "https://isadanislam.org/secret/internal-memo"

    html = "<html><body><p>Sample content here</p></body></html>"

    # Disallowed URL should be refused
    art_blocked, changed_blocked = await crawler.ingest_html(blocked_url, html)
    assert art_blocked is None
    assert changed_blocked is False

    # Allowed URL should succeed
    art_allowed, changed_allowed = await crawler.ingest_html(allowed_url, html)
    assert art_allowed is not None
    assert changed_allowed is True


def test_sitemap_xml_parsing():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://isadanislam.org/artikel-1</loc>
        <lastmod>2026-08-01</lastmod>
      </url>
      <url>
        <loc>https://isadanislam.org/artikel-2</loc>
        <lastmod>2026-08-15</lastmod>
      </url>
    </urlset>
    """
    urls = parse_sitemap_xml(xml)
    assert urls == [
        "https://isadanislam.org/artikel-1",
        "https://isadanislam.org/artikel-2",
    ]


def test_canonicalize_url():
    assert (
        canonicalize_url("https://isadanislam.org/kasih/?utm_source=fb#section")
        == "https://isadanislam.org/kasih"
    )
    assert canonicalize_url("http://ISADANISLAM.ORG/") == "http://isadanislam.org/"
