"""Tests for article chunking and forbidden-term screening (Task 4.2 & OI-1).

Coverage:
- Chunks stay within token bounds.
- Overlap is present between adjacent chunks.
- A chunk never spans two articles.
- Forbidden-term chunks ("Tuhan", "TUHAN", "Yesus", "Jesus") are flagged into review.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ingestion.chunker import ArticleChunker
from models import Article
from models.enums import ArticleStatus, ChunkDecision


def _sample_article(art_id: str, title: str, url: str) -> Article:
    now = datetime.now(UTC)
    return Article(
        id=art_id,
        site="isadanislam.org",
        url=url,
        title=title,
        content_hash="dummy_hash",
        first_seen_at=now,
        last_crawled_at=now,
        status=ArticleStatus.active,
    )


def test_chunks_stay_within_token_bound():
    chunker = ArticleChunker(target_tokens=400, overlap_tokens=80)
    article = _sample_article("art_test1", "Kasih Sejati", "https://isadanislam.org/kasih-sejati")

    # Generate multi-paragraph text totaling ~1200 words (~1600 tokens)
    paragraphs = [
        f"Paragraf ke-{i}: Ajaran mengenai kebaikan dan kebenaran selalu menjadi fondasi "
        "kehidupan manusia. Setiap pribadi merindukan kedamaian batin dan pemulihan jiwa dari "
        "beban yang menekan. Melalui hikmat yang benar, seseorang dapat menemukan jalan hidup "
        "yang penuh harapan dan sukacita sejati."
        for i in range(1, 30)
    ]
    text = "\n\n".join(paragraphs)

    result = chunker.chunk_article(article, text)

    assert len(result.chunks) > 1
    for chunk in result.chunks:
        assert chunk.token_count <= 480  # Target ~400 + small tolerance for paragraph integrity
        assert chunk.article_id == article.id
        assert chunk.site == article.site
        assert chunk.url == article.url
        assert chunk.title == article.title


def test_overlap_present_between_adjacent_chunks():
    chunker = ArticleChunker(target_tokens=200, overlap_tokens=60)
    article = _sample_article("art_test2", "Jalan Hidup", "https://isadanislam.org/jalan-hidup")

    paragraphs = [
        f"Poin {i}: Refleksi mendalam mengenai keselamatan dan kasih abadi "
        "yang tidak pernah berkesudahan bagi setiap orang."
        for i in range(1, 15)
    ]
    text = "\n\n".join(paragraphs)

    result = chunker.chunk_article(article, text)
    assert len(result.chunks) >= 2

    # Check that adjacent chunks share text from the overlap window
    for i in range(len(result.chunks) - 1):
        curr_text = result.chunks[i].text
        next_text = result.chunks[i + 1].text

        # Find paragraphs in current chunk
        curr_paras = set(curr_text.split("\n\n"))
        next_paras = set(next_text.split("\n\n"))

        shared = curr_paras.intersection(next_paras)
        assert len(shared) >= 1, f"Expected overlap between chunk {i} and {i + 1}"


def test_chunk_never_spans_two_articles():
    chunker = ArticleChunker()
    art1 = _sample_article("art_alpha", "Artikel Pertama", "https://isadanislam.org/pertama")
    art2 = _sample_article("art_beta", "Artikel Kedua", "https://isadanislam.org/kedua")

    text1 = "Isi dari artikel pertama yang membahas pengampunan dosa secara menyeluruh."
    text2 = (
        "Isi dari artikel kedua yang membahas makna ibadah yang berkenan di hadapan Sang Pencipta."
    )

    res1 = chunker.chunk_article(art1, text1)
    res2 = chunker.chunk_article(art2, text2)

    for c in res1.chunks:
        assert c.article_id == "art_alpha"
        assert c.url == "https://isadanislam.org/pertama"
        assert "kedua" not in c.text

    for c in res2.chunks:
        assert c.article_id == "art_beta"
        assert c.url == "https://isadanislam.org/kedua"
        assert "pertama" not in c.text


def test_forbidden_term_chunks_are_flagged():
    chunker = ArticleChunker()
    article = _sample_article("art_flagged", "Diskusi Teologis", "https://isadanislam.org/diskusi")

    # Paragraph 1 has forbidden term "Yesus" and "TUHAN"
    # Paragraph 2 has clean theological terms ("Isa Al-Masih", "Allah")
    text = (
        "Sebagian terjemahan kuno menuliskan nama Yesus Kristus dan menyebut "
        "gelar TUHAN dalam teks tertentu.\n\n"
        "Namun dalam konteks dialog dengan sahabat Muslim, sebutan Isa Al-Masih dan Kalimatullah "
        "merupakan istilah yang terhormat dan penuh dengan kebenaran ilahi."
    )

    result = chunker.chunk_article(article, text)
    assert len(result.chunks) >= 1

    # First chunk must flag the forbidden terms
    flagged_chunk = result.chunks[0]
    assert flagged_chunk.has_forbidden_term is True

    # Check generated FlaggedChunk entry in review collection
    assert len(result.flagged) == 1
    flag = result.flagged[0]
    assert flag.chunk_id == flagged_chunk.id
    assert flag.article_id == article.id
    assert "TUHAN" in flag.matched_terms
    assert "Yesus" in flag.matched_terms
    assert flag.decision == ChunkDecision.pending


def test_clean_text_produces_no_flags():
    chunker = ArticleChunker()
    article = _sample_article("art_clean", "Kasih Allah", "https://isadanislam.org/kasih-allah")

    text = (
        "Isa Al-Masih datang membawa kabar baik dan rahmat bagi seluruh umat manusia. "
        "Allah menunjukkan kasih-Nya yang sejati melalui firman dan kebenaran yang hidup."
    )

    result = chunker.chunk_article(article, text)
    assert len(result.chunks) == 1
    assert result.chunks[0].has_forbidden_term is False
    assert len(result.flagged) == 0
