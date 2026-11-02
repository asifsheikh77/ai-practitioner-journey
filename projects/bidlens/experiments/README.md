# BidLens experiments

Historical experiments preserve the project's successful and unsuccessful approaches. Active entry points remain in `../scripts/`; shared source modules, tests, evaluation definitions and historical results retain their existing locations.

## Directory guide and original-path mapping

All scripts below originally lived in `scripts/` with the same filename.

| Original script | New path | Purpose |
|---|---|---|
| `audit_ingestion.py` | `ingestion-and-layout/audit_ingestion.py` | V1 chunk quality and page coverage |
| `audit_ingestion_v2.py` | `ingestion-and-layout/audit_ingestion_v2.py` | Standalone V2 record audit |
| `inventory_pdf_layout.py` | `ingestion-and-layout/inventory_pdf_layout.py` | PDF table/layout inventory |
| `review_chunks.py` | `ingestion-and-layout/review_chunks.py` | Inspect V1 chunks by page |
| `audit_page12.py` | `eligibility-and-tables/audit_page12.py` | Raw text versus extracted eligibility table |
| `experiment_eligibility.py` | `eligibility-and-tables/experiment_eligibility.py` | Unverified automatic eligibility candidates |
| `experiment_eligibility_v2.py` | `eligibility-and-tables/experiment_eligibility_v2.py` | Reviewed eligibility augmentation of V1 |
| `experiment_table_replacement.py` | `eligibility-and-tables/experiment_table_replacement.py` | Reviewed page-12 replacement |
| `evaluate_candidates.py` | `retrieval-and-reranking/evaluate_candidates.py` | Candidate-depth coverage on repaired V1 |
| `experiment_reranking.py` | `retrieval-and-reranking/experiment_reranking.py` | Cross-encoder reranking on repaired V1 |
| `run_day36.py` | `retrieval-and-reranking/run_day36.py` | V2 reranking/context-budget experiment |
| `run_paired_semantic_hybrid.py` | `retrieval-and-reranking/run_paired_semantic_hybrid.py` | Paired V1/V2 semantic and hybrid diagnostic |
| `test_day36.py` | `retrieval-and-reranking/test_day36.py` | Synthetic context-budget/adjacency tests |
| `diagnose_q002.py` | `failure-analysis/diagnose_q002.py` | Original V1 query-sensitivity investigation |
| `diagnose_q002_repaired.py` | `failure-analysis/diagnose_q002_repaired.py` | Criterion-6 investigation on repaired V1 |

The ingestion/layout directory preserves extraction investigations; eligibility/tables preserves alternative representations of page 12; retrieval/reranking preserves ranking and context experiments; failure analysis preserves query-specific investigations.

## Environment and inputs

Run every command below from `projects/bidlens/`, using the existing project environment:

```powershell
..\..\.venv\Scripts\Activate.ps1
```

Use the dependencies already described in `../requirements.txt` and the existing project installation. Do not install or upgrade dependencies merely to perform repository cleanup. PyMuPDF supplies both `pymupdf` and `fitz`; retrieval uses NumPy, rank-bm25 and sentence-transformers. Retrieval imports sentence-transformers even for BM25, though BM25 does not load embedding weights.

Semantic/hybrid runs use `sentence-transformers/all-MiniLM-L6-v2` by default. Cross-encoder experiments use `cross-encoder/ms-marco-MiniLM-L-6-v2`. Model weights must already be cached for offline execution; otherwise model loading may download them. Preserve dependency versions, model revisions, PDF checksums and command parameters when comparing runs. Existing dependency ranges do not guarantee exact historical reproduction.

Required local inputs, depending on experiment:

- `data/raw/cbi_upi_rfp.pdf`: original source PDF, listed in `../sources.json`.
- `data/processed/cbi_upi_rfp_chunks.jsonl`: V1 narrative chunks, produced by `scripts/ingest_rfp.py`.
- `data/processed/cbi_upi_rfp_v2.jsonl`: integrated V2 structured records, produced by `scripts/ingest_rfp_v2.py`.
- `evaluation/cbi_eligibility_page12_review.json`: seven reviewed page-12 criteria.
- `evaluation/cbi_upi_rfp_questions.json`: original question wording and V1 chunk-ID labels.
- `evaluation/page12_criterion_gold.json`: three criterion-ID questions.
- `evaluation/rubric_42_narrow_assertions.json`: 16 questions with 42 provisional mapped facets.

PDFs and processed data are ignored by Git and are not supplied by a clean checkout. The standalone Day 3.6 unit tests need neither datasets nor model weights.

## Corpus and evaluation distinctions

- **V1:** original `_chunks.jsonl` and `:c...` chunk IDs. Active `search_rfp.py` and `evaluate_retrieval.py` still use this corpus.
- **Reviewed augmentation:** `experiment_eligibility_v2.py` adds reviewed eligibility records to V1 and scores source-ID equivalence. Its name does not mean the integrated V2 ingestion corpus.
- **Repaired V1:** page-12 original chunks are replaced in memory with seven reviewed `:req...` records. Candidate-depth, table-replacement and repaired-Q002 experiments use this view. Original data is retained.
- **V2:** integrated structured narrative, table and eligibility records, including `:elig...` IDs. `run_day36.py` uses searchable V2 records; the paired runner compares V1 and V2 using separate mapped evidence IDs.

Original chunk-ID labels, criterion-ID labels and provisional facet mappings are different evaluation definitions. Do not compare their metrics as if they were interchangeable. Pass `--confirm-page12-covered` only after confirming that the reviewed replacement covers page 12; the flag represents a substantive review assertion.

## Example commands

**Never overwrite historical outputs in `evaluation/results/`, the saved demo, or existing processed datasets.** Several scripts default to historical filenames. The examples with configurable destinations use a fresh, ignored directory; choose a different directory for each rerun. These are reproduction instructions, not commands required for structural cleanup.

```powershell
$runOutput = 'evaluation/results/temp/manual-reproduction-001'
if (Test-Path -LiteralPath $runOutput) { throw 'Choose a new output directory' }
New-Item -ItemType Directory -Path $runOutput | Out-Null
```

### Ingestion and layout

```powershell
python experiments/ingestion-and-layout/audit_ingestion.py --chunks data/processed/cbi_upi_rfp_chunks.jsonl --expected-pages 147
python experiments/ingestion-and-layout/audit_ingestion_v2.py --input data/processed/cbi_upi_rfp_v2.jsonl --output "$runOutput/standalone-v2-audit.json"
python experiments/ingestion-and-layout/inventory_pdf_layout.py --pdf data/raw/cbi_upi_rfp.pdf --output "$runOutput/layout.json" --summary "$runOutput/layout.txt"
python experiments/ingestion-and-layout/review_chunks.py --page 12 --chunks data/processed/cbi_upi_rfp_chunks.jsonl
```

The standalone V2 audit has its own checks and is separate from the integrated pipeline's acceptance report.

### Eligibility and tables

```powershell
python experiments/eligibility-and-tables/audit_page12.py --pdf data/raw/cbi_upi_rfp.pdf --page 12 --output "$runOutput/page12.txt"
python experiments/eligibility-and-tables/experiment_eligibility_v2.py --top-k 5 --review-file evaluation/cbi_eligibility_page12_review.json
python experiments/eligibility-and-tables/experiment_table_replacement.py --top-k 5 --review-file evaluation/cbi_eligibility_page12_review.json --labels evaluation/page12_criterion_gold.json --confirm-page12-covered
```

The original automatic-candidate experiment has a fixed output path, `data/processed/cbi_upi_rfp_eligibility_candidates.jsonl`, and no output override. **Do not execute it during cleanup or against an existing historical candidate file.** In a separate reproduction checkout with the required V1 input and no existing candidate output, its invocation is:

```powershell
python experiments/eligibility-and-tables/experiment_eligibility.py
```

Its candidates require human review; experimental rankings are not validated gold results.

### Retrieval and reranking

```powershell
python experiments/retrieval-and-reranking/evaluate_candidates.py --depths 20 50 100 --confirm-page12-covered
python experiments/retrieval-and-reranking/experiment_reranking.py --depth 50 --hybrid-depth 100 --top-k 5 --batch-size 16 --model cross-encoder/ms-marco-MiniLM-L-6-v2 --confirm-page12-covered
python experiments/retrieval-and-reranking/run_day36.py --root . --rubric evaluation/rubric_42_narrow_assertions.json --output "$runOutput/day36.json" --embedding-model sentence-transformers/all-MiniLM-L6-v2 --reranker-model cross-encoder/ms-marco-MiniLM-L-6-v2 --candidates 50 --batch-size 16
python experiments/retrieval-and-reranking/run_paired_semantic_hybrid.py --root . --rubric evaluation/rubric_42_narrow_assertions.json --output "$runOutput/paired.json" --model sentence-transformers/all-MiniLM-L6-v2
```

The paired runner also writes `v1_semantic_rankings.json`, `v1_hybrid_rankings.json`, `v2_semantic_rankings.json` and `v2_hybrid_rankings.json` beside its output. A fresh directory protects all five files. For both `--root` runners, corpus/source paths follow `--root`, but `--rubric` and `--output` resolve independently against the current working directory.

### Failure analysis

```powershell
python experiments/failure-analysis/diagnose_q002.py
python experiments/failure-analysis/diagnose_q002_repaired.py --top-k 5 --confirm-page12-covered
```

Execute these as scripts. `diagnose_q002.py` loads data and performs work at import time; `review_chunks.py` parses CLI arguments at import time. The repaired diagnostic depends on private retriever scoring methods. Rewritten-query rankings are diagnostic observations, not replacements for frozen original-question benchmark results.

### Tests and output capture

```powershell
python -m pytest tests -q -rs
python experiments/retrieval-and-reranking/test_day36.py
```

`test_day36.py` is not included in default `tests/` pytest discovery. Keep it beside `run_day36.py` for its sibling import. The V2 dataset test can skip when local V2 data is absent; inspect skip reasons. The synthetic Day 3.6 tests do not verify model-based retrieval performance.

Stdout-only experiments can be captured explicitly with PowerShell, for example:

```powershell
python experiments/retrieval-and-reranking/evaluate_candidates.py --depths 20 50 100 --confirm-page12-covered | Out-File -LiteralPath "$runOutput/candidate-depths.txt" -Encoding utf8 -NoClobber
```

## Preserved findings and limitations

Historical results remain at `../evaluation/results/`. Preserve their original bytes, including mixed UTF-16 and UTF-8 text logs. `baseline_k3.txt` is incomplete and misnamed: it reports `Top K: 10` and `recall_at_10`, then ends at the semantic-section heading. It is not reliable evidence for top-3 results; the original file has intentionally not been edited.

The repaired-V1 `reranking_day36.txt` and V2 `day36_retrieval_experiment.json` are different experiments. Candidate-pool coverage is not reranked top-5 performance; union pools can exceed individual method depths. Timing fields cover different operations and depend on the environment.

The 42-facet rubric is provisional (`facet_review_required`) and not exhaustive relevance gold. Mapped-facet hit rates are not certified recall, accuracy or compliance scores. Same-page context expansion is a heuristic, not semantic parent-section reconstruction. Preserve negative findings: reranking and expansion did not consistently improve question completeness. Source extraction, page coverage and semantic support still require human verification.
