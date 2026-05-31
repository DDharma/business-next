from __future__ import annotations

from datetime import datetime, timedelta

from ..constants import MAX_CANDIDATES, PRODUCT_HAS_COLUMN, TXN_WINDOW_DAYS
from ..db import get_db
from ..schemas import Filters


def get_candidates(filters: Filters, limit: int = MAX_CANDIDATES) -> list[dict]:
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

    q = q.order("monthly_income", desc=True).limit(limit)
    return q.execute().data or []


def get_recent_transactions(
    customer_ids: list[str], days: int = TXN_WINDOW_DAYS
) -> dict[str, list[dict]]:
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
