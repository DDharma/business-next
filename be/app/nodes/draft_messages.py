"""
Draft a personalized WhatsApp message + opener for each recommended customer.

One LLM call per customer. Gemma-3-4B can be slow, so we keep the prompt
tight and the temperature modest. JSON is parsed with the same multi-method
fallback used by parse_intent.
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .. import events
from ..llm import make_llm
from ..schemas import CustomerCard
from ..state import GraphState
from ..tools.scoring import top_factors

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "draft_message.txt").read_text()


class _Draft(BaseModel):
    whatsapp: str = Field(..., min_length=10, max_length=500)
    opener: str = Field(..., min_length=5, max_length=200)


def _tenure_years(opened: str | None) -> float:
    if not opened:
        return 0.0
    try:
        d = datetime.fromisoformat(opened).date()
    except Exception:
        return 0.0
    return round((date.today() - d).days / 365.25, 1)


def _ask_llm(prompt_vars: dict[str, Any]) -> _Draft | None:
    llm = make_llm(temperature=0.6)
    prompt = PROMPT.format(**prompt_vars)
    messages = [
        SystemMessage(content="You output strictly valid JSON. Nothing else."),
        HumanMessage(content=prompt),
    ]
    for method in ("json_schema", "json_mode", None):
        try:
            if method:
                draft = llm.with_structured_output(_Draft, method=method).invoke(messages)
                return draft  # type: ignore[return-value]
            raw = llm.invoke(messages)
            content = raw.content if hasattr(raw, "content") else str(raw)
            content = (
                content.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            return _Draft.model_validate(json.loads(content))
        except Exception:
            continue
    return None


def _fallback_draft(customer: dict, product: dict, reason: str) -> _Draft:
    first = customer["name"].split()[0]
    pname = product["name"]
    return _Draft(
        whatsapp=(
            f"Hi {first}, hope you are doing well. Based on your account "
            f"history with us, you may qualify for our {pname} on attractive "
            f"terms. Happy to share details whenever convenient."
        ),
        opener=f"Hi {first} — quick note about a {pname} option for you.",
    )


def run(state: GraphState) -> GraphState:
    started = time.monotonic()
    events.node_started(state, "draft_messages", "Drafting WhatsApp outreach")

    cards: list[CustomerCard] = []
    score_by_cust = {s.customer_id: s for s in state.get("scored", [])}

    for cust, product, reason in state.get("recommended", []):
        if product is None:
            # No eligible product — skip, but tell the user via an event
            events.tool_result(
                state, "draft_messages", "skip",
                f"{cust['name']} — {reason}",
            )
            continue

        prompt_vars = {
            "name": cust["name"],
            "city": cust["city"],
            "occupation": cust["occupation"],
            "employer_type": cust["employer_type"],
            "monthly_income": f"{cust['monthly_income']:,.0f}",
            "tenure_years": _tenure_years(cust.get("account_open_date")),
            "product_name": product["name"],
            "product_code": product["code"],
            "interest_rate": product.get("interest_rate") or "competitive",
            "max_amount": f"{(product.get('max_amount') or 0):,.0f}",
            "tenure_months": product.get("tenure_months") or "flexible",
            "reason": reason,
        }

        events.tool_call(
            state, "draft_messages", "llm.draft",
            {"customer": cust["name"], "product": product["code"]},
        )
        draft = _ask_llm(prompt_vars) or _fallback_draft(cust, product, reason)

        score = score_by_cust.get(cust["id"])
        if not score:
            continue

        card = CustomerCard(
            customer_id=cust["id"],
            name=cust["name"],
            city=cust["city"],
            monthly_income=float(cust["monthly_income"]),
            score=score.score,
            top_factors=top_factors(score, n=3),
            product_code=product["code"],
            product_name=product["name"],
            reason=reason,
            whatsapp_message=draft.whatsapp,
            opener=draft.opener,
        )
        cards.append(card)
        events.card(state, card)

    events.tool_result(
        state, "draft_messages", "llm.draft",
        f"Drafted {len(cards)} cards",
    )
    events.node_finished(state, "draft_messages", int((time.monotonic() - started) * 1000))
    return {"cards": cards}  # type: ignore[return-value]
