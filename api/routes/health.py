from fastapi import APIRouter
from api.models import HealthResponse
from qdrant_client import QdrantClient
import os

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    # Check Qdrant
    try:
        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        client.get_collections()
        qdrant_status = "ok"
    except Exception:
        qdrant_status = "unreachable"

    # LLM check is lightweight — just confirm env var is set
    llm_status = "ok" if os.getenv("GEMINI_API_KEY") else "missing api key"

    overall = "healthy" if qdrant_status == "ok" and llm_status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        qdrant=qdrant_status,
        llm=llm_status
    )