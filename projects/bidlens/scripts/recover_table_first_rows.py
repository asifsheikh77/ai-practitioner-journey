"""Recover table row 0 when PyMuPDF mistook an actual data row for headers."""
import argparse,json
from collections import Counter
from pathlib import Path
import fitz
from cleanup_ingestion_v2_2 import likely_data_header,clean

def recover(records,pdf):
    groups={}
    for r in records:
        if r['kind']=='table_row' and 'data_row_misidentified_as_header' in r.get('quality_flags',[]):
            groups[(r['page'],r['table_index'])]=r
    additions=[]
    with fitz.open(pdf) as doc:
        for (page,ti), sample in sorted(groups.items()):
            table=doc[page-1].find_tables().tables[ti-1]
            row=[clean(c) for c in table.extract()[0]]
            if not likely_data_header(row):continue
            rid=f"{sample['document_id']}:p{page:04d}:t{ti:02d}:r000"
            assert not any(r['chunk_id']==rid for r in records)
            bbox=[round(v,2) for v in table.rows[0].bbox]
            additions.append({'chunk_id':rid,'document_id':sample['document_id'],'page':page,'kind':'table_row',
               'table_index':ti,'row_index':0,'headers':row,'original_headers':row,
               'effective_headers':sample['effective_headers'],'cells':row,
               'text':' | '.join(f'{sample["effective_headers"][i]}: {v}' for i,v in enumerate(row) if v),
               'source_text':' | '.join(row),'bbox':bbox,'table_bbox':sample['table_bbox'],
               'record_role':'evidence_candidate','searchable':True,'v2_2_status':'recovered',
               'quality_flags':['recovered_first_data_row','continuation_table_header_uncertain']})
    return records+additions, additions

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--pdf',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    original=[json.loads(x) for x in Path(a.input).read_text(encoding='utf8').splitlines() if x.strip()]
    result,add=recover(original,a.pdf)
    with open(a.output,'w',encoding='utf8') as f:
        for r in result:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    Path(a.report).write_text(json.dumps({'recovered_rows':len(add),'pages':dict(Counter(str(x['page']) for x in add)),'recovered_ids':[x['chunk_id'] for x in add]},indent=2))
    print('Recovered',len(add),'first data rows; total records',len(result))
if __name__=='__main__':main()
