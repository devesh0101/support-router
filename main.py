from dotenv import load_dotenv
load_dotenv()

import uuid
from langchain_core.messages import HumanMessage
from graph.graph import graph
from langfuse.decorators import observe, langfuse_context
from observability.tracer import langfuse
from observability.error_tracking import init_sentry, capture_exception
from guardrails import process_input

# Initialize Sentry at startup
init_sentry()


@observe(name="support-ticket-session")
def process_ticket(ticket: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}

    langfuse_context.update_current_trace(
        input={"ticket": ticket},
        metadata={"thread_id": thread_id}
    )

    result = graph.invoke(
        {
            "ticket_text": ticket,
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

    langfuse_context.update_current_trace(
        output={
            "category": result["category"],
            "escalated": result["escalate"],
            "final_response": result["final_response"]
        }
    )

    return result


def main():
    print("Support Ticket Router")
    print("=" * 40)
    print("Paste your ticket below. Press Enter twice when done.\n")

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    raw_ticket = "\n".join(lines)

    if not raw_ticket.strip():
        print("No ticket provided.")
        return

    # Run guardrails before anything else
    print("\n🛡️  Running security checks...\n")
    processed_ticket, guard_report = process_input(raw_ticket)

    if guard_report["blocked"]:
        print(f"❌ Ticket blocked: {guard_report['block_reason']}")
        print("This request cannot be processed.")
        return

    if guard_report["pii_redacted"]:
        print(f"⚠️  PII detected and redacted: {', '.join(guard_report['pii_detected'])}")

    thread_id = str(uuid.uuid4())

    print("Processing...\n")

    try:
        result = process_ticket(processed_ticket, thread_id)
    except Exception as e:
        capture_exception(e, context={
            "ticket": processed_ticket,
            "thread_id": thread_id
        })
        print(f"An error occurred: {e}")
        raise

    print(f"Category:    {result['category'].upper()}")
    print(f"Confidence:  {result['confidence_score']}")
    print(f"Escalated:   {'YES' if result['escalate'] else 'NO'}")
    print(f"\n{'--- ESCALATION ---' if result['escalate'] else '--- Draft Reply ---'}")
    print(result["final_response"])

    langfuse.flush()

    print("\n" + "=" * 40)
    print("Follow-up mode. Type your question or 'exit' to quit.")
    print("=" * 40 + "\n")

    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("exit", "quit", "q"):
            print("Session ended.")
            break

        if not user_input:
            continue

        # Guardrails on follow-ups too
        processed_input, followup_report = process_input(user_input)

        if followup_report["blocked"]:
            print(f"❌ Message blocked: {followup_report['block_reason']}\n")
            continue

        followup_result = graph.invoke(
            {"messages": [HumanMessage(content=processed_input)]},
            config=config
        )

        print(f"\nBot: {followup_result['final_response']}\n")


if __name__ == "__main__":
    main()