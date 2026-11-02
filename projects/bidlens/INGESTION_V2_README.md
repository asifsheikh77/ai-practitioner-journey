# BidLens ingestion V2 — integrated reproducible pipeline

This package is the **user's supplied BidLens project** with new V2 ingestion scripts and outputs added. The original `src/bidlens/ingestion.py`, V1 dataset, and benchmark files have not been changed.

## Run (PowerShell, from BidLens root)

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
python scripts/ingest_rfp_v2.py `
  --pdf data/raw/cbi_upi_rfp.pdf `
  --output data/processed/cbi_upi_rfp_v2.jsonl `
  --report evaluation/results/ingestion_v2_report.json
python -m pytest tests/test_ingestion_v2_pipeline.py -q
```

The original PDF and processed datasets are **not tracked in this repository**. Place your `cbi_upi_rfp.pdf` at `data/raw/cbi_upi_rfp.pdf` (or change `--pdf`). Generate the V2 dataset locally or supply an existing local copy. The historical quality report is tracked at `evaluation/results/ingestion_v2_report.json`; use a separate report destination when reproducing the pipeline to preserve that result.

## Integrated pipeline

`scripts/ingest_rfp_v2.py` orchestrates:
1. `ingest_structured_v2_1.py`: page-layout extraction; table rows and outside-table text.
2. `cleanup_ingestion_v2_2.py`: classify non-evidence rows; preserve originals.
3. `recover_table_first_rows.py`: recover five data rows incorrectly treated as headers.
4. `enrich_ingestion_v2_3.py`: pricing column context, technical specification labels, continuation flags.

The scripts are retained as importable modules so a single command reproduces the whole process. No manual eligibility fixture is used to generate the output.

## Verified against the actual uploaded PDF

147 pages, 61 tables, 1,170 records (605 narrative, 553 table rows, 12 eligibility), 1,154 searchable records, five recovered first data rows, seven acceptance checks passed. The report contains full extraction and cleanup findings.

## Known limitations

- Six flagged page-boundary continuation candidates are **not** automatically merged.
- Complex merged commercial headers and source-text coverage still need manual verification.
- The V2 `chunk_id`s differ from V1. **Do not run the existing 16-question benchmark against V2 without remapping gold evidence IDs**; doing so would yield misleading scores.
- This is a reproducible experimental pipeline, not a production-certified parser.

## Recommended next gate

Inspect the flagged page-boundary cases and selected wide commercial tables; then map the existing evaluation questions to V2 evidence IDs and compare V1/V2 with unchanged ranking methods.
