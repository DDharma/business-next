"""
LangGraph wiring.

Flow:
                       ┌───────────────► retrieve ─► score ─► recommend ─┐
    START → parse_intent                                                 ▼
                       └─ (rewrite_message) ──────────────────────► draft_messages → END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import draft_messages, parse_intent, recommend, retrieve, score
from .state import GraphState


def _branch_from_intent(state: GraphState) -> str:
    intent = state.get("intent")
    if intent and intent.intent == "rewrite_message":
        return "draft_messages"
    return "retrieve"


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("parse_intent", parse_intent.run)
    g.add_node("retrieve", retrieve.run)
    g.add_node("score", score.run)
    g.add_node("recommend", recommend.run)
    g.add_node("draft_messages", draft_messages.run)

    g.add_edge(START, "parse_intent")
    g.add_conditional_edges(
        "parse_intent",
        _branch_from_intent,
        {"retrieve": "retrieve", "draft_messages": "draft_messages"},
    )
    g.add_edge("retrieve", "score")
    g.add_edge("score", "recommend")
    g.add_edge("recommend", "draft_messages")
    g.add_edge("draft_messages", END)

    return g.compile()
