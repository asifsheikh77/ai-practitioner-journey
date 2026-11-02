"""Read-only layout/table inventory for BidLens PDFs (PyMuPDF).

Usage: python scripts/inventory_pdf_layout.py --pdf data/raw/cbi_upi_rfp.pdf
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, default=Path('data/raw/cbi_upi_rfp.pdf'))
    parser.add_argument('--output', type=Path, default=Path('evaluation/results/cbi_layout_inventory.json'))
    parser.add_argument('--summary', type=Path, default=Path('evaluation/results/cbi_layout_summary.txt'))
    parser.add_argument('--reference-page', type=int, default=12, help='1-based page number for the verified eligibility table')
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f'PDF missing: {args.pdf}. The previous project ZIP did not contain raw PDFs.')

    report = {'pdf': str(args.pdf), 'pages': [], 'warnings': []}
    with pymupdf.open(args.pdf) as doc:
        if doc.needs_pass:
            parser.error('Password-protected PDFs are not supported')
        report['page_count'] = len(doc)
        for index, page in enumerate(doc):
            number = index + 1
            page_text = page.get_text('text', sort=True)
            blocks = page.get_text('blocks')
            record = {'page_number': number, 'text_chars': len(page_text), 'text_blocks': len(blocks), 'tables': [], 'warnings': []}
            try:
                tables = page.find_tables()
                for table_index, table in enumerate(tables.tables, start=1):
                    rows = table.extract()
                    if not rows:
                        record['warnings'].append(f'table_{table_index}:empty')
                    if any(len(row) != table.col_count for row in rows):
                        record['warnings'].append(f'table_{table_index}:inconsistent_columns')
                    record['tables'].append({
                        'table_index': table_index,
                        'bbox': [round(float(x), 2) for x in table.bbox],
                        'row_count': table.row_count,
                        'column_count': table.col_count,
                        'empty_cells': sum(cell is None or not str(cell).strip() for row in rows for cell in row),
                        'rows': rows,
                    })
            except Exception as exc:
                record['warnings'].append(f'table_detection_failed:{type(exc).__name__}:{exc}')
            if not page_text.strip():
                record['warnings'].append('no_extractable_text')
            report['pages'].append(record)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    pages_with_tables = [p for p in report['pages'] if p['tables']]
    total_tables = sum(len(p['tables']) for p in report['pages'])
    flagged = [p for p in report['pages'] if p['warnings']]
    ref = next((p for p in report['pages'] if p['page_number'] == args.reference_page), None)
    lines = [
        f'PDF: {args.pdf}',
        f'Pages: {report["page_count"]}',
        f'Pages with detected tables: {len(pages_with_tables)}',
        f'Total detected tables: {total_tables}',
        f'Pages with warnings: {len(flagged)}',
        '', 'TABLE INVENTORY (1-based PDF pages):',
    ]
    for p in pages_with_tables:
        shapes = ', '.join(f'{t["row_count"]}x{t["column_count"]}' for t in p['tables'])
        lines.append(f'page {p["page_number"]}: {len(p["tables"])} table(s); shapes={shapes}')
    lines.extend(['', 'WARNINGS:'])
    lines.extend(f'page {p["page_number"]}: {"; ".join(p["warnings"])}' for p in flagged)
    lines.extend(['', f'REFERENCE PAGE {args.reference_page}:'])
    if ref:
        for table in ref['tables']:
            lines.append(f'Table {table["table_index"]}: {table["row_count"]} rows x {table["column_count"]} cols')
            for i, row in enumerate(table['rows']):
                lines.append(f'  row {i}: {json.dumps(row, ensure_ascii=False)}')
        if not ref['tables']:
            lines.append('NO TABLE DETECTED — investigate before building V2')
    else:
        lines.append('Reference page is outside PDF')
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[:6]))
    print(f'Full inventory: {args.output}')
    print(f'Readable summary: {args.summary}')


if __name__ == '__main__':
    main()
