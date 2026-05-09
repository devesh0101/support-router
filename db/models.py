from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    session_id = Column(String, primary_key=True)
    ticket_text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    escalated = Column(Boolean, default=False)
    draft_reply = Column(Text)
    final_response = Column(Text, nullable=False)
    retrieved_context = Column(Text)
    pii_detected = Column(String)  # JSON string of list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# SQLite database setup
DATABASE_URL = "sqlite:///./support_router.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()