"""Day 3.6: frozen-label local cross-encoder reranking experiment."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bidlens.retrieval import BidLensRetriever, load_chunks
from bidlens.table_repair import load_verified_rows, build_replacement_corpus, score_ids


def load_questions(corpus_ids):
    questions = json.loads((ROOT / 'evaluation/cbi_upi_rfp_questions.json').read_text(encoding='utf-8-sig'))
    criterion = json.loads((ROOT / 'evaluation/page12_criterion_gold.json').read_text(encoding='utf-8-sig'))
    criterion_map = {q['id']: q['gold_record_ids'] for q in criterion if q.get('verified')}
    result = []
    for q in questions:
        if q.get('answerability') != 'answerable' or q.get('label_status') != 'verified':
            continue
        gold = set(criterion_map.get(q['id'], q.get('relevant_chunk_ids', [])))
        if not gold or gold - corpus_ids:
            raise ValueError(f"{q['id']}: invalid gold IDs: {sorted(gold - corpus_ids)}")
        result.append((q['id'], q['question'], gold))
    if not result:
        raise ValueError('No verified answerable questions')
    return result


def metrics(ids, gold):
    matches = gold.intersection(ids)
    first = next((i for i, cid in enumerate(ids, 1) if cid in gold), None)
    return (int(bool(matches)), len(matches) / len(gold), 1 / first if first else 0.)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depth', type=int, default=50, help='Top K from EACH BM25 and semantic ranking')
    parser.add_argument('--hybrid-depth', type=int, default=100, help='Hybrid candidate comparison pool')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--model', default='cross-encoder/ms-marco-MiniLM-L-6-v2')
    parser.add_argument('--confirm-page12-covered', action='store_true')
    args = parser.parse_args()
    if not args.confirm_page12_covered:
        parser.error('Confirm page-12 replacement coverage using --confirm-page12-covered')
    if min(args.depth, args.hybrid_depth, args.top_k, args.batch_size) < 1:
        parser.error('All depth, top-k and batch-size values must be positive')

    original = load_chunks(ROOT / 'data/processed/cbi_upi_rfp_chunks.jsonl')
    replacements = load_verified_rows(ROOT / 'evaluation/cbi_eligibility_page12_review.json')
    corpus, removed = build_replacement_corpus(original, replacements, True)
    id_to_chunk = {c['chunk_id']: c for c in corpus}
    questions = load_questions(set(id_to_chunk))
    retriever = BidLensRetriever(corpus)

    # Import only after input validation, so errors about files/labels are cheap.
    from sentence_transformers import CrossEncoder
    print(f'Corpus: {len(original)} - {len(removed)} + {len(replacements)} = {len(corpus)}', flush=True)
    print(f'Questions: {len(questions)} | model: {args.model}', flush=True)
    print('Union = BM25 top depth + semantic top depth (deduplicated).', flush=True)
    print('Hybrid comparison = hybrid top hybrid-depth.', flush=True)
    print('All results use original question wording and exact gold IDs.', flush=True)
    t0 = time.perf_counter()
    reranker = CrossEncoder(args.model)
    print(f'Cross-encoder loaded in {time.perf_counter()-t0:.1f}s', flush=True)

    methods = ('hybrid_baseline', 'union_reranked', 'hybrid_reranked')
    sums = {m: [0., 0., 0., 0., 0.] for m in methods}  # hit, recall, MRR, seconds, candidate count
    for qid, question, gold in questions:
        bm25 = retriever.search(question, 'bm25', min(args.depth, len(corpus)))
        semantic = retriever.search(question, 'semantic', min(args.depth, len(corpus)))
        hybrid = retriever.search(question, 'hybrid', min(args.hybrid_depth, len(corpus)))
        union_ids = list(dict.fromkeys([r['chunk_id'] for r in bm25 + semantic]))
        hybrid_ids = [r['chunk_id'] for r in hybrid]
        pools = {'union_reranked': union_ids, 'hybrid_reranked': hybrid_ids}
        outputs = {'hybrid_baseline': hybrid_ids[:args.top_k]}
        elapsed = {'hybrid_baseline': 0.}
        for method, ids in pools.items():
            pairs = [(question, id_to_chunk[cid]['text']) for cid in ids]
            start = time.perf_counter()
            scores = reranker.predict(pairs, batch_size=args.batch_size, show_progress_bar=False)
            elapsed[method] = time.perf_counter() - start
            ordered = sorted(range(len(ids)), key=lambda i: (-float(scores[i]), i))
            outputs[method] = [ids[i] for i in ordered[:args.top_k]]
        print(f'\n{qid} gold={len(gold)}')
        for method in methods:
            ids = outputs[method]
            hit, recall, rr = metrics(ids, gold)
            size = len(pools[method]) if method in pools else len(hybrid_ids)
            totals = sums[method]
            for i, value in enumerate((hit, recall, rr, elapsed[method], size)):
                totals[i] += value
            print(f'  {method:18} hit={hit} recall={recall:.3f} rr={rr:.3f} pool={size} '
                  f'rerank_s={elapsed[method]:.2f} ids={ids}', flush=True)
    print('\n=== SUMMARY: TOP-' + str(args.top_k) + ' ===')
    n = len(questions)
    for method in methods:
        h, r, m, seconds, size = (x / n for x in sums[method])
        print(f'{method:18} hit={h:.3f} recall={r:.3f} mrr={m:.3f} '
              f'avg_pool={size:.1f} avg_rerank_s={seconds:.2f}', flush=True)
    print('NOTE: baseline timing excludes candidate retrieval; rerank_s excludes embedding and BM25 search.')
    print('NOTE: top-5 recall may be capped for questions with >5 gold records.')


if __name__ == '__main__':
    main()
