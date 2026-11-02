"""Reproducible BidLens V2 pipeline: PDF -> extraction -> conservative repair -> enrichment.

V1 is never modified. Ambiguous cross-page fragments remain flagged for review.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from ingest_structured_v2_1 import extract
from cleanup_ingestion_v2_2 import cleanup
from recover_table_first_rows import recover
from enrich_ingestion_v2_3 import enrich


def run(pdf: Path, document_id: str = 'cbi_upi_rfp') -> tuple[list[dict], dict]:
    raw, extraction_issues, pages = extract(str(pdf), document_id)
    cleaned, cleanup_report = cleanup(raw)
    repaired, recovered = recover(cleaned, str(pdf))
    enriched, enrichment_report = enrich(repaired)
    for r in enriched:
        r.setdefault('page_number', r['page'])
        r.setdefault('searchable', True)
        r.setdefault('character_count', len(r['text']))
    ids = [r['chunk_id'] for r in enriched]
    eligibility = [r for r in enriched if r['kind'] == 'eligibility']
    checks = {
        'unique_ids': len(ids) == len(set(ids)),
        'eligibility_1_to_12': sorted(int(r['chunk_id'].split('elig')[-1]) for r in eligibility) == list(range(1, 13)),
        'criterion_6_transaction_threshold': any('1 Crore transactions' in r['source_text'] for r in eligibility if r['chunk_id'].endswith('elig006')),
        'criterion_6_supporting_document': any('Credential letter' in r['source_text'] for r in eligibility if r['chunk_id'].endswith('elig006')),
        'page_13_narrative': any(r['page'] == 13 and 'corporate restructuring' in r['text'] for r in enriched),
        'source_text_unchanged': all(a['source_text'] == b['source_text'] for a, b in zip(repaired, enriched)),
        'no_v1_ids': not any(':c' in r['chunk_id'].split(':')[-1] for r in enriched),
    }
    report = {
        'document_id': document_id, 'pages': len(pages),
        'detected_tables': sum(p['tables'] for p in pages),
        'raw_records': len(raw), 'output_records': len(enriched),
        'by_kind': dict(Counter(r['kind'] for r in enriched)),
        'searchable_records': sum(r['searchable'] for r in enriched),
        'recovered_first_rows': len(recovered),
        'checks': checks,
        'extraction_issues': extraction_issues,
        'cleanup_report': cleanup_report,
        'enrichment_report': enrichment_report,
        'limitations': [
            'Multi-page continuation candidates are flagged, not joined.',
            'Multi-level merged table headings remain uncertain.',
            'Source-text coverage has not been exhaustively verified.',
            'Original V1 benchmark gold chunk IDs do not apply to V2.',
        ],
    }
    if not all(checks.values()):
        raise AssertionError(f'Ingestion acceptance checks failed: {checks}')
    return enriched, report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pdf', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('data/processed/cbi_upi_rfp_v2.jsonl'))
    p.add_argument('--report', type=Path, default=Path('evaluation/results/ingestion_v2_report.json'))
    p.add_argument('--document-id', default='cbi_upi_rfp')
    a = p.parse_args()
    records, report = run(a.pdf, a.document_id)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('extraction_issues', 'cleanup_report', 'enrichment_report')}, indent=2))


if __name__ == '__main__':
    main()
