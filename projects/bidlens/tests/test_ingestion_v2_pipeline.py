"""Regression checks for the integrated V2 evidence output (no PDF required)."""
import json
from pathlib import Path


def test_integrated_v2_dataset():
    path = Path('data/processed/cbi_upi_rfp_v2.jsonl')
    if not path.exists():
        import pytest
        pytest.skip('Run scripts/ingest_rfp_v2.py first')
    records = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
    assert len(records) == 1170
    assert len({r['chunk_id'] for r in records}) == len(records)
    eligibility = [r for r in records if r['kind'] == 'eligibility']
    assert len(eligibility) == 12
    sixth = next(r for r in eligibility if r['chunk_id'].endswith('elig006'))
    assert '1 Crore transactions' in sixth['source_text']
    assert 'Credential letter' in sixth['source_text']
    assert any(r['page'] == 13 and 'corporate restructuring' in r['text'] for r in records)
    assert sum(r.get('v2_2_status') == 'recovered' for r in records) == 5
    assert sum(r.get('searchable', True) for r in records) == 1154
