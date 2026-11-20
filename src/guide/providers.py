"""Model provider abstraction.

GUIDE never falls back silently: a provider either returns a real completion or raises
:class:`~guide.errors.ProviderError`. The only non-network provider is
:class:`ScriptedProvider`, an explicit test double that must be constructed on purpose.
"""

from __future__ import annotations

import os
import random
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from guide.errors import ConfigurationError, ProviderError
from guide.types import ChatMessage


def _parse_retry_after(resp: Any) -> float:
    for h in ("retry-after", "x-ratelimit-reset-tokens"):
        val = resp.headers.get(h)
        if not val:
            continue
        try:
            return min(float(val), 20.0)
        except (ValueError, TypeError):
            pass
        total = 0.0
        for part in re.finditer(r"(\d+(?:\.\d+)?)(ms|m|s)", str(val)):
            num, unit = float(part.group(1)), part.group(2)
            if unit == "m":
                total += num * 60.0
            elif unit == "s":
                total += num
            elif unit == "ms":
                total += num / 1000.0
        if total > 0:
            return min(total, 20.0)
    return 0.0


@dataclass(frozen=True)
class ModelSettings:
    """Generation settings held identical across experimental conditions (model invariance)."""

    temperature: float = 0.0
    max_tokens: int = 1024
    seed: int | None = 42
    json_mode: bool = True


@dataclass(frozen=True)
class ModelResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_s: float
    model: str  # model identifier *reported by the provider*, recorded for reproducibility
    finish_reason: str = "stop"


@runtime_checkable
class ModelProvider(Protocol):
    name: str

    def complete(self, messages: Sequence[ChatMessage], settings: ModelSettings) -> ModelResponse: ...


class OpenAICompatibleProvider:
    """Chat-completions client for any OpenAI-compatible endpoint (OpenAI, DeepSeek, vLLM, ...).

    Retries only transient failures (timeouts, 429, 5xx) with jittered exponential backoff.
    The API key is read from an environment variable at construction and never logged.
    """

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key_env: str,
        timeout_s: float = 60.0,
        max_retries: int = 8,
        backoff_s: float = 1.5,
        min_interval_s: float = 0.0,
    ) -> None:
        try:
            import httpx  # optional dependency: pip install guide-mas[openai]
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ConfigurationError("OpenAICompatibleProvider requires the 'openai' extra (httpx)") from exc
        raw_key = os.environ.get(api_key_env)
        if not raw_key:
            raise ConfigurationError(f"environment variable {api_key_env} is not set")
        self._keys = [k.strip() for k in raw_key.split(",") if k.strip()]
        self._key_idx = 0
        self.name = f"openai-compatible:{model}"
        self.model = model
        self._max_retries = max_retries
        self._backoff_s = backoff_s
        self._min_interval_s = min_interval_s
        self._last_call_t: float | None = None
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
        )
        self._httpx = httpx

    def complete(self, messages: Sequence[ChatMessage], settings: ModelSettings) -> ModelResponse:
        if self._min_interval_s > 0 and self._last_call_t is not None:
            elapsed = time.perf_counter() - self._last_call_t
            wait = self._min_interval_s - elapsed
            if wait > 0:
                time.sleep(wait)
        self._last_call_t = time.perf_counter()
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }
        if settings.seed is not None:
            body["seed"] = settings.seed
        if settings.json_mode:
            body["response_format"] = {"type": "json_object"}

        active_key_idx = self._key_idx
        self._key_idx = (self._key_idx + 1) % len(self._keys)

        last_error: ProviderError | None = None
        for attempt in range(self._max_retries + 1):
            key = self._keys[active_key_idx]
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            start = time.perf_counter()
            wait_s = 0.0
            try:
                resp = self._client.post("/chat/completions", json=body, headers=headers)
            except self._httpx.TimeoutException as exc:
                last_error = ProviderError(f"timeout: {type(exc).__name__}", retryable=True)
            except self._httpx.TransportError as exc:
                last_error = ProviderError(f"transport error: {type(exc).__name__}", retryable=True)
            else:
                latency = time.perf_counter() - start
                if resp.status_code == 200:
                    payload = resp.json()
                    choice = payload["choices"][0]
                    usage = payload.get("usage") or {}
                    return ModelResponse(
                        content=choice["message"].get("content") or "",
                        prompt_tokens=int(usage.get("prompt_tokens", 0)),
                        completion_tokens=int(usage.get("completion_tokens", 0)),
                        latency_s=latency,
                        model=str(payload.get("model", self.model)),
                        finish_reason=str(choice.get("finish_reason") or "stop"),
                    )
                retryable = resp.status_code == 429 or resp.status_code >= 500
                wait_s = _parse_retry_after(resp) if resp.status_code == 429 else 0.0
                last_error = ProviderError(
                    f"HTTP {resp.status_code}: {resp.text}", retryable=retryable, status=resp.status_code
                )
            if not last_error.retryable or attempt == self._max_retries:
                break
            if len(self._keys) > 1 and last_error.status == 429:
                active_key_idx = (active_key_idx + 1) % len(self._keys)
                if attempt < len(self._keys) - 1:
                    time.sleep(0.5)
                    continue
            backoff = self._backoff_s * (2**attempt) * (0.5 + random.random())  # noqa: S311 - retry jitter, not security
            time.sleep(min(max(backoff, wait_s + 0.5), 25.0))
        assert last_error is not None
        raise last_error

    def close(self) -> None:
        self._client.close()


class ScriptedProvider:
    """Deterministic TEST DOUBLE. Replays scripted responses; never use for reported results.

    ``script`` is either a list of response strings (consumed in order) or a callable that
    maps the message list to a response string.
    """

    def __init__(self, script: Sequence[str] | Callable[[Sequence[ChatMessage]], str], model: str = "scripted") -> None:
        self.name = f"scripted:{model}"
        self._script = script
        self._index = 0
        self.calls: list[list[ChatMessage]] = []

    def complete(self, messages: Sequence[ChatMessage], settings: ModelSettings) -> ModelResponse:
        self.calls.append(list(messages))
        if callable(self._script):
            content = self._script(messages)
        else:
            if self._index >= len(self._script):
                raise ProviderError("scripted provider exhausted", retryable=False)
            content = self._script[self._index]
            self._index += 1
        prompt_tokens = sum(len(m.content) for m in messages) // 4
        return ModelResponse(content, prompt_tokens, len(content) // 4, 0.0, self.name)
