import os
import sys
import uuid
from pathlib import Path
from rag.embedder import embed_batch
from rag.vectorstore import create_collection_if_not_exists, upsert_documents
from dotenv import load_dotenv

load_dotenv()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Simple sliding window chunker.
    chunk_size: characters per chunk
    overlap: how many characters carry over to next chunk
    Overlap prevents losing context at chunk boundaries.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap

    return chunks


def ingest_directory(docs_path: str):
    path = Path(docs_path)
    all_chunks = []
    all_metadata = []

    for file in path.glob("**/*.md"):
        print(f"Processing: {file.name}")
        content = file.read_text(encoding="utf-8")
        chunks = chunk_text(content)

        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({
                "source": file.name,
                "text": chunk
            })

    print(f"Total chunks to embed: {len(all_chunks)}")

    # Embed in batches
    print("Embedding chunks...")
    vectors = embed_batch(all_chunks)

    # Build points for Qdrant
    points = []
    for i, (vector, metadata) in enumerate(zip(vectors, all_metadata)):
        points.append({
            "id": i + 1,
            "vector": vector,
            "payload": metadata
        })

    # Create collection and store
    create_collection_if_not_exists()
    upsert_documents(points)
    print(f"Successfully ingested {len(points)} chunks into Qdrant.")


if __name__ == "__main__":
    docs_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_docs"
    ingest_directory(docs_path)