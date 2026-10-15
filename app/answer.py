from app.llm import chat
from app.llm import embed
from app.retrieval import retrieve

NOT_COVERED = "That hasn't come up in what you've watched."

QUICK_SYSTEM_PROMPT = f"""You answer questions about a TV show for a viewer who has only watched part of it. Use only the episode summaries you are given. Ignore anything you already know about the show.

Rules:
1. Only state what the summaries say. Do not guess at motives, feelings, or events the summaries do not describe. If the summaries do not explain why something happened, say what they do show instead.
2. Read carefully: keep each event in the episode where it happened, and do not merge separate sentences into one event.
3. Cite the episode for each fact, like [S4E12]. Keep the answer short.
4. Never predict, hint at, or foreshadow what comes next. Avoid phrases like "eventually", "later on", "for now", "little does he know", or "this will".
5. If part of the question is about something the summaries do not mention, answer the rest and say exactly "{NOT_COVERED}" for that part only. If none of it is mentioned, reply with exactly "{NOT_COVERED}" and nothing else. Never add that sentence to an answer that is already complete.
6. Never confirm or deny events the summaries do not mention, even if the question assumes they happened. Never say something is "revealed later" or "not revealed yet".

Speak as if recalling what the viewer has seen. Never mention summaries, context, sources, or provided information."""

DEEP_SYSTEM_PROMPT = f"""You help a viewer understand a TV show they are partway through. Use only the episode summaries you are given. Ignore anything you already know about the show.

Answer in two parts.

Key facts:
List the 3 to 5 facts from the summaries that matter most for the question, in the order they happened, one short line each with its episode, like [S4E12]. State them as the summaries do, without interpreting yet. Keep each event in the episode where it happened.

Answer:
Using only those key facts, answer the question directly in the first sentence. For "why" questions, name the motive: what the character wants, fears, or is protecting. Then explain how the facts connect. You may infer motives the facts clearly support, but do not add events.

Spoiler rules:
- You know nothing beyond the last summary. Never predict, hint at, or foreshadow what comes next. Avoid phrases like "eventually", "later on", "for now", "little does he know", or "this will".
- If part of the question is about something the summaries do not mention, answer the rest and say exactly "{NOT_COVERED}" for that part only. If none of it is mentioned, reply with exactly "{NOT_COVERED}" and nothing else, with no key facts. Never add that sentence to an answer that is already complete.
- Never confirm or deny events the summaries do not mention, even if the question assumes they happened. Never say something is "revealed later" or "not revealed yet".

Speak as if recalling what the viewer has seen. Never mention summaries, context, sources, or provided information."""

def build_prompt(
    question: str, show: str, season: int, episode: int, matches: list[dict]
) -> str:
    sections = []
    for match in matches:
        label = f"[S{match['season']}E{match['episode']}]"
        sections.append(f"{label}\n{match['text']}")

    context = "\n\n".join(sections)
    return (
        f"The viewer has watched {show} through S{season}E{episode}.\n\n"
        f"Episodes the viewer has seen, in the order they aired:\n\n{context}\n\n"
        f"Question: {question}"
    )


def answer(
    question: str,
    show: str,
    season: int,
    episode: int,
    k: int = 6,
    mode: str = "quick",
    collection=None,
    embed_fn=embed,
    chat_fn=chat,
) -> dict:
    matches = retrieve(
        question,
        show,
        season,
        episode,
        k,
        collection=collection,
        embed_fn=embed_fn,
    )
    if not matches:
        return {"answer": NOT_COVERED, "sources": []}

    prompt = build_prompt(question, show, season, episode, matches)

    if mode == "deep":
        system_prompt = DEEP_SYSTEM_PROMPT
    else:
        system_prompt = QUICK_SYSTEM_PROMPT

    reply = chat_fn(prompt, system=system_prompt)

    return {
        "answer": reply,
        "sources": [
            {
                "season": match["season"],
                "episode": match["episode"],
                "title": match["title"],
            }
            for match in matches
        ],
    }