import ollama

response = ollama.chat(
    model='llama3.2',
    messages=[
        {"role": "user", "content": "Tell me a fun fact about space."}
    ]
)

print(response['message']['content'])
