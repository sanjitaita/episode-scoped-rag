import os
from pathlib import Path

import ollama
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen2.5:14b")
EMBED_MODEL = "nomic-embed-text"


def embed(text: str) -> list[float]:
    try:
        response = ollama.embed(model=EMBED_MODEL, input=text)
        return response["embeddings"][0]
    except AttributeError:
        response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
        return response["embedding"]


def chat(prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    options = {"temperature": temperature}

    try:
        response = ollama.chat(
            model=CHAT_MODEL, messages=messages, think=False, options=options
        )
    except ollama.ResponseError as error:
        if "think" not in str(error).lower():
            raise
        response = ollama.chat(model=CHAT_MODEL, messages=messages, options=options)

    return response["message"]["content"]
