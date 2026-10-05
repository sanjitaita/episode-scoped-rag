from app.ingest import get_collection, slugify


def episode_id(show: str, season: int, episode: int) -> str:
    return f"{slugify(show)}-s{season:02d}e{episode:02d}"


def _describe_miss(collection, show: str, season: int, episode: int) -> str:
    rows = collection.get(include=["metadatas"])["metadatas"]

    if not rows:
        return "No episodes have been ingested yet. Run: python -m app.ingest"

    shows = sorted({row["show"] for row in rows})
    if show not in shows:
        return f"Show '{show}' not found. Available: {', '.join(shows)}"

    seasons = sorted({row["season"] for row in rows if row["show"] == show})
    if season not in seasons:
        available = ", ".join(str(s) for s in seasons)
        return f"Season {season} not found for '{show}'. Available: {available}"

    episodes = sorted(
        row["episode"] for row in rows if row["show"] == show and row["season"] == season
    )
    contiguous = episodes == list(range(episodes[0], episodes[-1] + 1))
    available = (
        f"{episodes[0]}-{episodes[-1]}"
        if contiguous
        else ", ".join(str(e) for e in episodes)
    )
    return (
        f"Episode {episode} not found in '{show}' season {season}. "
        f"Available: {available}"
    )


def resolve_order(show: str, season: int, episode: int, collection=None) -> int:
    if collection is None:
        collection = get_collection()

    record = collection.get(
        ids=[episode_id(show, season, episode)], include=["metadatas"]
    )
    if record["ids"]:
        return record["metadatas"][0]["order"]

    raise ValueError(_describe_miss(collection, show, season, episode))