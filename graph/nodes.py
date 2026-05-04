import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import TicketState
from prompts.classifier import CLASSIFIER_SYSTEM_PROMPT

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=os.getenv("GEMINI_API_KEY")
)


def classify_node(state: TicketState) -> dict:
    """Classifies the ticket and extracts structured data."""
    print("🔍 Classifying ticket...")

    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(content=f"Support ticket:\n\n{state['ticket_text']}")
    ]

    response = llm.invoke(messages)
    raw_output = response.content.strip()

    # Strip markdown fences if present
    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
        raw_output = raw_output.strip()

    result = json.loads(raw_output)

    return {
        "messages": [HumanMessage(content=state["ticket_text"]), response],
        "category": result["category"],
        "confidence_score": result["confidence_score"],
        "escalate": result["escalate"],
        "draft_reply": result["draft_reply"],
    }


def draft_node(state: TicketState) -> dict:
    """Refines the draft reply with full conversation context."""
    print("✍️  Drafting response...")

    refinement_prompt = f"""
    You previously classified this ticket as '{state['category']}' 
    with confidence {state['confidence_score']}.
    
    Your draft reply was:
    {state['draft_reply']}
    
    Review the conversation history and confirm this is the best response.
    Return only the final reply text, no JSON, no explanation.
    """

    messages = state["messages"] + [HumanMessage(content=refinement_prompt)]
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "final_response": response.content.strip(),
    }


def escalate_node(state: TicketState) -> dict:
    """Handles tickets that need human review."""
    print("🚨 Escalating to human agent...")

    reason = []
    if state["confidence_score"] < 0.7:
        reason.append(f"low confidence score ({state['confidence_score']})")
    if state["escalate"]:
        reason.append("flagged for escalation by classifier")

    escalation_message = f"""
--- ESCALATION REQUIRED ---
Ticket Category: {state['category'].upper()}
Reason: {', '.join(reason)}
Original Ticket: {state['ticket_text']}
Suggested Draft: {state['draft_reply']}
---------------------------
A human agent should review and respond to this ticket.
    """.strip()

    return {
        "final_response": escalation_message,
    }


def route_after_classify(state: TicketState) -> str:
    """Decides which node to go to after classification."""
    if state["escalate"] or state["confidence_score"] < 0.7:
        return "escalate"
    return "draft"