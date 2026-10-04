# episode-scoped-rag

Spoiler-safe Q&A for TV shows: answers are built only from episodes the user has already watched.

## Setup (once)

Requires Python 3.11+ and [Ollama](https://ollama.com/download).

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull nomic-embed-text
python -m app.ingest
```

Pick your chat model by copying `.env.example` to `.env` and editing it (e.g. `CHAT_MODEL=qwen3.5:9b`). Pull that model with `ollama pull <model>`. `.env` is gitignored, so each person can use a different model.

## Every new terminal session

Activate the virtual environment before running anything:

```bash
cd path/to/episode-scoped-rag
source venv/bin/activate
```

Your prompt should start with `(venv)`. Run `deactivate` to leave it.

Run modules from the repo root with `python -m`, e.g. `python -m app.ingest`.
