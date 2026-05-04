from dotenv import load_dotenv
load_dotenv()

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

    print("\nProcessing...\n")

    result = graph.invoke({
        "ticket_text": ticket,
        "messages": [],
        "category": "",
        "confidence_score": 0.0,
        "escalate": False,
        "draft_reply": "",
        "final_response": ""
    })

    print(f"Category:    {result['category'].upper()}")
    print(f"Confidence:  {result['confidence_score']}")
    print(f"Escalated:   {'YES' if result['escalate'] else 'NO'}")
    print(f"\n{'--- ESCALATION ---' if result['escalate'] else '--- Draft Reply ---'}")
    print(result["final_response"])


if __name__ == "__main__":
    main()