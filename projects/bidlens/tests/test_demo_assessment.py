import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/demo_assessment.py'
spec = importlib.util.spec_from_file_location('demo_assessment', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fake_search(query, method, top_k):
    assert method == 'hybrid'
    return [{'chunk_id': 'demo:p0003:n001', 'page_number': 3, 'score': 0.2,
             'text': 'Illustrative retrieved passage'}][:top_k]

def test_searchable_filter():
    assert mod.searchable_v2([{'searchable': True}, {'searchable': False}, {}]) == [{'searchable': True}]

def test_report_has_citations_and_unknown_compliance():
    report = mod.build_report(fake_search)
    assert len(report['sections']) == 5
    assert all(s['vendor_compliance'].startswith('UNKNOWN') for s in report['sections'])
    assert all(s['evidence'][0]['chunk_id'] == 'demo:p0003:n001' for s in report['sections'])
    assert 'NOT ASSESSED' in report['decision']
    assert 'Page 3' in mod.markdown(report)

def test_no_evidence_does_not_imply_absence():
    report = mod.build_report(lambda *args, **kwargs: [])
    assert all(s['status'] == 'NO_EVIDENCE_RETRIEVED' for s in report['sections'])
    assert 'does not establish absence' in mod.markdown(report)
