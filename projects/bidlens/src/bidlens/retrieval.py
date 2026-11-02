
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def tokenize(text: str) -> list[str]:
    """Simple tokenizer for English RFP retrieval."""
    return re.findall(r"[a-z0-9]+", text.lower())


def load_chunks(path: Path) -> list[dict]:
    """Load and validate a JSONL chunk collection."""
    chunks = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                chunk = json.loads(line)

                required = {
                    "chunk_id",
                    "document_id",
                    "page_number",
                    "text",
                }

                if not required.issubset(chunk):
                    raise ValueError(
                        f"Missing chunk fields: {required - set(chunk)}"
                    )

                chunks.append(chunk)

    if not chunks:
        raise ValueError("No chunks found")

    ids = [chunk["chunk_id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk IDs")

    return chunks


def reciprocal_rank_fusion(
    rankings: list[list[int]],
    k: int = 60,
) -> dict[int, float]:
    """Combine ranked document indices using RRF."""
    scores = {}

    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            scores[index] = (
                scores.get(index, 0.0)
                + 1.0 / (k + rank)
            )

    return scores


class BidLensRetriever:
    def __init__(
        self,
        chunks: list[dict],
        model_name: str = MODEL_NAME,
    ):
        if not chunks:
            raise ValueError("Chunk collection cannot be empty")

        self.chunks = chunks
        self.model_name = model_name

        self.tokenized = [
            tokenize(chunk["text"])
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(self.tokenized)

        # Lazy initialization: BM25 can run without
        # loading or downloading an embedding model.
        self.model = None
        self.embeddings = None

    def _ensure_embeddings(self):
        if self.embeddings is not None:
            return

        self.model = SentenceTransformer(self.model_name)

        self.embeddings = self.model.encode(
            [chunk["text"] for chunk in self.chunks],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    def _bm25_scores(self, query: str) -> np.ndarray:
        return np.asarray(
            self.bm25.get_scores(tokenize(query)),
            dtype=float,
        )

    def _semantic_scores(self, query: str) -> np.ndarray:
        self._ensure_embeddings()

        query_vector = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        return self.embeddings @ query_vector

    def search(
        self,
        query: str,
        method: str = "hybrid",
        top_k: int = 5,
    ) -> list[dict]:
        if method not in {"bm25", "semantic", "hybrid"}:
            raise ValueError(f"Unknown method: {method}")

        if not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k < 1:
            raise ValueError("top_k must be positive")

        bm25_scores = None
        semantic_scores = None

        if method in {"bm25", "hybrid"}:
            bm25_scores = self._bm25_scores(query)

        if method in {"semantic", "hybrid"}:
            semantic_scores = self._semantic_scores(query)

        if method == "bm25":
            scores = bm25_scores
        elif method == "semantic":
            scores = semantic_scores
        else:
            bm25_ranking = np.argsort(
                -bm25_scores, kind="stable"
            ).tolist()

            semantic_ranking = np.argsort(
                -semantic_scores, kind="stable"
            ).tolist()

            fused = reciprocal_rank_fusion(
                [bm25_ranking, semantic_ranking]
            )

            scores = np.array([
                fused.get(i, 0.0)
                for i in range(len(self.chunks))
            ])

        indices = np.argsort(
            -scores, kind="stable"
        )[:top_k]

        results = []

        for rank, index in enumerate(indices, start=1):
            chunk = self.chunks[int(index)]

            results.append({
                "rank": rank,
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "page_number": chunk["page_number"],
                "score": float(scores[index]),
                "text": chunk["text"],
            })

        return results
