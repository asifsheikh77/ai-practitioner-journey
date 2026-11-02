"""Paired semantic/hybrid mapped-support diagnostic (NOT certified gold recall).
Run from BidLens project root. Requires installed project dependencies and local model download/cache.
"""
import argparse, json, sys, time, re
from pathlib import Path
import numpy as np

def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def tokens(text): return re.findall(r'[a-z0-9]+', text.lower())

def summarize(rubric, rankings, corpus, budgets=(1000,2000,4000), ks=(5,10,20,50)):
    facets=sum(len(q['facets']) for q in rubric)
    result={}
    for k in ks:
        hit=complete=0
        for q in rubric:
            results = rankings[q["id"]][:k]

            ids = {
                result["chunk_id"] if isinstance(result, dict) else result
                for result in results
            }

            hits = [
                bool(ids.intersection(f[f"{corpus}_evidence_ids"]))
                for f in q["facets"]
            ]
            hit+=sum(hits);complete+=all(hits)
        result[f'top_{k}']={'facet_hit_rate':hit/facets,'complete_question_rate':complete/len(rubric)}
    for budget in budgets:
        hit=complete=0
        for q in rubric:
            selected=[];used=0
            for r in rankings[q['id']]:
                n=len(tokens(r['text']))
                if used+n>budget: break  # whole-record prefix; no truncation
                used+=n;selected.append(r['chunk_id'])
            ids=set(selected); hits=[bool(ids.intersection(f[f'{corpus}_evidence_ids'])) for f in q['facets']]
            hit+=sum(hits);complete+=all(hits)
        result[f'tokens_{budget}']={'facet_hit_rate':hit/facets,'complete_question_rate':complete/len(rubric)}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='.')
    p.add_argument('--rubric',required=True)
    p.add_argument('--output',default='evaluation/results/paired_semantic_hybrid_diagnostic.json')
    p.add_argument('--model',default='sentence-transformers/all-MiniLM-L6-v2')
    a=p.parse_args();root=Path(a.root).resolve();sys.path.insert(0,str(root/'src'))
    from bidlens.retrieval import BidLensRetriever
    rubric=json.loads(Path(a.rubric).read_text(encoding='utf-8'))
    corpora={'v1':'cbi_upi_rfp_chunks.jsonl','v2':'cbi_upi_rfp_v2.jsonl'}
    output={'warning':'PROVISIONAL mapped-support hit rates; NOT certified Recall@k or MRR.', 'model':a.model,'methods':{},'corpora':{}}
    for corpus,filename in corpora.items():
        records=[r for r in load_jsonl(root/'data'/'processed'/filename) if r.get('searchable',True)]
        for r in records:
            r.setdefault('page_number',r.get('page'))
        ids={r['chunk_id'] for r in records}
        missing=[(f['facet_id'],eid) for q in rubric for f in q['facets'] for eid in f[f'{corpus}_evidence_ids'] if eid not in ids]
        if missing: raise ValueError(f'{corpus}: missing evidence IDs {missing[:8]}')
        retriever=BidLensRetriever(records,model_name=a.model)
        output['corpora'][corpus]={'searchable_records':len(records)}
        for method in ('semantic','hybrid'):
            start=time.perf_counter()
            rankings={q['id']:retriever.search(q['question'],method=method,top_k=len(records)) for q in rubric}
            elapsed=time.perf_counter()-start
            metrics=summarize(rubric,rankings,corpus)
            output['methods'].setdefault(method,{})[corpus]={'metrics':metrics,'elapsed_seconds':round(elapsed,2)}
            path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
            (path.parent/f'{corpus}_{method}_rankings.json').write_text(json.dumps({q:[r['chunk_id'] for r in rows] for q,rows in rankings.items()},indent=2),encoding='utf-8')
            print(corpus,method,json.dumps(metrics))
    Path(a.output).write_text(json.dumps(output,indent=2),encoding='utf-8')
    print('Wrote',a.output)

if __name__=='__main__': main()
