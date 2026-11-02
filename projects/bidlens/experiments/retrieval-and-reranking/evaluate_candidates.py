"""Day 3.5: candidate-pool coverage on repaired BidLens corpus."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bidlens.retrieval import BidLensRetriever, load_chunks
from bidlens.table_repair import load_verified_rows, build_replacement_corpus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--depths', type=int, nargs='+', default=[20, 50, 100])
    ap.add_argument('--confirm-page12-covered', action='store_true')
    args = ap.parse_args()
    if not args.confirm_page12_covered:
        ap.error('Pass --confirm-page12-covered only after reviewing page 12 coverage')
    if any(d < 1 for d in args.depths):
        ap.error('Depths must be positive')

    original = load_chunks(ROOT / 'data/processed/cbi_upi_rfp_chunks.jsonl')
    rows = load_verified_rows(ROOT / 'evaluation/cbi_eligibility_page12_review.json')
    corpus, removed = build_replacement_corpus(original, rows, True)
    questions = json.loads((ROOT / 'evaluation/cbi_upi_rfp_questions.json').read_text(encoding='utf-8-sig'))
    criterion_questions = json.loads((ROOT / 'evaluation/page12_criterion_gold.json').read_text(encoding='utf-8-sig'))
    criterion_map = {q['id']: q['gold_record_ids'] for q in criterion_questions if q.get('verified')}
    usable = []
    for q in questions:
        if q.get('answerability') != 'answerable' or q.get('label_status') != 'verified':
            continue
        gold = criterion_map.get(q['id'], q.get('relevant_chunk_ids', []))
        if not gold:
            raise ValueError(f"{q['id']} has no gold IDs")
        usable.append((q['id'], q['question'], set(gold)))
    if not usable:
        raise ValueError('No verified answerable questions')
    corpus_ids = {c['chunk_id'] for c in corpus}
    for qid, _, gold in usable:
        missing = gold - corpus_ids
        if missing:
            raise ValueError(f'{qid}: missing gold IDs: {sorted(missing)}')

    retriever = BidLensRetriever(corpus)
    max_k = min(max(args.depths), len(corpus))
    methods = ('bm25', 'semantic', 'hybrid')
    rankings = {}
    for qid, question, _ in usable:
        rankings[qid] = {m: [r['chunk_id'] for r in retriever.search(question, method=m, top_k=max_k)] for m in methods}

    print(f'Corpus: {len(original)} original - {len(removed)} page12 + {len(rows)} requirements = {len(corpus)}')
    print(f'Questions: {len(usable)} verified answerable; original wording preserved')
    print('NOTE: Q001-Q003 use criterion IDs; other questions use original chunk IDs.')
    print('NOTE: Union pools contain up to 2K records; compare recall AND actual pool size.')
    print('NOTE: This is candidate coverage, NOT reranked top-5 performance.')

    for depth in sorted(set(args.depths)):
        print(f'\n=== DEPTH {depth} ===')
        totals = {m: {'hit': 0, 'recall': 0., 'size': 0} for m in (*methods, 'union_bm25_semantic')}
        for qid, _, gold in usable:
            pools = {m: set(rankings[qid][m][:depth]) for m in methods}
            pools['union_bm25_semantic'] = pools['bm25'] | pools['semantic']
            row = []
            for method, pool in pools.items():
                hit = int(bool(pool & gold))
                recall = len(pool & gold) / len(gold)
                totals[method]['hit'] += hit
                totals[method]['recall'] += recall
                totals[method]['size'] += len(pool)
                row.append(f'{method}:hit={hit},rec={recall:.2f},n={len(pool)}')
            print(f'{qid} gold={len(gold)} | ' + ' | '.join(row))
        n = len(usable)
        print('SUMMARY')
        for method, x in totals.items():
            print(f'{method:22s} hit@pool={x["hit"]/n:.3f} recall@pool={x["recall"]/n:.3f} avg_pool_size={x["size"]/n:.1f}')


if __name__ == '__main__':
    main()
