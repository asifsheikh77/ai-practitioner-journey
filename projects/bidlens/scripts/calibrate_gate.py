"""Calibrate the evidence gate on the reviewed question set (no LLM needed).
Reports raw signals per question and a threshold grid. Q017-Q020 are labelled
unanswerable but 'absence_not_audited' - treat results as indicative only.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.gate import ANSWERABLE, EvidenceGate
from bidlens.runtime import DEFAULT_CORPUS, load_retriever


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--questions", type=Path, default=ROOT / "evaluation/cbi_upi_rfp_questions.json")
    p.add_argument("--out", type=Path, default=ROOT / "evaluation/results/phase2/gate_calibration.json")
    p.add_argument("--top-k", type=int, default=8)
    a = p.parse_args()

    retriever = load_retriever(a.corpus)
    questions = json.loads(a.questions.read_text(encoding="utf-8"))
    rows = []
    for q in questions:
        hits = retriever.search(q["question"], method="hybrid", top_k=a.top_k)
        d = EvidenceGate(0, 0).evaluate(q["question"], hits)  # thresholds 0: just collect signals
        rows.append({"id": q["id"], "answerable": q["answerability"] == "answerable",
                     "top_semantic": d.top_semantic, "coverage": d.coverage, "missing": d.missing_terms})
        print(f"{q['id']} {'ANS ' if rows[-1]['answerable'] else 'UNANS'} sem={d.top_semantic:.2f} cov={d.coverage:.2f} missing={d.missing_terms}")

    grid = []
    for sem, cov in itertools.product([x / 100 for x in range(10, 61, 5)], [x / 100 for x in range(20, 101, 10)]):
        gate = EvidenceGate(sem, cov)
        tp = fp = tn = fn = 0
        for r in rows:
            passed = (r["top_semantic"] >= sem) and (r["coverage"] >= cov)
            if r["answerable"]:
                tp += passed; fn += not passed
            else:
                fp += passed; tn += not passed
        grid.append({"min_semantic": sem, "min_coverage": cov, "answerable_passed": tp, "answerable_blocked": fn,
                     "unanswerable_blocked": tn, "unanswerable_passed": fp})
    # Never block a verified-answerable question if avoidable; then block as many unanswerable as possible.
    best = sorted(grid, key=lambda g: (g["answerable_blocked"], g["unanswerable_passed"], -g["min_semantic"]))[:5]
    print("\nBest thresholds (fewest answerable blocked, then fewest unanswerable passed):")
    for g in best:
        print(g)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"n_questions": len(rows), "rows": rows, "best": best, "grid": grid}, indent=2), encoding="utf-8")
    print(f"\nWrote {a.out}. Set EvidenceGate defaults only after reviewing; n is small (16 vs 4).")


if __name__ == "__main__":
    main()
