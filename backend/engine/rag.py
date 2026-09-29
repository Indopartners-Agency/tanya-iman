"""Production RAG Answer Engine (Phase 5).

Wires the complete deterministic and generative pipeline:
1. Relevance Classifier & Topic Resolver
2. Curated Answer Override
3. Vector Retrieval & Grounding Gate
4. Answer Composer
5. Compliance Validators (V1-V5) & Single Repair Loop
6. Response Assembler

Specification: AI Spec section 3, section 7, section 8, section 10, section 11.
"""

from __future__ import annotations

import logging

from config import get_settings
from config.loader import response
from engine.base import AnswerEngine, EngineRequest
from engine.classifier import RelevanceClassifier
from engine.composer import AnswerComposer
from engine.curated import CuratedResolver
from engine.retriever import VectorRetriever
from engine.validators import ComplianceValidator
from models.enums import AnswerSource, Relevance
from models.schemas import Citation, EngineResult
from storage import Storage, get_storage

logger = logging.getLogger(__name__)


class RAGEngine(AnswerEngine):
    name = "rag"

    def __init__(
        self,
        storage: Storage | None = None,
        retriever: VectorRetriever | None = None,
        classifier: RelevanceClassifier | None = None,
        curated_resolver: CuratedResolver | None = None,
        composer: AnswerComposer | None = None,
        validator: ComplianceValidator | None = None,
    ) -> None:
        self.storage = storage or get_storage()
        self.retriever = retriever or VectorRetriever(storage=self.storage)
        self.classifier = classifier or RelevanceClassifier()
        self.curated_resolver = curated_resolver or CuratedResolver(storage=self.storage)
        self.composer = composer or AnswerComposer()
        self.validator = validator or ComplianceValidator()

    async def answer(self, request: EngineRequest) -> EngineResult:
        settings = get_settings()

        # Step 1: Relevance Classifier & Topic Resolver (AI Spec 4 & 5)
        class_res = await self.classifier.classify(request.question_text, request.context)

        # Handle emotional_only inquiry (F-44, AI Spec 10.9)
        if class_res.relevance is Relevance.emotional_only:
            # Load optional contact details from system config
            contact_name = "Sahabat Peduli"
            contact_number = "+62 811-1234-5678"
            conf = await self.storage.get_system_config("contact_number")
            if conf:
                contact_number = conf.value
            conf_name = await self.storage.get_system_config("contact_name")
            if conf_name:
                contact_name = conf_name.value

            return EngineResult(
                answer_source=AnswerSource.emotional_deferral,
                answer_text=response(
                    "emotional_deferral",
                    contact_name=contact_name,
                    contact_number=contact_number,
                ),
                topic_slug=class_res.topic_slug,
                prompt_version=settings.prompt_version,
            )

        # Handle irrelevant inquiries and prompt injection attempts (F-10, AI Spec 4.3, 10.2)
        if class_res.relevance is Relevance.irrelevant or class_res.is_injection_attempt:
            return EngineResult(
                answer_source=AnswerSource.refusal,
                answer_text=response("refusal"),
                topic_slug=class_res.topic_slug,
                prompt_version=settings.prompt_version,
            )

        # Step 2: Curated Answer Override (F-23, AI Spec 11)
        curated_res = await self.curated_resolver.resolve(class_res.topic_slug)
        if curated_res.matched:
            return EngineResult(
                answer_source=AnswerSource.curated,
                answer_text=curated_res.answer_text,
                citations=curated_res.citations,
                topic_slug=curated_res.topic_slug,
                prompt_version=settings.prompt_version,
            )

        # Step 3: Vector Retrieval & Grounding Evaluation (F-15, F-29, AI Spec 6)
        retrieval = await self.retriever.retrieve(request.question_text, context=request.context)

        if not retrieval.has_grounding:
            return EngineResult(
                answer_source=AnswerSource.no_grounding,
                answer_text=response("no_grounding"),
                topic_slug=class_res.topic_slug,
                prompt_version=settings.prompt_version,
            )

        # Pass up to 4 retrieved passages to composer
        passages = retrieval.chunks[:4]

        # Step 4: Answer Composer (F-11 through F-14, AI Spec 7)
        comp_res = await self.composer.compose(request.question_text, passages, request.context)

        # Assemble citations from used_passages indices (up to 2 citations per F-14)
        citations = self._assemble_citations(passages, comp_res.used_passages)

        # Step 5: Compliance Validators V1-V5 (F-28, AI Spec 8)
        val_res = self.validator.validate(
            comp_res.answer,
            used_passages=comp_res.used_passages,
            retrieved_chunks=passages,
            citations=citations,
        )

        if not val_res.valid:
            logger.info(
                "Initial answer failed validation with %s; triggering repair loop",
                val_res.codes,
            )
            # Execute exactly one repair attempt (AI Spec 8.6)
            repaired_comp = await self.composer.repair(
                comp_res.answer, val_res.failures, passages, request.question_text
            )
            repaired_citations = self._assemble_citations(passages, repaired_comp.used_passages)
            repaired_val = self.validator.validate(
                repaired_comp.answer,
                used_passages=repaired_comp.used_passages,
                retrieved_chunks=passages,
                citations=repaired_citations,
            )

            if not repaired_val.valid:
                logger.warning(
                    "Repaired answer failed validation again with %s; serving fallback template",
                    repaired_val.codes,
                )
                return EngineResult(
                    answer_source=AnswerSource.generated,
                    answer_text=response("fallback"),
                    topic_slug=class_res.topic_slug,
                    retrieved_chunk_ids=[p.id for p in passages],
                    validator_failures=repaired_val.codes,
                    model=repaired_comp.model,
                    prompt_version=settings.prompt_version,
                )

            # Repaired answer succeeded
            return EngineResult(
                answer_source=AnswerSource.generated,
                answer_text=repaired_comp.answer,
                citations=repaired_citations,
                topic_slug=class_res.topic_slug,
                retrieved_chunk_ids=[p.id for p in passages],
                validator_failures=val_res.codes,  # Record original failures that required repair
                model=repaired_comp.model,
                prompt_version=settings.prompt_version,
            )

        # Passed validation on first attempt
        return EngineResult(
            answer_source=AnswerSource.generated,
            answer_text=comp_res.answer,
            citations=citations,
            topic_slug=class_res.topic_slug,
            retrieved_chunk_ids=[p.id for p in passages],
            validator_failures=[],
            model=comp_res.model,
            prompt_version=settings.prompt_version,
        )

    def _assemble_citations(self, passages: list, used_passages: list[int]) -> list[Citation]:
        """Convert 1-based passage indices into up to 2 deduplicated Citation records."""
        citations: list[Citation] = []
        seen_urls: set[str] = set()

        for idx in used_passages:
            if 1 <= idx <= len(passages):
                chunk = passages[idx - 1]
                if chunk.url not in seen_urls:
                    seen_urls.add(chunk.url)
                    citations.append(Citation(title=chunk.title, url=chunk.url, site=chunk.site))
            if len(citations) >= 2:
                break

        return citations
