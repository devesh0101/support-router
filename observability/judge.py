import os
import json
from google import genai
from google.genai import types
from prompts.judge import JUDGE_SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def evaluate_response(
    ticket: str,
    reply: str,
    retrieved_context: str = "",
    escalated: bool = False
) -> dict:
    """
    Uses Gemini as a judge to score a support reply.
    Returns a dict with dimension scores and reasoning.
    """

    # Escalated tickets get a simpler evaluation
    if escalated:
        return {
            "accuracy": None,
            "groundedness": None,
            "tone": None,
            "completeness": None,
            "total": None,
            "reasoning": "Skipped — ticket was escalated to human agent."
        }

    context_section = (
        f"Retrieved Documentation:\n{retrieved_context}"
        if retrieved_context
        else "Retrieved Documentation: None"
    )

    user_message = f"""
Ticket:
{ticket}

{context_section}

AI Reply:
{reply}
    """.strip()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_SYSTEM_PROMPT,
            temperature=0.1
        ),
        contents=user_message
    )

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)