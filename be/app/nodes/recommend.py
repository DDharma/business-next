"""Match each top-scored customer to the best-fit product."""

from __future__ import annotations

import time

from .. import events
from ..state import GraphState
from ..tools.product_match import match_product


def run(state: GraphState) -> GraphState:
    started = time.monotonic()
    events.node_started(state, "recommend", "Selecting product fit")

    intent = state["intent"]
    assert intent is not None
    requested = intent.filters.product
    products = state.get("products", [])
    candidates_by_id = {c["id"]: c for c in state.get("candidates", [])}

    events.tool_call(state, "recommend", "rules.match_product",
                     {"requested_product": requested, "products_in_catalog": len(products)})

    recommended: list[tuple[dict, dict | None, str]] = []
    for s in state.get("scored", []):
        cust = candidates_by_id.get(s.customer_id)
        if not cust:
            continue
        product, reason = match_product(cust, products, requested_code=requested)
        recommended.append((cust, product, reason))

    hits = sum(1 for _, p, _ in recommended if p is not None)
    events.tool_result(
        state, "recommend", "rules.match_product",
        f"{hits}/{len(recommended)} customers matched to a product",
    )
    events.node_finished(state, "recommend", int((time.monotonic() - started) * 1000))
    return {"recommended": recommended}  # type: ignore[return-value]
