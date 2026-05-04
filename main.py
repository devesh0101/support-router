from dotenv import load_dotenv
load_dotenv()

import uuid
from langchain_core.messages import HumanMessage
from graph.graph import graph


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

    ticket = "\n".join(lines)

    if not ticket.strip():
        print("No ticket provided.")
        return

    # Each session gets a unique thread ID
    # This is how LangGraph knows which memory to load
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("\nProcessing...\n")

    # First invocation — full pipeline
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

    if result.get("retrieved_context"):
        print("\n--- Retrieved Context ---")
        print(result["retrieved_context"])
        print("------------------------\n")

    print(f"Category:    {result['category'].upper()}")
    print(f"Confidence:  {result['confidence_score']}")
    print(f"Escalated:   {'YES' if result['escalate'] else 'NO'}")
    print(f"\n{'--- ESCALATION ---' if result['escalate'] else '--- Draft Reply ---'}")
    print(result["final_response"])

    # Conversation loop for follow-ups
    print("\n" + "=" * 40)
    print("Follow-up mode. Type your question or 'exit' to quit.")
    print("=" * 40 + "\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("exit", "quit", "q"):
            print("Session ended.")
            break

        if not user_input:
            continue

        followup_result = graph.invoke(
            {
                "messages": [HumanMessage(content=user_input)]
            },
            config=config  # same thread_id = same memory
        )

        print(f"\nBot: {followup_result['final_response']}\n")


if __name__ == "__main__":
    main()