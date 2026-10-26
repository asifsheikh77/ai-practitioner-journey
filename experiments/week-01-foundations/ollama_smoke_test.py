
from ollama import chat

MODEL = "gemma3:1b"

def main():
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "Explain what an LLM is in one sentence."
            }
        ],
        options={"temperature": 0}
    )

    print("Model:", MODEL)
    print("Response:", response.message.content)


if __name__ == "__main__":
    main()
