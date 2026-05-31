from datetime import datetime, timedelta

import pytest

from app.tools.scoring import WEIGHTS, score_customer, top_factors


def _txn(category: str, direction: str, amount: float, days_ago: int) -> dict:
    return {
        "category": category,
        "direction": direction,
        "amount": amount,
        "created_at": (datetime.utcnow() - timedelta(days=days_ago)).isoformat(),
    }


def _customer(**overrides) -> dict:
    base = {
        "id": "c1",
        "name": "Test User",
        "age": 35,
        "city": "Mumbai",
        "occupation": "salaried",
        "employer_type": "mnc",
        "income_tier": "high",
        "monthly_income": 120000.0,
        "account_open_date": (datetime.utcnow().date() - timedelta(days=365 * 6)).isoformat(),
        "has_personal_loan": False,
        "has_credit_card": True,
        "has_home_loan": False,
    }
    base.update(overrides)
    return base


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0


def test_strong_prospect_scores_high():
    cust = _customer()
    txns = [_txn("salary", "credit", 120000, d) for d in (5, 35, 65, 95, 125, 155)]
    txns += [_txn("emi", "debit", 8000, d) for d in (10, 40, 70)]
    s = score_customer(cust, txns, target_product="personal_loan")
    assert s.score >= 70
    # The "no existing personal loan" factor must contribute fully
    no_existing = next(f for f in s.factors if f.name == "no_existing")
    assert no_existing.raw == 100.0


def test_holder_of_target_product_is_penalised():
    cust = _customer(has_personal_loan=True)
    txns = [_txn("salary", "credit", 120000, d) for d in (5, 35, 65)]
    s = score_customer(cust, txns, target_product="personal_loan")
    no_existing = next(f for f in s.factors if f.name == "no_existing")
    assert no_existing.raw == 0.0


def test_low_income_low_tenure_low_score():
    cust = _customer(
        income_tier="low",
        monthly_income=18000,
        account_open_date=(datetime.utcnow().date() - timedelta(days=120)).isoformat(),
    )
    s = score_customer(cust, [], target_product="personal_loan")
    assert s.score < 50


def test_top_factors_returns_largest_contributors_sorted():
    cust = _customer()
    s = score_customer(cust, [], target_product="personal_loan")
    tops = top_factors(s, n=3)
    assert len(tops) == 3
    assert tops[0].contribution >= tops[1].contribution >= tops[2].contribution


def test_no_target_product_neutral_factor():
    cust = _customer()
    s = score_customer(cust, [], target_product=None)
    no_existing = next(f for f in s.factors if f.name == "no_existing")
    assert no_existing.raw == 50.0
