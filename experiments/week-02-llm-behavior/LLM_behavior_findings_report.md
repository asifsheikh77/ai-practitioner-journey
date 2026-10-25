# LLM Behavior Evaluation - Findings Report

**Project:** AI Practitioner Journey  
**Experiment:** Week 02 - LLM Behavior and Prompt Configuration  
**Evaluation Date:** 25 October 2026  
**Models Evaluated:** Qwen2.5 1.5B and Gemma 3 1B  
**Evaluation Type:** Exploratory comparative benchmark  
**Execution Environment:** Local inference using Ollama  
**Status:** Initial evaluation completed

---

## 1. Executive Summary

This experiment evaluated the response quality and inference latency of two locally hosted small language models, **Qwen2.5 1.5B** and **Gemma 3 1B**, under four prompting configurations.

The objective was to investigate how model selection, system prompt design, and temperature settings influence task completion and response quality.

Across the evaluated configurations, **Qwen2.5 1.5B demonstrated consistently stronger task performance than Gemma 3 1B**, achieving full-success rates of 85-95%, compared with 75-80% for Gemma 3 1B.

The highest-performing configuration was **Qwen2.5 1.5B with a direct prompt and temperature 0**, achieving:

- **Mean evaluation score:** 1.95 / 2
- **Full-success rate:** 95%
- **Mean response latency:** 1.151 seconds

However, the results also revealed that more elaborate system instructions did not necessarily improve task performance. In particular, the careful prompting strategy produced lower success rates than direct prompting in several configurations.

The experiment provides preliminary evidence that **model selection had a greater observed impact on task performance than either prompting strategy or temperature selection** within this test setup.

These findings should be interpreted as exploratory rather than conclusive, given the limited dataset, single execution per question and absence of repeated trials.

## 2. Evaluation Objectives

The experiment sought to answer five questions:

1. How do two relatively small language models compare on a common evaluation dataset?
2. Does a more explicit, accuracy-oriented system prompt improve response quality?
3. How does temperature influence task success?
4. What latency differences are observed across models and configurations?
5. Can a lightweight, reproducible evaluation workflow provide useful evidence for future AI application development?

## 3. Experimental Methodology

### 3.1 Models

Two locally hosted language models were evaluated:

| Model | Approximate parameter count | Inference platform |
|---|---:|---|
| Qwen2.5 | 1.5 billion | Ollama |
| Gemma 3 | 1 billion | Ollama |

### 3.2 Test Dataset

The evaluation used 20 questions covering five categories:

- Factual knowledge
- Basic reasoning
- Instruction following
- Handling uncertainty and missing information
- Text understanding

The same dataset was used for both models.

### 3.3 Experimental Configurations

Each model was evaluated under four conditions:

| Configuration | Prompt strategy | Temperature |
|---|---|---:|
| A | Direct | 0.0 |
| B | Direct | 0.7 |
| C | Careful | 0.0 |
| D | Careful | 0.7 |

The careful prompting strategy introduced additional instructions emphasizing accuracy, instruction adherence, and acknowledgment of uncertainty.

Each question was executed once per configuration, producing **80 responses per model and 160 responses overall**.

### 3.4 Evaluation Metrics

**Mean Score (/2)**

Average response quality using a three-level rubric:

- 2 - Fully correct and instruction-compliant
- 1 - Partially correct
- 0 - Incorrect or unsupported

**Full-Success Rate (%)**

Percentage of responses receiving the maximum score of 2.

**Mean Latency (seconds)**

Average elapsed time per model request, as measured by the experiment runner.

Latency reflects the observed local execution environment and should not be interpreted as a hardware-independent measure of model speed.

## 4. Evaluation Results

| Model | Configuration | Mean Score / 2 | Full Success | Mean Latency |
|---|---|---:|---:|---:|
| Qwen2.5 1.5B | Direct, T=0 | **1.95** | **95%** | 1.151 s |
| Qwen2.5 1.5B | Direct, T=0.7 | 1.90 | 90% | 0.916 s |
| Qwen2.5 1.5B | Careful, T=0 | 1.80 | 85% | 1.027 s |
| Qwen2.5 1.5B | Careful, T=0.7 | 1.90 | 90% | 1.003 s |
| Gemma 3 1B | Direct, T=0 | 1.65 | 75% | 1.939 s |
| Gemma 3 1B | Direct, T=0.7 | **1.70** | **80%** | 1.612 s |
| Gemma 3 1B | Careful, T=0 | 1.55 | 75% | 0.783 s |
| Gemma 3 1B | Careful, T=0.7 | 1.60 | 75% | **0.578 s** |

## 5. Key Findings

### Finding 1 - Qwen2.5 consistently outperformed Gemma 3 on task quality

Qwen2.5 achieved a higher mean score and full-success rate in all four matched configurations.

Averaged equally across configurations:

| Metric | Qwen2.5 1.5B | Gemma 3 1B |
|---|---:|---:|
| Mean evaluation score | 1.8875 / 2 | 1.625 / 2 |
| Full-success rate | 90.0% | 76.25% |
| Mean latency | 1.024 s | 1.228 s |

Qwen2.5 achieved a **13.75 percentage-point advantage in full-success rate** across the pooled test responses.

**Interpretation:** For the tasks represented in this dataset, Qwen2.5 delivered stronger overall performance despite having a relatively modest parameter count.

This result supports evaluating models against specific application requirements rather than assuming that models within a similar size category will behave equivalently.

### Finding 2 - Careful prompting did not consistently improve response quality

The expectation that more explicit instructions would improve model behavior was not supported consistently.

For Qwen2.5 at temperature 0, changing from direct to careful prompting reduced full success from 95% to 85%.

For Gemma 3 at temperature 0.7, careful prompting reduced full success from 80% to 75%.

Across both models and temperature settings, direct prompting achieved a pooled full-success rate of 85%, compared with 81.25% for careful prompting.

**Interpretation:** Additional system instructions are not automatically beneficial. Their impact may depend on the model, task category, wording and interaction with other generation settings.

The experiment does not establish why careful prompting performed worse. A question-level error analysis is required to identify possible causes.

**Practical implication:** Prompt engineering should be treated as an empirical optimization process, with changes evaluated against a stable test dataset.

### Finding 3 - Temperature effects were modest and model-dependent

Temperature adjustments produced different outcomes across the two models.

For Qwen2.5:

- Direct prompting declined from 95% to 90% full success when temperature increased from 0 to 0.7.
- Careful prompting improved from 85% to 90%.

For Gemma 3:

- Direct prompting improved from 75% to 80%.
- Careful prompting remained at 75%.

**Interpretation:** The results do not support a universal conclusion that lower temperatures always improve accuracy or that higher temperatures necessarily reduce reliability.

Because each condition was evaluated only once per question, observed differences may reflect generation variability.

Repeated trials are required before making stronger claims about temperature sensitivity.

### Finding 4 - Latency depended on both model and configuration

Qwen2.5 exhibited mean latencies between 0.916 and 1.151 seconds, whereas Gemma 3 ranged from 0.578 to 1.939 seconds.

The fastest observed configuration was Gemma 3 with careful prompting at temperature 0.7.

However, the fastest configuration was not the highest-performing configuration in terms of response quality.

The highest-quality configuration, Qwen2.5 with direct prompting at temperature 0, required an average of 1.151 seconds.

**Interpretation:** Latency and answer quality represent separate dimensions of model performance.

The variation in latency also suggests that additional controls are needed before drawing conclusions about relative inference efficiency.

Potential influences include model loading, hardware utilization, prompt and output lengths, runtime configuration and execution order.

### Finding 5 - A lightweight evaluation harness can reveal useful configuration differences

Despite its limited scale, the experiment identified observable differences in task success and response latency across models and prompting strategies.

The evaluation process demonstrates the value of:

- Using a consistent question dataset
- Defining explicit scoring criteria
- Testing multiple configurations
- Recording results systematically
- Separating observed outcomes from interpretations

**Interpretation:** A structured evaluation workflow is more informative than relying exclusively on informal model interactions or isolated demonstrations.

However, a larger and more representative dataset is necessary before using these results to select a model for production deployment.

## 6. Limitations

The following limitations affect the strength and generalizability of the findings.

**Limited sample size:** Each configuration was tested on only 20 questions. One additional successful response changes the full-success rate by five percentage points.

**Single execution per question:** The experiment does not quantify run-to-run variability or establish statistical confidence in observed differences.

**Simple task distribution:** The questions primarily evaluate foundational capabilities and may not represent complex enterprise workflows, multi-step reasoning or specialized domain requirements.

**Potential scoring subjectivity:** The three-level rubric involves human judgment. Category-specific scoring criteria and independent review would improve consistency.

**Uncontrolled inference conditions:** Hardware details, quantization, warm-up behavior, output lengths and system utilization were not included in the summary dataset.

**Limited model coverage:** Only two models were evaluated. Results cannot be generalized to other model families, sizes or deployment environments.

**No task-category breakdown:** Aggregate results do not reveal whether performance differences were driven by factual knowledge, reasoning, instruction following, uncertainty handling or text understanding.

## 7. Conclusions

The initial evaluation produced three primary conclusions.

First, **Qwen2.5 1.5B was the strongest model on the tested tasks**, outperforming Gemma 3 1B across every matched configuration.

Second, **more detailed prompting did not guarantee improved performance**. Direct prompting produced the strongest individual result, highlighting the importance of measuring prompt effectiveness rather than assuming it.

Third, **model performance must be assessed across multiple dimensions**. Accuracy, task completion, latency, consistency and reliability should be evaluated independently before making implementation decisions.

For this specific dataset, **Qwen2.5 1.5B with direct prompting at temperature 0 is the preferred baseline configuration for subsequent experiments**.

This is a provisional selection for further testing, not a recommendation for production deployment.

## 8. Recommended Next Steps

### Priority 1 - Repeat the experiments

Run each question at least five times per configuration to examine response variability.

Report mean success rates, variation across runs and uncertainty intervals where appropriate.

### Priority 2 - Perform question-level failure analysis

Identify the questions each model failed and classify the errors:

- Factual inaccuracy
- Reasoning failure
- Instruction violation
- Unsupported claim
- Incorrect handling of uncertainty

### Priority 3 - Improve latency measurement

Record hardware specifications, model quantization, token counts, warm-up status, execution order and Ollama timing metrics.

Measure median and percentile latency alongside the mean.

### Priority 4 - Expand the evaluation dataset

Increase the dataset to approximately 50-100 questions, with more challenging and representative tasks.

Include cases involving ambiguous instructions, conflicting information, structured outputs and multi-step reasoning.

### Priority 5 - Carry findings into the RAG project

Use the selected baseline model in the upcoming document-grounded question-answering application.

Introduce new evaluation dimensions, including retrieval relevance, citation correctness, faithfulness to source documents and appropriate abstention.

---

## 9. Final Assessment

This experiment represents an initial step toward a reproducible, evidence-based AI engineering practice.

Its primary value is not the ranking of two small language models, but the establishment of a systematic process for testing assumptions, measuring model behavior and documenting technical decisions.

Future experiments will extend this approach toward more realistic AI applications, with stronger controls, larger datasets and application-specific reliability criteria.

*All conclusions are limited to the supplied experimental results. No claims are made about performance on external benchmarks or production workloads.*

