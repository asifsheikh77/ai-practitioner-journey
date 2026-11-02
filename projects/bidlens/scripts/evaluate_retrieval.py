
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.retrieval import (
    BidLensRetriever,
    load_chunks,
)


def evaluate(retriever, questions, method, top_k=5):
    recalls = []
    reciprocal_ranks = []

    available_ids = {
        chunk["chunk_id"] for chunk in retriever.chunks
    }

    for item in questions:
        question_id = item["id"]
        question = item["question"]
        relevant = set(item.get("relevant_chunk_ids", []))

        # Unsupported questions are evaluated separately
        # during grounded answer generation.
        if item.get("answerability") == "unanswerable":
            print(f"SKIP {question_id}: unanswerable")
            continue
        
        if item.get("label_status") != "verified":
            print(f"SKIP {question_id}: labels not verified")
            continue
        
        if not relevant:
            print(f"SKIP {question_id}: not labeled")
            continue

        unknown_ids = relevant - available_ids
        if unknown_ids:
            raise ValueError(
                f"{question_id}: Unknown relevant chunk IDs: "
                f"{sorted(unknown_ids)}"
            )

        results = retriever.search(
            question,
            method=method,
            top_k=top_k,
        )

        retrieved = [
            result["chunk_id"] for result in results
        ]

        hits = relevant.intersection(retrieved)

        print(f"\n{question_id}: {question}")

        print("Expected chunk IDs:")
        for chunk_id in sorted(relevant):
            print("  ", chunk_id)

        print("Retrieved chunk IDs:")
        for rank, chunk_id in enumerate(retrieved, start=1):
            marker = "MATCH" if chunk_id in relevant else "     "
            print(f"  {rank}. [{marker}] {chunk_id}")

        print("Missing relevant chunks:")
        for chunk_id in sorted(relevant - set(retrieved)):
            print("  ", chunk_id)

        recall = len(hits) / len(relevant)
        recalls.append(recall)

        reciprocal_rank = 0.0

        for rank, chunk_id in enumerate(retrieved, 1):
            if chunk_id in relevant:
                reciprocal_rank = 1.0 / rank
                break

        reciprocal_ranks.append(reciprocal_rank)

        print(
            f"{question_id}: "
            f"Recall@{top_k}={recall:.2f}, "
            f"RR={reciprocal_rank:.2f}"
        )

    if not recalls:
        raise ValueError(
            "No labeled, answerable evaluation questions available. "
            "Populate relevant_chunk_ids first."
        )

    return {
        "method": method,
        "questions_evaluated": len(recalls),
        f"recall_at_{top_k}": sum(recalls) / len(recalls),
        f"mrr_at_{top_k}": (
            sum(reciprocal_ranks) / len(reciprocal_ranks)
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate BidLens retrieval performance"
    )

    parser.add_argument(
        "--document-id",
        default="cbi_upi_rfp",
        help="Document identifier used during ingestion",
    )

    parser.add_argument(
        "--questions",
        default=None,
        help="Path to the evaluation questions JSON file",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    if args.top_k < 1:
        parser.error("--top-k must be positive")

    chunks_path = (
        ROOT
        / "data"
        / "processed"
        / f"{args.document_id}_chunks.jsonl"
    )

    questions_path = (
        Path(args.questions)
        if args.questions
        else ROOT / "evaluation" / f"{args.document_id}_questions.json"
    )

    if not chunks_path.is_file():
        raise FileNotFoundError(
            f"Chunks file not found: {chunks_path}"
        )

    if not questions_path.is_file():
        raise FileNotFoundError(
            f"Questions file not found: {questions_path}"
        )

    chunks = load_chunks(chunks_path)

    questions = json.loads(
        questions_path.read_text(encoding="utf-8")
    )

    # Ensure every labeled question belongs to the
    # document being evaluated.
    for item in questions:
        labeled_document = item.get("document_id")
        if labeled_document and labeled_document != args.document_id:
            raise ValueError(
                f"{item['id']}: Question belongs to "
                f"{labeled_document}, not {args.document_id}"
            )

    print("\n=== BID LENS RETRIEVAL EVALUATION ===")
    print("Document:", args.document_id)
    print("Chunks:", len(chunks))
    print("Questions:", len(questions))
    print("Top K:", args.top_k)
    print("Questions file:", questions_path)

    retriever = BidLensRetriever(chunks)

    for method in ["bm25", "semantic", "hybrid"]:
        print(f"\n=== {method.upper()} ===")

        metrics = evaluate(
            retriever,
            questions,
            method,
            top_k=args.top_k,
        )

        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
