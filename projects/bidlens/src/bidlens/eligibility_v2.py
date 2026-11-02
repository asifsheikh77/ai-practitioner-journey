"""Reviewed, table-aware eligibility records. Never auto-verify extracted text."""
import json
from pathlib import Path

DOC = 'cbi_upi_rfp'


def load_reviewed_records(path, original_chunks):
    """Validate reviewed rows and create retrieval-compatible records.

    Only rows explicitly marked verified are indexed. Source IDs are used for
    evaluation equivalence, not to assert an exact byte-level text alignment.
    """
    chunks = {c['chunk_id']: c for c in original_chunks}
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError('Review file must contain a JSON list')
    seen = set()
    records = []
    for row in data:
        n = row['criterion_number']
        if not isinstance(n, int) or n not in range(1, 8) or n in seen:
            raise ValueError(f'Invalid/duplicate criterion: {n}')
        seen.add(n)
        if row.get('review_status') != 'verified':
            continue
        requirement = row.get('requirement', '').strip()
        documentation = row.get('supporting_documentation', '').strip()
        ids = row.get('source_chunk_ids', [])
        if not requirement or not ids:
            raise ValueError(f'Criterion {n}: verified record needs requirement and source IDs')
        if row.get('document_id') != DOC or row.get('page_number') != 12:
            raise ValueError(f'Criterion {n}: wrong document/page')
        for cid in ids:
            if cid not in chunks or chunks[cid]['page_number'] != 12:
                raise ValueError(f'Criterion {n}: invalid source chunk {cid}')
        rid = f'{DOC}:p0012:req{n:03d}'
        records.append({
            'chunk_id': rid,
            'document_id': DOC,
            'page_number': 12,
            'record_type': 'eligibility_requirement',
            'criterion_number': n,
            'section': 'Eligibility Criteria',
            'text': requirement,  # do not contaminate search text with documentation column
            'requirement': requirement,
            'supporting_documentation': documentation,
            'source_chunk_ids': ids,
            'review_status': 'verified',
        })
    return records


def make_experimental_corpus(original_chunks, records):
    """Keep baseline chunks intact; add reviewed records as a second index view."""
    existing = {c['chunk_id'] for c in original_chunks}
    if any(r['chunk_id'] in existing for r in records):
        raise ValueError('Duplicate record ID in baseline')
    return list(original_chunks) + records


def equivalence_ids(result_id, records_by_id):
    """Map structured record hits to precisely reviewed original evidence IDs."""
    row = records_by_id.get(result_id)
    return set(row['source_chunk_ids']) if row else {result_id}


def score_results(result_ids, gold_ids, records_by_id):
    """Gold chunk coverage and first relevant rank with source equivalence."""
    gold = set(gold_ids)
    if not gold:
        raise ValueError('Cannot score empty gold set')
    covered = set()
    first = None
    for rank, rid in enumerate(result_ids, start=1):
        matched = equivalence_ids(rid, records_by_id) & gold
        if matched and first is None:
            first = rank
        covered.update(matched)
    return {'recall': len(covered) / len(gold),
            'hit': int(bool(covered)),
            'rr': 1 / first if first else 0.0,
            'matched_gold_ids': sorted(covered)}
