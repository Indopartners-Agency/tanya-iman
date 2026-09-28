"""CLI and scheduled runner for corpus ingestion pipeline.

Usage:
    cd backend && uv run python -m ingestion.run
    cd backend && uv run python -m ingestion.run --site isadanislam.org
    cd backend && uv run python -m ingestion.run --dry-run
    cd backend && uv run python -m ingestion.run --force-embed
"""

from __future__ import annotations

import argparse
import asyncio
import logging

import httpx

from config.loader import approved_sites
from ingestion.chunker import ArticleChunker
from ingestion.crawler import Crawler, parse_sitemap_xml
from ingestion.embedder import CorpusEmbedder, get_embedder
from storage import get_storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingestion.run")


async def run_ingestion(
    site_filter: str | None = None,
    dry_run: bool = False,
    force_embed: bool = False,
) -> None:
    logger.info(
        "Starting ingestion run (site_filter=%s, dry_run=%s, force_embed=%s)",
        site_filter,
        dry_run,
        force_embed,
    )
    storage = get_storage()
    config = approved_sites()
    sites = config.get("sites", [])

    embedder = get_embedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker()

    total_articles_seen = 0
    total_articles_written = 0
    total_chunks_written = 0
    total_flags_raised = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        crawler = Crawler(storage=storage, client=client)

        for site_info in sites:
            domain = site_info["domain"]
            if site_filter and domain != site_filter:
                continue

            logger.info("Processing site: %s", domain)
            sitemap_url = site_info.get("sitemap")
            page_urls: list[str] = []

            if sitemap_url:
                try:
                    res = await client.get(sitemap_url, headers={"User-Agent": crawler.user_agent})
                    if res.status_code == 200:
                        page_urls = parse_sitemap_xml(res.text)
                        logger.info(
                            "Discovered %d URLs from sitemap for %s", len(page_urls), domain
                        )
                    else:
                        logger.warning("HTTP %d fetching sitemap %s", res.status_code, sitemap_url)
                except Exception as err:
                    logger.warning("Error fetching sitemap for %s: %s", domain, err)

            for url in page_urls:
                total_articles_seen += 1
                try:
                    article, changed = await crawler.crawl_url(url)
                    if article is None:
                        continue

                    if changed or force_embed:
                        clean_text = getattr(article, "cleaned_text", article.summary)
                        chunk_res = chunker.chunk_article(article, clean_text)
                        total_flags_raised += len(chunk_res.flagged)

                        if dry_run:
                            logger.info(
                                "[DRY RUN] Would index %d chunks (%d flagged) for %s",
                                len(chunk_res.chunks),
                                len(chunk_res.flagged),
                                url,
                            )
                        else:
                            written = await corpus_embedder.upsert_article_chunks(
                                article, chunk_res.chunks, chunk_res.flagged
                            )
                            total_chunks_written += written
                            total_articles_written += 1
                except Exception as err:
                    logger.error("Error processing URL %s: %s", url, err)

    logger.info(
        "Ingestion completed. Articles seen: %d, Articles written: %d, "
        "Chunks written: %d, Flags raised: %d",
        total_articles_seen,
        total_articles_written,
        total_chunks_written,
        total_flags_raised,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tanya Iman corpus ingestion pipeline.")
    parser.add_argument("--site", default=None, help="Filter crawl to a specific approved domain")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument(
        "--force-embed", action="store_true", help="Re-embed even unchanged articles"
    )
    args = parser.parse_args()

    asyncio.run(
        run_ingestion(
            site_filter=args.site,
            dry_run=args.dry_run,
            force_embed=args.force_embed,
        )
    )


if __name__ == "__main__":
    main()
