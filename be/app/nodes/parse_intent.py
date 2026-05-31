"""
Parse the RM's natural-language request into a structured IntentSchema.

Gemma-3-4B does not have native tool-calling in LM Studio, so we use the
OpenAI `response_format={"type": "json_object"}` (json_mode) path via
LangChain's `with_structured_output(..., method="json_mode")`.

Retry once on validation failure with a stricter reminder. If both
attempts fail we fall back to a safe default intent so the rest of the
graph still runs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from .. import events
from ..llm import make_llm
from ..schemas import Filters, IntentSchema
from ..state import GraphState

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "intent.txt").read_text()


def _format_history(history: list[dict] | None) -> str:
    if not history:
        return "(none)"
    lines = []
    for turn in history[-6:]:  # last 6 turns
        lines.append(f"{turn.get('role', 'user')}: {turn.get('content', '')}")
    return "\n".join(lines)


def _fallback_intent(user_message: str) -> IntentSchema:
    """Safe default when the LLM can't produce parseable JSON."""
    text = user_message.lower()
    product = None
    for code in ("personal_loan", "personal loan", "credit_card", "credit card",
                 "home_loan", "home loan", "savings"):
        if code in text:
            product = code.replace(" ", "_")
            if product == "savings":
                product = "savings_plus"
            break
    return IntentSchema(
        intent="find_prospects",
        filters=Filters(product=product),
        top_n=5,
        notes="fallback: LLM intent parse failed",
    )


def _ask_llm(user_message: str, history: list[dict] | None) -> IntentSchema:
    """One round-trip to LM Studio, parsed via json_mode."""
    llm = make_llm(temperature=0.0)
    prompt_text = PROMPT.format(
        history=_format_history(history),
        user_message=user_message,
    )
    # Two-message form keeps the LLM grounded
    messages = [
        SystemMessage(content="You output strictly valid JSON. Nothing else."),
        HumanMessage(content=prompt_text),
    ]
    # Try the strongest method first, then progressively looser fallbacks.
    last_err: Exception | None = None
    for method in ("json_schema", "json_mode", None):
        try:
            if method:
                structured = llm.with_structured_output(IntentSchema, method=method)
            else:
                # No native JSON support — ask for raw text and parse ourselves
                raw = llm.invoke(messages)
                content = raw.content if hasattr(raw, "content") else str(raw)
                # Strip code fences if the model added any
                content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                return IntentSchema.model_validate(json.loads(content))
            return structured.invoke(messages)  # type: ignore[union-attr]
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"all intent parse methods failed: {last_err}")


def run(state: GraphState) -> GraphState:
    started = time.monotonic()
    events.node_started(state, "parse_intent", "Understanding the request")
    events.tool_call(
        state,
        "parse_intent",
        "llm.json_mode",
        {"user_message": state["user_message"]},
    )

    try:
        intent = _ask_llm(state["user_message"], state.get("history"))
    except Exception:
        # Retry once with a fresh call before falling back
        try:
            intent = _ask_llm(state["user_message"], state.get("history"))
        except Exception as e:
            events.tool_result(
                state, "parse_intent", "llm.json_mode",
                f"LLM parse failed twice ({e}); using fallback",
            )
            intent = _fallback_intent(state["user_message"])

    events.tool_result(
        state, "parse_intent", "llm.json_mode",
        f"intent={intent.intent} filters={intent.filters.model_dump(exclude_none=True)} top_n={intent.top_n}",
    )
    events.node_finished(state, "parse_intent", int((time.monotonic() - started) * 1000))
    return {"intent": intent}  # type: ignore[return-value]
