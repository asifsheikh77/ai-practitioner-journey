
import re
from collections import defaultdict


CRITERION_START = re.compile(
    r"(?m)^\s*([1-7])\.\s+(?=(?:The |Bidder |At the time))"
)


def build_page_text(chunks, page_number):
    """Reconstruct page text, removing repeated chunk overlap."""
    page_chunks = sorted(
        (c for c in chunks if c["page_number"] == page_number),
        key=lambda c: c["chunk_id"],
    )

    if not page_chunks:
        raise ValueError(f"No chunks found for page {page_number}")

    text = page_chunks[0]["text"]

    for chunk in page_chunks[1:]:
        addition = chunk["text"]
        overlap = 0

        for size in range(min(len(text), len(addition)), 0, -1):
            if text.endswith(addition[:size]):
                overlap = size
                break

        text += addition[overlap:]

    return text, [c["chunk_id"] for c in page_chunks]


def extract_eligibility_records(chunks, page_number=12):
    """
    Extract numbered eligibility entries from a reviewed page.

    IMPORTANT: Raw PDF table extraction can interleave columns.
    These are candidate records requiring human verification.
    """
    text, source_ids = build_page_text(chunks, page_number)

    matches = list(CRITERION_START.finditer(text))

    records = []

    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        criterion = int(match.group(1))
        body = text[match.start():end].strip()

        # Remove trailing printed page footer, if present.
        body = re.sub(
            r"\s*Page\s+\d+\s+of\s+\d+\s*$",
            "",
            body,
            flags=re.IGNORECASE,
        ).strip()

        records.append({
            "chunk_id": (
                f"cbi_upi_rfp:p{page_number:04d}:req{criterion:03d}"
            ),
            "document_id": "cbi_upi_rfp",
            "page_number": page_number,
            "criterion_number": criterion,
            "section": "2. Eligibility Criteria",
            "text": body,
            "source_chunk_ids": source_ids,
            "record_type": "eligibility_candidate",
            "review_status": "pending",
        })

    return records
