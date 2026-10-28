
import sys
from pathlib import Path

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bidlens.pdf_inspector import inspect_pdf


def test_inspection_preserves_page_numbers(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    document = pymupdf.open()

    for text in ["Mandatory requirements", "Evaluation criteria"]:
        page = document.new_page()
        page.insert_text((72, 72), text)

    document.save(pdf_path)
    document.close()

    result = inspect_pdf(pdf_path, "sample")

    assert result["page_count"] == 2
    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][1]["page_number"] == 2

    assert "Mandatory requirements" in (
        result["pages"][0]["text"]
    )

    assert "Evaluation criteria" in (
        result["pages"][1]["text"]
    )

    assert len(result["sha256"]) == 64


def test_missing_pdf_raises_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_pdf(tmp_path / "missing.pdf", "missing")
