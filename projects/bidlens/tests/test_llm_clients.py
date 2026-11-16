import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bidlens import llm  # noqa: E402
from bidlens.llm import GeminiClient, LLMError, OllamaClient, OpenAIClient  # noqa: E402


@pytest.fixture
def captured(monkeypatch):
    box = {}

    def fake_post(url, payload, headers, timeout):
        box.update(url=url, payload=payload, headers=headers)
        return box["response"]

    monkeypatch.setattr(llm, "_post", fake_post)
    return box


def openai_ok(text="{}", finish="stop"):
    return {"choices": [{"message": {"content": text}, "finish_reason": finish}]}


def test_openai_request_shape(captured, monkeypatch):
    monkeypatch.delenv("BIDLENS_OPENAI_REASONING_EFFORT", raising=False)
    captured["response"] = openai_ok('{"a": 1}')
    out = OpenAIClient(api_key="k").complete("sys", "usr", max_tokens=500)
    p = captured["payload"]
    assert out == '{"a": 1}'
    assert p["max_completion_tokens"] == 500 and "max_tokens" not in p
    assert p["reasoning_effort"] == "none" and p["temperature"] == 0
    assert p["response_format"] == {"type": "json_object"}
    assert captured["headers"]["Authorization"] == "Bearer k"


def test_openai_temperature_omitted_when_reasoning_on(captured, monkeypatch):
    monkeypatch.setenv("BIDLENS_OPENAI_REASONING_EFFORT", "medium")
    captured["response"] = openai_ok()
    OpenAIClient(api_key="k").complete("s", "u")
    assert "temperature" not in captured["payload"] and captured["payload"]["reasoning_effort"] == "medium"


def test_openai_legacy_model_omits_reasoning_field(captured, monkeypatch):
    monkeypatch.setenv("BIDLENS_OPENAI_REASONING_EFFORT", "")
    captured["response"] = openai_ok()
    OpenAIClient(model="gpt-4o-mini", api_key="k").complete("s", "u")
    assert "reasoning_effort" not in captured["payload"] and captured["payload"]["temperature"] == 0


def test_openai_truncation_raises(captured):
    captured["response"] = openai_ok('{"claims": [', finish="length")
    with pytest.raises(LLMError, match="cut off"):
        OpenAIClient(api_key="k").complete("s", "u")


def test_gemini_request_and_thought_filtering(captured):
    captured["response"] = {"candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"text": "internal reasoning", "thought": True}, {"text": '{"ok": true}'}]}}]}
    out = GeminiClient(model="m", api_key="k").complete("sys", "usr", max_tokens=1000)
    p = captured["payload"]
    assert out == '{"ok": true}'
    assert captured["url"].endswith("/models/m:generateContent")
    assert captured["headers"]["x-goog-api-key"] == "k"
    assert p["generationConfig"]["responseMimeType"] == "application/json"
    assert p["generationConfig"]["maxOutputTokens"] == 1000 + 4000
    assert "temperature" not in p["generationConfig"]
    assert p["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "low"}
    assert p["systemInstruction"]["parts"][0]["text"] == "sys"


def test_gemini_truncation_and_block(captured):
    captured["response"] = {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": []}}]}
    with pytest.raises(LLMError, match="cut off"):
        GeminiClient(api_key="k").complete("s", "u")
    captured["response"] = {"promptFeedback": {"blockReason": "SAFETY"}}
    with pytest.raises(LLMError, match="blocked"):
        GeminiClient(api_key="k").complete("s", "u")


def test_gemini_accepts_google_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "g")
    assert GeminiClient().api_key == "g"


def test_ollama_truncation_raises(captured):
    captured["response"] = {"done_reason": "length", "message": {"content": '{"claims": ['}}
    with pytest.raises(LLMError, match="cut off"):
        OllamaClient().complete("s", "u")


def test_gemini_thinking_level_configurable(captured, monkeypatch):
    captured["response"] = {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}
    monkeypatch.setenv("BIDLENS_GEMINI_THINKING_LEVEL", "")
    GeminiClient(api_key="k").complete("s", "u")
    assert "thinkingConfig" not in captured["payload"]["generationConfig"]


def test_timeout_message_is_accurate(monkeypatch):
    def boom(*a, **k):
        raise TimeoutError("The read operation timed out")
    monkeypatch.setattr(llm.urllib.request, "urlopen", boom)
    with pytest.raises(LLMError, match="timed out") as e:
        llm._post("https://example.test/x", {}, {}, 5)
    assert "Cannot reach" not in str(e.value)


def test_timeout_env_override(monkeypatch):
    monkeypatch.setenv("BIDLENS_LLM_TIMEOUT", "300")
    assert GeminiClient(api_key="k").timeout == 300
    monkeypatch.delenv("BIDLENS_LLM_TIMEOUT")
    assert GeminiClient(api_key="k").timeout == 120


def test_ollama_uses_schema_and_falls_back_on_400(monkeypatch):
    calls = []

    def fake_post(url, payload, headers, timeout):
        calls.append(payload["format"])
        if isinstance(payload["format"], dict):
            raise LLMError("HTTP 400 from x: format must be a string")
        return {"message": {"content": "{}"}, "done_reason": "stop"}

    monkeypatch.setattr(llm, "_post", fake_post)
    c = OllamaClient()
    assert c.complete("s", "u", json_schema={"type": "object"}) == "{}"
    assert isinstance(calls[0], dict) and calls[1] == "json"
    c.complete("s", "u", json_schema={"type": "object"})
    assert calls[2] == "json"            # remembered: no repeated 400s


def test_truncation_carries_partial_text(captured):
    captured["response"] = {"done_reason": "length", "message": {"content": '{"claims": [{"te'}}
    with pytest.raises(llm.LLMTruncated) as e:
        OllamaClient().complete("s", "u")
    assert e.value.partial.startswith('{"claims"')


def test_ollama_structured_can_be_disabled(captured, monkeypatch):
    monkeypatch.setenv("BIDLENS_OLLAMA_STRUCTURED", "0")
    captured["response"] = {"message": {"content": "{}"}}
    OllamaClient().complete("s", "u", json_schema={"type": "object"})
    assert captured["payload"]["format"] == "json"
