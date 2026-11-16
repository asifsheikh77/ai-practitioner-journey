"""Ask a grounded question about the V2 RFP corpus.
python scripts/ask.py "What minimum annual turnover must a bidder demonstrate?" [--provider openai|gemini] [--judge]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bidlens.answering import answer_question
from bidlens.gate import EvidenceGate
from bidlens.llm import make_client
from bidlens.runtime import DEFAULT_CORPUS, load_retriever


def render(r) -> str:
    out = [f"STATUS: {r.status}  ({r.reason})"]
    for c in r.claims:
        out.append(f"  - {c.text}  [{', '.join(c.citations)}]")
    if r.gaps:
        out.append(f"GAPS: {r.gaps}")
    for x in r.rejected:
        out.append(f"  removed: {x['text']}  -> {x['reason']}")
    pages = {(e['chunk_id'], e['page_number']) for e in r.evidence}
    out.append("EVIDENCE: " + "; ".join(f"p.{p} {i}" for i, p in sorted(pages, key=lambda t: t[1])))
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("question")
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--provider", choices=["ollama", "openai", "gemini"], default="ollama")
    p.add_argument("--model")
    p.add_argument("--judge", action="store_true", help="add LLM claim-support judge")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    result = answer_question(a.question, load_retriever(a.corpus).search,
                             make_client(a.provider, a.model), EvidenceGate(), use_judge=a.judge)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) if a.json else render(result))


if __name__ == "__main__":
    main()
