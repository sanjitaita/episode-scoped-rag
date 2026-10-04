from app.episodes import resolve_order
from app.ingest import get_collection
from app.llm import embed


def retrieve(question: str, show: str, season: int, episode: int, k: int = 3) -> list[dict]:
    order = resolve_order(show, season, episode)
    collection = get_collection()
    query_vector = embed(question)

    results = collection.query(
        query_embeddings=[query_vector],
        where={"$and": [{"show": show}, {"order": {"$lte": order}}]},
        n_results=k,
    )

    matches = []
    for text, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        matches.append(
            {
                "text": text,
                "title": meta["title"],
                "season": meta["season"],
                "episode": meta["episode"],
                "order": meta["order"],
                "distance": distance,
            }
        )

    return matches
