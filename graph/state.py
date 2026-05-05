from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class TicketState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    ticket_text: str
    category: str
    confidence_score: float
    escalate: bool
    draft_reply: str
    final_response: str
    retrieved_context: str