"""Tests for ComplianceValidator V1 through V5 (PIP Task 5.5)."""

from __future__ import annotations

from datetime import UTC, datetime

from engine.validators import ComplianceValidator, format_failures_for_repair
from models.enums import ArticleStatus, ValidatorCode
from models.schemas import ArticleChunk, Citation


def _dummy_chunk(chunk_id: str, title: str, text: str, url: str) -> ArticleChunk:
    return ArticleChunk(
        id=chunk_id,
        article_id="art_1",
        site="isadanislam.org",
        url=url,
        title=title,
        chunk_index=0,
        text=text,
        created_at=datetime.now(UTC),
    )


def test_v1_length_validator():
    validator = ComplianceValidator()
    # 24 words
    text_24 = " ".join(["kata"] * 23) + " Allah"
    res_24 = validator.validate(text_24)
    assert not res_24.valid
    assert ValidatorCode.v1_too_short in res_24.codes

    # 25 words
    text_25 = " ".join(["kata"] * 24) + " Allah"
    res_25 = validator.validate(text_25)
    assert ValidatorCode.v1_too_short not in res_25.codes

    # 250 words
    text_250 = " ".join(["kata"] * 249) + " Allah"
    res_250 = validator.validate(text_250)
    assert ValidatorCode.v1_too_long not in res_250.codes

    # 251 words
    text_251 = " ".join(["kata"] * 250) + " Allah"
    res_251 = validator.validate(text_251)
    assert not res_251.valid
    assert ValidatorCode.v1_too_long in res_251.codes


def test_v2_terminology_validator():
    validator = ComplianceValidator()
    clean_base = " ".join(["kata"] * 25)

    # Missing both Allah and Isa Al-Masih
    res_missing = validator.validate(clean_base)
    assert ValidatorCode.v2_missing_required_term in res_missing.codes

    # Forbidden term 'Yesus'
    res_yesus = validator.validate(clean_base + " Allah Yesus")
    assert ValidatorCode.v2_forbidden_term in res_yesus.codes

    # Forbidden term 'TUHAN'
    res_tuhan = validator.validate(clean_base + " Allah TUHAN semesta")
    assert ValidatorCode.v2_forbidden_term in res_tuhan.codes

    # Clean terminology
    res_clean = validator.validate(clean_base + " Allah Isa Al-Masih")
    assert ValidatorCode.v2_forbidden_term not in res_clean.codes
    assert ValidatorCode.v2_missing_required_term not in res_clean.codes


def test_v3_scripture_balance_validator():
    validator = ComplianceValidator()
    words_pad = " ".join(["berkata"] * 30)

    # Multiple Quran references
    text_multi_quran = (
        f"Allah mengasihi manusia seperti tertulis dalam QS Al-Baqarah 2:255 "
        f"dan juga QS Ali-Imran 3:3. {words_pad} Yohanes 3:16 dan Roma 5:8."
    )
    res_multi = validator.validate(text_multi_quran)
    assert ValidatorCode.v3_multiple_quran_refs in res_multi.codes

    # Quran ref in late position (> 25% of answer)
    text_late_quran = (
        f"Allah yang pengasih mengajarkan kebajikan sejati. {words_pad} "
        f"Hal ini selaras dengan QS Al-Baqarah 2:255 serta Yohanes 3:16 dan Roma 5:8."
    )
    res_late = validator.validate(text_late_quran)
    assert ValidatorCode.v3_quran_not_leading in res_late.codes

    # Quran ref with insufficient Bible refs (needs at least 2)
    text_quran_one_bible = (
        f"QS Al-Fatihah 1:1 mengingatkan kita akan rahmat Allah. {words_pad} "
        f"Sebagaimana juga Yohanes 3:16."
    )
    res_minority = validator.validate(text_quran_one_bible)
    assert ValidatorCode.v3_bible_minority in res_minority.codes

    # Valid scripture balance: leading Quran ref + 2 Bible refs
    text_valid = (
        f"Dalam QS Ali-Imran 3:45 disebutkan tentang kemuliaan Isa Al-Masih. {words_pad} "
        f"Kitab Suci menegaskan kasih Allah dalam Yohanes 3:16 serta Roma 5:8 bagi kita."
    )
    res_valid = validator.validate(text_valid)
    assert ValidatorCode.v3_multiple_quran_refs not in res_valid.codes
    assert ValidatorCode.v3_quran_not_leading not in res_valid.codes
    assert ValidatorCode.v3_bible_minority not in res_valid.codes

    # No scripture cited at all is completely valid
    text_no_scripture = (
        f"Allah penuh dengan kasih dan rahmat kepada setiap manusia yang mencari-Nya. {words_pad} "
        f"Isa Al-Masih menuntun setiap hati menuju kedamaian sejati."
    )
    res_none = validator.validate(text_no_scripture)
    assert ValidatorCode.v3_multiple_quran_refs not in res_none.codes
    assert ValidatorCode.v3_quran_not_leading not in res_none.codes
    assert ValidatorCode.v3_bible_minority not in res_none.codes


def test_v4_citation_integrity():
    validator = ComplianceValidator()
    chunk1 = _dummy_chunk("c1", "Kasih Allah", "Penjelasan kasih", "https://isadanislam.org/kasih")
    retrieved = [chunk1]

    # Citation count outside 1..2
    sample_text = "Allah mengasihi manusia dengan damai sejahtera yang kekal melalui Isa Al-Masih."
    res_zero = validator.validate(
        sample_text,
        citations=[],
        retrieved_chunks=retrieved,
    )
    assert ValidatorCode.v4_citation_count in res_zero.codes

    # Citation not retrieved
    unretrieved_cit = Citation(
        title="Buku Lain", url="https://isadanislam.org/lain", site="isadanislam.org"
    )
    res_unretrieved = validator.validate(
        sample_text,
        citations=[unretrieved_cit],
        retrieved_chunks=retrieved,
    )
    assert ValidatorCode.v4_citation_not_retrieved in res_unretrieved.codes

    # Citation off allowlist
    rogue_cit = Citation(
        title="Situs Luar", url="https://wikipedia.org/wiki/Isa", site="wikipedia.org"
    )
    res_rogue = validator.validate(
        sample_text,
        citations=[rogue_cit],
        retrieved_chunks=[_dummy_chunk("c2", "W", "T", "https://wikipedia.org/wiki/Isa")],
    )
    assert ValidatorCode.v4_citation_off_allowlist in res_rogue.codes

    # Citation from retired article
    valid_cit = Citation(
        title="Kasih Allah", url="https://isadanislam.org/kasih", site="isadanislam.org"
    )
    res_retired = validator.validate(
        sample_text,
        citations=[valid_cit],
        retrieved_chunks=retrieved,
        article_statuses={"https://isadanislam.org/kasih": ArticleStatus.retired},
    )
    assert ValidatorCode.v4_citation_retired in res_retired.codes


def test_v5_grounding_and_repair_formatting():
    validator = ComplianceValidator()
    chunk_text = (
        "Melalui Isa Al-Masih setiap orang beroleh pengampunan dosa dan "
        "hidup kekal oleh rahmat Allah."
    )
    chunk = _dummy_chunk(
        "c1",
        "Pengampunan Dosa",
        chunk_text,
        "https://isadanislam.org/pengampunan",
    )

    # Empty used_passages
    res_no_support = validator.validate(
        "Allah mengampuni segala dosa melalui Isa Al-Masih dalam hidup ini.",
        used_passages=[],
        retrieved_chunks=[chunk],
    )
    assert ValidatorCode.v5_no_support in res_no_support.codes

    # Low overlap with passages
    low_overlap_text = (
        "Allah menuntun astronot melintasi galaksi nebula spektakuler "
        "antariksa kosmik Isa Al-Masih bintang planet satelit."
    )
    res_low = validator.validate(
        low_overlap_text,
        used_passages=[1],
        retrieved_chunks=[chunk],
    )
    assert ValidatorCode.v5_low_overlap in res_low.codes

    # Repair format
    failures = res_low.failures
    formatted = format_failures_for_repair(failures)
    assert "- " in formatted
