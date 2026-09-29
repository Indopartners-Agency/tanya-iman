"""Compliance validators (V1 through V5) and repair loop (F-28).

Every generated answer passes all five validators before reaching the seeker:
- V1: Length bounds (25 <= words <= 250) using shared word counting
- V2: Terminology screening (no 'Tuhan'/'Yesus', must have 'Allah'/'Isa Al-Masih')
- V3: Scripture balance (max 1 Quran ref leading in first 25%, Bible >= 2 if Quran present)
- V4: Citation integrity (1-2 citations, provenance, allowlist, active liveness)
- V5: Grounding (non-empty support, content word overlap)

Specification: AI Spec section 8.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from config.loader import approved_domains
from models.enums import ArticleStatus, ValidatorCode
from models.schemas import ArticleChunk, Citation
from services.text import MAX_WORDS, MIN_WORDS, count_words

logger = logging.getLogger(__name__)

# V2: Terminology
_FORBIDDEN_TERMS_RE = re.compile(r"\b(Tuhan|TUHAN|Yesus|Jesus)\b")
_REQUIRED_TERMS_RE = re.compile(r"\b(Allah|Isa\s+Al-Masih)\b", re.IGNORECASE)

# V3: Scripture
_QURAN_RE = re.compile(
    r"\b(?:Qs\.|QS|Surah|Surat)\s+([A-Za-z0-9\-]+(?:\s+[0-9]+(?::[0-9]+)?)?)",
    re.IGNORECASE,
)

_BIBLE_BOOKS = (
    r"1\s+Samuel|2\s+Samuel|1\s+Raja-raja|2\s+Raja-raja|1\s+Tawarikh|2\s+Tawarikh|"
    r"Kidung\s+Agung|Kisah\s+Para\s+Rasul|1\s+Korintus|2\s+Korintus|1\s+Tesalonika|"
    r"2\s+Tesalonika|1\s+Timotius|2\s+Timotius|1\s+Petrus|2\s+Petrus|1\s+Yohanes|"
    r"2\s+Yohanes|3\s+Yohanes|Kejadian|Keluaran|Imamat|Bilangan|Ulangan|Yosua|"
    r"Hakim-hakim|Rut|Ezra|Nehemia|Ester|Ayub|Mazmur|Amsal|Pengkhotbah|Yesaya|"
    r"Yeremia|Ratapan|Yehezkiel|Daniel|Hosea|Yoel|Amos|Obaja|Yunus|Mikha|Nahum|"
    r"Habakuk|Zefanya|Hagai|Zakharia|Maleakhi|Matius|Markus|Lukas|Yohanes|Roma|"
    r"Galatia|Efesus|Filipi|Kolose|Titus|Filemon|Ibrani|Yakobus|Yudas|Wahyu"
)
_BIBLE_RE = re.compile(rf"\b(?:{_BIBLE_BOOKS})\s+\d+(?::\d+(?:-\d+)?)?", re.IGNORECASE)

_INDONESIAN_STOPWORDS = frozenset(
    {
        "yang",
        "untuk",
        "pada",
        "ke",
        "para",
        "namun",
        "menurut",
        "antara",
        "dia",
        "dua",
        "ia",
        "seperti",
        "jika",
        "sehingga",
        "kembali",
        "dan",
        "tidak",
        "ini",
        "karena",
        "kepada",
        "oleh",
        "saat",
        "harus",
        "sementara",
        "setelah",
        "belum",
        "kami",
        "sekitar",
        "bagi",
        "serta",
        "di",
        "dari",
        "telah",
        "sebagai",
        "masih",
        "hal",
        "ketika",
        "adalah",
        "itu",
        "atau",
        "kita",
        "dengan",
        "akan",
        "juga",
        "ada",
        "mereka",
        "sudah",
        "saya",
        "anda",
        "bisa",
        "lebih",
        "tentang",
        "dapat",
        "dalam",
        "banyak",
        "orang",
    }
)


@dataclass(frozen=True)
class ValidatorFailure:
    code: ValidatorCode
    message: str


@dataclass
class ValidationResult:
    valid: bool
    failures: list[ValidatorFailure] = field(default_factory=list)

    @property
    def codes(self) -> list[ValidatorCode]:
        return [f.code for f in self.failures]


class ComplianceValidator:
    """Enforces V1-V5 rules on answer drafts."""

    def validate(
        self,
        answer: str,
        *,
        used_passages: list[int] | None = None,
        retrieved_chunks: list[ArticleChunk] | None = None,
        citations: list[Citation] | None = None,
        article_statuses: dict[str, ArticleStatus] | None = None,
    ) -> ValidationResult:
        failures: list[ValidatorFailure] = []

        # --- V1: Word Count ---
        words = count_words(answer)
        if words < MIN_WORDS:
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v1_too_short,
                    f"Panjang jawaban {words} kata; batas minimum adalah {MIN_WORDS} kata.",
                )
            )
        elif words > MAX_WORDS:
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v1_too_long,
                    f"Panjang jawaban {words} kata; batas maksimum adalah {MAX_WORDS} kata.",
                )
            )

        # --- V2: Terminology ---
        forbidden_match = _FORBIDDEN_TERMS_RE.search(answer)
        if forbidden_match:
            term = forbidden_match.group(0)
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v2_forbidden_term,
                    f"Jawaban memuat kata terlarang '{term}'. Gunakan 'Allah' / 'Isa Al-Masih'.",
                )
            )

        if not _REQUIRED_TERMS_RE.search(answer):
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v2_missing_required_term,
                    "Jawaban harus memuat sekurang-kurangnya satu sebutan 'Allah' "
                    "atau 'Isa Al-Masih'.",
                )
            )

        # --- V3: Scripture Balance ---
        quran_matches = list(_QURAN_RE.finditer(answer))
        bible_matches = list(_BIBLE_RE.finditer(answer))

        quran_count = len(quran_matches)
        bible_count = len(bible_matches)

        if quran_count > 1:
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v3_multiple_quran_refs,
                    f"Jumlah rujukan Al-Quran ({quran_count}) melebihi batas maksimal 1 rujukan.",
                )
            )

        if quran_count == 1:
            # Must fall within the first 25% of answer words
            q_pos = quran_matches[0].start()
            words_before = count_words(answer[:q_pos])
            if words > 0 and (words_before / words) > 0.25:
                failures.append(
                    ValidatorFailure(
                        ValidatorCode.v3_quran_not_leading,
                        "Rujukan Al-Quran harus berada di bagian awal jawaban (25% pertama).",
                    )
                )

            # If Quran ref present, at least 2 Bible refs required
            if bible_count < 2:
                failures.append(
                    ValidatorFailure(
                        ValidatorCode.v3_bible_minority,
                        f"Rujukan Al-Quran disertai {bible_count} rujukan Kitab Suci; "
                        "minimal diperlukan 2 rujukan Alkitab.",
                    )
                )
        elif bible_count == 0 and quran_count > 0:
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v3_bible_minority,
                    "Rujukan Al-Quran harus disertai sekurang-kurangnya rujukan Kitab Suci.",
                )
            )

        # --- V4: Citations ---
        if citations is not None:
            if not (1 <= len(citations) <= 2):
                failures.append(
                    ValidatorFailure(
                        ValidatorCode.v4_citation_count,
                        f"Jumlah sitasi ({len(citations)}) tidak memenuhi syarat 1 atau 2 sitasi.",
                    )
                )

            allowed = approved_domains()
            retrieved_urls = {c.url for c in (retrieved_chunks or [])}

            for cit in citations:
                if retrieved_chunks is not None and cit.url not in retrieved_urls:
                    failures.append(
                        ValidatorFailure(
                            ValidatorCode.v4_citation_not_retrieved,
                            f"Sitasi '{cit.url}' tidak berasal dari kutipan pencarian.",
                        )
                    )
                if cit.site not in allowed:
                    failures.append(
                        ValidatorFailure(
                            ValidatorCode.v4_citation_off_allowlist,
                            f"Domain sitasi '{cit.site}' berada di luar domain yang disetujui.",
                        )
                    )
                if (
                    article_statuses
                    and cit.url in article_statuses
                    and article_statuses[cit.url] == ArticleStatus.retired
                ):
                    failures.append(
                        ValidatorFailure(
                            ValidatorCode.v4_citation_retired,
                            f"Artikel sitasi '{cit.url}' sudah berstatus tidak aktif (retired).",
                        )
                    )

        # --- V5: Grounding ---
        if used_passages is not None and len(used_passages) == 0:
            failures.append(
                ValidatorFailure(
                    ValidatorCode.v5_no_support,
                    "Jawaban tidak mencantumkan kutipan bahan yang digunakan.",
                )
            )

        if retrieved_chunks and used_passages:
            # Check lexical overlap with cited passages
            cited_texts = []
            for idx in used_passages:
                # 1-indexed
                if 1 <= idx <= len(retrieved_chunks):
                    cited_texts.append(retrieved_chunks[idx - 1].text)

            if cited_texts:
                answer_tokens = set(re.findall(r"\w+", answer.lower()))
                answer_content = {
                    t for t in answer_tokens if len(t) >= 4 and t not in _INDONESIAN_STOPWORDS
                }

                passages_tokens = set(re.findall(r"\w+", " ".join(cited_texts).lower()))
                passages_content = {
                    t for t in passages_tokens if len(t) >= 4 and t not in _INDONESIAN_STOPWORDS
                }

                overlap = answer_content.intersection(passages_content)
                overlap_ratio = len(overlap) / max(len(answer_content), 1)

                if overlap_ratio < 0.10 and len(overlap) < 3:
                    failures.append(
                        ValidatorFailure(
                            ValidatorCode.v5_low_overlap,
                            "Kandungan kata kunci jawaban terlalu rendah "
                            f"({len(overlap)} kata bersama) dengan bahan kutipan.",
                        )
                    )

        return ValidationResult(valid=len(failures) == 0, failures=failures)


def format_failures_for_repair(failures: list[ValidatorFailure]) -> str:
    """Format validator failures into concise bullet points for the repair prompt."""
    lines = [f"- {f.message}" for f in failures]
    return "\n".join(lines)
