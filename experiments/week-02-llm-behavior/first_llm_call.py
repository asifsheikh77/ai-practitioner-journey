from ollama import chat

MODEL = "qwen2.5:1.5b"

response = chat(
    model=MODEL,
    messages=[
        {"role": "user", 
         "content": "Explain what single agent vs. multiagent AI systems in a language a 10 year old will understand."
        }
    ],
    options={
        "temperature": 0,
    }
)

print("MODEL RESPONSE:")
print(response.message.content)