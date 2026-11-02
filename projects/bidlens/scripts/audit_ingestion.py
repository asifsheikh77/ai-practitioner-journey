
import argparse
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", required=True)
    parser.add_argument("--expected-pages", type=int, default=147)
    args = parser.parse_args()

    path = Path(args.chunks)

    chunks = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not chunks:
        raise ValueError("No chunks found")

    sizes = [len(c["text"]) for c in chunks]
    pages = Counter(c["page_number"] for c in chunks)
    ids = [c["chunk_id"] for c in chunks]

    print("=== BID LENS INGESTION AUDIT ===")
    print("Total chunks:", len(chunks))
    print("Pages with chunks:", len(pages))
    print("Minimum characters:", min(sizes))
    print("Maximum characters:", max(sizes))
    print("Average characters:", round(sum(sizes) / len(sizes), 1))
    print("Duplicate IDs:", len(ids) - len(set(ids)))

    missing = [
        p for p in range(1, args.expected_pages + 1)
        if p not in pages
    ]

    print("Pages without chunks:", missing)
    print("Chunks above 1200 chars:", sum(s > 1200 for s in sizes))
    print("Chunks below 200 chars:", sum(s < 200 for s in sizes))

    print("\nFive smallest chunks:")
    for c in sorted(chunks, key=lambda x: len(x["text"]))[:5]:
        print(
            c["chunk_id"],
            len(c["text"]),
            repr(c["text"][:100]),
        )

    print("\nChunks on important pages:")
    for page in [12, 13, 48, 49, 55, 108, 109, 115, 116, 145]:
        print(f"Page {page}: {pages.get(page, 0)} chunks")


if __name__ == "__main__":
    main()
