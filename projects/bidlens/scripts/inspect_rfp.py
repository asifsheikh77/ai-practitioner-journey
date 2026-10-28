
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.pdf_inspector import inspect_pdf


def main():
    parser = argparse.ArgumentParser(
        description="Inspect an RFP PDF"
    )
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--document-id", required=True)
    args = parser.parse_args()

    pdf_path = ROOT / args.pdf

    report = inspect_pdf(
        path=pdf_path,
        document_id=args.document_id,
    )

    output_dir = ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / (
        f"{args.document_id}_inspection.json"
    )

    output_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Document: {report['document_id']}")
    print(f"Pages: {report['page_count']}")
    print(f"Characters: {report['total_characters']}")
    print(f"SHA-256: {report['sha256']}")
    print(f"Saved: {output_file}")

    print("\nFirst-page preview:")
    print(report["pages"][0]["text"][:1000])


if __name__ == "__main__":
    main()
