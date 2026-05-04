import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import TicketState
from prompts.classifier import CLASSIFIER_SYSTEM_PROMPT

from rag.embedder import embed_text
from rag.vectorstore import search

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


def retrieve_node(state: TicketState) -> dict:
    """Retrieves relevant support docs from Qdrant based on the ticket."""
    print("📚 Retrieving relevant context...\n")

    query_vector = embed_text(state["ticket_text"])
    results = search(query_vector, top_k=3)

    if not results:
        return {"retrieved_context": "No relevant documentation found."}

    # Format retrieved chunks into a readable context block
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(
            f"[Source {i}: {r['source']} | Relevance: {r['score']:.2f}]\n{r['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)
    print(f"Retrieved {len(results)} relevant chunks.\n")

    return {"retrieved_context": context}

def draft_node(state: TicketState) -> dict:
    """Drafts a reply grounded in retrieved documentation."""
    print("✍️  Drafting response...\n")

    context_section = ""
    if state.get("retrieved_context"):
        context_section = f"""
Relevant documentation retrieved for this ticket:

{state['retrieved_context']}

Use the above documentation to ground your response. 
Only use information present in the docs — do not invent policies or procedures.
"""

    refinement_prompt = f"""
You have classified this ticket as '{state['category']}' 
with confidence {state['confidence_score']}.

Your initial draft was:
{state['draft_reply']}

{context_section}

Now write a final, polished reply to the customer.
- Be empathetic and professional
- Reference specific information from the documentation where relevant
- Keep it concise — no more than 3-4 sentences
- Return only the reply text, nothing else
    """.strip()

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


def followup_node(state: TicketState) -> dict:
    """Handles follow-up questions after initial classification."""
    print("💬 Processing follow-up...\n")

    # Build context summary for the model
    context = f"""
You are a helpful support assistant. You have already processed a support ticket.

Here is what you know:
- Original ticket: {state['ticket_text']}
- Category: {state['category']}
- Confidence score: {state['confidence_score']}
- Escalation required: {state['escalate']}
- Your drafted reply was: {state['draft_reply']}

Now answer the user's follow-up question or fulfill their request.
If they ask you to rewrite or improve the reply, return only the new reply text.
If they ask a question, answer it directly and concisely.
    """.strip()

    messages = [SystemMessage(content=context)] + state["messages"]
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "final_response": response.content.strip(),
    }


def route_entry(state: TicketState) -> str:
    """
    Routes to classify on first run.
    Routes to followup if ticket already classified.
    """
    if state.get("category"):
        return "followup"
    return "classify"