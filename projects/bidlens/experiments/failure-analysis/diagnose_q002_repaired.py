"""Diagnose criterion 6 ranking without modifying the corpus or benchmark."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bidlens.retrieval import BidLensRetriever, load_chunks, reciprocal_rank_fusion
from bidlens.table_repair import build_replacement_corpus, load_verified_rows

TARGET = 'cbi_upi_rfp:p0012:req006'
QUERIES = {
    'original': 'What prior UPI implementation experience must the bidder demonstrate?',
    'specific': 'What UPI solution experience is required in Scheduled Commercial Banks?',
    'lexical': 'Bidder implemented UPI solution running Scheduled Commercial Banks 1 Crore transactions per day',
}


def ranking(scores):
    return np.argsort(-scores, kind='stable').tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--confirm-page12-covered', action='store_true')
    args = parser.parse_args()
    if not args.confirm_page12_covered:
        parser.error('Pass --confirm-page12-covered after reviewing the page-12 replacement')
    if args.top_k < 1:
        parser.error('--top-k must be positive')

    original = load_chunks(ROOT / 'data/processed/cbi_upi_rfp_chunks.jsonl')
    reviewed = load_verified_rows(ROOT / 'evaluation/cbi_eligibility_page12_review.json')
    corpus, removed = build_replacement_corpus(original, reviewed, page12_fully_covered=True)
    matches = [i for i, row in enumerate(corpus) if row['chunk_id'] == TARGET]
    if len(matches) != 1:
        raise RuntimeError(f'Expected exactly one {TARGET}, got {len(matches)}')
    target_index = matches[0]
    print(f'Corpus: {len(original)} original - {len(removed)} removed + {len(reviewed)} added = {len(corpus)}')
    print(f'\nTARGET {TARGET}\nINDEXED TEXT:\n{corpus[target_index]["text"]}')

    retriever = BidLensRetriever(corpus)
    for label, query in QUERIES.items():
        print(f'\n=== {label.upper()} QUERY ===\n{query}')
        bm25 = retriever._bm25_scores(query)
        semantic = retriever._semantic_scores(query)
        bm25_rank = ranking(bm25)
        semantic_rank = ranking(semantic)
        fused = reciprocal_rank_fusion([bm25_rank, semantic_rank])
        hybrid = np.array([fused.get(i, 0.0) for i in range(len(corpus))])
        for method, scores in [('BM25', bm25), ('SEMANTIC', semantic), ('HYBRID', hybrid)]:
            indices = ranking(scores)
            rank = indices.index(target_index) + 1
            print(f'\n{method}: target_rank={rank}/{len(corpus)} target_score={scores[target_index]:.6f}')
            for position, idx in enumerate(indices[:args.top_k], start=1):
                print(f'  {position:2}. {corpus[idx]["chunk_id"]}  score={scores[idx]:.6f}  {corpus[idx]["text"][:110].replace(chr(10), " ")}')

if __name__ == '__main__':
    main()
