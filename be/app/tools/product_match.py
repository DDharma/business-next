from __future__ import annotations

from ..constants import PRODUCT_HAS_COLUMN, TIER_PREFERENCE


def _eligible(customer: dict, product: dict) -> tuple[bool, str]:
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
        "credit_card": f"{tier.title()} tier income — qualifies for {product['name']}",
        "home_loan": f"Salaried, ₹{income:,.0f}/mo — meets home loan eligibility",
        "savings_plus": f"Eligible across the board; {product['name']} fits as upsell",
    }
    return headline.get(product["code"], product["name"])


def match_product(
    customer: dict,
    products: list[dict],
    *,
    requested_code: str | None = None,
) -> tuple[dict | None, str]:
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
