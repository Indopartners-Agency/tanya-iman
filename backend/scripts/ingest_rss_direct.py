import asyncio
import logging
from pathlib import Path
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.chunker import ArticleChunker
from ingestion.crawler import HTMLContentExtractor, compute_content_hash, stable_article_id
from ingestion.embedder import CorpusEmbedder, VertexAIEmbedder
from models.schemas import Article
from storage.firestore import FirestoreStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_rss")


async def process_single_item(
    item: ET.Element,
    file_name: str,
    namespaces: dict[str, str],
    storage: FirestoreStorage,
    embedder: CorpusEmbedder,
    chunker: ArticleChunker,
    sem: asyncio.Semaphore,
) -> str:
    """Processes a single RSS item.

    Returns: 'ingested', 'skipped', or 'error'
    """
    async with sem:
        link_elem = item.find("link")
        title_elem = item.find("title")
        content_elem = item.find("content:encoded", namespaces)

        if link_elem is None or content_elem is None or not content_elem.text:
            return "skipped"

        url = link_elem.text.strip()
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled"
        raw_html = content_elem.text

        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")

        extractor = HTMLContentExtractor()
        try:
            extractor.feed(raw_html)
            ext_title, clean_content = extractor.get_result()
        except Exception as e:
            logger.error(f"Failed to extract HTML for {url}: {e}")
            return "error"

        if not clean_content:
            return "skipped"

        # Prefer RSS item title if available, otherwise extracted title
        final_title = title if (title and title != "Untitled") else (ext_title if ext_title != "Untitled Article" else "Untitled")

        content_hash = compute_content_hash(clean_content)
        art_id = stable_article_id(url)

        try:
            existing = await storage.get_article(art_id)
            if existing and existing.content_hash == content_hash:
                return "skipped"  # Unchanged
        except Exception as e:
            logger.warning(f"Could not check existing article {art_id}: {e}")
            existing = None

        summary = clean_content[:280] + "..." if len(clean_content) > 280 else clean_content
        now = datetime.now(timezone.utc)

        article = Article(
            id=art_id,
            site=domain,
            url=url,
            title=final_title,
            summary=summary,
            cleaned_text=clean_content,
            topic_slugs=existing.topic_slugs if existing else [],
            content_hash=content_hash,
            first_seen_at=existing.first_seen_at if existing else now,
            last_crawled_at=now,
        )

        chunk_result = chunker.chunk_article(article, clean_content, now=now)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await embedder.upsert_article_chunks(article, chunk_result.chunks, chunk_result.flagged)
                return "ingested"
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to upsert chunks for '{final_title}' ({url}): {e}")
                    return "error"
                await asyncio.sleep(1.0 * (attempt + 1))
        return "error"


async def process_rss_file(
    file_path: Path,
    storage: FirestoreStorage,
    embedder: CorpusEmbedder,
    chunker: ArticleChunker,
    sem: asyncio.Semaphore,
) -> None:
    logger.info(f"==> Processing RSS file: {file_path.name}")

    content_xml = file_path.read_text(encoding="utf-8", errors="replace")

    try:
        root = ET.fromstring(content_xml)
    except Exception as e:
        logger.error(f"Failed to parse {file_path.name}: {e}")
        return

    namespaces = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    channel = root.find("channel")
    if channel is None:
        return

    items = channel.findall("item")
    total_items = len(items)
    logger.info(f"Found {total_items} items in {file_path.name}")

    batch_size = 20
    ingested_count = 0
    skipped_count = 0
    error_count = 0

    for i in range(0, total_items, batch_size):
        batch = items[i : i + batch_size]
        tasks = [
            process_single_item(item, file_path.name, namespaces, storage, embedder, chunker, sem)
            for item in batch
        ]
        results = await asyncio.gather(*tasks)
        for res in results:
            if res == "ingested":
                ingested_count += 1
            elif res == "skipped":
                skipped_count += 1
            else:
                error_count += 1

        logger.info(
            f"[{file_path.name}] Progress: {ingested_count} ingested, {skipped_count} skipped/unchanged, "
            f"{error_count} errors ({min(i + batch_size, total_items)}/{total_items})"
        )

    logger.info(
        f"Finished {file_path.name}: {ingested_count} ingested, {skipped_count} skipped, {error_count} errors."
    )


async def main() -> None:
    project_id = "project-philip-501910"
    db_name = "tanya-iman"

    logger.info(f"Connecting to Firestore ({project_id} / {db_name}) with ADC...")
    storage = FirestoreStorage(project=project_id, database=db_name)
    embedder_provider = VertexAIEmbedder(project_id=project_id)
    embedder = CorpusEmbedder(storage=storage, embedder=embedder_provider)
    chunker = ArticleChunker()

    sem = asyncio.Semaphore(8)

    rss_dir = Path("/root/projects/tanya-iman/Websites-rss-feed")
    rss_files = sorted(list(rss_dir.glob("*.rss.txt")))

    for rss_file in rss_files:
        await process_rss_file(rss_file, storage, embedder, chunker, sem)

    logger.info("==> ALL RSS FEEDS INGESTION COMPLETE!")


if __name__ == "__main__":
    asyncio.run(main())
