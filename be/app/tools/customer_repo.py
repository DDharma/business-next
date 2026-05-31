"""Read-only DAO functions used by the retrieve node."""

from __future__ import annotations

from datetime import datetime, timedelta

from ..db import get_db
from ..schemas import Filters

# Map product code → the "has_*" customer column. Customers already holding
# the target product are excluded by default (`Filters.exclude_existing_product_holders`).
PRODUCT_HAS_COLUMN = {
    "personal_loan": "has_personal_loan",
    "credit_card": "has_credit_card",
    "home_loan": "has_home_loan",
}


def get_candidates(filters: Filters, limit: int = 100) -> list[dict]:
    """Pull candidate customers matching the requested filters."""
    db = get_db()
    q = db.table("customers").select("*")

    if filters.city:
        q = q.eq("city", filters.city)

    if filters.min_income is not None:
        q = q.gte("monthly_income", filters.min_income)

    if filters.product and filters.exclude_existing_product_holders:
        col = PRODUCT_HAS_COLUMN.get(filters.product)
        if col:
            q = q.eq(col, False)

    # Order by income desc so the heuristic has a sensible starting pool;
    # the score node will re-rank within this set.
    q = q.order("monthly_income", desc=True).limit(limit)

    res = q.execute()
    return res.data or []


def get_recent_transactions(
    customer_ids: list[str], days: int = 90
) -> dict[str, list[dict]]:
    """Return {customer_id: [txns…]} for the requested window."""
    if not customer_ids:
        return {}

    db = get_db()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    res = (
        db.table("transactions")
        .select("*")
        .in_("customer_id", customer_ids)
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
    )

    out: dict[str, list[dict]] = {cid: [] for cid in customer_ids}
    for row in res.data or []:
        out.setdefault(row["customer_id"], []).append(row)
    return out


def get_products() -> list[dict]:
    return get_db().table("products").select("*").execute().data or []
