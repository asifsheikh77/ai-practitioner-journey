import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from pathvalidate import sanitize_filename

from ollama import chat


# 1. Initialize the parser
parser = argparse.ArgumentParser(description="LLM Behavior Experiment Runner")

# 2. Add arguments
parser.add_argument("modelname", type=str, help="model name to use for the experiment")
parser.add_argument("-n", "--number", type=int, default=1, help="Nummber of times to run each question")

# 3. Parse the arguments
args = parser.parse_args()

MODEL = args.modelname

BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

clean_modelname = sanitize_filename(MODEL)

with QUESTIONS_FILE.open(encoding="utf-8") as f:
    questions = json.load(f)

strategies = {
    "direct": "Answer the user's question.",
    "careful": (
        "Follow the user's instructions precisely. "
        "Be accurate and concise. "
        "If you lack the information needed to answer, "
        "clearly say so rather than inventing details."
    ),
}

temperatures = [0.0, 0.7]

timestamp = datetime.now(timezone.utc).strftime(
    "%Y%m%d_%H%M%S"
)

output_file = RESULTS_DIR / f"{clean_modelname}_experiment_{timestamp}.csv"

fieldnames = [
    "question_id",
    "category",
    "question",
    "expected",
    "strategy",
    "temperature",
    "response",
    "latency_seconds",
    "status",
]

with output_file.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    for item in questions:
        for strategy, system_prompt in strategies.items():
            for temperature in temperatures:
                for i in range(1, args.number+1):

                    start = time.perf_counter()
                    answer = ""
                    status = "success"

                    try:
                        result = chat(
                            model=MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": system_prompt,
                                },
                                {
                                    "role": "user",
                                    "content": item["question"],
                                },
                            ],
                            options={
                                "temperature": temperature,
                                "seed": 42,
                            },
                        )

                        answer = result.message.content or ""

                    except Exception as error:
                        status = f"error: {error}"

                    latency = round(
                        time.perf_counter() - start, 3
                    )

                    writer.writerow({
                        "question_id": item["id"],
                        "category": item["category"],
                        "question": item["question"],
                        "expected": item["expected"],
                        "strategy": strategy,
                        "temperature": temperature,
                        "response": answer,
                        "latency_seconds": latency,
                        "status": status,
                    })

                    print(
                        f"Q{item['id']} | {strategy} | "
                        f"T={temperature} | {latency}s"
                    )

print(f"\nResults saved to: {output_file}")
