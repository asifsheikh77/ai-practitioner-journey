

\# BidLens



AI-Assisted RFP Qualification \& Risk Intelligence.



\## Objective



Build an evidence-grounded system for analyzing IT procurement

RFPs, extracting requirements, assessing vendor compliance,

and identifying bid risks.



\## Technology



\- Python 3.12

\- PyMuPDF

\- Pytest

\- Ollama (planned)

\- Local retrieval and embeddings (planned)

\- Streamlit (planned)



\## Day 1 capabilities



\- Extract text from PDF documents

\- Preserve document and page references

\- Calculate SHA-256 checksums

\- Export inspection reports to JSON

\- Run automated tests



\## Setup



```powershell

py -3.12 -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

python -m pip install -r requirements.txt

```



\## Run



```powershell

python scripts/inspect\_rfp.py --pdf data/raw/usao\_it\_managed\_services.pdf --document-id usao\_it\_managed\_services

```



\## Tests



```powershell

python -m pytest tests/ -v

```



\## Source documents



See `sources.json`.



Source PDFs are not redistributed in this repository.



\## Limitations



\- Scanned/image-only PDFs are not yet supported.

\- Tables may lose layout during text extraction.

\- Retrieval and LLM-based reasoning are not yet implemented.

\- This project is a research prototype, not a legal or

&#x20; procurement compliance decision system.

```



