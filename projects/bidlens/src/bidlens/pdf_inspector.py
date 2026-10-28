
from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def inspect_pdf(path: Path, document_id: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Expected a PDF file")

    pages = []

    with pymupdf.open(path) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDF is unsupported")

        for index, page in enumerate(document):
            text = page.get_text("text", sort=True)

            pages.append({
                "document_id": document_id,
                "page_number": index + 1,
                "text": text,
                "character_count": len(text),
                "word_count": len(text.split()),
            })

    return {
        "document_id": document_id,
        "filename": path.name,
        "sha256": sha256_file(path),
        "page_count": len(pages),
        "total_characters": sum(
            p["character_count"] for p in pages
        ),
        "pages": pages,
    }
