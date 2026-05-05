import os
import sys
import uuid
from pathlib import Path
from rag.embedder import embed_batch
from rag.vectorstore import create_collection_if_not_exists, upsert_documents
from dotenv import load_dotenv
import re

load_dotenv()


import re

def chunk_text(text: str, max_chunk_size: int = 600, overlap_sentences: int = 1) -> list[str]:
    """
    Sentence-aware chunker.
    - Splits on sentence boundaries instead of raw character count
    - Keeps section headers attached to their first sentence
    - Overlaps by N sentences to preserve cross-boundary context
    """
    # Split into sentences (handles . ? ! and newlines)
    sentences = re.split(r'(?<=[.!?])\s+|\n{2,}', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        if current_length + sentence_length > max_chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep last N sentences for overlap
            current_chunk = current_chunk[-overlap_sentences:]
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

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