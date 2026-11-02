"""Deterministic quality audit for BidLens V2 evidence records."""
import argparse, collections, json, re
from pathlib import Path

def audit(records):
    findings=[]; stats=collections.Counter(); bypage=collections.defaultdict(list)
    for r in records:
        stats[r['kind']]+=1; bypage[r['page']].append(r)
        if r['kind']=='table_row':
            row=r.get('cells',[]); header=r.get('headers',[])
            if r.get('row_index')==0:
                findings.append({'severity':'medium','type':'header_as_evidence','id':r['chunk_id']})
            if row and sum(bool(c) for c in row)==1:
                findings.append({'severity':'medium','type':'single_cell_row','id':r['chunk_id'],'text':r['source_text'][:160]})
            if len(header)>8:
                findings.append({'severity':'high','type':'wide_table_row','id':r['chunk_id'],'columns':len(header)})
            if any(not x for x in header):
                findings.append({'severity':'medium','type':'blank_header','id':r['chunk_id']})
        if r['kind']=='narrative':
            t=r['text']
            if re.search(r'RFP for UPI Solution - Tender No\.',t):
                findings.append({'severity':'low','type':'repeated_page_header','id':r['chunk_id']})
            if re.search(r'Page \d+ of 147',t):
                findings.append({'severity':'low','type':'page_footer','id':r['chunk_id']})
    eligibility=[r for r in records if r['kind']=='eligibility']
    nums=sorted(int(re.search(r'elig(\d+)$',r['chunk_id']).group(1)) for r in eligibility)
    checks={
      'all_12_eligibility':nums==list(range(1,13)),
      'criterion6_exact_threshold':any('1 Crore transactions' in r['source_text'] and 'two Scheduled Commercial Banks' in r['source_text'] for r in eligibility),
      'criterion6_evidence':any('Credential letter along with Proof of transaction' in r['source_text'] for r in eligibility),
      'page13_post_table_narrative':any(r['kind']=='narrative' and 'corporate restructuring' in r['text'] for r in bypage[13]),
      'page14_scb_exclusion':any('Scheduled Commercial Bank does not include Payments Bank' in r['text'] for r in bypage[14]),
      'page21_projection_table':any(r['kind']=='table_row' and 'Sep-24' in r['text'] and '475' in r['text'] for r in bypage[21]),
      'unique_ids':len(records)==len({r['chunk_id'] for r in records}),
    }
    return {'records':len(records),'by_kind':dict(stats),'checks':checks,'findings_count':len(findings),'findings_by_type':dict(collections.Counter(x['type'] for x in findings)),'findings':findings}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    records=[json.loads(s) for s in Path(a.input).read_text(encoding='utf-8').splitlines() if s.strip()]
    result=audit(records);Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='findings'},indent=2))
    if not all(result['checks'].values()):raise SystemExit(1)
if __name__=='__main__':main()
