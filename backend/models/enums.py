from __future__ import annotations

from enum import StrEnum


class AuthMethod(StrEnum):
    sms = "sms"
    whatsapp = "whatsapp"
    guest = "guest"


class Platform(StrEnum):
    web = "web"
    widget = "widget"
    android = "android"


class AnswerSource(StrEnum):
    """How a response was produced.

    The client selects its rendering on this value rather than reimplementing
    the business rules — see Chat UX Specification section 8.
    """

    curated = "curated"
    generated = "generated"
    refusal = "refusal"
    no_grounding = "no_grounding"
    crisis = "crisis"
    emotional_deferral = "emotional_deferral"
    error = "error"

    @property
    def likeable(self) -> bool:
        """F-17: only a composed/curated answer can be liked — never templates."""
        return self in (AnswerSource.curated, AnswerSource.generated)


class Relevance(StrEnum):
    theology = "theology"
    emotional_only = "emotional_only"
    ambiguous = "ambiguous"
    irrelevant = "irrelevant"
    # Legacy alias used in early stub code / tests
    relevant = "relevant"


class ValidatorCode(StrEnum):
    """Compliance validator failure codes (AI Spec section 8.7)."""

    v1_too_short = "V1_TOO_SHORT"
    v1_too_long = "V1_TOO_LONG"
    v2_forbidden_term = "V2_FORBIDDEN_TERM"
    v2_missing_required_term = "V2_MISSING_REQUIRED_TERM"
    v3_multiple_quran_refs = "V3_MULTIPLE_QURAN_REFS"
    v3_quran_not_leading = "V3_QURAN_NOT_LEADING"
    v3_bible_minority = "V3_BIBLE_MINORITY"
    v4_citation_count = "V4_CITATION_COUNT"
    v4_citation_not_retrieved = "V4_CITATION_NOT_RETRIEVED"
    v4_citation_off_allowlist = "V4_CITATION_OFF_ALLOWLIST"
    v4_citation_retired = "V4_CITATION_RETIRED"
    v5_no_support = "V5_NO_SUPPORT"
    v5_low_overlap = "V5_LOW_OVERLAP"
    v5_external_entity = "V5_EXTERNAL_ENTITY"
