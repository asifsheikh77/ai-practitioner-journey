# Final QA and publication gate

## Evidence review of uploaded sample (2026-11-02)

| Section | Assessment | Publication treatment |
|---|---|---|
| Eligibility | Good requirement-bearing evidence | Keep, verify p.12 |
| Scope | Useful scope passage, plus repetitive form/title | Keep with qualification |
| Integration | Strong p.34 protocol requirement, but one glossary hit | Showcase p.34 only |
| Reporting | Substantive p.38 transaction/risk reporting | Showcase p.38 |
| Security | Annexure headings/index and abbreviation, not actual controls | Flag as a known failure; do not summarize as security requirements |

## Automated check

`python scripts/validate_demo.py --report demo_output/assessment.json --chunks data/processed/cbi_upi_rfp_v2.jsonl`

Checks citation IDs, searchable source membership, page numbers, exact extracted text and abstention. Does not judge semantic relevance or original-PDF extraction fidelity.

## Stop conditions

Once the provenance validator and local tests pass, source passages are manually spot-checked, README commands are confirmed, rights reviewed and the case study is published, stop BidLens work and move to the next practitioner project.
