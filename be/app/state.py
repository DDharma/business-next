from __future__ import annotations

from typing import Any, TypedDict

from .schemas import CustomerCard, CustomerScore, IntentSchema


class GraphState(TypedDict, total=False):
    # Inputs
    chat_id: str | None
    user_message: str
    history: list[dict[str, str]]  # [{role, content}, ...] prior turns
    products: list[dict[str, Any]]  # cached product catalog for the run

    # Per-node intermediate outputs
    intent: IntentSchema | None
    candidates: list[dict[str, Any]]
    transactions: dict[str, list[dict[str, Any]]]
    scored: list[CustomerScore]
    recommended: list[tuple[dict[str, Any], dict[str, Any] | None, str]]
    # ↑ list of (customer, product_or_none, reason)

    # Final output
    cards: list[CustomerCard]

    # Optional control / debug
    error: str | None
    emit: Any  # Callable[[StepEvent], None] — injected by main.py / run_cli.py
