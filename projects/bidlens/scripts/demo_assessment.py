"""Portfolio demonstration: evidence review, NOT an automated compliance decision.
Run from project root: python scripts/demo_assessment.py --output-dir demo_output
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

# Explicit, reproducible review topics; these are searches, not verified requirements.
REVIEW_TOPICS = [
    ('Eligibility', 'bidder eligibility qualification criteria turnover experience'),
    ('Scope', 'UPI solution supply implementation migration maintenance scope'),
    ('Integration', 'ISO 8583 ISO 20022 APIs MQ XML interface integration'),
    ('Reporting', 'MIS transaction reports channel wise risk reporting'),
    ('Security', 'information security vulnerability malware data protection'),
]


def searchable_v2(chunks):
    return [c for c in chunks if c.get('searchable') is True]


def evidence_item(hit):
    return {
        'chunk_id': hit['chunk_id'],
        'page_number': hit['page_number'],
        'score': round(float(hit['score']), 6),
        'text': hit['text'],
    }


def build_report(search, top_k=3):
    sections = []
    for topic, query in REVIEW_TOPICS:
        hits = search(query, method='hybrid', top_k=top_k)
        sections.append({
            'topic': topic,
            'query': query,
            'status': 'EVIDENCE_FOR_HUMAN_REVIEW' if hits else 'NO_EVIDENCE_RETRIEVED',
            'evidence': [evidence_item(h) for h in hits],
            'interpretation': 'Not assessed: retrieved text requires human interpretation.',
            'vendor_compliance': 'UNKNOWN — no vendor capability evidence supplied',
        })
    return {
        'title': 'BidLens — Evidence Review Demonstration',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'retrieval_method': 'V2 hybrid (BM25 + semantic RRF)',
        'scope': 'Evidence discovery for selected RFP topics; not exhaustive requirement extraction.',
        'decision': 'NOT ASSESSED — no vendor response or capability evidence',
        'limitations': [
            'Retrieved passages are candidates, not verified requirements.',
            'Relevance scores are not confidence or compliance probabilities.',
            'No bid/no-bid recommendation is generated.',
            'Review source PDF pages before relying on extracted text.',
        ],
        'sections': sections,
    }


def markdown(report):
    lines = [f"# {report['title']}", '',
             f"**Retrieval:** {report['retrieval_method']}",
             f"**Scope:** {report['scope']}",
             f"**Bid decision:** {report['decision']}", '',
             '> This is a retrieval-assisted review, not a compliance determination.', '']
    for s in report['sections']:
        lines += [f"## {s['topic']}", '', f"**Search:** {s['query']}",
                  f"**Status:** {s['status']}", f"**Vendor compliance:** {s['vendor_compliance']}", '']
        if not s['evidence']:
            lines += ['No supporting passage retrieved. This does not establish absence in the RFP.', '']
        for e in s['evidence']:
            safe = e['text'].replace('\n', ' ').strip()
            lines += [f"- **Page {e['page_number']} · `{e['chunk_id']}`**: {safe}"]
        lines += ['', s['interpretation'], '']
    lines += ['## Limitations', ''] + [f'- {x}' for x in report['limitations']]
    return '\n'.join(lines) + '\n'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--output-dir', type=Path, default=Path('demo_output'))
    p.add_argument('--top-k', type=int, default=3)
    args = p.parse_args()
    if args.top_k < 1:
        p.error('--top-k must be >= 1')
    from bidlens.retrieval import BidLensRetriever, load_chunks
    source = args.root / 'data/processed/cbi_upi_rfp_v2.jsonl'
    chunks = searchable_v2(load_chunks(source))
    if not chunks:
        raise RuntimeError('No searchable V2 records')
    retriever = BidLensRetriever(chunks)
    report = build_report(retriever.search, args.top_k)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / 'assessment.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    (out / 'assessment.md').write_text(markdown(report), encoding='utf-8')
    print(f"Wrote {out / 'assessment.json'} and {out / 'assessment.md'}")
    print('Review all cited pages; vendor compliance remains UNKNOWN.')

if __name__ == '__main__':
    main()
