# Week 01 — Development Environment & Python Foundations

## Overview

Week 01 establishes the foundational development environment for the AI Practitioner Journey.

The objective is to prepare a reproducible local workspace, review essential Python programming concepts, and verify the ability to execute locally hosted language models.

This foundation supports the more structured LLM experiments, RAG applications, and agentic workflows planned for subsequent weeks.

## Learning Objectives

- Configure Python and a local development environment.
- Establish a Git and GitHub workflow.
- Review essential Python programming concepts.
- Understand Python virtual environments and package dependencies.
- Install and run a local language model using Ollama.
- Verify programmatic communication with a local model.
- Establish basic documentation and reproducibility practices.

## Technology Stack

| Technology 		 | Purpose |
| Python			 | Programming and AI application development |
| Visual Studio Code | Development environment |
| Git & GitHub 		 | Version control and collaboration |
| Ollama 			 | Local LLM inference |
| Docker Desktop 	 | Container tooling for subsequent projects |

## Exercises

### Exercise 01 — Python Fundamentals

**File:** `python_basics.py`

A small inventory-processing exercise using entirely synthetic product data.

Concepts demonstrated:

- Variables and data structures
- Lists and dictionaries
- Functions
- Loops and conditional logic
- Error handling
- Simple business calculations

### Exercise 02 — Environment Verification

**File:** `environment_check.py`

Checks the Python runtime, operating system, interpreter path and connectivity to the local Ollama API.

### Exercise 03 — Local LLM Smoke Test

**File:** `ollama_smoke_test.py`

Sends a basic prompt to a locally hosted language model and displays the response.

This is a functional connectivity check, not an evaluation of model quality.

## Getting Started

Clone the repository and navigate to the Week 01 folder.

```bash
git clone https://github.com/asifsheikh77/ai-practitioner-journey.git
cd ai-practitioner-journey/experiments/week-01-foundations
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required Python package:

```bash
pip install -r requirements.txt
```

Run the exercises:

```bash
python python_basics.py
python environment_check.py
```

To run the LLM smoke test, install Ollama, download the configured model and ensure the Ollama service is running.

```bash
ollama pull gemma3:1b
python ollama_smoke_test.py
```

## Expected Outcomes

Successful completion should demonstrate:

1. A functioning Python development environment.
2. Basic Python programming competency.
3. Working Git and GitHub version control.
4. Access to a locally hosted language model.
5. The ability to call that model from Python.

## Lessons Learned

See [learning-notes.md](learning-notes.md) for implementation notes, troubleshooting observations and reflections.

## Next Step

**Week 02 — LLM Behavior Experiments**

The next stage introduces structured model evaluation using a common question dataset, different prompting strategies, temperature configurations, scoring and latency measurements.

---

*Part of the AI Practitioner Journey — Learn → Build → Test → Measure → Document → Share.*