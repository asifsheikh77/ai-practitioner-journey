"""Evidence-sufficiency gate (FR-07).

RRF scores depend only on rank, so they say nothing about relevance: a
nonsense query still gets a "top" hit. This gate looks at two raw signals
instead:

* semantic similarity of the best hit (cosine, MiniLM scale), and
* query-term coverage: the share of the query's content words that appear
  anywhere in the retrieved passages.

Thresholds are provisional until calibrated with ``scripts/calibrate_gate.py``
on reviewed answerable / unanswerable questions. The gate catches off-topic
questions; it cannot catch "plausible but absent" questions (e.g. "who won
this tender?"), which is why generation-time abstention and the claim-support
check exist as later layers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

ANSWERABLE = "ANSWERABLE"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"

_TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    """a an and are as at be by can do does for from has have how if in into is it
    its of on or our shall should that the their this to under was were what when
    where which who whom why will with must may any all each per than then there
    these those they used using ultimately actually exact final""".split()
)


def content_terms(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


@dataclass(frozen=True)
class GateDecision:
    status: str
    reason: str
    top_semantic: float | None
    coverage: float
    missing_terms: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceGate:
    min_semantic: float = 0.30   # provisional - calibrate before reporting
    min_coverage: float = 0.50   # provisional - calibrate before reporting

    def evaluate(self, query: str, hits: list[dict]) -> GateDecision:
        terms = sorted(set(content_terms(query)))
        if not hits:
            return GateDecision(INSUFFICIENT, "no passages retrieved", None, 0.0, terms)

        corpus = set()
        for hit in hits:
            corpus.update(_TOKEN.findall(hit["text"].lower()))
        missing = [t for t in terms if t not in corpus]
        coverage = 1.0 - len(missing) / len(terms) if terms else 0.0

        sems = [h.get("semantic_score") for h in hits if h.get("semantic_score") is not None]
        top_sem = max(sems) if sems else None

        if top_sem is not None and top_sem < self.min_semantic:
            return GateDecision(
                INSUFFICIENT,
                f"best semantic similarity {top_sem:.2f} < {self.min_semantic:.2f}",
                top_sem, coverage, missing)
        if coverage < self.min_coverage:
            return GateDecision(
                INSUFFICIENT,
                f"only {coverage:.0%} of query terms appear in retrieved text "
                f"(need {self.min_coverage:.0%})",
                top_sem, coverage, missing)
        return GateDecision(ANSWERABLE, "retrieval signals pass thresholds",
                            top_sem, coverage, missing)
