"""Run from the BidLens project root: python scripts/experiment_eligibility_v2.py"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bidlens.retrieval import BidLensRetriever, load_chunks
from bidlens.eligibility_v2 import (load_reviewed_records,
                                    make_experimental_corpus, score_results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--review-file', default='evaluation/cbi_eligibility_page12_review.json')
    args = parser.parse_args()
    original = load_chunks(ROOT / 'data/processed/cbi_upi_rfp_chunks.jsonl')
    records = load_reviewed_records(ROOT / args.review_file, original)
    if not records:
        raise SystemExit('No verified records. Review page 12 and update review JSON first.')
    print(f'Baseline: {len(original)} chunks; augmented: {len(original)+len(records)}; verified records: {len(records)}')
    questions = json.loads((ROOT / 'evaluation/cbi_upi_rfp_questions.json').read_text(encoding='utf-8'))
    questions = [q for q in questions if q.get('answerability') == 'answerable'
                 and q.get('label_status') == 'verified' and q.get('relevant_chunk_ids')]
    print(f'Questions: {len(questions)} verified')
    by_id = {r['chunk_id']: r for r in records}
    for method in ('bm25', 'semantic', 'hybrid'):
        print(f'\n=== {method.upper()} ===')
        # Model is constructed once per corpus, not per question.
        base = BidLensRetriever(original)
        aug = BidLensRetriever(make_experimental_corpus(original, records))
        for label, retriever, mapping in [('baseline', base, {}), ('augmented', aug, by_id)]:
            totals = {'recall': 0.0, 'hit': 0.0, 'rr': 0.0}
            for q in questions:
                results = retriever.search(q['question'], method=method, top_k=args.top_k)
                scores = score_results([r['chunk_id'] for r in results], q['relevant_chunk_ids'], mapping)
                for key in totals:
                    totals[key] += scores[key]
                if q['id'] in ('Q001', 'Q002', 'Q003'):
                    print(f"{label:9} {q['id']} recall={scores['recall']:.2f} hit={scores['hit']} rr={scores['rr']:.2f}")
            count = len(questions)
            if count:
                print(f"{label:9} ALL {count}: recall@{args.top_k}={totals['recall']/count:.3f} "
                      f"hit@{args.top_k}={totals['hit']/count:.3f} mrr@{args.top_k}={totals['rr']/count:.3f}")


if __name__ == '__main__':
    main()
