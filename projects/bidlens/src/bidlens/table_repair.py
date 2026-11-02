"""Controlled page-replacement experiment. Does not change original chunks."""
import json
from pathlib import Path

DOC = 'cbi_upi_rfp'
PAGE = 12


def load_verified_rows(path):
    rows = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(rows, list):
        raise ValueError('Review JSON must be an array')
    if {r.get('criterion_number') for r in rows} != set(range(1, 8)):
        raise ValueError('Expected exactly seven numbered criteria (1..7)')
    result = []
    for row in rows:
        n = row['criterion_number']
        if row.get('review_status') != 'verified':
            raise ValueError(f'Criterion {n} not verified against the PDF')
        if row.get('document_id') != DOC or row.get('page_number') != PAGE:
            raise ValueError(f'Criterion {n}: wrong document or page')
        req = row.get('requirement', '').strip()
        if not req:
            raise ValueError(f'Criterion {n}: empty requirement')
        result.append({'chunk_id': f'{DOC}:p0012:req{n:03d}', 'document_id': DOC,
                       'page_number': PAGE, 'record_type': 'eligibility_requirement',
                       'criterion_number': n, 'text': req,
                       'supporting_documentation': row.get('supporting_documentation', '').strip(),
                       'review_status': 'verified'})
    return result


def build_replacement_corpus(original, replacement, page12_fully_covered=False):
    """Fail closed: never silently discard non-table material on page 12."""
    if not page12_fully_covered:
        raise ValueError('Explicit page-12 full-coverage confirmation required')
    page = [c for c in original if c['document_id'] == DOC and c['page_number'] == PAGE]
    if not page:
        raise ValueError('No original page-12 chunks found')
    if len(replacement) != 7:
        raise ValueError('Need all seven verified replacement records')
    kept = [c for c in original if not (c['document_id'] == DOC and c['page_number'] == PAGE)]
    ids = [c['chunk_id'] for c in kept + replacement]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate chunk IDs')
    return kept + replacement, page


def score_ids(results, gold):
    gold = set(gold)
    if not gold:
        raise ValueError('Missing criterion-level gold IDs')
    retrieved = [r['chunk_id'] for r in results]
    hits = gold.intersection(retrieved)
    rank = next((i for i, cid in enumerate(retrieved, 1) if cid in gold), None)
    return {'recall': len(hits) / len(gold), 'hit': int(bool(hits)),
            'rr': 1 / rank if rank else 0.0}
