import uuid
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from langfuse.decorators import observe, langfuse_context

from api.models import (
    TicketSubmitRequest,
    TicketSubmitResponse,
    FollowUpRequest,
    FollowUpResponse
)
from graph.graph import graph
from guardrails import process_input
from observability.error_tracking import capture_exception

router = APIRouter()

# In-memory session store for now
# Day 12 replaces this with PostgreSQL
sessions: dict = {}


@router.post("/tickets/submit", response_model=TicketSubmitResponse)
@observe(name="api-submit-ticket")
async def submit_ticket(request: TicketSubmitRequest):
    # Run guardrails
    processed_ticket, guard_report = process_input(request.ticket)

    if guard_report["blocked"]:
        return TicketSubmitResponse(
            session_id="",
            category="",
            confidence_score=0.0,
            escalated=False,
            response="",
            pii_redacted=False,
            pii_types_found=[],
            blocked=True,
            block_reason=guard_report["block_reason"]
        )

    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    langfuse_context.update_current_trace(
        input={"ticket": processed_ticket},
        metadata={"session_id": session_id}
    )

    try:
        result = graph.invoke(
            {
                "ticket_text": processed_ticket,
                "messages": [],
                "category": "",
                "confidence_score": 0.0,
                "escalate": False,
                "draft_reply": "",
                "final_response": "",
                "retrieved_context": ""
            },
            config=config
        )
    except Exception as e:
        capture_exception(e, context={"session_id": session_id, "ticket": processed_ticket})
        raise HTTPException(status_code=500, detail="Pipeline error. Our team has been notified.")

    # Store session state for follow-ups
    sessions[session_id] = {
        "ticket": processed_ticket,
        "category": result["category"],
        "confidence_score": result["confidence_score"],
        "escalate": result["escalate"],
        "draft_reply": result["draft_reply"]
    }

    langfuse_context.update_current_trace(
        output={
            "category": result["category"],
            "escalated": result["escalate"]
        }
    )

    return TicketSubmitResponse(
        session_id=session_id,
        category=result["category"],
        confidence_score=result["confidence_score"],
        escalated=result["escalate"],
        response=result["final_response"],
        pii_redacted=guard_report["pii_redacted"],
        pii_types_found=guard_report["pii_detected"],
        blocked=False
    )


@router.post("/tickets/followup", response_model=FollowUpResponse)
async def followup(request: FollowUpRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Run guardrails on follow-up too
    processed_message, guard_report = process_input(request.message)

    if guard_report["blocked"]:
        raise HTTPException(
            status_code=400,
            detail=f"Message blocked: {guard_report['block_reason']}"
        )

    config = {"configurable": {"thread_id": request.session_id}}

    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=processed_message)]},
            config=config
        )
    except Exception as e:
        capture_exception(e, context={"session_id": request.session_id})
        raise HTTPException(status_code=500, detail="Pipeline error. Our team has been notified.")

    return FollowUpResponse(
        session_id=request.session_id,
        response=result["final_response"]
    )


@router.get("/tickets/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, **sessions[session_id]}