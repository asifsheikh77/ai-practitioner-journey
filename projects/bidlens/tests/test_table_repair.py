import json
import pytest
from bidlens.table_repair import load_verified_rows, build_replacement_corpus, score_ids


def test_requires_full_coverage():
    with pytest.raises(ValueError, match='confirmation'):
        build_replacement_corpus([], [], False)


def test_replacement_removes_only_target_page():
    original = [{'chunk_id': 'a', 'document_id': 'cbi_upi_rfp', 'page_number': 12},
                {'chunk_id': 'b', 'document_id': 'cbi_upi_rfp', 'page_number': 13}]
    rows = [{'chunk_id': f'new{i}'} for i in range(7)]
    result, removed = build_replacement_corpus(original, rows, True)
    assert len(result) == 8 and len(removed) == 1
    assert result[0]['chunk_id'] == 'b'


def test_exact_criterion_gold_not_page_equivalence():
    found = [{'chunk_id': 'cbi_upi_rfp:p0012:req005'},
             {'chunk_id': 'cbi_upi_rfp:p0012:req006'}]
    score = score_ids(found, ['cbi_upi_rfp:p0012:req006'])
    assert score == {'recall': 1.0, 'hit': 1, 'rr': 0.5}


def test_unreviewed_rejected(tmp_path):
    rows = [{'criterion_number': i, 'document_id': 'cbi_upi_rfp',
             'page_number': 12, 'requirement': 'test', 'review_status': 'pending'}
            for i in range(1, 8)]
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='not verified'):
        load_verified_rows(path)
