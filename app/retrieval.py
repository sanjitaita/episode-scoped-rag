from app.episodes import resolve_order
from app.ingest import get_collection
from app.llm import embed


class SpoilerFilterError(RuntimeError):
    pass


def retrieve(
    question: str,
    show: str,
    season: int,
    episode: int,
    k: int = 3,
    collection=None,
    embed_fn=embed,
) -> list[dict]:
    if collection is None:
        collection = get_collection()

    order = resolve_order(show, season, episode, collection=collection)

    results = collection.query(
        query_embeddings=[embed_fn(question)],
        where={"$and": [{"show": show}, {"order": {"$lte": order}}]},
        n_results=min(k, order),
    )

    matches = []
    for text, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        if meta["show"] != show or meta["order"] > order:
            raise SpoilerFilterError(
                f"Refusing to return S{meta['season']}E{meta['episode']} "
                f"({meta['show']}, order {meta['order']}) for a viewer watching "
                f"{show} through order {order}. Re-run: python -m app.ingest"
            )

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