"""Conservative cleanup of BidLens V2.1 records.

No content is discarded. Repairs misidentified table headers, classifies
non-evidence rows, and flags ambiguous layout for manual review.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

NUMBER = re.compile(r'^\d{1,3}\.?$')
COLUMN_LABELS = {'s. no.', 'sr. no.', 'sn', '#', 'requirements', 'requirement', 'functional specification description', 'eligibility of the bidder', 'documents to be submitted'}


def clean(v):
    return re.sub(r'\s+', ' ', str(v or '')).strip()


def likely_data_header(headers):
    if not headers:
        return False
    first = clean(headers[0]); second = clean(headers[1]) if len(headers)>1 else ''
    if NUMBER.fullmatch(first):
        return True
    # Page-continuation tables start with a letter/number and a substantive requirement.
    if re.fullmatch(r'[A-Z]', first) and len(second)>35 and not any(clean(h).lower() in COLUMN_LABELS for h in headers):
        return True
    return False


def classify(r):
    cells=[clean(c) for c in r.get('cells',[])]
    headers=[clean(h) for h in r.get('headers',[])]
    joined=' '.join(cells).lower()
    if cells and (sum(bool(c) for c in cells)==0):
        return 'empty_row'
    if 'year1' in joined and 'year2' in joined and sum(bool(c) for c in cells)>=4:
        return 'column_header_continuation'
    if r['page'] in (126,127,128) and ('(y/n)' in joined or ('eligibility of the bidder' in joined and 'documents to be submitted' in joined)):
        return 'column_header_continuation'
    if len(cells)>1 and len(cells[1])<80 and clean(cells[0]) in ('A','B','C','D','E','F') and not any(clean(c) for c in cells[2:]):
        return 'section_heading'
    return 'evidence_candidate'


def cleanup(records):
    findings=[]; count=Counter(); output=[]
    for original in records:
        r=dict(original)
        r['v2_2_status']='preserved'
        if r['kind'] not in ('table_row','eligibility'):
            output.append(r); continue
        cells=[clean(c) for c in r.get('cells',[])]
        headers=[clean(h) for h in r.get('headers',[])]
        flags=[]
        if r['kind']=='eligibility':
            r['record_role']='eligibility_requirement'; output.append(r); continue
        role=classify(r)
        r['record_role']=role
        if role!='evidence_candidate':
            flags.append(role)
        if likely_data_header(headers):
            # Do not present a previous requirement as a field name.
            # Preserve raw headers and original source text for inspection.
            r['original_headers']=headers
            headers=['Item', 'Requirement'] + [f'Field {i+1}' for i in range(2,len(headers))]
            flags.append('data_row_misidentified_as_header')
        if any(not h for h in headers):
            flags.append('blank_or_merged_header')
        if len(headers)>8:
            flags.append('wide_table_needs_hierarchy_review')
        if sum(bool(c) for c in cells)==1:
            flags.append('single_cell_row_review')
        if r['page'] in range(108,120) and r.get('row_index')==1 and likely_data_header(r.get('original_headers',r.get('headers',[]))):
            flags.append('first_data_row_missing_from_extraction')
        r['effective_headers']=headers
        # Label only populated fields, never use previous row text as a header.
        r['text']=' | '.join(f'{headers[i] if i<len(headers) else f"Field {i+1}"}: {c}' for i,c in enumerate(cells) if c)
        r['quality_flags']=sorted(set(flags))
        r['searchable']=role=='evidence_candidate'
        if flags:
            r['v2_2_status']='review_required'
            for flag in sorted(set(flags)):
                findings.append({'id':r['chunk_id'],'page':r['page'],'type':flag,'severity':'high' if flag in ('data_row_misidentified_as_header','first_data_row_missing_from_extraction') else 'medium'})
                count[flag]+=1
        output.append(r)
    return output, {'record_count':len(output),'by_kind':dict(Counter(r['kind'] for r in output)), 'record_roles':dict(Counter(r.get('record_role','narrative') for r in output)), 'findings_count':len(findings),'findings_by_type':dict(count),'findings':findings}


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    records=[json.loads(line) for line in Path(a.input).read_text(encoding='utf-8').splitlines() if line.strip()]
    out, report=cleanup(records)
    assert len(out)==len(records)
    assert len(set(r['chunk_id'] for r in out))==len(out)
    assert len([r for r in out if r['kind']=='eligibility'])==12
    assert all(r['source_text']==s['source_text'] for r,s in zip(out,records))
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    with Path(a.output).open('w',encoding='utf-8') as f:
        for r in out:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    Path(a.report).parent.mkdir(parents=True,exist_ok=True)
    Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='findings'},indent=2))
if __name__=='__main__':main()
