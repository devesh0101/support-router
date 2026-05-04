import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts.classifier import CLASSIFIER_SYSTEM_PROMPT

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def classify_ticket(ticket_text: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=CLASSIFIER_SYSTEM_PROMPT,
            temperature=0.2,
        ),
        contents=f"Support ticket:\n\n{ticket_text}"
    )

    raw_output = response.text.strip()

    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
        raw_output = raw_output.strip()

    try:
        result = json.loads(raw_output)
    except json.JSONDecodeError:
        print("Model returned invalid JSON:")
        print(raw_output)
        raise

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

    ticket = "\n".join(lines)

    if not ticket.strip():
        print("No ticket provided.")
        return

    print("\nProcessing...\n")
    result = classify_ticket(ticket)

    print(f"Category:         {result['category'].upper()}")
    print(f"Confidence:       {result['confidence_score']}")
    print(f"Escalate:         {'YES' if result['escalate'] else 'NO'}")
    print(f"\nDraft Reply:\n{result['draft_reply']}")


if __name__ == "__main__":
    main()