# Week 02 — LLM Behavior Experiments

## Objective
Investigate how prompting strategies and temperature settings affect a local LLM.

## Model and Environment
- Model name and version: qwen2.5:1.5b & gemma3:1b
- Ollama version: 0.40.11
- Operating system: Windows 11 64bit
- CPU / GPU: 12th Gen Intel(R) Core(TM) i7-12800H (1.80 GHz) / NVIDIA GeForce MX550 (2 GB)
- RAM: 32GB DDR5

## Methodology
20 questions across five categories.
Two prompt strategies (Direct, Careful).
Two temperature settings (0,0.7).
80 primary responses.

## Prompt Strategies
Direct: Answer the user's question
Careful: - Follow the user's instructions precisely.
         - Be accurate and concise.
         - If you lack the information needed to answer, clearly say so rather than inventing details.


## How to Run
1. Install dependencies.
2. Download the model.
3. Run the experiment script.
4. Review the generated CSV.

## Results
Model	        Runs	Configuration	Mean score / 2	Full success	Mean latency
qwen2.5:1.5b	1	    Direct, T=0 	1.95 / 2	    95.00%	        1.151 s
qwen2.5:1.5b	1	    Direct, T=0.7	1.9 / 2	        90.00%	        0.916 s
qwen2.5:1.5b	1	    Careful, T=0	1.8 / 2	        85.00%	        1.027 s
qwen2.5:1.5b	1	    Careful, T=0.7	1.9 / 2	        90.00%	        1.0025 s
gemma3:1b   	1	    Direct, T=0	    1.65 / 2	    75.00%	        1.939 s
gemma3:1b	    1	    Direct, T=0.7	1.7 / 2	        80.00%	        1.612 s
gemma3:1b	    1	    Careful, T=0	1.55 / 2	    75.00%	        0.7833 s
gemma3:1b	    1	    Careful, T=0.7	1.6 /2	        75.00%	        0.578 s

## Findings
[see the detailed report in LLM_behavior_findings_report.md]

## Limitations
- Small test dataset
- 2 basic models
- Subjective grading
- Limited repeated trials
- Hardware-dependent latency

## Next Steps
Improve evaluations and build a RAG system.