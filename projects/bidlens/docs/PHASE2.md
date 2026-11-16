# BidLens Phase 2 — Grounded RFP Q&A

Status (November 2026): implemented and unit-tested with test doubles. Two in-sample, single-document Ollama evaluation runs are recorded in `evaluation/results/phase2/`. The latest run answered 16/16 labeled answerable questions (12 full, 4 partial) and abstained on 4/4 labeled unanswerable questions; these are development-set results, not independently verified accuracy or completeness.

## Pipeline

```
question -> hybrid retrieval (top 8) -> evidence gate -> token-bounded context
         -> LLM (JSON claims + citation IDs) -> citation check -> claim-support check
         -> ANSWERED | PARTIAL | INSUFFICIENT_EVIDENCE
```

Each stage can only remove content. The LLM is never called when the gate fails.

| Layer | Module | Catches | Does not catch |
|---|---|---|---|
| Evidence gate | `gate.py` | Off-topic questions (low semantic similarity / query terms absent from retrieved text) | Plausible-but-absent questions ("who won this tender?") |
| Generation abstention | `answering.py` prompt | Model declines when passages lack the answer | Model ignoring the instruction |
| Citation integrity | `answering.py` | Claims citing IDs not in the context, or no ID | Cited passage that is irrelevant |
| Claim support (deterministic) | `check_claim_support` | Fabricated figures; claims whose terms are absent from the cited text | Subtle entailment errors, negation |
| Claim support (LLM judge, optional) | `--judge` | Second opinion on entailment | It is itself a model; fails closed on bad output |

Retrieved passages are escaped and wrapped in `<passage>` tags; the system prompt tells the model to treat them as untrusted data. No vendor-compliance or bid/no-bid output exists.

## Runtimes

- **Local (default):** Ollama, `BIDLENS_OLLAMA_MODEL` (default `llama3.1:8b`), `OLLAMA_HOST`.
- **OpenAI (opt-in):** `OPENAI_API_KEY`, `BIDLENS_OPENAI_MODEL` (default `gpt-6-luna`). Reasoning is off by default (`BIDLENS_OPENAI_REASONING_EFFORT=none`) for speed; set it to an empty string for older models that reject the field.
- **Gemini (opt-in):** `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), `BIDLENS_GEMINI_MODEL` (default `gemini-3.8-flash`).
- Cloud runtimes send retrieved RFP passages to an external service. Model IDs change often; override the defaults via the env vars if a default is retired.
- A response cut off by the token limit triggers one shorter retry; if that also truncates, complete claim objects may be recovered and marked partial. If none can be recovered, the call returns an error outcome. This recovery has limitations: it can assume answerability from incomplete JSON.

## First run (PowerShell, from `projects/bidlens/`)

```powershell
python -m pip install -r requirements.txt -r requirements-phase2.txt
python -m pip install -e .
python -m pytest tests -q -rs
# needs data/processed/cbi_upi_rfp_v2.jsonl (see sources.json, then scripts/ingest_rfp_v2.py)
python scripts/calibrate_gate.py                 # no LLM; review signals, then set gate defaults
python scripts/ask.py "What minimum annual turnover must a bidder demonstrate?"
python scripts/evaluate_qa.py --provider ollama   # writes evaluation/results/phase2/qa_eval_*.json
streamlit run app/streamlit_app.py
```

## Recorded evaluation and interpretation

The initial saved run answered 6/16 answerable questions; after citation-format and generation-output fixes, the latest run answered 16/16 (12 full, 4 partial), with no operational errors recorded. The same 20 questions informed the fixes, so the comparison is **in-sample**. One reviewer graded the latest surviving answers correct, but answer completeness and independent semantic entailment were not established. Four unanswerable labels have not been exhaustively audited for absence. The 42-facet retrieval rubric remains provisional. Source files: `evaluation/results/phase2/qa_eval_20261116-134258.json` and `qa_eval_20261116-140949.json`. Verify these files before quoting exact intermediate-run numbers.

## Evaluation notes

`evaluate_qa.py` reports abstention on Q017–Q020, over-abstention on the 16 answerable questions, whether provisional gold evidence reached the context and was cited, claims removed by verification, and latency. It does **not** measure answer correctness: grade the `human_review` fields in the output file. Gate defaults (0.30 / 0.50) are provisional until calibrated; with 16 vs 4 questions, report counts, not percentages with confidence.

## Known weak spots to document honestly

- Q017–Q020 reuse RFP vocabulary (cloud, UPI, contract), so the lexical gate may pass them; they test generation-time abstention.
- The security topic retrieves mostly headings; expect abstention or thin answers there.
- Everything is validated against one document (CBI UPI RFP).
