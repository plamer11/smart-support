
from langgraph.graph import END, START, StateGraph

from .nodes import chitchat_node, faq_node, handoff_node, intent_node, route, tool_node
from .state import AgentState


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("intent", intent_node)
    g.add_node("faq", faq_node)
    g.add_node("tool", tool_node)
    g.add_node("chitchat", chitchat_node)
    g.add_node("handoff", handoff_node)

    g.add_edge(START, "intent")
    g.add_conditional_edges(
        "intent",
        route,
        {"faq": "faq", "tool": "tool", "chitchat": "chitchat", "handoff": "handoff"},
    )
    for node in ("faq", "tool", "chitchat", "handoff"):
        g.add_edge(node, END)

    return g.compile()


graph = build_graph()
