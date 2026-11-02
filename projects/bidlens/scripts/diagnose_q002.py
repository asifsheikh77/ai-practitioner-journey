
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.retrieval import BidLensRetriever, load_chunks


chunks = load_chunks(
    ROOT / "data" / "processed" / "cbi_upi_rfp_chunks.jsonl"
)

retriever = BidLensRetriever(chunks)

target = "cbi_upi_rfp:p0012:c002"

queries = {
    "original": (
        "What prior UPI implementation experience "
        "must the bidder demonstrate?"
    ),
    "specific": (
        "What UPI solution experience is required "
        "in Scheduled Commercial Banks?"
    ),
    "threshold": (
        "How many Scheduled Commercial Banks must "
        "the bidder have implemented a UPI solution in, "
        "and what daily transaction volume is required?"
    ),
    "lexical": (
        "Bidder implemented UPI solution running "
        "Scheduled Commercial Banks 1 Crore "
        "transactions per day"
    ),
}

for label, query in queries.items():
    print(f"\n=== {label.upper()} ===")
    print(query)

    for method in ["bm25", "semantic", "hybrid"]:
        results = retriever.search(
            query,
            method=method,
            top_k=len(chunks),
        )

        rank = next(
            (
                result["rank"]
                for result in results
                if result["chunk_id"] == target
            ),
            None,
        )

        print(f"{method:8s}: rank {rank}")
