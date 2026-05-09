import uuid
import json
from fastapi import APIRouter, HTTPException, Depends
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from api.models import (
    TicketSubmitRequest,
    TicketSubmitResponse,
    FollowUpRequest,
    FollowUpResponse
)
from graph.graph import graph
from guardrails import process_input
from observability.error_tracking import capture_exception
from db.models import get_db
from db.service import TicketService
from langfuse.decorators import observe, langfuse_context

router = APIRouter()


@router.post("/tickets/submit", response_model=TicketSubmitResponse)
@observe(name="api-submit-ticket")
async def submit_ticket(request: TicketSubmitRequest, db: Session = Depends(get_db)):
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

    # Store in database
    ticket = TicketService.create_ticket(
        session_id=session_id,
        ticket_text=processed_ticket,
        category=result["category"],
        confidence_score=result["confidence_score"],
        escalated=result["escalate"],
        draft_reply=result["draft_reply"],
        final_response=result["final_response"],
        retrieved_context=result.get("retrieved_context", ""),
        pii_detected=guard_report["pii_detected"],
        db=db
    )

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
async def followup(request: FollowUpRequest, db: Session = Depends(get_db)):
    # Check if session exists
    ticket = TicketService.get_ticket(request.session_id, db=db)
    if not ticket:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Run guardrails on follow-up
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

    # Update ticket with new response
    TicketService.update_ticket(
        request.session_id,
        result["final_response"],
        db=db
    )

    return FollowUpResponse(
        session_id=request.session_id,
        response=result["final_response"]
    )


@router.get("/tickets/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Fetch a ticket session."""
    ticket = TicketService.get_ticket(session_id, db=db)
    if not ticket:
        raise HTTPException(status_code=404, detail="Session not found.")

    pii_list = json.loads(ticket.pii_detected) if ticket.pii_detected else []

    return {
        "session_id": ticket.session_id,
        "ticket": ticket.ticket_text,
        "category": ticket.category,
        "confidence_score": ticket.confidence_score,
        "escalated": ticket.escalated,
        "response": ticket.final_response,
        "pii_detected": pii_list,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat()
    }


@router.get("/tickets/list")
async def list_tickets(limit: int = 50, db: Session = Depends(get_db)):
    """List all tickets."""
    tickets = TicketService.list_tickets(limit=limit, db=db)
    return {
        "count": len(tickets),
        "tickets": [
            {
                "session_id": t.session_id,
                "category": t.category,
                "escalated": t.escalated,
                "created_at": t.created_at.isoformat()
            }
            for t in tickets
        ]
    }