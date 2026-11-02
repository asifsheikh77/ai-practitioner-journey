import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--page", type=int, required=True)
parser.add_argument(
    "--chunks",
    default="data/processed/cbi_upi_rfp_chunks.jsonl",
)
args = parser.parse_args()

with Path(args.chunks).open(encoding="utf-8") as file:
    for line in file:
        chunk = json.loads(line)

        if chunk["page_number"] == args.page:
            print("\n" + "=" * 70)
            print(chunk["chunk_id"])
            print("=" * 70)
            print(chunk["text"])