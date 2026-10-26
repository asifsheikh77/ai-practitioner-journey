# Week 01 — Learning Notes

**Project:** AI Practitioner Journey  
**Module:** Week 01 — Development Environment & Python Foundations  
**Status:** Foundation exercises documented  
**Focus:** Python, local AI inference, Git/GitHub, and reproducible development

---

## 1. Overview

The first week focused on establishing a practical development environment for building and evaluating AI applications locally.

The objective was not to develop a sophisticated AI application immediately, but to understand and validate the foundational tools required for subsequent experiments.

The activities covered Python development, dependency management, version control, basic application logic, and local LLM inference using Ollama.

An important takeaway was that working with AI models involves much more than writing prompts. Even simple AI applications depend on a functioning software environment, reproducible configurations, reliable integrations, and systematic testing.

## 2. Development Environment

The following tools form the initial development stack.

| Component | Tool | Purpose |
|---|---|---|
| Programming language | Python 3.x | Application logic and AI integration |
| IDE | Visual Studio Code | Development and debugging |
| Version control | Git | Tracking code changes |
| Code repository | GitHub | Public documentation and project history |
| Local model runtime | Ollama | Running LLMs locally |
| Containerization | Docker Desktop | Preparing for containerized applications |
| Python dependencies | pip and venv | Isolating project dependencies |

**Environment details to record:**

- Operating system: Windows 11 64-bit
- Python version: 3.15.1
- VS Code version: 1.127.0
- Ollama version: 0.40.11
- Docker version: 29.4.2
- Local model(s): gemma3:1b, qwen2.5:1.5b
- Hardware specifications: Intel i7-12800H, 32 GB DDR5 RAM, Nvidia GeForce MX550 (2GB)

### Key Learning

A reproducible environment is a prerequisite for meaningful technical experiments.

If the same application behaves differently across machines, the difference may arise from dependencies, hardware, model versions, configuration, or runtime conditions—not necessarily from the application code.

Documenting these details early makes future debugging and benchmarking more reliable.

## 3. Python Fundamentals

### 3.1 Data Structures

Reviewed Python lists, dictionaries, strings, numeric types, and Boolean values.

A useful observation was that lists and dictionaries naturally represent many business entities.

For example, an inventory record can be represented as:

```python
product = {
    "sku": "SRV-001",
    "description": "Demo Server",
    "quantity": 5,
    "unit_price": 450
}
```

A list of such dictionaries can represent a basic inventory collection without requiring a database.

**Learning:** Python's built-in data structures are sufficient for prototyping simple workflows, although production applications may require stronger validation, persistence, and concurrency controls.

### 3.2 Functions and Modular Design

Practiced separating business logic into reusable functions.

For example, inventory valuation, product lookup, and quotation generation can be implemented as independent functions.

**Learning:** Modular code is easier to test, understand, and reuse.

This becomes particularly relevant for AI agents because external tools exposed to an agent should ideally perform small, clearly defined operations.

### 3.3 Error Handling

Explored exceptions and basic error-handling patterns.

A quotation function should not silently proceed when a product does not exist or the requested quantity exceeds available stock.

Instead, it should return a controlled error or raise an appropriate exception.

**Learning:** Error handling is part of application correctness, not an optional improvement.

In future agentic applications, tool failures must be handled explicitly to avoid misleading the AI model or allowing an invalid workflow to continue.

### 3.4 Input Validation

Reviewed the importance of checking inputs before executing business logic.

Examples include:

- Rejecting negative quantities
- Handling missing product identifiers
- Checking stock availability
- Ensuring numeric values are valid

**Learning:** AI-generated requests should not be trusted automatically. The application must validate parameters independently of the model.

## 4. Git and GitHub

Established a Git-based workflow for tracking code changes and publishing experiments.

### Concepts Reviewed

- Local repositories and remote repositories
- Staging changes
- Commits and commit messages
- Pushing changes to GitHub
- Repository organization
- `.gitignore` and exclusion of local environment files

### Key Learning

Git is more than a backup mechanism.

A meaningful commit history provides traceability and helps explain how a project evolved.

For AI experiments, version control becomes especially valuable when comparing changes to prompts, model settings, evaluation datasets, or application architecture.

### Practical Observation

Generated outputs, virtual environments, credentials, and machine-specific files should not automatically be committed.

The repository should contain the source code, necessary configuration templates, documentation, and carefully selected experiment artifacts needed for reproducibility.

## 5. Python Virtual Environments and Dependencies

Explored the use of `venv` to isolate Python dependencies for individual projects.

A virtual environment helps prevent package conflicts between applications that may require different library versions.

For example:

```bash
python -m venv .venv
```

After activating the environment, dependencies can be installed using:

```bash
pip install -r requirements.txt
```

### Key Learning

A working application on one developer's computer does not guarantee that it will work elsewhere.

Dependency management, version pinning, environment configuration, and setup documentation are essential parts of reproducible engineering.

For future projects, dependency versions should be recorded and tested in a clean environment.

## 6. Local LLM Inference with Ollama

### 6.1 Understanding Local Inference

Explored the distinction between model training and model inference.

Training involves optimizing a model's parameters using data.

Inference involves using an already trained model to process input and generate output.

Ollama provides a convenient interface for downloading, managing, and running compatible models locally.

### Key Learning

Running a model locally gives greater control over the execution environment and can avoid sending prompts to an external hosted inference service.

However, local inference is still constrained by hardware capabilities, model size, available memory, and runtime configuration.

Local execution alone does not guarantee that an entire application is secure or private.

### 6.2 Model Size and Resource Requirements

Reviewed the significance of model parameter counts and quantization.

Smaller models generally require fewer computational resources than larger models, although actual memory use and performance also depend on quantization, context length, architecture, and runtime implementation.

**Learning:** Model selection is a trade-off involving capability, resource requirements, latency, and deployment constraints.

The largest available model is not automatically the most appropriate model for every application.

### 6.3 Programmatic Model Interaction

Explored how Python applications communicate with a locally running model through Ollama.

A basic model call involves:

1. Selecting the model.
2. Providing one or more messages.
3. Setting optional inference parameters.
4. Sending the request.
5. Reading and processing the response.

### Key Learning

A programmatic model interface is the foundation for building more complex AI systems.

The same basic request-response pattern can later be extended with retrieval, tool execution, structured outputs, workflow state, and application-level validation.

## 7. Initial Observations About LLM Behavior

The following are conceptual observations and questions that motivated the next stage of experimentation.

### Observation 1 — Fluent answers are not necessarily correct

Language models can produce convincing explanations even when the underlying information is incorrect or unavailable.

**Implication:** Output quality must be evaluated against evidence and explicit acceptance criteria.

### Observation 2 — Prompts influence model behavior

The wording and structure of instructions can affect how a model responds.

**Implication:** Prompt design should be treated as a configurable component that can be tested rather than a collection of informal tricks.

### Observation 3 — Model output is not equivalent to deterministic program output

Unlike ordinary business functions, generative models may produce different valid or invalid responses for similar requests.

**Implication:** AI applications require evaluation methods that accommodate variability while enforcing deterministic rules for critical operations.

### Observation 4 — A working demonstration is not proof of reliability

A model successfully answering one question does not establish that it can reliably handle an entire category of tasks.

**Implication:** Testing should use multiple questions, clearly defined success criteria, and repeated trials where appropriate.

These observations informed the design of the Week 02 LLM behavior evaluation.

## 8. Troubleshooting and Implementation Notes

The table below is a template for documenting actual issues encountered during setup. Replace these illustrative examples with verified experiences.

| Potential Issue | Possible Cause | Suggested Resolution |
|---|---|---|
| Python command not recognized | Python not on system PATH | Verify installation and interpreter configuration |
| Virtual environment fails to activate | Shell execution restrictions | Review the applicable shell policy or use another supported activation method |
| Ollama connection refused | Local service not running | Start Ollama and verify the local API |
| Model not found | Model not downloaded or incorrect tag | Check `ollama list` and pull the correct model |
| Python package import fails | Dependency installed in another environment | Verify the active interpreter and reinstall in the correct environment |

## 9. Key Takeaways

The most important lessons from the foundation stage are:

1. **AI engineering builds on conventional software engineering.** Good programming practices, testing, version control, and error handling remain essential.

2. **Reproducibility matters from the beginning.** Model versions, dependencies, hardware, and configuration details can materially influence experimental outcomes.

3. **Models should be treated as probabilistic components.** Their outputs require validation and should not be trusted merely because they appear plausible.

4. **Application logic must remain under programmatic control.** Critical business rules, permissions, and validations should not depend solely on model-generated text.

5. **Local inference provides a useful experimental environment.** It enables low-cost exploration and direct control over model configurations, subject to available hardware.

6. **Evidence is more valuable than demonstrations alone.** Systematic experiments are necessary to understand the capabilities and limitations of AI models.

## 10. Questions for Further Investigation

The foundation exercises raised several questions:

- How do different local LLMs compare on the same set of questions?
- Does a detailed system prompt improve answer quality?
- How do temperature settings influence response consistency?
- What is the relationship between response quality and latency?
- How can incorrect answers and hallucinations be identified systematically?
- How should AI application performance be measured?

These questions form the basis of the Week 02 evaluation experiments.

## 11. Transition to Week 02

Week 01 established the environment and programming foundation for practical AI experimentation.

Week 02 extends this work by introducing a structured evaluation harness that compares local models across prompting strategies and inference settings.

The next objective is to move from asking whether a model can generate an answer to investigating **how consistently and accurately it completes defined tasks**.

---

**Next module:** Week 02 — LLM Behavior Experiments

*AI Practitioner Journey — Learn → Build → Test → Measure → Document → Share*