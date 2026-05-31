from typing import Any, Literal

from pydantic import BaseModel, Field


# ── LLM-facing structured output ─────────────────────────────────────────

class Filters(BaseModel):
    product: str | None = Field(
        default=None,
        description="Product code: personal_loan | credit_card | savings_plus | home_loan",
    )
    city: str | None = None
    min_income: float | None = None
    exclude_existing_product_holders: bool = True


class IntentSchema(BaseModel):
    intent: Literal["find_prospects", "refine", "rewrite_message", "explain"]
    filters: Filters = Field(default_factory=Filters)
    top_n: int = Field(default=5, ge=1, le=25)
    notes: str | None = None


# ── Scoring ──────────────────────────────────────────────────────────────

class ScoreFactor(BaseModel):
    name: str
    weight: float
    raw: float
    contribution: float


class CustomerScore(BaseModel):
    customer_id: str
    score: float
    factors: list[ScoreFactor]


# ── Customer card (final UI payload) ─────────────────────────────────────

class CustomerCard(BaseModel):
    customer_id: str
    name: str
    city: str
    monthly_income: float
    score: float
    top_factors: list[ScoreFactor]
    product_code: str
    product_name: str
    reason: str
    whatsapp_message: str
    opener: str | None = None


# ── SSE step events ──────────────────────────────────────────────────────

class StepEvent(BaseModel):
    type: Literal[
        "node_started",
        "tool_call",
        "tool_result",
        "node_finished",
        "card",
        "done",
        "error",
    ]
    node: str | None = None
    label: str | None = None
    tool: str | None = None
    args: dict[str, Any] | None = None
    preview: str | None = None
    ms: int | None = None
    card: CustomerCard | None = None
    message: str | None = None
