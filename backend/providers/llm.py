from __future__ import annotations

import json
import logging
import re
from typing import Any, Protocol

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    name: str

    async def complete_json(
        self, system: str, user: str, *, max_tokens: int = 700, temperature: float = 0.4
    ) -> dict[str, Any]:
        """Return parsed structured output. Raises on transport failure."""
        ...


class FakeLLM:
    """Deterministic stand-in used by tests and `LLM_PROVIDER=fake`.

    Its existence is what lets the engine test suite run with no network, no
    cost, and no flakiness. Phase 5 tests assert against this, then the
    benchmark suite exercises the real provider separately.
    """

    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.next_response: dict[str, Any] | None = None

    async def complete_json(
        self, system: str, user: str, *, max_tokens: int = 700, temperature: float = 0.4
    ) -> dict[str, Any]:
        self.calls.append((system, user))
        if self.next_response is not None:
            return self.next_response
        return {
            "answer": (
                "Terima kasih sudah bertanya. Allah mengenal apa yang sedang Anda "
                "rasakan, dan Isa Al-Masih datang untuk membawa pengharapan bagi "
                "mereka yang mencari kebenaran dengan sungguh-sungguh."
            ),
            "used_passages": [1],
            "quran_reference": None,
            "bible_references": [],
            "confidence": "medium",
        }


class GeminiLLM:
    """Gemini model provider using Google Generative Language REST API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.8-flash",
        timeout: float = 7.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client = client
        self.name = f"gemini:{model}"

    async def complete_json(
        self, system: str, user: str, *, max_tokens: int = 700, temperature: float = 0.4
    ) -> dict[str, Any]:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        async def _call(cli: httpx.AsyncClient) -> dict[str, Any]:
            resp = await cli.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                logger.error("Gemini API error %d: %s", resp.status_code, resp.text)
                raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No candidate returned by Gemini API")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise RuntimeError("No content parts in Gemini API response")
            raw_text = parts[0].get("text", "").strip()

            # Clean markdown codeblocks if model returned ```json ... ```
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
            return json.loads(cleaned)

        if self._client is not None:
            return await _call(self._client)
        async with httpx.AsyncClient() as client:
            return await _call(client)


_instance: LLMProvider | None = None


def get_llm(fallback: bool = False) -> LLMProvider:
    global _instance
    settings = get_settings()
    provider_name = settings.llm_fallback_provider if fallback else settings.llm_provider
    model_name = settings.llm_fallback_model if fallback else settings.llm_model

    if fallback:
        if provider_name == "gemini":
            return GeminiLLM(api_key=settings.llm_api_key, model=model_name)
        return FakeLLM()

    if _instance is None:
        if provider_name == "fake":
            _instance = FakeLLM()
        elif provider_name == "gemini":
            _instance = GeminiLLM(api_key=settings.llm_api_key, model=model_name)
        else:
            raise NotImplementedError(f"LLM provider '{provider_name}' is not implemented.")
    return _instance


def reset_llm(provider: LLMProvider | None = None) -> None:
    global _instance
    _instance = provider
