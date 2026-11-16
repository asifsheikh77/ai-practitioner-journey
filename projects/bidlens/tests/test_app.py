import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.llm import FakeClient  # noqa: E402

PASSAGE = {"chunk_id": "d:p0012:elig003", "document_id": "d", "page_number": 12,
           "text": "Bidder must have annual turnover of INR 20 crore in each of three financial years.",
           "semantic_score": 0.62, "bm25_score": 9.0}
OFF_TOPIC = dict(PASSAGE, semantic_score=0.05)


class FakeRetriever:
    def search(self, q, method="hybrid", top_k=5):
        return [OFF_TOPIC if "france" in q.lower() else PASSAGE]


@pytest.fixture
def app(monkeypatch):
    import streamlit as st
    st.cache_resource.clear()
    replies = []
    monkeypatch.setattr("bidlens.runtime.load_retriever", lambda *a, **k: FakeRetriever())
    monkeypatch.setattr("bidlens.llm.make_client", lambda *a, **k: FakeClient(replies))
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=20)
    at.replies = replies
    return at.run()


def ask(at, text):
    at.text_input(key="question").set_value(text)
    next(b for b in at.button if b.label == "Ask").click()
    return at.run()


def texts(at):
    groups = (at.warning, at.success, at.info, at.error)
    return " ".join(e.value for g in groups for e in g)


def test_free_text_answer(app):
    app.replies.append(json.dumps({"answerable": True, "gaps": "", "claims": [
        {"text": "Annual turnover of INR 20 crore is required.", "citations": ["d:p0012:elig003"]}]}))
    at = ask(app, "What annual turnover must a bidder have?")
    assert not at.exception and "Answer found" in texts(at)


def test_out_of_scope_message(app):
    at = ask(app, "What is the capital of France?")
    assert not at.exception and "outside the scope" in texts(at)


def test_not_in_document_message(app):
    app.replies.append(json.dumps({"answerable": False, "claims": [], "gaps": "winner not stated"}))
    at = ask(app, "Which annual turnover winner was selected?")
    assert "doesn't appear to state" in texts(at)


def test_too_short_input(app):
    assert "at least a few words" in texts(ask(app, "hi"))


def test_example_button_fills_box(app):
    next(b for b in app.button if b.label.startswith("What minimum annual turnover")).click()
    at = app.run()
    assert at.text_input(key="question").value.startswith("What minimum annual turnover")
