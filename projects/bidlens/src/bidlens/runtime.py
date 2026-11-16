"""Shared loader so the CLI, evaluation scripts and UI use the same V2 corpus."""
from __future__ import annotations

from pathlib import Path

from .retrieval import BidLensRetriever, load_chunks

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = ROOT / "data/processed/cbi_upi_rfp_v2.jsonl"
CACHE_DIR = ROOT / "data/processed/.embedding_cache"


def load_retriever(corpus: Path = DEFAULT_CORPUS) -> BidLensRetriever:
    if not corpus.exists():
        raise FileNotFoundError(
            f"{corpus} not found. Download the RFP (see sources.json) and run "
            "scripts/ingest_rfp_v2.py first; processed data is git-ignored.")
    chunks = [c for c in load_chunks(corpus) if c.get("searchable") is True]
    return BidLensRetriever(chunks, cache_dir=CACHE_DIR)
