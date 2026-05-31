"""Rule-based product fit. No LLM."""

from __future__ import annotations

# Preferred product per income tier when the RM didn't pin a product.
TIER_PREFERENCE = {
    "premium": ["home_loan", "personal_loan", "credit_card"],
    "high":    ["personal_loan", "home_loan", "credit_card"],
    "mid":     ["personal_loan", "credit_card", "savings_plus"],
    "low":     ["savings_plus", "credit_card"],
}

PRODUCT_HAS_COLUMN = {
    "personal_loan": "has_personal_loan",
    "credit_card":   "has_credit_card",
    "home_loan":     "has_home_loan",
}


def _eligible(customer: dict, product: dict) -> tuple[bool, str]:
    """Return (ok, reason_if_blocked)."""
    if customer["monthly_income"] < float(product["min_income"]):
        return False, f"income below product floor ₹{product['min_income']:.0f}"

    if product["target_segment"] not in ("any", customer["occupation"]):
        return False, f"segment mismatch ({product['target_segment']})"

    col = PRODUCT_HAS_COLUMN.get(product["code"])
    if col and customer.get(col):
        return False, "already holds this product"

    return True, ""


def _humanize_reason(customer: dict, product: dict) -> str:
    income = customer["monthly_income"]
    tier = customer["income_tier"]
    headline = {
        "personal_loan": f"₹{income:,.0f}/mo income — comfortably above ₹{product['min_income']:,.0f} floor, no existing personal loan",
        "credit_card":   f"{tier.title()} tier income — qualifies for {product['name']}",
        "home_loan":     f"Salaried, ₹{income:,.0f}/mo — meets home loan eligibility",
        "savings_plus":  f"Eligible across the board; {product['name']} fits as upsell",
    }
    return headline.get(product["code"], product["name"])


def match_product(
    customer: dict,
    products: list[dict],
    *,
    requested_code: str | None = None,
) -> tuple[dict | None, str]:
    """
    Choose the best product for this customer.

    If the RM asked for a specific product code, prefer it (must still pass
    eligibility). Otherwise pick by the tier preference order.
    Returns (product_dict, reason_string). Product may be None if nothing fits.
    """
    by_code = {p["code"]: p for p in products}

    if requested_code:
        product = by_code.get(requested_code)
        if product:
            ok, why = _eligible(customer, product)
            if ok:
                return product, _humanize_reason(customer, product)
            return None, f"Customer not eligible for {requested_code}: {why}"

    tier = customer.get("income_tier", "mid")
    for code in TIER_PREFERENCE.get(tier, []):
        product = by_code.get(code)
        if not product:
            continue
        ok, _ = _eligible(customer, product)
        if ok:
            return product, _humanize_reason(customer, product)

    return None, "no eligible product"
