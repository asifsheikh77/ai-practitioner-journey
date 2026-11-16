"""End-to-end Phase 2 evaluation. Writes metrics plus a human-review file.
Automated metrics here are NOT answer correctness: correctness and claim
support need the human grades requested in the review file.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.answering import INSUFFICIENT, answer_question
from bidlens.gate import EvidenceGate
from bidlens.llm import make_client
from bidlens.runtime import DEFAULT_CORPUS, load_retriever


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--provider", choices=["ollama", "openai", "gemini"], default="ollama")
    p.add_argument("--model")
    p.add_argument("--judge", action="store_true")
    p.add_argument("--min-semantic", type=float, default=EvidenceGate().min_semantic)
    p.add_argument("--min-coverage", type=float, default=EvidenceGate().min_coverage)
    p.add_argument("--out-dir", type=Path, default=ROOT / "evaluation/results/phase2")
    a = p.parse_args()

    questions = json.loads((ROOT / "evaluation/cbi_upi_rfp_questions.json").read_text(encoding="utf-8"))
    rubric = {r["id"]: r for r in json.loads((ROOT / "evaluation/rubric_42_narrow_assertions.json").read_text(encoding="utf-8"))}
    retriever, client = load_retriever(a.corpus), make_client(a.provider, a.model)
    gate = EvidenceGate(a.min_semantic, a.min_coverage)

    records = []
    for q in questions:
        r = answer_question(q["question"], retriever.search, client, gate, use_judge=a.judge)
        gold = set(rubric.get(q["id"], {}).get("v2_support_candidate_ids", []))
        ctx = {e["chunk_id"] for e in r.evidence}
        cited = {c for cl in r.claims for c in cl.citations}
        records.append({
            "id": q["id"], "question": q["question"], "answerable": q["answerability"] == "answerable",
            "status": r.status, "outcome": r.outcome, "reason": r.reason, "truncated": r.truncated,
            "notes": r.notes, "gate": r.gate,
            "gold_in_context": (bool(gold & ctx) if gold else None),
            "gold_cited": (bool(gold & cited) if gold else None),
            "claims": [c.__dict__ for c in r.claims], "rejected": r.rejected, "gaps": r.gaps,
            "timings_s": r.timings_s,
            "human_review": {"answer_correct": None, "claims_supported": None, "notes": ""},
        })
        print(q["id"], r.status)

    ans = [x for x in records if x["answerable"]]
    unans = [x for x in records if not x["answerable"]]
    gold = [x for x in ans if x["gold_in_context"] is not None]
    totals = [x["timings_s"].get("total") for x in records if x["timings_s"].get("total")]
    summary = {
        "model": client.name, "gate": {"min_semantic": gate.min_semantic, "min_coverage": gate.min_coverage},
        "n_answerable": len(ans), "n_unanswerable": len(unans),
        "unanswerable_abstained": sum(x["status"] == INSUFFICIENT and x["outcome"] != "error" for x in unans),
        "answerable_over_abstained": sum(x["status"] == INSUFFICIENT and x["outcome"] != "error" for x in ans),
        "gold_in_context": f"{sum(x['gold_in_context'] for x in gold)}/{len(gold)}",
        "gold_cited": f"{sum(bool(x['gold_cited']) for x in gold)}/{len(gold)}",
        "operational_errors": sum(x["outcome"] == "error" for x in records),
        "truncation_recoveries": sum(bool(x["truncated"]) for x in records),
        "claims_kept": sum(len(x["claims"]) for x in records),
        "claims_removed_by_verification": sum(len(x["rejected"]) for x in records),
        "median_total_latency_s": statistics.median(totals) if totals else None,
        "caveats": ["Gold = provisional rubric candidates, not certified.",
                    "Unanswerable absence not fully audited.",
                    "Correctness and semantic support require human review of human_review fields."],
    }
    a.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = a.out_dir / f"qa_eval_{stamp}.json"
    path.write_text(json.dumps({"summary": summary, "records": records}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
