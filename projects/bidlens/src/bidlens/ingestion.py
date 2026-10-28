
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from bidlens.pdf_inspector import inspect_pdf


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_text(text: str, max_chars: int) -> list[str]:
    """Split oversized paragraphs without losing characters."""
    parts = []
    remaining = text.strip()

    while len(remaining) > max_chars:
        boundary = remaining.rfind(" ", 0, max_chars + 1)

        if boundary <= 0:
            boundary = max_chars

        parts.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()

    if remaining:
        parts.append(remaining)

    return parts


def chunk_text(
    text: str,
    max_chars: int = 1200,
    overlap_chars: int = 200,
) -> list[str]:
    """Create paragraph-aware chunks with bounded overlap."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    if not 0 <= overlap_chars < max_chars:
        raise ValueError(
            "overlap_chars must be between 0 and max_chars"
        )

    text = normalize_text(text)

    if not text:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    units = []
    for paragraph in paragraphs:
        units.extend(split_long_text(paragraph, max_chars))

    chunks = []
    current = ""

    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        # Retain context from the previous chunk.
        # The overlap is approximate and may start mid-word.
        previous_tail = (
            current[-overlap_chars:].strip()
            if overlap_chars and current
            else ""
        )

        candidate = (
            f"{previous_tail}\n\n{unit}"
            if previous_tail
            else unit
        )

        # Never exceed the configured maximum.
        if len(candidate) > max_chars:
            candidate = unit

        current = candidate

    if current:
        chunks.append(current)

    return chunks


def ingest_pdf(
    pdf_path: Path,
    document_id: str,
    max_chars: int = 1200,
    overlap_chars: int = 200,
) -> dict:
    """Extract and chunk a PDF with source provenance."""
    report = inspect_pdf(pdf_path, document_id)

    chunks = []

    for page in report["pages"]:
        page_chunks = chunk_text(
            page["text"],
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )

        for page_index, content in enumerate(page_chunks, 1):
            chunk_id = (
                f"{document_id}:"
                f"p{page['page_number']:04d}:"
                f"c{page_index:03d}"
            )

            chunks.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source_sha256": report["sha256"],
                "page_number": page["page_number"],
                "chunk_index": page_index,
                "text": content,
                "character_count": len(content),
            })

    return {
        "document_id": document_id,
        "source_sha256": report["sha256"],
        "page_count": report["page_count"],
        "chunk_count": len(chunks),
        "settings": {
            "max_chars": max_chars,
            "overlap_chars": overlap_chars,
        },
        "chunks": chunks,
    }


def save_chunks_jsonl(result: dict, output_path: Path) -> None:
    """Write one JSON object per line."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w", encoding="utf-8") as file:
        for chunk in result["chunks"]:
            file.write(
                json.dumps(chunk, ensure_ascii=False) + "\n"
            )
