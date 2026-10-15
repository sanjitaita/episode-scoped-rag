from app.episodes import episode_id, resolve_order
from app.ingest import get_collection
from app.llm import embed


class SpoilerFilterError(RuntimeError):
    pass


def retrieve(
    question: str,
    show: str,
    season: int,
    episode: int,
    k: int = 6,
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

    found = False;
    for match in matches:
        if match["order"] == order:
            found = True;
            break;

    if not found:
        latest = collection.get(
            ids=[episode_id(show, season, episode)],
            include=["documents", "metadatas"],
        )

        latest_meta = latest["metadatas"][0]
        matches.append(
            {
                "text": latest["documents"][0],
                "title": latest_meta["title"],
                "season": latest_meta["season"],
                "episode": latest_meta["episode"],
                "order": latest_meta["order"],
                "distance": None,
            }
        )
        
    matches.sort(key=lambda match: match["order"])

    return matches