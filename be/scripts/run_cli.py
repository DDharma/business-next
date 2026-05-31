"""
CLI driver — exercise the graph end-to-end against the seeded DB and a
running LM Studio. Used as the Phase 2 smoke test.

Usage:
    python scripts/run_cli.py
    python scripts/run_cli.py "find 5 high-value personal-loan prospects in Mumbai"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.graph import build_graph  # noqa: E402
from app.schemas import StepEvent  # noqa: E402


def _print_event(ev: StepEvent) -> None:
    if ev.type == "node_started":
        print(f"\n┌─ {ev.node}  ·  {ev.label}")
    elif ev.type == "tool_call":
        args_preview = ", ".join(f"{k}={v}" for k, v in (ev.args or {}).items())
        print(f"│  → {ev.tool}({args_preview})")
    elif ev.type == "tool_result":
        print(f"│  ← {ev.preview}")
    elif ev.type == "node_finished":
        print(f"└─ {ev.node} done in {ev.ms} ms")
    elif ev.type == "card":
        c = ev.card
        if c is None:
            return
        print()
        print(f"  ┃ {c.name}  ({c.city}) · score {c.score:.1f}")
        print(f"  ┃ ₹{c.monthly_income:,.0f}/mo · {c.product_name}")
        for f in c.top_factors:
            print(f"  ┃   • {f.name}: {f.raw:.0f}/100 (weight {f.weight:.2f})")
        print(f"  ┃ reason: {c.reason}")
        print(f"  ┃ opener: {c.opener}")
        print(f"  ┃ whatsapp:")
        for line in c.whatsapp_message.split("\n"):
            print(f"  ┃   {line}")
    elif ev.type == "error":
        print(f"!! error: {ev.message}")


def main() -> None:
    user_message = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "find 5 high-value personal-loan prospects in Mumbai"
    )

    print(f"\n=== RM: {user_message} ===")

    graph = build_graph()
    state = {
        "chat_id": None,
        "user_message": user_message,
        "history": [],
        "emit": _print_event,
    }
    result = graph.invoke(state)

    print(f"\n=== Done. {len(result.get('cards', []))} cards generated. ===")


if __name__ == "__main__":
    main()
