
import sys
from pathlib import Path

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.ingestion import (
    chunk_text,
    ingest_pdf,
    normalize_text,
)


def test_normalization():
    text = "Hello   world\r\n\r\nSecond paragraph"

    assert normalize_text(text) == (
        "Hello world\n\nSecond paragraph"
    )


def test_empty_text():
    assert chunk_text("") == []


def test_chunk_size_limit():
    text = " ".join(["requirement"] * 500)

    chunks = chunk_text(
        text,
        max_chars=120,
        overlap_chars=20,
    )

    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_invalid_settings():
    with pytest.raises(ValueError):
        chunk_text("sample", max_chars=100, overlap_chars=100)


def test_page_provenance(tmp_path):
    pdf_path = tmp_path / "test.pdf"

    document = pymupdf.open()

    for content in [
        "Mandatory vendor qualifications",
        "Technical evaluation requirements",
    ]:
        page = document.new_page()
        page.insert_text((72, 72), content)

    document.save(pdf_path)
    document.close()

    result = ingest_pdf(
        pdf_path=pdf_path,
        document_id="test_rfp",
        max_chars=120,
        overlap_chars=20,
    )

    assert result["page_count"] == 2
    assert result["chunk_count"] == 2

    assert result["chunks"][0]["page_number"] == 1
    assert result["chunks"][1]["page_number"] == 2

    assert result["chunks"][0]["document_id"] == "test_rfp"
    assert len(result["source_sha256"]) == 64
