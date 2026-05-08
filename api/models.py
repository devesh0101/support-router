from pydantic import BaseModel
from typing import Optional


class TicketSubmitRequest(BaseModel):
    ticket: str
    session_id: Optional[str] = None  # optional — client can provide their own


class TicketSubmitResponse(BaseModel):
    session_id: str
    category: str
    confidence_score: float
    escalated: bool
    response: str
    pii_redacted: bool
    pii_types_found: list[str]
    blocked: bool
    block_reason: Optional[str] = None


class FollowUpRequest(BaseModel):
    session_id: str
    message: str


class FollowUpResponse(BaseModel):
    session_id: str
    response: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    llm: str