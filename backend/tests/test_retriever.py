"""Tests for vector retriever and allowlist gates (Task 4.4).

Coverage:
- A known question retrieves its known source article.
- An off-topic query returns nothing above threshold.
- The site filter is applied even when a rogue chunk exists in the collection.
- No more than 2 chunks from one article are returned.
- Fewer than 2 surviving chunks emits has_grounding=False.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from engine.retriever import VectorRetriever
from ingestion.chunker import ArticleChunker
from ingestion.embedder import CorpusEmbedder, DeterministicEmbedder
from models import Article, ArticleChunk
from models.enums import ArticleStatus
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


def _make_article(art_id: str, title: str, url: str, site: str) -> Article:
    now = datetime.now(UTC)
    return Article(
        id=art_id,
        site=site,
        url=url,
        title=title,
        content_hash="h123",
        first_seen_at=now,
        last_crawled_at=now,
        status=ArticleStatus.active,
    )


async def _seed_corpus(storage: MemoryStorage, embedder: DeterministicEmbedder):
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker(target_tokens=35, overlap_tokens=10)

    # Article 1: Kasih dan Pengampunan (isadanislam.org)
    art1 = _make_article(
        "art_kasih",
        "Kasih dan Pengampunan Sejati",
        "https://isadanislam.org/kasih-dan-pengampunan",
        "isadanislam.org",
    )
    text1 = (
        "Kasih Allah dan pengampunan dosa melalui pengorbanan Isa Al-Masih adalah "
        "pokok iman yang agung.\n\n"
        "Setiap orang yang mencari pengampunan sejati dapat menghampiri Allah dengan "
        "penuh keyakinan.\n\n"
        "Melalui Isa Al-Masih, manusia dipulihkan dari dosa dan menerima jaminan "
        "hidup kekal serta keselamatan abadi."
    )
    res1 = chunker.chunk_article(art1, text1)
    await corpus_embedder.upsert_article_chunks(art1, res1.chunks)

    # Article 2: Ketenangan Hati (isadanalquran.com)
    art2 = _make_article(
        "art_ketenangan",
        "Mencari Ketenangan Hati",
        "https://isadanalquran.com/ketenangan-hati",
        "isadanalquran.com",
    )
    text2 = (
        "Banyak manusia mengalami kekhawatiran dan ketakutan dalam menghadapi hari "
        "esok yang tidak pasti.\n\n"
        "Doa dan penyerahan diri kepada Sang Pencipta memberikan damai sejahtera "
        "melampaui akal pikiran.\n\n"
        "Ketenangan sejati bersumber dari kepastian kasih dan perlindungan Tuhan semesta alam."
    )
    res2 = chunker.chunk_article(art2, text2)
    await corpus_embedder.upsert_article_chunks(art2, res2.chunks)


async def test_known_question_retrieves_source_article():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    await _seed_corpus(storage, embedder)

    retriever = VectorRetriever(storage=storage, embedder=embedder, default_threshold=0.25)
    result = await retriever.retrieve(
        question="Bagaimana saya memperoleh kasih dan pengampunan dosa dari Isa Al-Masih?"
    )

    assert result.has_grounding is True
    assert len(result.chunks) >= 2
    # Verify the most relevant article was retrieved
    article_ids = [c.article_id for c in result.chunks]
    assert "art_kasih" in article_ids

    # Citations match the chunks
    assert len(result.citations) >= 1
    assert result.citations[0].url == "https://isadanislam.org/kasih-dan-pengampunan"


async def test_off_topic_query_returns_no_grounding():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    await _seed_corpus(storage, embedder)

    # Use high threshold for strict testing
    retriever = VectorRetriever(storage=storage, embedder=embedder, default_threshold=0.72)
    result = await retriever.retrieve(
        question="Berapa harga resep kue bolu pandan kukus di pasar swalayan surabaya?"
    )

    # Completely off-topic question has no semantic overlap with theology
    assert result.has_grounding is False
    assert len(result.chunks) < 2


async def test_site_filter_rejects_rogue_chunk():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    await _seed_corpus(storage, embedder)

    # Insert a rogue chunk directly with an off-allowlist domain
    now = datetime.now(UTC)
    rogue_vec = await embedder.embed_query("kasih pengampunan dosa isa al-masih")
    rogue_chunk = ArticleChunk(
        id="rogue_chunk_99",
        article_id="art_rogue",
        site="rogue-unapproved-site.com",  # NOT in approved_sites.yml
        url="https://rogue-unapproved-site.com/fake-article",
        title="Rogue Unapproved Article",
        chunk_index=0,
        text="Kasih dan pengampunan dosa palsu yang disisipkan dari luar.",
        embedding=rogue_vec,
        token_count=100,
        is_retrievable=True,
        created_at=now,
    )
    await storage.save_chunk(rogue_chunk)

    retriever = VectorRetriever(storage=storage, embedder=embedder, default_threshold=0.20)
    result = await retriever.retrieve(question="kasih pengampunan dosa")

    # Defense-in-depth: Rogue site MUST NOT appear in retrieved chunks or citations
    retrieved_sites = [c.site for c in result.chunks]
    assert "rogue-unapproved-site.com" not in retrieved_sites
    citation_urls = [cit.url for cit in result.citations]
    assert "https://rogue-unapproved-site.com/fake-article" not in citation_urls


async def test_per_article_cap_max_two_chunks():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)

    # Create an article with 5 chunks
    now = datetime.now(UTC)
    art = _make_article(
        "art_multi", "Artikel Panjang", "https://isadanislam.org/panjang", "isadanislam.org"
    )
    query_text = "keselamatan kekal"
    vec = await embedder.embed_query(query_text)

    chunks = [
        ArticleChunk(
            id=f"art_multi#{i}",
            article_id="art_multi",
            site="isadanislam.org",
            url="https://isadanislam.org/panjang",
            title="Artikel Panjang",
            chunk_index=i,
            text=f"Bagian {i} tentang keselamatan kekal dan damai.",
            embedding=vec,
            token_count=80,
            is_retrievable=True,
            created_at=now,
        )
        for i in range(5)
    ]
    await corpus_embedder.upsert_article_chunks(art, chunks)

    retriever = VectorRetriever(storage=storage, embedder=embedder, default_threshold=0.20)
    result = await retriever.retrieve(question=query_text)

    # Per-article cap: At most 2 chunks from "art_multi"
    multi_chunks = [c for c in result.chunks if c.article_id == "art_multi"]
    assert len(multi_chunks) <= 2


async def test_query_includes_recent_turns():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    retriever = VectorRetriever(storage=storage, embedder=embedder)

    query = retriever.build_query_text(
        question="Lalu apa jaminannya?",
        recent_turns=[
            "Apa yang diajarkan Isa tentang keselamatan?",
            "Isa mengajarkan bahwa Dialah jalan kebenaran dan hidup.",
        ],
    )
    assert "Apa yang diajarkan Isa tentang keselamatan?" in query
    assert "Isa mengajarkan bahwa Dialah jalan kebenaran dan hidup." in query
    assert "Lalu apa jaminannya?" in query


async def test_multi_topic_session_does_not_pollute_standalone_question():
    from engine.retriever import extract_relevant_context_turns, is_followup_question
    from models.enums import AnswerSource
    from models.schemas import Question

    # Standalone questions on new topics should NOT pull in prior fasting turns
    assert is_followup_question("Apakah orang Kristen menyembah 3 tuhan?") is False
    assert is_followup_question("Siapakah Isa?") is False
    assert is_followup_question("Bagaimana cara berpuasa?") is False

    # Dependent follow-ups SHOULD be recognized as follow-ups
    assert is_followup_question("Lalu apa jaminannya?") is True
    assert is_followup_question("Mengapa demikian?") is True

    prior_q = Question(
        id="q_fasting",
        session_id="s1",
        uid="u1",
        question_text="Bagaimana pandangan tentang puasa?",
        answer_text="Puasa dalam ajaran Isa Al-Masih...",
        answer_source=AnswerSource.generated,
        topic_slug="ibadah-dan-doa",
        created_at=datetime.now(UTC),
    )

    # When switching to a standalone topic, context turns are excluded from vector query
    turns_standalone = extract_relevant_context_turns(
        "Siapakah Isa?", [prior_q], topic_slug="identitas-isa"
    )
    assert turns_standalone == []

    # When asking a follow-up on the same topic, context turns are preserved
    turns_followup = extract_relevant_context_turns(
        "Lalu apa jaminannya?", [prior_q], topic_slug="ibadah-dan-doa"
    )
    assert turns_followup == ["Bagaimana pandangan tentang puasa?"]


async def test_retriever_skips_index_and_category_chunks():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    await _seed_corpus(storage, embedder)

    now = datetime.now(UTC)
    vec = await embedder.embed_query(
        "Bagaimana saya memperoleh kasih dan pengampunan dosa dari Isa Al-Masih?"
    )
    index_chunk = ArticleChunk(
        id="index_chunk_1",
        article_id="art_index",
        site="isadanislam.org",
        url="https://isadanislam.org/maksud-situs-ini/daftar-artikel",
        title="Daftar Artikel-artikel dalam situs Isa dan Islam",
        chunk_index=0,
        text="Daftar seluruh artikel tentang kasih dan pengampunan dosa.",
        embedding=vec,
        token_count=50,
        is_retrievable=True,
        created_at=now,
    )
    cat_chunk = ArticleChunk(
        id="cat_chunk_1",
        article_id="art_cat",
        site="isadanislam.org",
        url="https://isadanislam.org/alkitab-infographic",
        title="Alkitab Arsip",
        chunk_index=0,
        text="Arsip kategori alkitab infographic tentang kasih.",
        embedding=vec,
        token_count=50,
        is_retrievable=True,
        created_at=now,
    )
    await storage.save_chunk(index_chunk)
    await storage.save_chunk(cat_chunk)

    retriever = VectorRetriever(storage=storage, embedder=embedder, default_threshold=0.20)
    result = await retriever.retrieve(
        question="Bagaimana saya memperoleh kasih dan pengampunan dosa dari Isa Al-Masih?"
    )

    cited_urls = [c.url for c in result.citations]
    assert "https://isadanislam.org/maksud-situs-ini/daftar-artikel" not in cited_urls
    assert "https://isadanislam.org/alkitab-infographic" not in cited_urls
