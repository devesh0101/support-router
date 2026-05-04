from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict




class TicketState(TypedDict):
    # Full conversation history - add_messages handles appending automatically
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Ticket analysis results
    ticket_text: str
    category: str
    confidence_score: float
    escalate: bool
    draft_reply: str
    
    # Final output to show the user
    final_response: str

    retrieved_context: str