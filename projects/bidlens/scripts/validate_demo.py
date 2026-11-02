"""Validate demo output provenance and structural safeguards; no model dependencies."""
import argparse
import json
from pathlib import Path


def validate(report, chunks):
    index = {c['chunk_id']: c for c in chunks if c.get('searchable') is True}
    issues = []
    sections = report.get('sections', [])
    if not sections:
        issues.append('No report sections')
    for section in sections:
        topic = section.get('topic', '<missing>')
        if not str(section.get('vendor_compliance', '')).startswith('UNKNOWN'):
            issues.append(f'{topic}: vendor compliance must be UNKNOWN without vendor evidence')
        for evidence in section.get('evidence', []):
            cid = evidence.get('chunk_id')
            source = index.get(cid)
            if source is None:
                issues.append(f'{topic}: unknown or nonsearchable chunk {cid}')
                continue
            if evidence.get('page_number') != source['page_number']:
                issues.append(f'{topic}: page mismatch {cid}')
            if evidence.get('text') != source['text']:
                issues.append(f'{topic}: text mismatch {cid}')
    if report.get('decision', '').startswith('NOT ASSESSED') is False:
        issues.append('Decision must be NOT ASSESSED')
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, default=Path('demo_output/assessment.json'))
    parser.add_argument('--chunks', type=Path, default=Path('data/processed/cbi_upi_rfp_v2.jsonl'))
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding='utf-8'))
    chunks = [json.loads(line) for line in args.chunks.read_text(encoding='utf-8').splitlines() if line.strip()]
    issues = validate(report, chunks)
    print(f'Checked {len(report.get("sections", []))} sections, {sum(len(s.get("evidence", [])) for s in report.get("sections", []))} citations')
    if issues:
        print('FAIL:')
        for issue in issues:
            print(' -', issue)
        raise SystemExit(1)
    print('PASS: structural citation provenance and abstention checks')
    print('NOTE: This does not verify semantic relevance, completeness, or PDF extraction accuracy.')


if __name__ == '__main__':
    main()
