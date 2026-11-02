
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.retrieval import (
    BidLensRetriever,
    reciprocal_rank_fusion,
    tokenize,
)


@pytest.fixture
def sample_chunks():
    return [
        {
            "chunk_id": "rfp:p0001:c001",
            "document_id": "rfp",
            "page_number": 1,
            "text": "Vendor must provide three references.",
        },
        {
            "chunk_id": "rfp:p0002:c001",
            "document_id": "rfp",
            "page_number": 2,
            "text": "The network requires redundant switches.",
        },
        {
            "chunk_id": "rfp:p0003:c001",
            "document_id": "rfp",
            "page_number": 3,
            "text": "Payment terms are net thirty days.",
        },
    ]


def test_tokenize():
    assert tokenize("UPI, SLA & MSP!") == [
        "upi", "sla", "msp"
    ]


def test_bm25_retrieval(sample_chunks):
    retriever = BidLensRetriever(sample_chunks)

    results = retriever.search(
        "vendor references",
        method="bm25",
        top_k=1,
    )

    assert results[0]["page_number"] == 1


def test_rrf():
    scores = reciprocal_rank_fusion([
        [0, 1, 2],
        [1, 0, 2],
    ])

    assert scores[0] == pytest.approx(scores[1])
    assert scores[0] > scores[2]


def test_invalid_method(sample_chunks):
    retriever = BidLensRetriever(sample_chunks)

    with pytest.raises(ValueError):
        retriever.search("references", method="invalid")


def test_empty_query(sample_chunks):
    retriever = BidLensRetriever(sample_chunks)

    with pytest.raises(ValueError):
        retriever.search("   ", method="bm25")
