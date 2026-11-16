"""Minimal LLM adapter: one method, three real backends, one test double.

No SDKs - plain HTTPS via urllib - so the project gains no new dependencies.
Local (Ollama) is the default so RFP text need not leave the machine. The
OpenAI and Gemini backends are opt-in and send retrieved passages to an
external API.

Provider quirks handled here (verified against current docs, Nov 2026):
* OpenAI gpt-6 models reject ``max_tokens`` (use ``max_completion_tokens``) and
  only accept ``temperature`` when reasoning is off; reasoning tokens also count
  against the output limit, so reasoning is switched off by default.
* Gemini thinking tokens count against ``maxOutputTokens``, so headroom is added;
  ``temperature`` is omitted because newer Gemini models deprecate it.
A response cut off by the token limit raises ``LLMError`` instead of returning
truncated JSON.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

PROVIDERS = ("ollama", "openai", "gemini")


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    name: str

    def complete(self, system: str, user: str, max_tokens: int = 1000) -> str: ...


def default_timeout(fallback: float) -> float:
    """BIDLENS_LLM_TIMEOUT (seconds) overrides every backend's default."""
    try:
        return float(os.getenv("BIDLENS_LLM_TIMEOUT", fallback))
    except ValueError:
        return fallback


def _post(url: str, payload: dict, headers: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise LLMError(f"HTTP {e.code} from {url}: {e.read().decode()[:300]}") from e
    except TimeoutError as e:
        raise LLMError(f"No response from {url} within {timeout:.0f}s (timed out). The model may be too "
                       "slow or the network may be blocking it; raise BIDLENS_LLM_TIMEOUT or run "
                       "scripts/check_llm.py to tell which.") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            raise LLMError(f"Timed out connecting to {url} after {timeout:.0f}s; check your network, "
                           "VPN or proxy.") from e
        raise LLMError(f"Cannot reach {url}: {e.reason}") from e


def _truncated(provider: str, max_tokens: int) -> LLMError:
    return LLMError(f"{provider} output hit the {max_tokens}-token limit and was cut off; "
                    "ask a narrower question or raise max_output_tokens")


class OllamaClient:
    def __init__(self, model: str | None = None, host: str | None = None, timeout: float | None = None):
        self.model = model or os.getenv("BIDLENS_OLLAMA_MODEL", "llama3.1:8b")
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout or default_timeout(300)
        # Ollama's default context window can be as small as 2048 tokens and
        # silently truncates longer prompts, so set it explicitly.
        self.num_ctx = int(os.getenv("BIDLENS_OLLAMA_NUM_CTX", "8192"))
        self.name = f"ollama:{self.model}"

    def complete(self, system: str, user: str, max_tokens: int = 1000) -> str:
        data = _post(f"{self.host}/api/chat", {
            "model": self.model, "stream": False, "format": "json",
            "options": {"temperature": 0, "num_predict": max_tokens, "num_ctx": self.num_ctx},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }, {}, self.timeout)
        if data.get("done_reason") == "length":
            raise _truncated("ollama", max_tokens)
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as e:
            raise LLMError(f"Unexpected Ollama response: {str(data)[:200]}") from e


class OpenAIClient:
    URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, model: str | None = None, api_key: str | None = None, timeout: float | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMError("OPENAI_API_KEY is not set")
        self.model = model or os.getenv("BIDLENS_OPENAI_MODEL", "gpt-6-luna")
        # "none" keeps answers fast and temperature usable on gpt-6 models.
        # Set BIDLENS_OPENAI_REASONING_EFFORT="" for older models that reject the field.
        self.effort = os.getenv("BIDLENS_OPENAI_REASONING_EFFORT", "none").strip()
        self.timeout = timeout or default_timeout(120)
        self.name = f"openai:{self.model}"

    def complete(self, system: str, user: str, max_tokens: int = 1000) -> str:
        payload = {
            "model": self.model,
            "max_completion_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }
        if self.effort:
            payload["reasoning_effort"] = self.effort
        if self.effort in ("", "none"):   # temperature is only accepted with reasoning off
            payload["temperature"] = 0
        data = _post(self.URL, payload, {"Authorization": f"Bearer {self.api_key}"}, self.timeout)
        try:
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise _truncated("openai", max_tokens)
            return choice["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"Unexpected OpenAI response: {str(data)[:200]}") from e


class GeminiClient:
    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model: str | None = None, api_key: str | None = None, timeout: float | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise LLMError("GEMINI_API_KEY is not set")
        self.model = model or os.getenv("BIDLENS_GEMINI_MODEL", "gemini-3.8-flash")
        # Thinking tokens share the output budget; headroom stops them starving the answer.
        self.headroom = int(os.getenv("BIDLENS_GEMINI_THINKING_HEADROOM", "4000"))
        # Gemini 3.x defaults to medium/high thinking, which is slow for extraction.
        # gemini-3.8-flash accepts low|medium|high (not minimal); other models differ,
        # so set BIDLENS_GEMINI_THINKING_LEVEL="" to omit the field.
        self.thinking_level = os.getenv("BIDLENS_GEMINI_THINKING_LEVEL", "low").strip()
        self.timeout = timeout or default_timeout(120)
        self.name = f"gemini:{self.model}"

    def complete(self, system: str, user: str, max_tokens: int = 1000) -> str:
        config = {"maxOutputTokens": max_tokens + self.headroom,
                  "responseMimeType": "application/json"}
        if self.thinking_level:
            config["thinkingConfig"] = {"thinkingLevel": self.thinking_level}
        data = _post(f"{self.BASE}/{self.model}:generateContent", {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": config,
        }, {"x-goog-api-key": self.api_key}, self.timeout)
        block = (data.get("promptFeedback") or {}).get("blockReason")
        if block:
            raise LLMError(f"Gemini blocked the prompt: {block}")
        try:
            cand = data["candidates"][0]
            if cand.get("finishReason") == "MAX_TOKENS":
                raise _truncated("gemini", max_tokens + self.headroom)
            parts = cand["content"]["parts"]
            return "".join(p.get("text", "") for p in parts if not p.get("thought"))
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"Unexpected Gemini response: {str(data)[:200]}") from e


class FakeClient:
    """Deterministic test double: returns queued responses in order."""

    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []
        self.name = "fake"

    def complete(self, system: str, user: str, max_tokens: int = 1000) -> str:
        self.calls.append((system, user))
        if not self.responses:
            raise LLMError("FakeClient exhausted")
        return self.responses.pop(0)


def make_client(provider: str = "ollama", model: str | None = None) -> LLMClient:
    if provider == "ollama":
        return OllamaClient(model)
    if provider == "openai":
        return OpenAIClient(model)
    if provider == "gemini":
        return GeminiClient(model)
    raise ValueError(f"Unknown provider: {provider!r} (use one of {', '.join(PROVIDERS)})")
