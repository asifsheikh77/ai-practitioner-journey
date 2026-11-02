"""Inspect extracted page-12 text and compare with PyMuPDF table extraction."""
import argparse
import json
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pdf', default='data/raw/cbi_upi_rfp.pdf')
    p.add_argument('--page', type=int, default=12, help='1-based PDF page index')
    p.add_argument('--output', default='evaluation/results/page12_audit.txt')
    args = p.parse_args()
    pdf = ROOT / args.pdf
    if not pdf.exists():
        raise SystemExit(f'Missing PDF: {pdf}')
    doc = fitz.open(pdf)
    if not 1 <= args.page <= len(doc):
        raise SystemExit(f'Page must be 1..{len(doc)}')
    page = doc[args.page - 1]
    out = [f'PDF: {pdf.name}; PDF page index: {args.page}; total pages: {len(doc)}',
           '\n=== RAW TEXT ===\n', page.get_text('text', sort=False),
           '\n=== SORTED TEXT ===\n', page.get_text('text', sort=True),
           '\n=== TABLE DETECTION ===\n']
    try:
        tabs = page.find_tables()
        out.append(f'Tables detected: {len(tabs.tables)}\n')
        for i, table in enumerate(tabs.tables, 1):
            out.append(f'\nTABLE {i}: rows={table.row_count} cols={table.col_count}\n')
            for row in table.extract():
                out.append(json.dumps(row, ensure_ascii=False) + '\n')
    except Exception as exc:
        out.append(f'Table detection unavailable or failed: {exc}\n')
    dest = ROOT / args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(''.join(out), encoding='utf-8')
    print(f'Wrote {dest}')
    print('Inspect PDF page numbering, table boundaries, and any non-table content before approving replacement.')

if __name__ == '__main__':
    main()
