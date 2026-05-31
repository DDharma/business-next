"""Score every candidate, keep the top-N."""

from __future__ import annotations

import time

from .. import events
from ..state import GraphState
from ..tools.scoring import score_customer


def run(state: GraphState) -> GraphState:
    started = time.monotonic()
    events.node_started(state, "score", "Scoring candidates")

    intent = state["intent"]
    assert intent is not None

    target = intent.filters.product
    events.tool_call(state, "score", "heuristic.score_customer",
                     {"target_product": target, "factor_count": 7})

    scored = []
    for cust in state.get("candidates", []):
        txns = state.get("transactions", {}).get(cust["id"], [])
        scored.append(score_customer(cust, txns, target_product=target))

    scored.sort(key=lambda s: s.score, reverse=True)
    top = scored[: intent.top_n]

    events.tool_result(
        state, "score", "heuristic.score_customer",
        f"Scored {len(scored)}; kept top {len(top)} "
        f"(range: {top[-1].score:.1f}–{top[0].score:.1f})" if top else "no candidates",
    )
    events.node_finished(state, "score", int((time.monotonic() - started) * 1000))
    return {"scored": top}  # type: ignore[return-value]
