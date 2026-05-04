# test_retrieval.py
from dotenv import load_dotenv
load_dotenv()

from rag.embedder import embed_text
from rag.vectorstore import search

query = "I was charged twice and need a refund"
vector = embed_text(query)
results = search(vector, top_k=3)

for r in results:
    print(f"Score: {r['score']:.3f} | Source: {r['source']}")
    print(f"Text: {r['text'][:200]}")
    print("---")