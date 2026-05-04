import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


def get_embedder():
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )


def embed_text(text: str) -> list[float]:
    embedder = get_embedder()
    return embedder.embed_query(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    embedder = get_embedder()
    return embedder.embed_documents(texts)