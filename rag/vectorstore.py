import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "support_docs")
VECTOR_SIZE = 3072  # text-embedding-004 output dimension


def get_client() -> QdrantClient:
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


def create_collection_if_not_exists():
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


def upsert_documents(points: list[dict]):
    client = get_client()
    qdrant_points = [
        PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload=p["payload"]
        )
        for p in points
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=qdrant_points)


def search(query_vector: list[float], top_k: int = 3, min_score: float = 0.60) -> list[dict]:
    client = get_client()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        score_threshold=min_score
    )
    return [
        {
            "text": r.payload.get("text", ""),
            "source": r.payload.get("source", ""),
            "score": r.score
        }
        for r in results.points
    ]