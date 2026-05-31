from __future__ import annotations

from datetime import datetime

from ..constants import (
    AGE_BAND_MAX,
    AGE_BAND_MIN,
    AGE_BAND_PEAK,
    PRODUCT_HAS_COLUMN,
    SCORING_WEIGHTS,
    TENURE_CAP_YEARS,
    TIER_RAW,
)
from ..schemas import CustomerScore, ScoreFactor

# Kept for backwards-compat with existing tests that import WEIGHTS.
WEIGHTS = SCORING_WEIGHTS


def _factor(name: str, raw: float) -> ScoreFactor:
    raw = max(0.0, min(100.0, raw))
    w = SCORING_WEIGHTS[name]
    return ScoreFactor(name=name, weight=w, raw=raw, contribution=raw * w)


def _income_tier(customer: dict) -> ScoreFactor:
    return _factor("income_tier", TIER_RAW.get(customer.get("income_tier", "mid"), 60.0))


def _salary_stability(txns: list[dict]) -> ScoreFactor:
    months_with_salary = {
        t["created_at"][:7]
        for t in txns
        if t["category"] == "salary" and t["direction"] == "credit"
    }
    raw = (len(months_with_salary) / 6.0) * 100.0
    return _factor("salary_stability", raw)


def _balance_trend(txns: list[dict]) -> ScoreFactor:
    if len(txns) < 4:
        return _factor("balance_trend", 50.0)

    sorted_txns = sorted(txns, key=lambda t: t["created_at"])
    mid = len(sorted_txns) // 2
    old, new = sorted_txns[:mid], sorted_txns[mid:]

    def net(group: list[dict]) -> float:
        return sum(
            (1 if t["direction"] == "credit" else -1) * float(t["amount"])
            for t in group
        )

    old_net, new_net = net(old), net(new)
    if old_net == 0:
        raw = 75.0 if new_net > 0 else 25.0
    else:
        ratio = (new_net - old_net) / (abs(old_net) + 1.0)
        raw = 50.0 + ratio * 50.0
    return _factor("balance_trend", raw)


def _no_existing(customer: dict, target_product: str | None) -> ScoreFactor:
    col = PRODUCT_HAS_COLUMN.get(target_product or "")
    if not col:
        return _factor("no_existing", 50.0)
    return _factor("no_existing", 0.0 if customer.get(col) else 100.0)


def _emi_signal(txns: list[dict]) -> ScoreFactor:
    # Existing EMI activity → comfort with debt servicing, positive signal for personal loan.
    emis = [t for t in txns if t["category"] == "emi"]
    if not emis:
        return _factor("emi_signal", 30.0)
    months = {t["created_at"][:7] for t in emis}
    avg_per_month = len(emis) / max(1, len(months))
    raw = min(100.0, 30.0 + avg_per_month * 30.0)
    return _factor("emi_signal", raw)


def _tenure(customer: dict) -> ScoreFactor:
    try:
        opened = datetime.fromisoformat(customer["account_open_date"]).date()
    except Exception:
        return _factor("tenure", 50.0)
    years = (datetime.utcnow().date() - opened).days / 365.25
    raw = min(100.0, (years / TENURE_CAP_YEARS) * 100.0)
    return _factor("tenure", raw)


def _age_band(customer: dict) -> ScoreFactor:
    # Triangular preference around AGE_BAND_PEAK; banks favor 28–50 for unsecured credit.
    age = customer.get("age", AGE_BAND_PEAK)
    if AGE_BAND_MIN <= age <= AGE_BAND_MAX:
        raw = 100.0 - abs(age - AGE_BAND_PEAK) * 2.0
    elif age < AGE_BAND_MIN:
        raw = max(40.0, 100.0 - (AGE_BAND_MIN - age) * 8.0)
    else:
        raw = max(20.0, 100.0 - (age - AGE_BAND_MAX) * 5.0)
    return _factor("age_band", raw)


def score_customer(
    customer: dict,
    transactions: list[dict],
    target_product: str | None = None,
) -> CustomerScore:
    factors = [
        _income_tier(customer),
        _salary_stability(transactions),
        _balance_trend(transactions),
        _no_existing(customer, target_product),
        _emi_signal(transactions),
        _tenure(customer),
        _age_band(customer),
    ]
    total = sum(f.contribution for f in factors)
    return CustomerScore(
        customer_id=customer["id"],
        score=round(total, 2),
        factors=factors,
    )


def top_factors(score: CustomerScore, n: int = 3) -> list[ScoreFactor]:
    return sorted(score.factors, key=lambda f: f.contribution, reverse=True)[:n]
