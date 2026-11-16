# BidLens Phase 2 — Grounded RFP Q&A

Status: implemented and unit-tested with test doubles. **Not yet run end-to-end on the real V2 corpus or scored** — do the steps in "First run" and record the numbers before quoting any.

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
- A response cut off by the token limit raises an explicit error rather than returning broken JSON.

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

## Evaluation notes

`evaluate_qa.py` reports abstention on Q017–Q020, over-abstention on the 16 answerable questions, whether provisional gold evidence reached the context and was cited, claims removed by verification, and latency. It does **not** measure answer correctness: grade the `human_review` fields in the output file. Gate defaults (0.30 / 0.50) are provisional until calibrated; with 16 vs 4 questions, report counts, not percentages with confidence.

## Known weak spots to document honestly

- Q017–Q020 reuse RFP vocabulary (cloud, UPI, contract), so the lexical gate may pass them; they test generation-time abstention.
- The security topic retrieves mostly headings; expect abstention or thin answers there.
- Everything is validated against one document (CBI UPI RFP).
