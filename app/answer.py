from app.llm import chat
from app.llm import embed
from app.retrieval import retrieve

NOT_COVERED = "That hasn't come up in what you've watched."

SYSTEM_PROMPT = f"""You answer questions about a TV show for a viewer who has only watched part of it.

Rules:
1. Use only the episode summaries provided. Ignore anything you already know about the show.
2. You do not know what happens after the provided episodes. Never predict, hint at, or foreshadow future events. Avoid forward-looking phrases like "eventually", "later on", "for now", "little does he know", or "this will".
3. Start with the evidence: what happened, citing episodes in brackets like [S1E5].
4. If the question asks for opinion or interpretation, add a short interpretation based only on that evidence.
5. If a question has several parts, answer the parts the summaries cover. For any part they do not cover, say exactly: "{NOT_COVERED}"
6. If none of the question is covered, reply with exactly "{NOT_COVERED}" and nothing else.
7. Never confirm or deny events the summaries do not mention, even if the question assumes they happened.
8. Never mention "summaries", "context", or "provided information". Speak as if recalling what the viewer has seen.
9. Never say something is "revealed later" or "not revealed yet"."""


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
        f"Relevant episode summaries:\n\n{context}\n\n"
        f"Question: {question}"
    )


def answer(
    question: str,
    show: str,
    season: int,
    episode: int,
    k: int = 3,
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
    reply = chat_fn(prompt, system=SYSTEM_PROMPT)

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