# BidLens: When More Sophisticated Retrieval Didn't Produce Better RFP Evidence Coverage

## The problem

A 147-page banking technology RFP contains qualification criteria, functional scope, integrations, reporting requirements and security obligations distributed across narrative text and tables. A keyword search can miss related language; an embedding search can retrieve semantically similar but nonresponsive passages. The goal was to build a transparent evidence-review demonstration, not an automated procurement adjudicator.

## Design decisions

1. **Preserve provenance during ingestion.** The structured V2 representation retains page and chunk identifiers and makes eligibility-table rows independently searchable.
2. **Use hybrid retrieval.** BM25 handles exact terms and protocol names; sentence embeddings handle broader semantic matches. Reciprocal rank fusion combines ranked results without pretending scores are calibrated probabilities.
3. **Evaluate against the actual review task.** The evaluation uses 16 questions and 42 provisionally mapped evidence facets, alongside fixed context budgets.
4. **Keep a human in the loop.** Retrieved passages are evidence candidates; the system does not certify compliance without vendor information.

## What the measurements showed

At a **4,000-token budget**, the Day 3.6 experiment reported:

| Method | Provisional mapped facets present | Questions with all mapped facets present |
|---|---:|---:|
| V2 hybrid | 33/42 (78.6%) | 10/16 |
| Hybrid + same-page expansion | 31/42 (73.8%) | 10/16 |
| Cross-encoder reranking | 33/42 (78.6%) | 9/16 |
| Reranking + same-page expansion | 32/42 (76.2%) | 8/16 |

At **1,000 tokens**, same-page expansion substantially reduced coverage (22/42 versus 28/42 for hybrid). Reranking changed which facets were recovered, but did not consistently improve overall question completeness.

These are **diagnostic mapped-facet hit rates**, not certified recall. The mapped evidence is provisional and not an exhaustive judged relevance set. The benchmark is one document and a small question set; it does not establish generalization.

## What the end-to-end demo showed

The five-topic demonstration successfully produced JSON and Markdown evidence reports. Strong examples included turnover eligibility (p. 12), protocol integration (p. 34) and transaction reporting (p. 38). The security section, however, surfaced annexure headings and glossary references instead of substantive security obligations. This is a useful visible failure mode: **a technically valid citation may still be poor evidence**.

The demo correctly marks vendor compliance **UNKNOWN** and the bid decision **NOT ASSESSED**, because no vendor response or capability evidence is present.

## What I would improve in a real product

A production system would require independently judged evidence labels, robust requirement classification, citation entailment checks, vendor-document comparison, calibrated review workflows, security testing and operational monitoring. Those are deliberately out of scope here.

## Practitioner takeaway

The project taught me to treat retrieval as an evidence supply chain: extraction quality, document structure, ranking, context budgets and validation all affect the trustworthiness of the result. It also taught me when to stop optimizing. A reproducible system with honest limitations is more credible than an overclaimed benchmark.

## Publishing checklist

- [ ] Run full local demo and provenance validator against the exact V2 source dataset
- [ ] Manually verify sample passages against the PDF pages
- [ ] Verify document redistribution rights and scrub restricted source text if necessary
- [ ] Confirm README paths and commands match the published repository
- [ ] Add a short terminal demo or screenshot
- [ ] Link this case study from the repository landing page
