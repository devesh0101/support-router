from sqlalchemy.orm import Session
from db.models import Ticket
import json
from datetime import datetime


class TicketService:
    @staticmethod
    def create_ticket(
        session_id: str,
        ticket_text: str,
        category: str,
        confidence_score: float,
        escalated: bool,
        draft_reply: str,
        final_response: str,
        retrieved_context: str = "",
        pii_detected: list = None,
        db: Session = None
    ) -> Ticket:
        """Create and store a new ticket."""
        ticket = Ticket(
            session_id=session_id,
            ticket_text=ticket_text,
            category=category,
            confidence_score=confidence_score,
            escalated=escalated,
            draft_reply=draft_reply,
            final_response=final_response,
            retrieved_context=retrieved_context,
            pii_detected=json.dumps(pii_detected or [])
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_ticket(session_id: str, db: Session = None) -> Ticket:
        """Fetch a ticket by session ID."""
        return db.query(Ticket).filter(Ticket.session_id == session_id).first()

    @staticmethod
    def update_ticket(session_id: str, final_response: str, db: Session = None) -> Ticket:
        """Update a ticket's response."""
        ticket = db.query(Ticket).filter(Ticket.session_id == session_id).first()
        if ticket:
            ticket.final_response = final_response
            ticket.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(ticket)
        return ticket

    @staticmethod
    def list_tickets(limit: int = 50, db: Session = None) -> list:
        """List all tickets."""
        return db.query(Ticket).order_by(Ticket.created_at.desc()).limit(limit).all()