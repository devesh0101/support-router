import json
import uuid
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from graph.graph import graph


def run_ticket(ticket_text: str) -> dict:
    """Run a single ticket through the full pipeline."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {
            "ticket_text": ticket_text,
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
    return result


def score_response(result: dict, test_case: dict) -> dict:
    """
    Score a response against expected outputs.
    Returns a dict with individual scores and a total.
    """
    scores = {}

    # 1. Category match (0 or 1)
    scores["category_correct"] = int(
        result["category"] == test_case["expected_category"]
    )

    # 2. Escalation match (0 or 1)
    scores["escalation_correct"] = int(
        result["escalate"] == test_case["should_escalate"]
    )

    # 3. Keyword coverage — how many expected keywords appear in the reply
    reply = result["final_response"].lower()
    keywords = test_case["expected_keywords"]
    if keywords:
        hits = sum(1 for kw in keywords if kw.lower() in reply)
        scores["keyword_coverage"] = round(hits / len(keywords), 2)
    else:
        scores["keyword_coverage"] = None  # vague ticket, skip

    # 4. Confidence score (just record it, don't score it)
    scores["confidence"] = result["confidence_score"]

    # 5. Has retrieved context (0 or 1)
    scores["has_rag_context"] = int(
        bool(result.get("retrieved_context")) and
        result["retrieved_context"] != "No relevant documentation found."
    )

    return scores


def run_evaluation():
    with open("data/test_tickets.json") as f:
        test_cases = json.load(f)

    results = []
    print("Running evaluation...\n")
    print("=" * 60)

    for tc in test_cases:
        print(f"Ticket {tc['id']}: {tc['ticket'][:60]}...")

        result = run_ticket(tc["ticket"])
        scores = score_response(result, tc)

        results.append({
            "id": tc["id"],
            "ticket": tc["ticket"],
            "expected_category": tc["expected_category"],
            "got_category": result["category"],
            "expected_escalate": tc["should_escalate"],
            "got_escalate": result["escalate"],
            "confidence": scores["confidence"],
            "category_correct": scores["category_correct"],
            "escalation_correct": scores["escalation_correct"],
            "keyword_coverage": scores["keyword_coverage"],
            "has_rag_context": scores["has_rag_context"],
            "final_response": result["final_response"],
            "retrieved_context": result.get("retrieved_context", "")
        })

        status = "✅" if scores["category_correct"] else "❌"
        kw = f"{scores['keyword_coverage']:.0%}" if scores["keyword_coverage"] is not None else "N/A"
        print(f"  {status} Category: {result['category']} | "
              f"Escalate: {result['escalate']} | "
              f"Keyword coverage: {kw} | "
              f"RAG: {'yes' if scores['has_rag_context'] else 'no'}\n")

    # Summary stats
    total = len(results)
    category_acc = sum(r["category_correct"] for r in results) / total
    escalation_acc = sum(r["escalation_correct"] for r in results) / total
    kw_results = [r["keyword_coverage"] for r in results if r["keyword_coverage"] is not None]
    avg_kw = sum(kw_results) / len(kw_results) if kw_results else 0
    rag_coverage = sum(r["has_rag_context"] for r in results) / total

    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tickets:        {total}")
    print(f"Category accuracy:    {category_acc:.0%}")
    print(f"Escalation accuracy:  {escalation_acc:.0%}")
    print(f"Avg keyword coverage: {avg_kw:.0%}")
    print(f"RAG context rate:     {rag_coverage:.0%}")

    # Save full results to file
    with open("data/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nFull results saved to data/eval_results.json")
    return results


if __name__ == "__main__":
    run_evaluation()