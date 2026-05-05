import json
import uuid
import os
from dotenv import load_dotenv
load_dotenv()

from graph.graph import graph
from observability.judge import evaluate_response


def run_ticket(ticket_text: str) -> dict:
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
    scores = {}

    scores["category_correct"] = int(
        result["category"] == test_case["expected_category"]
    )

    scores["escalation_correct"] = int(
        result["escalate"] == test_case["should_escalate"]
    )

    keywords = test_case["expected_keywords"]
    if keywords and not result["escalate"]:
        reply = result["final_response"].lower()
        hits = sum(1 for kw in keywords if kw.lower() in reply)
        scores["keyword_coverage"] = round(hits / len(keywords), 2)
    else:
        scores["keyword_coverage"] = None

    scores["confidence"] = result["confidence_score"]
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

        # LLM-as-a-judge scoring
        print(f"  🧑‍⚖️  Running judge evaluation...")
        judge_scores = evaluate_response(
            ticket=tc["ticket"],
            reply=result["final_response"],
            retrieved_context=result.get("retrieved_context", ""),
            escalated=result["escalate"]
        )

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
            "retrieved_context": result.get("retrieved_context", ""),
            "judge_scores": judge_scores
        })

        cat_status = "✅" if scores["category_correct"] else "❌"
        kw = f"{scores['keyword_coverage']:.0%}" if scores["keyword_coverage"] is not None else "N/A"

        if judge_scores["total"] is not None:
            print(f"  {cat_status} Category: {result['category']} | "
                  f"Keyword coverage: {kw} | "
                  f"Judge score: {judge_scores['total']}/20")
            print(f"     Reasoning: {judge_scores['reasoning']}\n")
        else:
            print(f"  {cat_status} Category: {result['category']} | "
                  f"Escalated — judge skipped\n")

    # Summary
    total = len(results)
    category_acc = sum(r["category_correct"] for r in results) / total
    escalation_acc = sum(r["escalation_correct"] for r in results) / total

    kw_results = [r["keyword_coverage"] for r in results if r["keyword_coverage"] is not None]
    avg_kw = sum(kw_results) / len(kw_results) if kw_results else 0

    judge_results = [r["judge_scores"]["total"] for r in results if r["judge_scores"]["total"] is not None]
    avg_judge = sum(judge_results) / len(judge_results) if judge_results else 0

    # Per-dimension averages
    dims = ["accuracy", "groundedness", "tone", "completeness"]
    dim_avgs = {}
    for dim in dims:
        vals = [r["judge_scores"][dim] for r in results if r["judge_scores"][dim] is not None]
        dim_avgs[dim] = round(sum(vals) / len(vals), 2) if vals else 0

    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tickets:          {total}")
    print(f"Category accuracy:      {category_acc:.0%}")
    print(f"Escalation accuracy:    {escalation_acc:.0%}")
    print(f"Avg keyword coverage:   {avg_kw:.0%}")
    print(f"Avg judge score:        {avg_judge:.1f}/20")
    print(f"\nJudge breakdown:")
    for dim, avg in dim_avgs.items():
        print(f"  {dim.capitalize():<16} {avg}/5")

    with open("data/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nFull results saved to data/eval_results.json")
    return results


if __name__ == "__main__":
    run_evaluation()