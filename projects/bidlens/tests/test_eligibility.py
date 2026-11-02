
from bidlens.eligibility import (
    build_page_text,
    extract_eligibility_records,
)


def test_reconstructs_overlapping_chunks():
    chunks = [
        {
            "chunk_id": "doc:p0012:c001",
            "page_number": 12,
            "text": "First requirement.\nSecond",
        },
        {
            "chunk_id": "doc:p0012:c002",
            "page_number": 12,
            "text": "Second requirement.",
        },
    ]

    text, source_ids = build_page_text(chunks, 12)

    assert text == "First requirement.\nSecond requirement."
    assert len(source_ids) == 2


def test_extracts_numbered_eligibility_criteria():
    chunks = [
        {
            "chunk_id": "doc:p0012:c001",
            "page_number": 12,
            "text": (
                "2. Eligibility Criteria\n"
                "3. The bidder must have an annual turnover.\n"
                "6. The Bidder should have implemented "
                "the proposed UPI solution.\n"
                "Page 12 of 147"
            ),
        }
    ]

    records = extract_eligibility_records(chunks)

    assert [r["criterion_number"] for r in records] == [3, 6]
    assert "annual turnover" in records[0]["text"]
    assert "UPI solution" in records[1]["text"]
    assert records[1]["review_status"] == "pending"
