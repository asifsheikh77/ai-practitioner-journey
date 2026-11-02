"""BidLens Day 3.6: hybrid baseline, cross-encoder rerank, and page-local context expansion.
Provisional facet evidence hits only; labels are NOT exhaustive gold.
"""
import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

TOKEN_RE = re.compile(r'[a-z0-9]+')
def count_tokens(s):
    return len(TOKEN_RE.findall(s.lower()))

def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def page_of(record):
    return record.get('page_number', record.get('page'))

def neighbors_for(records):
    """Conservative adjacency: narrative neighbors on same page, or rows in same table."""
    groups = defaultdict(list)
    for i, r in enumerate(records):
        kind = r.get('kind', 'narrative')
        if kind == 'eligibility':
            continue
        if kind == 'table_row':
            group = (page_of(r), 'table', r.get('table_index'))
        elif kind == 'narrative':
            group = (page_of(r), 'narrative')
        else:
            continue
        groups[group].append(i)
    adj = defaultdict(list)
    for members in groups.values():
        for j, idx in enumerate(members):
            if j: adj[idx].append(members[j-1])
            if j+1 < len(members): adj[idx].append(members[j+1])
    return adj

def build_context(ranking, records, adjacency, budget, expand=False):
    """Whole-record prefix, then optional neighboring records; no cross-page stitching.
    All selected records count toward budget. Stop on first oversized anchor.
    """
    by_id = {r['chunk_id']: i for i, r in enumerate(records)}
    chosen = []
    seen = set()
    used = 0
    for result in ranking:
        i = by_id[result['chunk_id']]
        if i in seen: continue
        n = count_tokens(records[i]['text'])
        if used + n > budget: break
        seen.add(i); chosen.append(i); used += n
        if expand:
            for ni in adjacency.get(i, []):
                if ni in seen: continue
                extra = count_tokens(records[ni]['text'])
                if used + extra <= budget:
                    seen.add(ni); chosen.append(ni); used += extra
    return [records[i]['chunk_id'] for i in chosen], used

def metrics(rubric, rankings, records, budgets=(1000, 2000, 4000), expand=False):
    adjacency = neighbors_for(records)
    facet_total = sum(len(q['facets']) for q in rubric)
    output = {}
    for budget in budgets:
        hits = complete = 0
        total_used = 0
        question_results = {}
        for q in rubric:
            selected, used = build_context(rankings[q['id']], records, adjacency, budget, expand)
            total_used += used
            ids = set(selected)
            facets = {f['facet_id']: bool(ids.intersection(f['v2_evidence_ids'])) for f in q['facets']}
            hits += sum(facets.values())
            complete += all(facets.values())
            question_results[q['id']] = {'facet_hits': facets, 'retrieved_ids': selected, 'tokens': used}
        output[str(budget)] = {
            'facet_hit_rate': hits/facet_total,
            'complete_question_rate': complete/len(rubric),
            'facet_hits': hits, 'total_facets': facet_total,
            'complete_questions': complete,
            'mean_tokens_used': round(total_used/len(rubric),1),
            'questions': question_results,
        }
    return output

def run(args):
    root = Path(args.root).resolve()
    sys.path.insert(0, str(root/'src'))
    from bidlens.retrieval import BidLensRetriever
    from sentence_transformers import CrossEncoder
    rubric = json.loads(Path(args.rubric).read_text(encoding='utf-8'))
    records = [r for r in load_jsonl(root/'data/processed/cbi_upi_rfp_v2.jsonl') if r.get('searchable', True)]
    for r in records:
        r.setdefault('page_number', page_of(r))
    known = {r['chunk_id'] for r in records}
    missing = [(f['facet_id'], eid) for q in rubric for f in q['facets'] for eid in f['v2_evidence_ids'] if eid not in known]
    if missing: raise ValueError(f'Missing evidence IDs: {missing[:10]}')
    retriever = BidLensRetriever(records, model_name=args.embedding_model)
    cross = CrossEncoder(args.reranker_model, max_length=512)
    rankings = {'hybrid': {}, 'reranked': {}}
    latency = {'hybrid': [], 'reranked': []}
    for q in rubric:
        query = q['question']
        t0 = time.perf_counter()
        candidates = retriever.search(query, method='hybrid', top_k=min(args.candidates,len(records)))
        latency['hybrid'].append(time.perf_counter()-t0)
        rankings['hybrid'][q['id']] = candidates
        t1 = time.perf_counter()
        scores = cross.predict([(query, r['text']) for r in candidates], batch_size=args.batch_size, show_progress_bar=False)
        reranked = [r for _, r in sorted(zip(scores, candidates), key=lambda pair: -float(pair[0]))]
        latency['reranked'].append(time.perf_counter()-t1)
        rankings['reranked'][q['id']] = reranked
        print(f"{q['id']} candidates={len(candidates)} hybrid={latency['hybrid'][-1]:.2f}s rerank={latency['reranked'][-1]:.2f}s", flush=True)
    configurations = {
        'hybrid': metrics(rubric, rankings['hybrid'], records),
        'hybrid_parent': metrics(rubric, rankings['hybrid'], records, expand=True),
        'reranked': metrics(rubric, rankings['reranked'], records),
        'reranked_parent': metrics(rubric, rankings['reranked'], records, expand=True),
    }
    out = {
        'warning': 'PROVISIONAL mapped-support hit rates; NOT certified Recall@k or MRR. Expansion is same-page heuristic, not semantic parent sections.',
        'corpus': 'v2', 'records': len(records), 'questions': len(rubric),
        'candidates': args.candidates, 'embedding_model': args.embedding_model,
        'reranker_model': args.reranker_model,
        'mean_query_seconds': {k: round(sum(v)/len(v),3) for k,v in latency.items()},
        'configurations': configurations,
        'rankings': {method: {qid: [r['chunk_id'] for r in ranking] for qid, ranking in rr.items()} for method, rr in rankings.items()}
    }
    path = Path(args.output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('\nSUMMARY')
    for name, values in configurations.items():
        print(name, ' '.join(f"{b}: {values[str(b)]['facet_hit_rate']:.1%}" for b in (1000,2000,4000)))
    print('Saved', path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='.')
    p.add_argument('--rubric', default='evaluation/rubric_42_narrow_assertions.json')
    p.add_argument('--output', default='evaluation/results/day36_retrieval_experiment.json')
    p.add_argument('--embedding-model', default='sentence-transformers/all-MiniLM-L6-v2')
    p.add_argument('--reranker-model', default='cross-encoder/ms-marco-MiniLM-L-6-v2')
    p.add_argument('--candidates', type=int, default=50)
    p.add_argument('--batch-size', type=int, default=16)
    args = p.parse_args()
    if args.candidates < 1: p.error('--candidates must be positive')
    run(args)
if __name__ == '__main__': main()
