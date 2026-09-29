"""Tests for full production RAG pipeline (PIP Task 5.6)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from engine.base import EngineRequest
from engine.classifier import RelevanceClassifier
from engine.composer import AnswerComposer
from engine.rag import RAGEngine
from engine.retriever import VectorRetriever
from ingestion.chunker import ArticleChunker
from ingestion.embedder import CorpusEmbedder, DeterministicEmbedder
from models.enums import AnswerSource
from models.schemas import Article, Citation, Topic
from providers.llm import FakeLLM
from storage.memory import MemoryStorage


def _make_article(article_id: str, title: str, url: str) -> Article:
    return Article(
        id=article_id,
        site="isadanislam.org",
        url=url,
        title=title,
        content_hash="hash",
        first_seen_at=datetime.now(UTC),
        last_crawled_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_storage():
    return MemoryStorage()


@pytest.mark.asyncio
async def test_pipeline_refusal_on_irrelevant():
    storage = MemoryStorage()
    llm = FakeLLM()
    llm.next_response = {"relevance": "irrelevant", "topic_slug": None}

    classifier = RelevanceClassifier(llm=llm)
    engine = RAGEngine(storage=storage, classifier=classifier)

    req = EngineRequest(
        question_text="Bagaimana cara memperbaiki kulkas?",
        uid="u_test",
        session_id="s_test",
    )

    result = await engine.answer(req)
    assert result.answer_source == AnswerSource.refusal
    assert "hanya dapat menjawab pertanyaan seputar iman" in result.answer_text


@pytest.mark.asyncio
async def test_pipeline_emotional_only_deferral():
    storage = MemoryStorage()
    llm = FakeLLM()
    llm.next_response = {"relevance": "emotional_only", "topic_slug": None}

    classifier = RelevanceClassifier(llm=llm)
    engine = RAGEngine(storage=storage, classifier=classifier)

    req = EngineRequest(
        question_text="Saya sangat sedih dan hancur hati, tolong dengarkan saya.",
        uid="u_test",
        session_id="s_test",
    )

    result = await engine.answer(req)
    assert result.answer_source == AnswerSource.emotional_deferral
    assert "tidak membahas topik emosional sebagai bahan jawaban" in result.answer_text


@pytest.mark.asyncio
async def test_pipeline_curated_answer_override():
    storage = MemoryStorage()
    llm = FakeLLM()
    llm.next_response = {"relevance": "theology", "topic_slug": "jalan-keselamatan"}

    # Seed published curated topic
    topic = Topic(
        slug="jalan-keselamatan",
        name_id="Jalan Keselamatan",
        name_en="Path of Salvation",
        curated_answer="Keselamatan kekal adalah anugerah Allah yang sejati bagi setiap orang.",
        curated_citations=[
            Citation(title="Kasih", url="https://isadanislam.org/kasih", site="isadanislam.org")
        ],
        curated_status="published",
    )
    await storage.save_topic(topic)

    classifier = RelevanceClassifier(llm=llm)
    engine = RAGEngine(storage=storage, classifier=classifier)

    req = EngineRequest(
        question_text="Bagaimana jalan keselamatan?",
        uid="u_test",
        session_id="s_test",
    )

    result = await engine.answer(req)
    assert result.answer_source == AnswerSource.curated
    assert result.answer_text == topic.curated_answer
    assert len(result.citations) == 1


@pytest.mark.asyncio
async def test_pipeline_no_grounding():
    storage = MemoryStorage()  # Empty corpus
    llm = FakeLLM()
    llm.next_response = {"relevance": "theology", "topic_slug": "lainnya"}

    classifier = RelevanceClassifier(llm=llm)
    engine = RAGEngine(storage=storage, classifier=classifier)

    req = EngineRequest(
        question_text="Siapakah nama nabi yang menulis kitab ini?",
        uid="u_test",
        session_id="s_test",
    )

    result = await engine.answer(req)
    assert result.answer_source == AnswerSource.no_grounding
    assert "belum memiliki bahan yang cukup" in result.answer_text


@pytest.mark.asyncio
async def test_pipeline_full_grounded_answer():
    storage = MemoryStorage()
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker()

    # Seed 2 articles in corpus
    art1 = _make_article("art1", "Kasih Allah", "https://isadanislam.org/kasih-allah")
    art2 = _make_article("art2", "Pengampunan Dosa", "https://isadanislam.org/pengampunan-dosa")

    text1 = (
        "Kasih Allah melimpah bagi seluruh umat manusia melalui pengorbanan Isa Al-Masih.\n\n"
        "Setiap orang yang mencari pengampunan sejati dapat menghampiri Allah dengan "
        "ketulusan hati."
    )
    text2 = (
        "Kasih Allah dan pengampunan dosa menghapus segala beban jiwa dan ketakutan manusia.\n\n"
        "Melalui Isa Al-Masih manusia diperdamaikan dengan Sang Pencipta dalam damai abadi."
    )

    res1 = chunker.chunk_article(art1, text1)
    res2 = chunker.chunk_article(art2, text2)
    await corpus_embedder.upsert_article_chunks(art1, res1.chunks)
    await corpus_embedder.upsert_article_chunks(art2, res2.chunks)

    # Mock classifier and composer
    llm = FakeLLM()
    # 1st call: classifier
    # 2nd call: composer
    responses = [
        {"relevance": "theology", "topic_slug": "jalan-keselamatan"},
        {
            "answer": (
                "Terima kasih atas pertanyaan Anda yang sangat berharga. Kasih Allah melimpah "
                "bagi seluruh umat manusia, dan melalui Isa Al-Masih setiap orang memperoleh "
                "pengampunan dosa serta damai sejahtera abadi dalam kehidupan mereka yang "
                "mencari kebenaran dengan ketulusan hati."
            ),
            "used_passages": [1, 2],
            "quran_reference": None,
            "bible_references": ["Yohanes 3:16"],
            "confidence": "high",
        },
    ]

    async def _mock_complete(system, user, *args, **kwargs):
        return responses.pop(0)

    llm.complete_json = _mock_complete  # type: ignore

    retriever = VectorRetriever(storage=storage, embedder=embedder, default_threshold=0.10)
    classifier = RelevanceClassifier(llm=llm)
    composer = AnswerComposer(primary_llm=llm)

    engine = RAGEngine(
        storage=storage,
        retriever=retriever,
        classifier=classifier,
        composer=composer,
    )

    req = EngineRequest(
        question_text="Bagaimana kasih Allah mengampuni dosa manusia?",
        uid="u_test",
        session_id="s_test",
    )

    result = await engine.answer(req)
    assert result.answer_source == AnswerSource.generated
    assert "Isa Al-Masih" in result.answer_text
    assert len(result.citations) >= 1
    assert result.citations[0].site == "isadanislam.org"
    assert len(result.validator_failures) == 0


def test_get_engine_rag_factory(monkeypatch):
    import config.settings
    from engine.base import get_engine, reset_engine
    from engine.rag import RAGEngine

    reset_engine(None)
    monkeypatch.setenv("ANSWER_ENGINE", "rag")
    config.settings.get_settings.cache_clear()

    engine = get_engine()
    assert isinstance(engine, RAGEngine)
    assert engine.name == "rag"

    reset_engine(None)
    config.settings.get_settings.cache_clear()
