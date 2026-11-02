import json
import pytest
from bidlens.eligibility_v2 import load_reviewed_records, score_results

CHUNKS = [{'chunk_id': 'cbi_upi_rfp:p0012:c002', 'page_number': 12, 'document_id': 'cbi_upi_rfp', 'text': 'raw'}]


def test_pending_not_indexed(tmp_path):
    f = tmp_path / 'rows.json'
    f.write_text(json.dumps([{'criterion_number': 6, 'review_status': 'pending'}]), encoding='utf-8')
    assert load_reviewed_records(f, CHUNKS) == []


def test_verified_record_and_equivalence(tmp_path):
    f = tmp_path / 'rows.json'
    f.write_text(json.dumps([{'criterion_number': 6, 'document_id': 'cbi_upi_rfp',
                              'page_number': 12, 'review_status': 'verified',
                              'requirement': 'Two banks', 'supporting_documentation': 'Credential letter',
                              'source_chunk_ids': ['cbi_upi_rfp:p0012:c002']}]), encoding='utf-8')
    records = load_reviewed_records(f, CHUNKS)
    assert records[0]['text'] == 'Two banks'
    assert 'Credential' not in records[0]['text']
    scored = score_results([records[0]['chunk_id']], ['cbi_upi_rfp:p0012:c002'], {records[0]['chunk_id']: records[0]})
    assert scored['recall'] == scored['rr'] == 1


def test_bad_source_rejected(tmp_path):
    f = tmp_path / 'rows.json'
    f.write_text(json.dumps([{'criterion_number': 6, 'document_id': 'cbi_upi_rfp',
                              'page_number': 12, 'review_status': 'verified',
                              'requirement': 'Two banks', 'source_chunk_ids': ['missing']}]), encoding='utf-8')
    with pytest.raises(ValueError):
        load_reviewed_records(f, CHUNKS)
