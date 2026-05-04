from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import TicketState

from graph.nodes import (
    classify_node, draft_node, escalate_node,
    route_after_classify, followup_node, route_entry
)



def build_graph():
    builder = StateGraph(TicketState)

    builder.add_node("classify", classify_node)
    builder.add_node("draft", draft_node)
    builder.add_node("escalate", escalate_node)
    builder.add_node("followup", followup_node)

    builder.set_entry_point("classify")

    # Conditional entry — not set_entry_point anymore
    builder.set_conditional_entry_point(
        route_entry,
        {
            "classify": "classify",
            "followup": "followup"
        }
    )

    builder.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "draft": "draft",
            "escalate": "escalate"
        }
    )
    
    builder.add_edge("draft", END)
    builder.add_edge("escalate", END)
    builder.add_edge("followup", END)

    # Attach memory checkpointer
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


graph = build_graph()