"""Answer engines.

The router calls ``get_engine().answer(...)`` and nothing else. Phase 2 ships
the stub; Phase 5 replaces it with the RAG pipeline described in
docs/ai-answer-engine-specification.md. Because both satisfy ``EngineResult``, the swap
is a one-line change in the factory and no change at all in ``routers/``.
"""

from engine.base import AnswerEngine, EngineRequest, get_engine, reset_engine
from engine.classifier import ClassificationResult, RelevanceClassifier
from engine.composer import AnswerComposer, ComposerResult
from engine.curated import CuratedResolver, CuratedResult
from engine.rag import RAGEngine
from engine.retriever import RetrievalResult, VectorRetriever
from engine.validators import ComplianceValidator, ValidationResult, ValidatorFailure

__all__ = [
    "AnswerEngine",
    "AnswerComposer",
    "ClassificationResult",
    "ComplianceValidator",
    "ComposerResult",
    "CuratedResolver",
    "CuratedResult",
    "EngineRequest",
    "RAGEngine",
    "RelevanceClassifier",
    "RetrievalResult",
    "ValidationResult",
    "ValidatorFailure",
    "VectorRetriever",
    "get_engine",
    "reset_engine",
]
