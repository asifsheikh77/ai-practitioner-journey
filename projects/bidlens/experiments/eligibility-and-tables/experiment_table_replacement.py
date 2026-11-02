"""Run criterion-level retrieval on a fully reviewed replacement page 12."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bidlens.retrieval import BidLensRetriever, load_chunks
from bidlens.table_repair import load_verified_rows, build_replacement_corpus, score_ids


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--top-k', type=int, default=5)
    p.add_argument('--confirm-page12-covered', action='store_true',
                   help='Confirm all content of page 12 is represented by reviewed rows or is irrelevant')
    p.add_argument('--review-file', default='evaluation/cbi_eligibility_page12_review.json')
    p.add_argument('--labels', default='evaluation/page12_criterion_gold.json')
    args = p.parse_args()
    if args.top_k < 1:
        p.error('--top-k must be positive')
    original = load_chunks(ROOT / 'data/processed/cbi_upi_rfp_chunks.jsonl')
    replacement = load_verified_rows(ROOT / args.review_file)
    corpus, removed = build_replacement_corpus(original, replacement, args.confirm_page12_covered)
    questions = json.loads((ROOT / args.labels).read_text(encoding='utf-8'))
    if not questions or any(not q.get('verified') or not q.get('gold_record_ids') for q in questions):
        raise ValueError('All criterion-level labels must be reviewed and verified')
    replacement_ids = {r['chunk_id'] for r in replacement}
    if any(not set(q['gold_record_ids']) <= replacement_ids for q in questions):
        raise ValueError('Gold record ID not found in replacement corpus')
    print(f'Original {len(original)}; removed page 12: {len(removed)}; added {len(replacement)}; repaired {len(corpus)}')
    print('IMPORTANT: Original chunk-ID benchmark is not directly comparable to criterion-ID labels.')
    for method in ('bm25', 'semantic', 'hybrid'):
        retriever = BidLensRetriever(corpus)
        scores = []
        print(f'\n=== {method.upper()} ===')
        for q in questions:
            found = retriever.search(q['question'], method=method, top_k=args.top_k)
            score = score_ids(found, q['gold_record_ids'])
            scores.append(score)
            print(f"{q['id']} hit={score['hit']} recall={score['recall']:.2f} rr={score['rr']:.2f} ")
            print('  top IDs: ' + ', '.join(r['chunk_id'] for r in found))
        n = len(scores)
        print(f"MEAN hit@{args.top_k}={sum(s['hit'] for s in scores)/n:.3f} "
              f"recall@{args.top_k}={sum(s['recall'] for s in scores)/n:.3f} "
              f"mrr@{args.top_k}={sum(s['rr'] for s in scores)/n:.3f}")

if __name__ == '__main__':
    main()
