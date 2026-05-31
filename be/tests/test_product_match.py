from app.tools.product_match import match_product


PRODUCTS = [
    {"code": "personal_loan", "name": "Personal Loan", "type": "loan",
     "min_income": 30000, "target_segment": "any"},
    {"code": "credit_card", "name": "Platinum Credit Card", "type": "card",
     "min_income": 25000, "target_segment": "any"},
    {"code": "savings_plus", "name": "Savings Plus", "type": "deposit",
     "min_income": 0, "target_segment": "any"},
    {"code": "home_loan", "name": "Home Loan", "type": "loan",
     "min_income": 80000, "target_segment": "salaried"},
]


def _cust(**kw):
    base = {
        "income_tier": "high",
        "occupation": "salaried",
        "monthly_income": 120000.0,
        "has_personal_loan": False,
        "has_credit_card": False,
        "has_home_loan": False,
    }
    base.update(kw)
    return base


def test_requested_product_wins_when_eligible():
    p, reason = match_product(_cust(), PRODUCTS, requested_code="personal_loan")
    assert p["code"] == "personal_loan"
    assert "personal loan" in reason.lower()


def test_requested_product_blocked_when_holder():
    p, reason = match_product(
        _cust(has_personal_loan=True), PRODUCTS, requested_code="personal_loan"
    )
    assert p is None
    assert "already holds" in reason


def test_requested_product_blocked_by_income_floor():
    p, reason = match_product(
        _cust(monthly_income=50000), PRODUCTS, requested_code="home_loan"
    )
    assert p is None
    assert "income below" in reason


def test_self_employed_blocked_from_home_loan():
    p, reason = match_product(
        _cust(occupation="self_employed"), PRODUCTS, requested_code="home_loan"
    )
    assert p is None


def test_tier_preference_when_no_request():
    p, _ = match_product(_cust(income_tier="premium", monthly_income=300000), PRODUCTS)
    assert p["code"] == "home_loan"


def test_low_tier_falls_back_to_savings():
    p, _ = match_product(
        _cust(income_tier="low", monthly_income=20000, occupation="self_employed"),
        PRODUCTS,
    )
    assert p["code"] == "savings_plus"
