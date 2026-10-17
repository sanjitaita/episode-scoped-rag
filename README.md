# episode-scoped-rag

Spoiler-safe Q&A for TV shows: answers are built only from episodes the user has already watched.

Tell it how far you've watched, ask anything about the plot or characters, and it answers using
only what has aired up to that point. Nothing from later episodes reaches the model.

## How it works

The spoiler guarantee is enforced in the database query, not in the prompt.

```
question ──► embed ──► Chroma query
                         │
                         ├── where: show = X AND order <= watch point   ← the filter
                         │
                         └──► top matches ──► prompt ──► local LLM ──► answer
```

Every episode is stored with an `order` field: its position in the whole series, counting
straight through from the first episode. When you ask a question, the retrieval query excludes
every episode past your watch point **before** similarity search runs, so future episodes are
never scored, never ranked, and never returned. Asking the model nicely not to spoil is not
part of the design; it never sees the text in the first place.

`order` is written once, during ingestion, and read back from Chroma at query time. Ingestion
is the only thing that assigns it, so the number used by the filter can never drift from the
number stored alongside the episode.

### Retrieval

- The top **6** episodes by similarity are retrieved (`k` in `retrieval.py` and `answer.py`).
- The viewer's **most recent watched episode is always included**, even if it didn't rank in the
  top 6, so questions about "right now" have current context.
- Retrieved episodes are **sorted into story order** before the prompt is built, so the model
  reads them in the order they happened.
- After the query, every result is checked again against the watch point. Anything past it
  raises `SpoilerFilterError` instead of being returned.

Everything runs locally. No API keys, no per-query cost, and no episode text or question
leaves the machine.

### Stack

| Layer | Choice |
|---|---|
| Chat model | Ollama, default `qwen2.5:14b` (also tested with `qwen3.5:9b`), set in `.env` |
| Embeddings | `nomic-embed-text` via Ollama |
| Vector store | ChromaDB, persisted to `chroma_db/` |
| API | FastAPI |
| Frontend | Plain HTML, CSS, and JavaScript in `static/`, served by FastAPI |
| Episode data | hand-written per-episode summaries in `data/shows/` |

The episode summaries are written so that each one contains only what a viewer knows by the end
of that episode — no hindsight, no foreshadowing, and characters are never named before they
first appear. A summary written with hindsight would leak straight through the filter.

## Setup

Requires Python 3.11+ and [Ollama](https://ollama.com/download).

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
ollama pull nomic-embed-text
```

Name the virtual environment `venv` (not `.venv`); that's the name `.gitignore` excludes.

Pick your chat model by copying `.env.example` to `.env` and editing it
(e.g. `CHAT_MODEL=qwen2.5:14b` or `CHAT_MODEL=qwen3.5:9b`). Pull it with `ollama pull <model>`.
`.env` is gitignored, so each person can run a different model.

Then build the vector database:

```bash
python -m app.ingest
```

Re-run that whenever anything in `data/shows/` changes.

### Every new terminal session

```bash
cd path/to/episode-scoped-rag
source venv/bin/activate
```

Make sure Ollama is running (the llama icon in the menu bar, or `ollama list` responds).

## Running it

```bash
python -m uvicorn app.main:app --reload
```

- **<http://localhost:8000>**: the web app.
- **<http://localhost:8000/docs>**: an interactive page where you can call any endpoint directly.

`--reload` restarts the server whenever a Python file is saved. For changes to files in
`static/`, hard-refresh the browser (Cmd+Shift+R).

There is also a command-line client:

```bash
python -m app.ask --show "Breaking Bad" --season 1 --episode 2 \
  --question "Why did Walter start cooking meth?"
```

## Web app

1. **Home:** every show in the database appears as a poster tile.
2. **Picker:** choose the season and the last episode you've watched. A progress bar shows how far
   through the series that is. The choice is remembered per show in the browser.
3. **Chat:** ask questions. Each answer shows its episode citations (e.g. `S2·E11`) and the episodes
   it was drawn from. "Change" reopens the picker.

The current position lives in the URL (`#/ask/breaking-bad/3/5`), so refreshing, the back
button, and bookmarks all work.

Titles are never shown for episodes past the watch point. The picker shows episode numbers only.

### Answer modes: Quick and Deep

The chat has a **Quick | Deep** switch. The choice is remembered in the browser.

| | Quick | Deep |
|---|---|---|
| Prompt | Strict: only states what the summaries say, cites each fact, does not guess at motives | Lists 3–5 key facts first, then answers, and may infer motives the facts support |
| Best for | "Who is…", "What happened…" | "Why did…", "What is he thinking…" |
| Trade-off | Fast, but won't explain *why* when the summaries don't state it outright | Slower, and can vary from run to run |

Deep answers are shown with the answer first and the key facts in a collapsible box underneath.

Both modes use the same retrieval, so spoiler safety is identical in both. The difference is only
how much interpretation the model is allowed.

**Model thinking is turned off** (`think=False` in `llm.py`). With `qwen3.5:9b`, built-in thinking
took 3–5+ minutes per answer and often filled the context window before writing anything. Deep mode
gets most of the benefit by asking for key facts before the answer instead. Models without a
thinking mode (like `qwen2.5:14b`) fall back automatically.

The context window is set to 8192 tokens (`num_ctx` in `llm.py`). The default 4096 was too small
once longer prompts and Deep answers were involved.

### Posters

Show posters go in `static/posters/`, named after the show in lowercase with dashes:
`Breaking Bad` → `static/posters/breaking-bad.jpg`. The file must be `.jpg` (not `.jpeg`).
A 2:3 portrait image works best. Shows without a poster get a styled title card instead.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /api/shows` | Shows present in the database |
| `GET /api/shows/{show}/seasons` | Seasons and their episode numbers |
| `POST /api/ask` | `{show, season, episode, question, mode}` → `{answer, sources}` |

`mode` is optional: `"quick"` (default) or `"deep"`. Any other value returns 422.

`/seasons` returns episode numbers only, never titles. Titles are themselves mild spoilers
(*Ozymandias*, *Face Off*), and this endpoint has to describe episodes the viewer has not
reached. Titles appear only in the `sources` of an answer, which are always behind the watch
point.

Errors: unknown show or episode returns 404 naming what is available, invalid input returns 422,
and an unreachable Ollama returns 503.

## Verifying spoiler safety

Six adversarial prompts, run through **POST /api/ask** at <http://localhost:8000/docs>.
They probe the failure modes that matter — not just whether it answers, but whether it refuses
cleanly when it should. All six pass with `qwen2.5:14b`. Run them in both modes by adding
`"mode": "quick"` or `"mode": "deep"` to the request.

**1. Control — it should answer**

```json
{"show":"Breaking Bad","season":1,"episode":3,"question":"What happened to Krazy-8?"}
```

Expected: describes the killing, cites `[S1E3]`. A refusal here would mean retrieval is too narrow.

**2. Flat refusal for an unintroduced character**

```json
{"show":"Breaking Bad","season":1,"episode":2,"question":"Who is Gus Fring?"}
```

Expected: `That hasn't come up in what you've watched.` Any mention of Los Pollos Hermanos would
be training-data leakage, since Gus does not appear until S2E11.

**3. False premise**

```json
{"show":"Breaking Bad","season":1,"episode":2,"question":"Why did Walter poison Brock?"}
```

Brock is poisoned in S4E13. Expected: a refusal that neither confirms nor denies the event.
Answering "that hasn't happened yet" would itself confirm that it happens — the subtle failure
this tests for.

**4. Boundary A/B**

```json
{"show":"Breaking Bad","season":1,"episode":5,"question":"Who is Tuco Salamanca?"}
```

Then the identical question with `"episode": 6`. Tuco first appears in S1E6. Expected: refusal at
E5, a real answer at E6. Same question, one episode apart, different answers.

**5. No forward-teasing**

```json
{"show":"Breaking Bad","season":2,"episode":9,"question":"How is Walter's cancer going?"}
```

Expected: reports the remission and stops. Phrases like "for now" or "things take a turn" leak
the shape of the future without naming it, and count as a failure.

**6. Multi-part question**

```json
{"show":"Breaking Bad","season":2,"episode":5,"question":"Who is Jesse's neighbor, and how does Hank get shot?"}
```

Expected: answers the first half, refuses the second (Hank is shot in S3E7) rather than refusing
or answering both.

If a response leaks but the `sources` in that same response are all behind the watch point, the
retrieval filter did its job and the model ignored its instructions — a prompt or model-size
problem, not a code one.

## Project layout

```
app/
  main.py        FastAPI app and routes; also serves the web app
  models.py      Pydantic request/response schemas
  ingest.py      Reads data/shows/ -> embeds -> stores in Chroma
  episodes.py    Watch-point lookup and show/season listings
  retrieval.py   The spoiler filter, latest-episode guarantee, story-order sort
  answer.py      Quick and Deep prompts, prompt construction, the grounded answer
  ask.py         Command-line client
  llm.py         Ollama wrapper (chat + embeddings, model from .env)
static/
  index.html     Page shell
  styles.css     All styling
  logo.svg       Logo and favicon
  posters/       Show posters (<show-slug>.jpg)
  js/
    main.js      Routing between home and chat (URL hash)
    api.js       Calls to the FastAPI endpoints
    home.js      Show tiles
    picker.js    Season/episode picker
    chat.js      Chat view and the Quick/Deep switch
    util.js      Shared helpers
data/shows/      Per-episode summaries, one JSON file per show
chroma_db/       Generated by ingestion; gitignored
```

## Adding a show

Create `data/shows/<show>.json`:

```json
{
  "show": "Show Name",
  "episodes": [
    {"season": 1, "episode": 1, "title": "Pilot", "summary": "..."}
  ]
}
```

Write each summary using only what a viewer knows by the end of that episode, then re-run
`python -m app.ingest`. Add a poster at `static/posters/<show-name-with-dashes>.jpg`.

## Limitations

- **The guarantee covers retrieval, not the model's memory.** The filter makes it impossible for
  future episode text to reach the model. It cannot erase what the model already learned about a
  popular show during training. Grounding instructions and a low temperature keep it in line, and
  the checks above are how that behaviour is verified rather than assumed.
- **Small local models misread sometimes.** Answers can merge two separate events or attach a
  detail to the wrong person or episode, even though the right text was retrieved. Quick mode keeps
  this low by not interpreting; Deep mode can still vary from run to run. Citations and the source
  list let the reader check.
- **Retrieval can include loosely related episodes,** which adds noise to the prompt. Reranking or a
  similarity cutoff would help.
- Broad questions like "what has happened so far?" draw on at most 6–7 episodes, which may not be
  enough for a full recap. Rolling season-level summaries would fix this.
- The summaries describe *what* happens more than *why*, which limits how deeply even Deep mode
  can explain motives.
- Each question is independent; there is no conversation history yet.
