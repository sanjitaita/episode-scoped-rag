import ollama

CHAT_MODEL = "qwen2.5:14b"
EMBED_MODEL = "nomic-embed-text"


def embed(text: str) -> list[float]:
    try:
        response = ollama.embed(model=EMBED_MODEL, input=text)
        return response["embeddings"][0]
    except AttributeError:
        response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
        return response["embedding"]


def chat(prompt: str) -> str:
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]