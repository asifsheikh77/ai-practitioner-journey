"""Non-destructive enrichment of BidLens V2.2 evidence records.

Preserves source_text, IDs and records; adds structured pricing column paths,
normalized spec column labels, and conservative cross-page continuation candidates.
"""
import argparse, json, re
from collections import Counter
from pathlib import Path

SPEC_PAGES = set(range(109,115)) | {116,117}
PRICE_PAGES = set(range(82,87))

def norm(s): return re.sub(r'\s+', ' ', str(s or '')).strip()

def price_columns(headers, cells):
    """Map year subcolumns under their parent; never infer prices or fill blanks."""
    year_start = next((i for i,v in enumerate(cells) if re.fullmatch(r'Year\s*1', norm(v),re.I)),None)
    if year_start is None: return None
    result=[]
    for i,h in enumerate(headers):
        if year_start <= i < year_start+7:
            result.append('Recurring Cost in ₹ / Year '+str(i-year_start+1))
        elif norm(h): result.append(norm(h))
        else: result.append('Unlabeled column '+str(i+1))
    return result

def enrich(records):
    by_page={}
    for r in records: by_page.setdefault(r['page'],[]).append(r)
    out=[]; findings=[]; counters=Counter(); last_spec=None
    for r0 in records:
        r=dict(r0); page=r['page']; kind=r.get('kind'); cells=[norm(x) for x in r.get('cells',[])]; headers=[norm(x) for x in r.get('headers',[])]
        if kind=='table_row' and page in PRICE_PAGES:
            if cells and any(re.fullmatch(r'Year\s*[1-7]',c,re.I) for c in cells):
                paths=price_columns(headers,cells)
                if paths:
                    r['column_paths']=paths; r['record_role']='column_header_continuation'; r['searchable']=False
                    counters['pricing_header_rows']+=1
            else:
                page_rows=by_page[page]
                template=next((x for x in page_rows if x.get('kind')=='table_row' and any(re.fullmatch(r'Year\s*1',norm(v),re.I) for v in x.get('cells',[]))),None)
                paths=price_columns([norm(x) for x in template.get('headers',[])],[norm(x) for x in template.get('cells',[])]) if template else None
                if paths and len(paths)==len(cells):
                    r['column_paths']=paths
                    r['text']=' | '.join(f'{paths[i]}: {v}' for i,v in enumerate(cells) if v)
                    counters['pricing_rows_labeled']+=1
                else:
                    findings.append({'chunk_id':r['chunk_id'],'page':page,'type':'pricing_hierarchy_unresolved'})
        if kind=='table_row' and page in SPEC_PAGES:
            if len(cells)>=2:
                r['column_paths']=['Item','Requirement']+[f'Field {i+1}' for i in range(2,len(cells))]
                if r.get('searchable',True):
                    r['text']=' | '.join(f'{r["column_paths"][i]}: {v}' for i,v in enumerate(cells) if v)
                counters['spec_rows_normalized']+=1
            # An unnumbered row near a page boundary can be a continuation;
            # flag only, never merge without visual verification.
            if cells and not re.fullmatch(r'(?:\d+[.]?|[A-Z])',cells[0]) and any(cells):
                r['continuation_review']='unnumbered_spec_row'; counters['spec_unnumbered_review']+=1
                findings.append({'chunk_id':r['chunk_id'],'page':page,'type':'unnumbered_spec_row'})
        out.append(r)
    # Candidate continuation across page boundaries: a table's first extracted
    # header looks like trailing prose, or is a numbered row instead of a label.
    for p in sorted(SPEC_PAGES):
        first=next((r for r in out if r['page']==p and r.get('kind')=='table_row'),None)
        if not first: continue
        h=[norm(x) for x in first.get('headers',[])]
        if h and ((not h[0] and len(h)>1 and len(h[1])>20) or (re.fullmatch(r'\d+[.]?',h[0]) and len(h)>1 and len(h[1])>20)):
            first['continuation_review']='page_boundary_header_contains_data_or_fragment'
            findings.append({'chunk_id':first['chunk_id'],'page':p,'type':'page_boundary_continuation_review','raw_header':h[:2]})
            counters['page_boundary_review']+=1
    assert len(out)==len(records)
    assert len({r['chunk_id'] for r in out})==len(out)
    assert all(a['source_text']==b['source_text'] for a,b in zip(records,out))
    return out, {'input_records':len(records),'output_records':len(out),'counts':dict(counters),'findings':findings,'limitations':['Cross-page text is flagged, not merged','Pricing header hierarchy inferred only when Year1–Year7 are explicit','No retrieval benchmark executed']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    original=[json.loads(x) for x in Path(a.input).read_text(encoding='utf-8').splitlines() if x.strip()]
    out,report=enrich(original)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    with open(a.output,'w',encoding='utf-8') as f:
        for r in out:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='findings'},indent=2))
if __name__=='__main__':main()
