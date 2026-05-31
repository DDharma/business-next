"""Pull candidate customers + their recent transactions from Supabase."""

from __future__ import annotations

import time

from .. import events
from ..state import GraphState
from ..tools import customer_repo


def run(state: GraphState) -> GraphState:
    started = time.monotonic()
    events.node_started(state, "retrieve", "Querying customer database")

    intent = state["intent"]
    assert intent is not None, "parse_intent must run before retrieve"
    filters = intent.filters

    events.tool_call(
        state, "retrieve", "supabase.customers",
        filters.model_dump(exclude_none=True) or {"all": True},
    )
    candidates = customer_repo.get_candidates(filters, limit=80)
    events.tool_result(
        state, "retrieve", "supabase.customers",
        f"{len(candidates)} candidates",
    )

    ids = [c["id"] for c in candidates]
    events.tool_call(state, "retrieve", "supabase.transactions",
                     {"customer_ids": len(ids), "window_days": 180})
    txns = customer_repo.get_recent_transactions(ids, days=180)
    total_txns = sum(len(v) for v in txns.values())
    events.tool_result(
        state, "retrieve", "supabase.transactions",
        f"{total_txns} transactions across {len(ids)} customers",
    )

    # Cache product catalog once per run
    products = customer_repo.get_products()

    events.node_finished(state, "retrieve", int((time.monotonic() - started) * 1000))
    return {  # type: ignore[return-value]
        "candidates": candidates,
        "transactions": txns,
        "products": products,
    }
