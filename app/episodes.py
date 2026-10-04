from functools import lru_cache

from app.ingest import load_shows


@lru_cache(maxsize=1)
def episode_index():
    records = load_shows()
    index = {}
    for record in records:
        name = record["show"]
        season = record["season"]
        episode = record["episode"]
        key = (name, season, episode)
        index[key] = record
    return index


def resolve_order(show: str, season: int, episode: int) -> int:
    key = (show, season, episode)
    index = episode_index()
    if key in index:
        return index[key]["order"]
    names = set()
    seasons = set()
    episodes = set()
    for k in index:
        names.add(k[0])
        if k[0] == show:
            seasons.add(k[1])
        if k[0] == show and k[1] == season:
            episodes.add(k[2])

    if show not in names:
        raise ValueError(f"Show '{show}' not found in index")
    if season not in seasons:
        raise ValueError(f"Season '{season}' not found in index for show '{show}'")
    raise ValueError(f"Episode '{episode}' not found in index for show '{show}' season '{season}'")