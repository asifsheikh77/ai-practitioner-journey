
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.ingestion import (
    ingest_pdf,
    save_chunks_jsonl,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=200)
    args = parser.parse_args()

    result = ingest_pdf(
        pdf_path=ROOT / args.pdf,
        document_id=args.document_id,
        max_chars=args.max_chars,
        overlap_chars=args.overlap,
    )

    output_dir = ROOT / "data" / "processed"

    chunks_path = output_dir / (
        f"{args.document_id}_chunks.jsonl"
    )
    metadata_path = output_dir / (
        f"{args.document_id}_metadata.json"
    )

    save_chunks_jsonl(result, chunks_path)

    metadata = {
        key: value
        for key, value in result.items()
        if key != "chunks"
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"Document: {result['document_id']}")
    print(f"Pages: {result['page_count']}")
    print(f"Chunks: {result['chunk_count']}")
    print(f"Saved chunks: {chunks_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()
