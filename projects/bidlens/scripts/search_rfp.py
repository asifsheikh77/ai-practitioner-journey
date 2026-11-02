
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.retrieval import (
    BidLensRetriever,
    load_chunks,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--method",
        choices=["bm25", "semantic", "hybrid"],
        default="hybrid",
    )
    parser.add_argument("--top-k", type=int, default=5)

    parser.add_argument(
        "--document-id",
        default="cbi_upi_rfp",
        choices=["cbi_upi_rfp", "usao_it_managed_services"],
    )

    args = parser.parse_args()

    chunks_path = (
        ROOT
        / "data"
        / "processed"
        / f"{args.document_id}_chunks.jsonl"
    )

    retriever = BidLensRetriever(
        load_chunks(chunks_path)
    )

    results = retriever.search(
        query=args.query,
        method=args.method,
        top_k=args.top_k,
    )

    print(f"\nQuery: {args.query}")
    print(f"Method: {args.method}\n")

    for result in results:
        print(
            f"[{result['rank']}] "
            f"{result['chunk_id']} "
            f"(page {result['page_number']}) "
            f"score={result['score']:.4f}"
        )
        print(result["text"][:350])
        print("-" * 70)


if __name__ == "__main__":
    main()
