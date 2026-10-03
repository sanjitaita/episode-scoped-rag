import json
import re
from pathlib import Path

import chromadb

from app.llm import embed

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "shows"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "episodes"


def slugify(name: str) -> str:
    """'Breaking Bad' -> 'breaking-bad' (used to build readable ids)."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_shows(data_dir: Path = DATA_DIR) -> list[dict]:
    records = []

    for path in sorted(data_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        show = payload["show"]

        episodes = sorted(
            payload["episodes"], key=lambda ep: (ep["season"], ep["episode"])
        )

        for order, ep in enumerate(episodes, start=1):
            records.append(
                {
                    "id": f"{slugify(show)}-s{ep['season']:02d}e{ep['episode']:02d}",
                    "show": show,
                    "season": ep["season"],
                    "episode": ep["episode"],
                    "title": ep["title"],
                    "order": order,
                    "summary": ep["summary"],
                }
            )

    return records


def get_collection(chroma_dir: Path = CHROMA_DIR):
    """Open (or create) the persistent Chroma collection."""
    client = chromadb.PersistentClient(path=str(chroma_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        # Cosine similarity is the right measure for text embeddings.
        # Chroma defaults to squared L2, so set this explicitly.
        metadata={"hnsw:space": "cosine"},
    )


def ingest(records: list[dict], collection, embed_fn=embed) -> None:
    """Embed each episode summary and upsert it into Chroma."""
    ids, documents, embeddings, metadatas = [], [], [], []

    for i, record in enumerate(records, start=1):
        # The text we embed and later show the chat model.
        document = f"{record['title']}\n\n{record['summary']}"

        print(
            f"  [{i}/{len(records)}] "
            f"S{record['season']}E{record['episode']} {record['title']}"
        )

        ids.append(record["id"])
        documents.append(document)
        embeddings.append(embed_fn(document))
        metadatas.append(
            {
                "show": record["show"],
                "season": record["season"],
                "episode": record["episode"],
                "title": record["title"],
                "order": record["order"],
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def smoke_test(collection, embed_fn=embed) -> None:
    question = "Why did Walter start cooking meth?"
    watched_order = 2

    results = collection.query(
        query_embeddings=[embed_fn(question)],
        where={
            "$and": [
                {"show": "Breaking Bad"},
                {"order": {"$lte": watched_order}},
            ]
        },
        n_results=3,
    )

    print(f'\nSmoke test -- "{question}" (watched through order {watched_order})')
    for meta, distance in zip(results["metadatas"][0], results["distances"][0]):
        print(
            f"  S{meta['season']}E{meta['episode']} {meta['title']}"
            f"  (order {meta['order']}, distance {distance:.3f})"
        )

    leaked = [m for m in results["metadatas"][0] if m["order"] > watched_order]
    print("  LEAK DETECTED" if leaked else "  OK: nothing past the watch point")


if __name__ == "__main__":
    records = load_shows()
    print(f"Loaded {len(records)} episodes from {DATA_DIR}")

    collection = get_collection()
    ingest(records, collection)

    print(f"\nStored {collection.count()} episodes in '{COLLECTION_NAME}'")
    smoke_test(collection)