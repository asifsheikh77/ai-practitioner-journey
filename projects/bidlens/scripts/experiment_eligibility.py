
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.eligibility import extract_eligibility_records
from bidlens.retrieval import BidLensRetriever, load_chunks


CHUNKS_PATH = (
    ROOT / "data" / "processed" / "cbi_upi_rfp_chunks.jsonl"
)

OUTPUT_PATH = (
    ROOT / "data" / "processed" / "cbi_upi_rfp_eligibility_candidates.jsonl"
)

QUESTIONS = {
    "Q001": {
        "query": "What minimum annual turnover must a bidder demonstrate?",
        "baseline_id": "cbi_upi_rfp:p0012:c001",
        "criterion": 3,
    },
    "Q002": {
        "query": "What prior UPI implementation experience must the bidder demonstrate?",
        "baseline_id": "cbi_upi_rfp:p0012:c002",
        "criterion": 6,
    },
}


def rank_of(retriever, query, target_id, method):
    results = retriever.search(
        query,
        method=method,
        top_k=len(retriever.chunks),
    )

    for result in results:
        if result["chunk_id"] == target_id:
            return result["rank"]

    return None


def main():
    chunks = load_chunks(CHUNKS_PATH)

    candidates = extract_eligibility_records(chunks, page_number=12)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for record in candidates:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Extracted {len(candidates)} candidate records")
    print(f"Saved: {OUTPUT_PATH}")

    for record in candidates:
        print(
            f"Criterion {record['criterion_number']}: "
            f"{record['text'][:120]!r}"
        )

    criterion_map = {
        record["criterion_number"]: record
        for record in candidates
    }

    required = {3, 6}
    missing = required - set(criterion_map)

    if missing:
        raise ValueError(
            f"Missing criteria {sorted(missing)}. "
            "Inspect extraction before evaluating."
        )

    print("\nWARNING: Review the extracted records against the PDF.")
    print("The following rankings are experimental, not validated gold results.")

    # Preserve the original 443-chunk baseline.
    baseline = BidLensRetriever(chunks)

    # Replace the original page-12 chunks with atomic candidates.
    # This tests a focused representation change without
    # duplicating the same source page in the index.
    experimental_chunks = [
        c for c in chunks
        if c["page_number"] != 12
    ] + candidates

    experimental = BidLensRetriever(experimental_chunks)

    print(f"\nBaseline corpus: {len(chunks)} chunks")
    print(f"Experimental corpus: {len(experimental_chunks)} records")

    for question_id, question in QUESTIONS.items():
        target = criterion_map[question["criterion"]]["chunk_id"]

        print(f"\n=== {question_id} ===")
        print(question["query"])

        for method in ["bm25", "semantic", "hybrid"]:
            old_rank = rank_of(
                baseline,
                question["query"],
                question["baseline_id"],
                method,
            )

            new_rank = rank_of(
                experimental,
                question["query"],
                target,
                method,
            )

            print(
                f"{method:8s} "
                f"baseline={str(old_rank):>4s} "
                f"experimental={str(new_rank):>4s}"
            )


if __name__ == "__main__":
    main()
