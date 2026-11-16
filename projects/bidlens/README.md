# BidLens — Evidence-Grounded RFP Review

**Portfolio project | Python 3.12 | PDF ingestion | Hybrid retrieval | Evaluation**

BidLens is a local, reproducible demonstration of evidence discovery in complex IT procurement RFPs. It extracts structured, page-referenced passages from PDFs, retrieves relevant evidence using BM25 and sentence embeddings, and creates a human-reviewable report with source citations. **Phase 2** adds grounded question answering: free-text questions are answered only from retrieved passages, every statement carries a verified citation, and the system says so when the document does not contain the answer.

> **Scope boundary:** BidLens does not certify requirements, assess a vendor's compliance, or make bid/no-bid decisions. Retrieved evidence is a candidate for human review. No vendor capability documents are provided in the sample.

## Why this project?

Enterprise RFPs mix eligibility criteria, functional requirements, technical protocols, reporting obligations and security controls across narrative sections and tables. A useful AI assistant must locate supporting evidence and know when it cannot make a justified determination.

## Demonstration

The sample review searches five fixed topics: **eligibility, scope, integration, reporting, security**. It outputs `assessment.json` and `assessment.md`, each with source page numbers and chunk identifiers. The sample report has 15 citations across five sections. **Security evidence is a known weakness:** the current top results are largely annexure headings and index references, not substantive controls. Do not treat this section as a validated security review.

Example retrieved evidence from the sample document:

| Topic | Example passage | Source |
|---|---|---|
| Eligibility | INR 20 crore annual turnover in India for each of three specified financial years | p. 12, `cbi_upi_rfp:p0012:elig003` |
| Integration | Interfaces using ISO 8583/ISO 20022, web services, MQ, XML and APIs | p. 34, `cbi_upi_rfp:p0034:n006` |
| Reporting | Transaction and channel-wise reporting, reconciliation and risk reporting | p. 38, `cbi_upi_rfp:p0038:n005` and `...:n006` |

These are **human-reviewed examples from the generated retrieval report**, not an automatically generated compliance verdict.

## Grounded Q&A (Phase 2)

Ask any question about the RFP. BidLens retrieves evidence, checks whether it is sufficient, generates an answer constrained to cited passages, then removes anything it cannot verify. Out-of-scope questions get a plain explanation instead of a guess.

```mermaid
flowchart TD
    Q[Free-text question] --> R[Hybrid retrieval, top 8]
    R --> G{Evidence gate}
    G -- fails --> X[Out of scope message]
    G -- passes --> C[Token-bounded context with citation IDs]
    C --> L[LLM returns JSON claims with citations]
    L --> V[Citation check, then claim-support check]
    V --> A[Answered, partial, or insufficient evidence]
```

| Layer | Catches | Does not catch |
|---|---|---|
| Evidence gate (semantic similarity and query-term coverage) | Off-topic questions | Plausible questions the document does not answer |
| Model abstention | Answer absent from retrieved passages | Model ignoring the instruction |
| Citation check | Claims citing passages that were not in the context | An irrelevant but real citation |
| Claim-support check (figures and term overlap; optional LLM judge) | Invented numbers, unsupported claims | Subtle entailment errors such as negation |

Each layer can only remove content. Retrieved text is passed to the model as untrusted data. Model runtimes sit behind one adapter: **local Ollama by default**, with opt-in OpenAI and Gemini (these send retrieved RFP passages to an external API). Details and configuration: [`docs/PHASE2.md`](docs/PHASE2.md).

## Architecture

```mermaid
flowchart TD
    A[RFP PDF] --> B[Inspect and extract]
    B --> C[Structured V2 records with page and chunk IDs]
    C --> D[Searchable records only]
    D --> E[BM25]
    D --> F[Sentence embeddings]
    E --> G[Reciprocal rank fusion]
    F --> G
    G --> H[Five fixed review topics]
    H --> I[JSON and Markdown evidence report]
    I --> J[Human review and source verification]
```

## Quick start (Windows PowerShell)

Requires Python 3.12, an existing project checkout, the V2 JSONL data and the demo script from the portfolio MVP patch.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest tests/test_demo_assessment.py -q
python scripts/demo_assessment.py --root . --output-dir demo_output
python scripts/validate_demo.py --report demo_output/assessment.json --chunks data/processed/cbi_upi_rfp_v2.jsonl
```

The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) may download on the first run. The demo uses **V2 hybrid retrieval (BM25 + semantic reciprocal rank fusion)**. The validation command checks source record IDs, page metadata, exact extracted text and the explicit abstention status. It **does not** verify that a passage truly supports a requirement or that the original PDF was extracted correctly.

## Running Phase 2

```powershell
python -m pip install -r requirements.txt -r requirements-phase2.txt
python scripts/calibrate_gate.py                      # inspect gate signals on the question set
python scripts/ask.py "What minimum annual turnover must a bidder demonstrate?"
python scripts/evaluate_qa.py                         # writes evaluation/results/phase2/qa_eval_*.json
streamlit run app/streamlit_app.py
```

For a cloud runtime, set `OPENAI_API_KEY` or `GEMINI_API_KEY` and pass `--provider openai|gemini` (or choose it in the app sidebar). `python scripts/check_llm.py --provider gemini` tests connectivity without sending RFP text.

## Evaluation and engineering findings

Across 16 review questions and **42 provisionally mapped evidence facets**, at a 4,000-token context budget, V2 hybrid retrieved **33/42 facets (78.6%)**, with all mapped facets present for **10/16 questions**. In the Day 3.6 comparison, reranking also retrieved 33/42 facets, but only 9/16 questions were complete; same-page context expansion did not consistently improve results. These are **mapped-facet hit rates**, *not certified recall, accuracy or compliance scores*. The 42 mappings are not exhaustive relevance judgments.

This project's central engineering lesson: **more sophisticated ranking does not necessarily produce more complete evidence coverage**.

### Phase 2 question answering: first graded run (before fixes)

20 questions (16 answerable, 4 unanswerable with absence not fully audited), Llama 3.1 8B via Ollama, provisional gate thresholds (0.30 similarity, 0.50 coverage), one reviewer. Counts, not rates:

| Measure | Result |
|---|---|
| Unanswerable questions correctly abstained | 4/4 (1 blocked by the gate, 3 declined by the model) |
| Answerable questions blocked by the gate | 0/16 |
| Answers shown to the user | 6 (5 answered, 1 partial); all surviving claims graded supported; 5 fully correct, 1 partial |
| Answerable questions where the system abstained | 10/16 |
| Provisional gold evidence present in retrieved context | 14/16 |

The 10 over-abstentions were implementation faults, not retrieval or knowledge failures. Six were caused by the model writing citations as `<passage id="...">` instead of the bare ID, which strict validation rejected (for four of those questions the rejected answer was graded correct). Four were JSON parse failures that cluster near a 1,000-token output cap, most likely truncation, though the run did not record the cause. Of 20 claims removed by verification, 19 were this citation-format artifact and one was a genuine support-check rejection, so that count should not be read as the verifier catching bad claims.

Fixes made afterwards: tolerant citation parsing (the ID must still be a passage that was sent), a 2,000-token output limit with explicit errors on truncation, and an explicit 8,192-token Ollama context window. Results of a re-run after these fixes have not been added yet.

Everything is measured on one document with 20 questions, provisional gold evidence and a single reviewer, so these figures describe behavior on this sample and do not generalize. Median generation latency on a local 8B model was about 40 seconds.

## Repository guide

- `src/bidlens/`: PDF extraction, structured ingestion, retrieval, and Phase 2 modules (`gate.py`, `answering.py`, `llm.py`, `runtime.py`)
- `scripts/`: ingestion, search, evaluation and portfolio demo entry points; Phase 2 adds `ask.py`, `calibrate_gate.py`, `evaluate_qa.py`, `check_llm.py`
- `app/`: Streamlit question-answering demo
- `tests/`: extraction, retrieval, demo and Phase 2 tests
- `evaluation/`: question set, rubric and experiment artifacts
- `docs/`: architecture, evaluation findings and portfolio case study
- `demo_output/`: generated local artifacts (publish only after source-rights review)

## Experiments

Historical ingestion, eligibility, retrieval and failure-analysis scripts are preserved under `experiments/`. See the [experiment guide](experiments/README.md) for original-to-current paths, dataset requirements, reproduction commands and evaluation limitations. Active entry points remain in `scripts/`; historical results remain in `evaluation/results/`.

## Limitations

- Five fixed searches are **not exhaustive requirement extraction**.
- Results include low-information passages such as glossary entries and annexure headings.
- Security results in the current sample do not establish substantive security coverage.
- No vendor evidence is supplied; vendor compliance is **UNKNOWN** and bid decision **NOT ASSESSED**.
- Evidence citation integrity is not the same as semantic correctness.
- Generated answers come from a language model. The support check is a screen, not proof of entailment, and the evidence gate is a heuristic: it can misjudge vague but legitimate questions.
- Gate thresholds are provisional, and Phase 2 is evaluated on a single RFP.
- Cloud runtimes (OpenAI, Gemini) send retrieved RFP passages to an external service; local Ollama does not.
- Source document permissions must be checked before publishing the PDF or extracted text.
- No hosted deployment, authentication, production monitoring or procurement certification is claimed.

## Reproducibility and provenance

Record the exact PDF edition, checksum, extraction configuration, model identifier and local environment when reproducing results. See `sources.json` for the project's document registry. The sample analysis is based on a Central Bank of India UPI RFP; confirm redistribution rights before committing any full document or derived passages to a public repository.

## What I learned

How to structure difficult PDF evidence, combine lexical and semantic search, evaluate retrieval at fixed context budgets, interpret negative experiments, validate provenance and avoid unsupported business conclusions. See [`docs/ENGINEERING_CASE_STUDY.md`](docs/ENGINEERING_CASE_STUDY.md).

## Status

**Portfolio demonstration — Phase 2 (grounded Q&A) implemented; post-fix evaluation re-run pending.** Retrieval experiments are frozen. This is an educational engineering artifact, not a production compliance system.
