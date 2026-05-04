from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from graph.state import TicketState
from graph.nodes import classify_node, draft_node, escalate_node, route_after_classify


def build_graph():
    builder = StateGraph(TicketState)

    # Add nodes
    builder.add_node("classify", classify_node)
    builder.add_node("draft", draft_node)
    builder.add_node("escalate", escalate_node)

    # Entry point
    builder.set_entry_point("classify")

    # Conditional routing after classification
    builder.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "draft": "draft",
            "escalate": "escalate"
        }
    )

    # Both terminal nodes lead to END
    builder.add_edge("draft", END)
    builder.add_edge("escalate", END)

    return builder.compile()


graph = build_graph()