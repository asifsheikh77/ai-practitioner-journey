"""BidLens ingestion V2: layout-aware, auditable PDF evidence extraction.

Requires PyMuPDF >= 1.23. Run independently of the V1 pipeline.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
import fitz


def clean(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def overlap(a, b):
    x0=max(a[0],b[0]); y0=max(a[1],b[1]); x1=min(a[2],b[2]); y1=min(a[3],b[3])
    return max(0,x1-x0)*max(0,y1-y0)


def outside_lines(page, boxes):
    # Exclude individual words inside tables, not entire text blocks that may overlap.
    words = page.get_text('words', sort=True)
    lines = {}
    for w in words:
        bbox=w[:4]
        if any(overlap(bbox, box) / max(1e-6,(bbox[2]-bbox[0])*(bbox[3]-bbox[1])) > .50 for box in boxes):
            continue
        # (block_no,line_no,word_no) from PyMuPDF
        key=(w[5],w[6]); lines.setdefault(key,[]).append(w)
    out=[]
    for _, ws in sorted(lines.items(), key=lambda kv:(min(w[1] for w in kv[1]),min(w[0] for w in kv[1]))):
        ws.sort(key=lambda w:w[7]); txt=clean(' '.join(w[4] for w in ws))
        if txt:
            out.append({'text':txt,'bbox':[round(min(w[0] for w in ws),2),round(min(w[1] for w in ws),2),round(max(w[2] for w in ws),2),round(max(w[3] for w in ws),2)]})
    return out


def is_header(row):
    joined=' '.join(clean(x).lower() for x in row)
    return any(k in joined for k in ('eligibility of the bidder','documents to be submitted','technical specification','functional specification','compliance (y/n)'))


def extract(pdf, doc_id='cbi_upi_rfp'):
    records=[]; issues=[]; pages=[]
    with fitz.open(pdf) as doc:
        for pi,page in enumerate(doc):
            pn=pi+1; tables=list(page.find_tables().tables)
            boxes=[tuple(t.bbox) for t in tables]
            lines=outside_lines(page,boxes)
            # Narrative grouped into bounded paragraphs; retain page and bbox provenance.
            # Keep all non-table text, including section titles and footnotes.
            groups=[]; current=[]; last=None
            for line in lines:
                if last is not None and (line['bbox'][1]-last['bbox'][3] > 15 or sum(len(x['text']) for x in current)>850):
                    groups.append(current); current=[]
                current.append(line); last=line
            if current: groups.append(current)
            for idx,g in enumerate(groups,1):
                txt=clean(' '.join(x['text'] for x in g))
                if not txt: continue
                # Remove repeated page furniture, but keep surrounding narrative.
                txt=re.sub(r'RFP for UPI Solution\s*-\s*Tender No\.\s*GEM/2024/B/5670501', '', txt).strip()
                txt=re.sub(r'Page\s+\d+\s+of\s+147', '', txt).strip()
                if not txt: continue
                records.append({'chunk_id':f'{doc_id}:p{pn:04d}:n{idx:03d}','document_id':doc_id,'page':pn,'kind':'narrative','text':txt,'source_text':txt,'bbox':[min(x['bbox'][0] for x in g),min(x['bbox'][1] for x in g),max(x['bbox'][2] for x in g),max(x['bbox'][3] for x in g)]})
            for ti,t in enumerate(tables,1):
                raw=t.extract(); rows=[[clean(c) for c in r] for r in raw]
                if not rows: issues.append({'page':pn,'table':ti,'issue':'empty_table'}); continue
                header=rows[0]; eligibility=(pn in (12,13) and len(header)==4 and 'Eligibility of the Bidder' in header[1])
                if len(header)>8: issues.append({'page':pn,'table':ti,'issue':'wide_table_manual_review','columns':len(header)})
                if any(any(c is None for c in r) for r in raw): issues.append({'page':pn,'table':ti,'issue':'merged_cells_or_nulls'})
                for ri,row in enumerate(rows):
                    if ri==0: continue  # Header is metadata, never a searchable requirement
                    if eligibility and not re.fullmatch(r'\d+\.',row[0]):
                        issues.append({'page':pn,'table':ti,'row':ri,'issue':'unexpected_eligibility_number'}); continue
                    if not any(row):
                        issues.append({'page':pn,'table':ti,'row':ri,'issue':'empty_row'}); continue
                    if eligibility:
                        number=int(row[0].rstrip('.'))
                        searchable=f'Eligibility Criteria | Criterion {number} | Eligibility of the Bidder: {row[1]} | Documents to be submitted: {row[2]}'
                        record_id=f'{doc_id}:p{pn:04d}:elig{number:03d}'
                        kind='eligibility'
                    else:
                        searchable=' | '.join(f'{header[j] if j<len(header) and header[j] else f"Column {j+1}"}: {v}' for j,v in enumerate(row) if v)
                        record_id=f'{doc_id}:p{pn:04d}:t{ti:02d}:r{ri:03d}'
                        kind='table_row'
                    # Row-level provenance; table bbox retained separately.
                    rb = t.rows[ri].bbox if ri < len(t.rows) else t.bbox
                    records.append({'chunk_id':record_id,'document_id':doc_id,'page':pn,'kind':kind,'table_index':ti,'row_index':ri,'headers':header,'cells':row,'text':searchable,'source_text':' | '.join(row),'bbox':[round(v,2) for v in rb],'table_bbox':[round(v,2) for v in t.bbox]})
            pages.append({'page':pn,'tables':len(tables),'narrative_records':len(groups),'table_rows':sum(max(0,len(t.extract())-(1 if pn in (12,13) else 0)) for t in tables)})
    return records,issues,pages


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pdf',required=True); ap.add_argument('--output',required=True); ap.add_argument('--report',required=True); ap.add_argument('--document-id',default='cbi_upi_rfp'); args=ap.parse_args()
    records,issues,pages=extract(args.pdf,args.document_id)
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:
        for r in records: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    eligibility=[r for r in records if r['kind']=='eligibility']
    numbers=[int(re.search(r'elig(\d+)$',r['chunk_id']).group(1)) for r in eligibility]
    checks={'eligibility_1_through_12':sorted(numbers)==list(range(1,13)),
            'criterion_6_mentions_1_crore':any('1 Crore transactions' in r['text'] for r in eligibility if r['chunk_id'].endswith('elig006')),
            'criterion_6_evidence':any('Credential letter' in r['text'] for r in eligibility if r['chunk_id'].endswith('elig006')),
            'page_13_narrative_preserved':any(r['page']==13 and r['kind']=='narrative' and 'corporate restructuring' in r['text'] for r in records),
            'unique_record_ids':len({r['chunk_id'] for r in records})==len(records)}
    report={'pdf':args.pdf,'page_count':len(pages),'table_count':sum(p['tables'] for p in pages),'records':len(records),'by_kind':dict(Counter(r['kind'] for r in records)),'eligibility_numbers':numbers,'checks':checks,'issues_count':len(issues),'issues_by_type':dict(Counter(x['issue'] for x in issues)),'issues':issues,'pages':pages}
    rp=Path(args.report);rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('issues','pages')},indent=2))
    if not all(checks.values()): raise SystemExit('Acceptance checks failed: inspect report')

if __name__=='__main__':main()
