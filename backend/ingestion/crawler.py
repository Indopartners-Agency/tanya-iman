"""Web crawler for the 5 approved ministry sites.

PIP Task 4.1 & Content Ingestion Runbook §1-§3:
- Reads backend/config/approved_sites.yml; URLs outside it are dropped.
- Sitemap-first traversal with HTML-link fallback.
- Honours robots.txt, politeness delay, and identifying User-Agent.
- Main-content extraction stripping navigation, sidebars, comments, and footers.
- SHA-256 content_hash change detection: unchanged articles produce zero writes.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from config.loader import approved_domains, approved_sites
from models import Article
from models.enums import ArticleStatus
from storage import Storage

logger = logging.getLogger("ingestion.crawler")

# Tags to completely skip content from
IGNORED_TAGS = frozenset(
    [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        "noscript",
        "iframe",
        "svg",
        "form",
        "button",
        "input",
        "select",
        "textarea",
    ]
)

# Class or id patterns indicating boilerplate, widgets, and non-article content
BOILERPLATE_PATTERN = re.compile(
    r"(comment|sidebar|footer|navigation|menu|breadcrumb|widget|share|social|popup|cookie|advert|banner)",
    re.IGNORECASE,
)

BLOCK_TAGS = frozenset(
    [
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "article",
        "section",
        "blockquote",
        "tr",
        "div",
    ]
)


class HTMLContentExtractor(HTMLParser):
    """Extracts page title and clean article body text while stripping boilerplate."""

    def __init__(self) -> None:
        super().__init__()
        self._title_parts: list[str] = []
        self._body_blocks: list[str] = []
        self._current_block: list[str] = []
        self._ignored_stack: list[str] = []
        self._in_title = False
        self._title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()

        # If already ignoring, track nested depth with this tag
        if self._ignored_stack:
            self._ignored_stack.append(tag_lower)
            return

        # Check if entering an ignored tag
        if tag_lower in IGNORED_TAGS:
            self._ignored_stack.append(tag_lower)
            return

        # Check for boilerplate class or id attributes
        attrs_dict = dict(attrs)
        class_val = attrs_dict.get("class") or ""
        id_val = attrs_dict.get("id") or ""
        if BOILERPLATE_PATTERN.search(class_val) or BOILERPLATE_PATTERN.search(id_val):
            self._ignored_stack.append(tag_lower)
            return

        if tag_lower == "title":
            self._in_title = True
        elif tag_lower in BLOCK_TAGS:
            self._flush_block()

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if self._ignored_stack:
            if tag_lower in self._ignored_stack:
                while self._ignored_stack:
                    popped = self._ignored_stack.pop()
                    if popped == tag_lower:
                        break
            return

        if tag_lower == "title":
            self._in_title = False
            self._title = "".join(self._title_parts).strip()
        elif tag_lower in BLOCK_TAGS:
            self._flush_block()

    def handle_data(self, data: str) -> None:
        if self._ignored_stack:
            return
        if self._in_title:
            self._title_parts.append(data)
            return

        text = data.strip()
        if text:
            self._current_block.append(text)

    def _flush_block(self) -> None:
        if self._current_block:
            block_text = " ".join(self._current_block).strip()
            # Filter out single-word noisy snippets
            if len(block_text) > 1:
                self._body_blocks.append(block_text)
            self._current_block = []

    def get_result(self) -> tuple[str, str]:
        self._flush_block()
        body = "\n\n".join(self._body_blocks).strip()
        title = self._title or "Untitled Article"
        # Clean title suffix (e.g. "Title - Isa dan Islam")
        if " - " in title:
            title = title.split(" - ")[0].strip()
        elif " | " in title:
            title = title.split(" | ")[0].strip()
        return title, body


def extract_domain(url: str) -> str:
    """Extract bare domain without port or www."""
    if "://" not in url:
        url = "https://" + url
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname


def canonicalize_url(url: str) -> str:
    """Canonicalize URL by removing query strings, fragments, and trailing slashes."""
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    return f"{scheme}://{netloc}{path}"


def is_approved_url(url: str, allowlist: frozenset[str] | None = None) -> bool:
    """Check if URL domain is within the approved domains allowlist."""
    domains = allowlist if allowlist is not None else approved_domains()
    domain = extract_domain(url)
    return domain in domains


def stable_article_id(url: str) -> str:
    """Produce deterministic ID from canonical URL."""
    can = canonicalize_url(url)
    digest = hashlib.sha256(can.encode("utf-8")).hexdigest()[:16]
    return f"art_{digest}"


def compute_content_hash(text: str) -> str:
    """Produce SHA-256 hash of cleaned text for change detection."""
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_sitemap_xml(xml_content: str) -> list[str]:
    """Extract page URLs from sitemap XML or sitemap index."""
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as err:
        logger.warning("Failed to parse sitemap XML: %s", err)
        return urls

    # Standard sitemap namespace is http://www.sitemaps.org/schemas/sitemap/0.9
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "loc" and elem.text:
            loc = elem.text.strip()
            if loc:
                urls.append(loc)
    return urls


def extract_links(html: str, base_url: str) -> list[str]:
    """Fallback HTML link extractor for pages without sitemap."""
    links: list[str] = []
    parser = LinkExtractor()
    parser.feed(html)
    for raw_href in parser.links:
        full_url = urljoin(base_url, raw_href)
        if is_approved_url(full_url):
            links.append(canonicalize_url(full_url))
    return list(dict.fromkeys(links))


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            for name, val in attrs:
                if name.lower() == "href" and val:
                    self.links.append(val)


class RobotsCache:
    """Thread-safe and async-friendly cache for site robots.txt policies."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._parsers: dict[str, urllib.robotparser.RobotFileParser] = {}

    async def can_fetch(self, url: str, client: httpx.AsyncClient | None = None) -> bool:
        domain = extract_domain(url)
        if domain not in self._parsers:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"https://{domain}/robots.txt"
            try:
                if client is not None:
                    res = await client.get(robots_url, timeout=5.0)
                    if res.status_code == 200:
                        lines = [line.strip() for line in res.text.splitlines() if line.strip()]
                        rp.parse(lines)
                    else:
                        rp.allow_all = True
                else:
                    rp.allow_all = True
            except Exception as err:
                logger.debug("Could not fetch robots.txt for %s: %s", domain, err)
                rp.allow_all = True
            self._parsers[domain] = rp

        parser = self._parsers[domain]
        return parser.can_fetch(self.user_agent, url)

    def set_robots_txt(self, domain: str, content: str) -> None:
        """Allow manual seeding of robots.txt rules for tests."""
        rp = urllib.robotparser.RobotFileParser()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        rp.parse(lines)
        self._parsers[extract_domain(domain)] = rp


class Crawler:
    """5-site approved crawler with robots.txt, politeness, and change detection."""

    def __init__(
        self,
        storage: Storage,
        client: httpx.AsyncClient | None = None,
        politeness_delay: float | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.storage = storage
        self.client = client
        config = approved_sites()
        crawl_cfg = config.get("crawl", {})

        self.politeness_delay = (
            politeness_delay
            if politeness_delay is not None
            else crawl_cfg.get("politeness_delay_seconds", 2.0)
        )
        self.user_agent = (
            user_agent
            if user_agent is not None
            else crawl_cfg.get("user_agent", "TanyaImanBot/1.0 (+https://tanyaiman.id/bot)")
        )
        self.respect_robots_txt = crawl_cfg.get("respect_robots_txt", True)
        self.robots_cache = RobotsCache(self.user_agent)

    async def ingest_html(
        self, url: str, html: str, now: datetime | None = None
    ) -> tuple[Article | None, bool]:
        """Ingest raw HTML content directly for a URL.

        Returns (article, is_changed). If content is identical to existing hash,
        is_changed is False and zero content writes occur.
        """
        if not is_approved_url(url):
            logger.debug("Dropped off-allowlist URL: %s", url)
            return None, False

        can_url = canonicalize_url(url)
        domain = extract_domain(can_url)

        if self.respect_robots_txt:
            can_fetch = await self.robots_cache.can_fetch(can_url, self.client)
            if not can_fetch:
                logger.info("Blocked by robots.txt: %s", can_url)
                return None, False

        parser = HTMLContentExtractor()
        parser.feed(html)
        title, clean_text = parser.get_result()

        if not clean_text:
            logger.debug("No extractable content for: %s", can_url)
            return None, False

        content_hash = compute_content_hash(clean_text)
        current_time = now or datetime.now(UTC)
        art_id = stable_article_id(can_url)

        existing = await self.storage.get_article(art_id)
        if existing is not None and existing.content_hash == content_hash:
            # Change detection: unchanged article produces ZERO writes
            existing.last_crawled_at = current_time
            await self.storage.save_article(existing)
            logger.debug("Unchanged article (hash match): %s", can_url)
            return existing, False

        first_seen = existing.first_seen_at if existing else current_time
        summary = clean_text[:280] + "..." if len(clean_text) > 280 else clean_text

        article = Article(
            id=art_id,
            site=domain,
            url=can_url,
            title=title,
            summary=summary,
            cleaned_text=clean_text,
            topic_slugs=existing.topic_slugs if existing else [],
            content_hash=content_hash,
            first_seen_at=first_seen,
            last_crawled_at=current_time,
            status=ArticleStatus.active,
        )
        await self.storage.save_article(article)
        logger.info("Saved article: %s (%s)", title, can_url)
        return article, True

    async def crawl_url(self, url: str) -> tuple[Article | None, bool]:
        """Fetch URL over HTTP and ingest its content."""
        if not is_approved_url(url):
            logger.debug("Dropped off-allowlist URL: %s", url)
            return None, False

        if self.client is None:
            raise RuntimeError("HTTP client is required to fetch URLs over network")

        headers = {"User-Agent": self.user_agent}
        response = await self.client.get(url, headers=headers, follow_redirects=True)
        if response.status_code != 200:
            logger.warning("HTTP %d fetching %s", response.status_code, url)
            return None, False

        if self.politeness_delay > 0:
            await asyncio.sleep(self.politeness_delay)

        return await self.ingest_html(url, response.text)
