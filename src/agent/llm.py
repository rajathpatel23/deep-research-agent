import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional

from src.agent.config import Config, LLMProvider

_MAX_RETRIES = 4
_RETRY_BASE_SECS = 35  # Groq rate limit windows are ~30s
_REQUEST_TIMEOUT_SECS = 60

_NEBIUS_BASE_URL = "https://api.tokenfactory.us-central1.nebius.com/v1/"
_MINIMAX_BASE_URL = "https://api.minimax.io/v1"


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, model_override: str | None = None) -> str: ...


class GroqProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        from groq import Groq
        self._client = Groq(api_key=config.groq_api_key)
        self._model = config.llm_model

    def complete(self, system: str, user: str, model_override: str | None = None) -> str:
        from groq import RateLimitError
        from groq import BadRequestError
        model = model_override or self._model
        for attempt in range(_MAX_RETRIES):
            try:
                create_kwargs = dict(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.6,
                    max_completion_tokens=1024,
                    top_p=0.95,
                    stream=True,
                    stop=None,
                )
                # Some Groq models (for example Llama 3.1 8B) do not support reasoning_effort.
                # Keep the optimization when available, but fail open for unsupported models.
                try:
                    stream = self._client.chat.completions.create(
                        **create_kwargs,
                        reasoning_effort="none",
                    )
                except BadRequestError as e:
                    if "reasoning_effort" in str(e):
                        stream = self._client.chat.completions.create(**create_kwargs)
                    else:
                        raise
                return "".join(chunk.choices[0].delta.content or "" for chunk in stream)
            except RateLimitError as e:
                wait = _RETRY_BASE_SECS * (attempt + 1)
                print(f"  [rate limit] waiting {wait}s (attempt {attempt + 1}/{_MAX_RETRIES})")
                time.sleep(wait)
            except Exception as e:
                if "413" in str(e) or "Request too large" in str(e):
                    raise RuntimeError(f"Request too large for model: {e}") from e
                raise
        raise RuntimeError(f"Groq rate limit exceeded after {_MAX_RETRIES} retries")


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        import anthropic
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._model = config.llm_model

    def complete(self, system: str, user: str, model_override: str | None = None) -> str:
        response = self._client.messages.create(
            model=model_override or self._model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


class NebiusProvider(BaseLLMProvider):
    """OpenAI-compatible Nebius Token Factory endpoint."""
    def __init__(self, config: Config):
        from openai import OpenAI
        self._client = OpenAI(
            base_url=_NEBIUS_BASE_URL,
            api_key=config.nebius_api_key,
        )
        self._model = config.llm_model

    def complete(self, system: str, user: str, model_override: str | None = None) -> str:
        response = self._client.chat.completions.create(
            model=model_override or self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": [{"type": "text", "text": user}]},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


class MinimaxProvider(BaseLLMProvider):
    """OpenAI-compatible MiniMax endpoint."""
    def __init__(self, config: Config):
        from openai import OpenAI
        self._client = OpenAI(
            base_url=_MINIMAX_BASE_URL,
            api_key=config.minimax_api_key,
        )
        self._model = config.llm_model

    def complete(self, system: str, user: str, model_override: str | None = None) -> str:
        model = model_override or self._model
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.2,
                    timeout=_REQUEST_TIMEOUT_SECS,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                # Client/model validation errors (4xx) are non-retryable; fail fast.
                err = str(e).lower()
                if (
                    "bad_request_error" in err
                    or "http_code': '400'" in err
                    or 'http_code": "400"' in err
                    or "error code: 400" in err
                    or "invalid params" in err
                    or "unknown model" in err
                ):
                    raise
                if attempt < _MAX_RETRIES - 1:
                    wait = min(2 ** attempt, 8)
                    print(
                        f"  [minimax retry] waiting {wait}s "
                        f"(attempt {attempt + 1}/{_MAX_RETRIES}) due to: {e}"
                    )
                    time.sleep(wait)
                    continue
                raise


class OllamaProvider(BaseLLMProvider):
    """OpenAI-compatible Ollama local endpoint."""
    def __init__(self, config: Config):
        from openai import OpenAI
        self._client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        self._model = config.llm_model

    def complete(self, system: str, user: str, model_override: str | None = None) -> str:
        response = self._client.chat.completions.create(
            model=model_override or self._model,
            messages=[
                {"role": "system", "content": system},
                # /no_think disables qwen3's chain-of-thought reasoning, cutting latency ~10x
                {"role": "user", "content": f"/no_think\n{user}"},
            ],
            temperature=0.6,
        )
        return response.choices[0].message.content or ""


class MockProvider(BaseLLMProvider):
    def complete(self, system: str, user: str, model_override: str | None = None) -> str:
        s = system.lower()
        if "decompos" in s or "sub-question" in s:
            return json.dumps([
                {"id": "sq1", "text": "What is the primary evidence supporting this topic?", "kind": "supporting"},
                {"id": "sq2", "text": "What are the main criticisms or limitations?", "kind": "adversarial"},
                {"id": "sq3", "text": "What empirical studies exist on this topic?", "kind": "supporting"},
            ])
        if "claim extractor" in s:
            return json.dumps([
                {
                    "source_index": 0,
                    "text": "The topic shows measurable positive effects in controlled studies",
                    "scope": "laboratory settings with standardized protocols",
                    "claim_type": "empirical",
                    "verbatim": "studies show positive effects",
                },
                {
                    "source_index": 0,
                    "text": "Effects may not generalize beyond controlled conditions",
                    "scope": "real-world applications",
                    "claim_type": "speculative",
                    "verbatim": "generalizability remains uncertain",
                },
            ])
        if "support" in s and "contradict" in s:
            # Detect opposing claims so mock runs exercise conflict paths.
            # Returns CONTRADICT when one claim is clearly positive and the other negative.
            u = user.lower()
            positive_markers = ("positive effects", "improves", "beneficial", "effective", "supports")
            negative_markers = ("not generalize", "fails", "limitations", "does not", "ineffective", "criticisms")
            has_positive = any(m in u for m in positive_markers)
            has_negative = any(m in u for m in negative_markers)
            if has_positive and has_negative:
                return "CONTRADICT"
            return "COMPATIBLE"
        if "analyst" in s or "summary" in s:
            return (
                "Research on this topic shows mixed evidence. "
                "Supporting studies exist in controlled settings, but limitations around "
                "generalizability remain unresolved. Confidence is moderate overall."
            )
        return "[]"


_PROVIDER_MAP = {
    LLMProvider.GROQ: GroqProvider,
    LLMProvider.ANTHROPIC: AnthropicProvider,
    LLMProvider.NEBIUS: NebiusProvider,
    LLMProvider.MINIMAX: MinimaxProvider,
    LLMProvider.OLLAMA: OllamaProvider,
    LLMProvider.MOCK: MockProvider,
}


def create_provider(config: Config) -> BaseLLMProvider:
    if config.mock_mode:
        return MockProvider()
    cls = _PROVIDER_MAP.get(config.llm_provider)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{config.llm_provider}'. "
            f"Choose from: {[p.value for p in LLMProvider]}"
        )
    return cls(config)


class LLMClient:
    """Routes calls through the configured provider."""
    def __init__(self, config: Config):
        self._config = config
        self._provider = create_provider(config)
        self._calls: list[dict] = []
        self._calls_lock = Lock()

    def complete(
        self,
        system: str,
        user: str,
        trace: Optional[Dict[str, Any]] = None,
        model_override: Optional[str] = None,
    ) -> str:
        response = self._provider.complete(system, user, model_override=model_override)
        trace = trace or {}
        with self._calls_lock:
            call_id = f"llm_{len(self._calls):05d}"
        call_record = {
            "id": call_id,
            "step": int(trace.get("step", -1)),
            "component": str(trace.get("component", "unknown")),
            "provider": str(self._config.llm_provider.value if hasattr(self._config.llm_provider, "value") else self._config.llm_provider),
            "model": model_override or self._config.llm_model,
            "system_prompt": system,
            "user_prompt": user,
            "response_text": response,
            "meta": {k: v for k, v in trace.items() if k not in {"step", "component"}},
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        with self._calls_lock:
            if call_record["id"] != f"llm_{len(self._calls):05d}":
                call_record["id"] = f"llm_{len(self._calls):05d}"
            self._calls.append(call_record)
        return response

    def get_trace(self) -> list[dict]:
        with self._calls_lock:
            return list(self._calls)
