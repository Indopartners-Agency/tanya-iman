"""Tests for vector embedder and corpus upsert pipeline (Task 4.3).

Coverage:
- Embeddings are written at declared dimensionality (768).
- Model identifier is stamped onto every chunk (embedding_model).
- Re-chunking/re-embedding replaces obsolete chunks from previous runs.
- Retired articles' chunks leave the searchable set.
- Resumable: repeated upserts do not duplicate chunks.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ingestion.chunker import ArticleChunker
from ingestion.embedder import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_NAME,
    CorpusEmbedder,
    DeterministicEmbedder,
)
from models import Article
from models.enums import ArticleStatus
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


def _make_article(art_id: str, title: str, url: str) -> Article:
    now = datetime.now(UTC)
    return Article(
        id=art_id,
        site="isadanislam.org",
        url=url,
        title=title,
        content_hash="hash_123",
        first_seen_at=now,
        last_crawled_at=now,
        status=ArticleStatus.active,
    )


async def test_embeddings_dimensionality_and_model_stamp():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker()

    article = _make_article(
        "art_dim_test", "Tentang Kasih", "https://isadanislam.org/tentang-kasih"
    )
    text = (
        "Kasih sejati tidak menuntut balas, melainkan memberi diri bagi keselamatan sesama. "
        "Melalui ajaran Isa Al-Masih, kita belajar mengasihi musuh dan memberkati orang yang "
        "mengutuk."
    )

    chunk_res = chunker.chunk_article(article, text)
    written_count = await corpus_embedder.upsert_article_chunks(
        article, chunk_res.chunks, chunk_res.flagged
    )

    assert written_count == len(chunk_res.chunks)
    assert written_count > 0

    saved_chunks = await storage.list_chunks_by_article(article.id)
    assert len(saved_chunks) == written_count

    for chunk in saved_chunks:
        assert chunk.embedding is not None
        assert len(chunk.embedding) == EMBEDDING_DIMENSION  # 768
        assert chunk.embedding_model == EMBEDDING_MODEL_NAME


async def test_upsert_replaces_obsolete_chunks():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker()

    article = _make_article("art_obsolete", "Artikel Berganti", "https://isadanislam.org/berganti")

    # Initial crawl produces 3 paragraphs / chunks
    initial_text = "Paragraf satu.\n\nParagraf dua.\n\nParagraf tiga."
    res1 = chunker.chunk_article(article, initial_text)
    await corpus_embedder.upsert_article_chunks(article, res1.chunks)

    initial_chunks = await storage.list_chunks_by_article(article.id)
    assert len(initial_chunks) >= 1

    # Second crawl of same article with completely new text -> Old chunks replaced
    new_text = "Teks yang diperbarui sepenuhnya dengan satu penjelasan ringkas."
    res2 = chunker.chunk_article(article, new_text)
    await corpus_embedder.upsert_article_chunks(article, res2.chunks)

    updated_chunks = await storage.list_chunks_by_article(article.id)
    assert len(updated_chunks) == len(res2.chunks)

    # Obsolete chunk texts should no longer exist
    all_texts = " ".join(c.text for c in updated_chunks)
    assert "Paragraf satu" not in all_texts
    assert "Teks yang diperbarui" in all_texts


async def test_retired_articles_leave_searchable_set():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker()

    article = _make_article("art_retire", "Artikel Lama", "https://isadanislam.org/artikel-lama")
    text = "Dokumen ini akan dihapus dari situs sumber pada masa mendatang."

    res = chunker.chunk_article(article, text)
    await corpus_embedder.upsert_article_chunks(article, res.chunks)

    assert len(await storage.list_chunks_by_article(article.id)) > 0

    # Retire article
    await corpus_embedder.retire_article(article.id)

    # Chunks are purged from searchable set
    chunks_after = await storage.list_chunks_by_article(article.id)
    assert len(chunks_after) == 0

    # Article status is marked retired
    saved_art = await storage.get_article(article.id)
    assert saved_art is not None
    assert saved_art.status == ArticleStatus.retired


async def test_resumable_upsert_no_duplicates():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker()

    article = _make_article("art_resumable", "Idempotensi", "https://isadanislam.org/idempotensi")
    text = "Menjamin bahwa eksekusi ulang tidak menduplikasi data di Firestore."

    res = chunker.chunk_article(article, text)

    # First run
    await corpus_embedder.upsert_article_chunks(article, res.chunks)
    count1 = await storage.count_article_chunks()

    # Second run (simulating resumed or re-triggered ingestion)
    await corpus_embedder.upsert_article_chunks(article, res.chunks)
    count2 = await storage.count_article_chunks()

    assert count1 == count2
