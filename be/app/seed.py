"""
Faker seeder for the Banking CRM demo.

Run from be/:
    python -m app.seed

Generates:
  • 4 products
  • ~400 customers across 10 Indian metros, tiered by income
  • 12 months of transactions per customer (~50 each)
  • ~15% of customers deliberately shaped as strong personal-loan prospects
    (high income, no existing personal loan, stable salary, EMI spend pattern)
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from faker import Faker

from .db import get_db

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Gurgaon",
]

OCCUPATIONS = ["salaried", "self_employed", "business_owner"]
EMPLOYER_TYPES = ["mnc", "startup", "govt", "sme", "self"]
INCOME_TIERS = ["low", "mid", "high", "premium"]

PRODUCTS = [
    {
        "code": "personal_loan",
        "name": "Personal Loan",
        "type": "loan",
        "min_income": 30000,
        "target_segment": "any",
        "interest_rate": 12.5,
        "tenure_months": 36,
        "max_amount": 2_500_000,
    },
    {
        "code": "credit_card",
        "name": "Platinum Credit Card",
        "type": "card",
        "min_income": 25000,
        "target_segment": "any",
        "interest_rate": 36.0,
        "tenure_months": None,
        "max_amount": 500_000,
    },
    {
        "code": "savings_plus",
        "name": "Savings Plus Account",
        "type": "deposit",
        "min_income": 0,
        "target_segment": "any",
        "interest_rate": 6.5,
        "tenure_months": None,
        "max_amount": None,
    },
    {
        "code": "home_loan",
        "name": "Home Loan",
        "type": "loan",
        "min_income": 80000,
        "target_segment": "salaried",
        "interest_rate": 8.6,
        "tenure_months": 240,
        "max_amount": 30_000_000,
    },
]

# Income tier → monthly INR range
TIER_INCOME = {
    "low": (15_000, 30_000),
    "mid": (30_000, 80_000),
    "high": (80_000, 200_000),
    "premium": (200_000, 600_000),
}
# Tier distribution (sums to 1.0)
TIER_WEIGHTS = {"low": 0.15, "mid": 0.35, "high": 0.30, "premium": 0.20}


def pick_tier() -> str:
    r = random.random()
    cum = 0.0
    for tier, w in TIER_WEIGHTS.items():
        cum += w
        if r <= cum:
            return tier
    return "mid"


def gen_phone() -> str:
    return f"+91{random.randint(70000, 99999)}{random.randint(10000, 99999)}"


def make_customer(*, force_prospect: bool = False) -> dict:
    """Build one customer dict ready for Supabase insert."""
    tier = "high" if force_prospect else pick_tier()
    low, high = TIER_INCOME[tier]
    monthly = round(random.uniform(low, high), 2)

    occupation = "salaried" if force_prospect else random.choice(OCCUPATIONS)
    employer = (
        random.choice(["mnc", "startup", "sme"])
        if occupation == "salaried"
        else random.choice(["sme", "self"])
    )

    age = random.randint(25, 55) if force_prospect else random.randint(22, 65)
    opened = fake.date_between(start_date="-8y", end_date="-1y")

    if force_prospect:
        has_pl, has_cc, has_hl = False, random.random() < 0.5, False
    else:
        has_pl = random.random() < 0.18
        has_cc = random.random() < 0.45
        has_hl = random.random() < 0.10

    return {
        "name": fake.name(),
        "age": age,
        "city": random.choice(CITIES),
        "occupation": occupation,
        "employer_type": employer,
        "income_tier": tier,
        "monthly_income": monthly,
        "account_open_date": opened.isoformat(),
        "has_personal_loan": has_pl,
        "has_credit_card": has_cc,
        "has_home_loan": has_hl,
        "phone": gen_phone(),
        "email": fake.unique.email(),
    }


def make_transactions(customer: dict, *, force_prospect: bool = False) -> list[dict]:
    """Generate ~12 months of transactions for a customer."""
    txns: list[dict] = []
    cid = customer["id"]
    monthly = float(customer["monthly_income"])
    is_salaried = customer["occupation"] == "salaried"

    end = datetime.utcnow()
    for month_back in range(12):
        month_start = (end - timedelta(days=30 * (month_back + 1))).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Salary credit (salaried only)
        if is_salaried:
            txns.append({
                "customer_id": cid,
                "amount": round(monthly, 2),
                "direction": "credit",
                "category": "salary",
                "description": "Monthly salary credit",
                "created_at": (month_start + timedelta(days=random.randint(1, 3))).isoformat(),
            })
        else:
            # Business credits — lumpier
            for _ in range(random.randint(1, 4)):
                txns.append({
                    "customer_id": cid,
                    "amount": round(random.uniform(0.2, 0.5) * monthly, 2),
                    "direction": "credit",
                    "category": "transfer",
                    "description": "Business receipt",
                    "created_at": (month_start + timedelta(days=random.randint(2, 28))).isoformat(),
                })

        # Rent
        if random.random() < 0.85:
            txns.append({
                "customer_id": cid,
                "amount": round(monthly * random.uniform(0.18, 0.32), 2),
                "direction": "debit",
                "category": "rent",
                "description": "Rent payment",
                "created_at": (month_start + timedelta(days=random.randint(2, 5))).isoformat(),
            })

        # Utilities
        for _ in range(random.randint(1, 3)):
            txns.append({
                "customer_id": cid,
                "amount": round(random.uniform(800, 4500), 2),
                "direction": "debit",
                "category": "utility",
                "description": "Utility bill",
                "created_at": (month_start + timedelta(days=random.randint(5, 27))).isoformat(),
            })

        # EMIs — prospects get more (signal: they're managing debt and could consolidate)
        emi_count = 2 if force_prospect else (1 if random.random() < 0.5 else 0)
        for _ in range(emi_count):
            txns.append({
                "customer_id": cid,
                "amount": round(random.uniform(3500, 15000), 2),
                "direction": "debit",
                "category": "emi",
                "description": "Existing EMI",
                "created_at": (month_start + timedelta(days=random.randint(3, 10))).isoformat(),
            })

        # Shopping / discretionary
        for _ in range(random.randint(3, 7)):
            txns.append({
                "customer_id": cid,
                "amount": round(random.uniform(300, monthly * 0.08), 2),
                "direction": "debit",
                "category": "shopping",
                "description": fake.bs().title()[:40],
                "created_at": (month_start + timedelta(days=random.randint(1, 28))).isoformat(),
            })

    return txns


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def main(n_customers: int = 400, prospect_ratio: float = 0.15) -> None:
    db = get_db()

    print("→ Seeding products …")
    db.table("products").insert(PRODUCTS).execute()

    n_prospects = int(n_customers * prospect_ratio)
    print(f"→ Seeding {n_customers} customers ({n_prospects} forced prospects) …")

    rows = []
    for i in range(n_customers):
        rows.append(make_customer(force_prospect=i < n_prospects))

    # Insert in chunks; capture returned ids
    inserted: list[dict] = []
    for chunk in chunked(rows, 100):
        res = db.table("customers").insert(chunk).execute()
        inserted.extend(res.data)

    print(f"  inserted {len(inserted)} customers")

    print("→ Seeding transactions …")
    total_txns = 0
    for i, cust in enumerate(inserted):
        is_prospect = i < n_prospects
        txns = make_transactions(cust, force_prospect=is_prospect)
        for chunk in chunked(txns, 200):
            db.table("transactions").insert(chunk).execute()
        total_txns += len(txns)
        if (i + 1) % 50 == 0:
            print(f"  …{i + 1}/{len(inserted)} customers ({total_txns} txns so far)")

    print(f"✓ Done. {len(inserted)} customers, {total_txns} transactions, {len(PRODUCTS)} products.")


if __name__ == "__main__":
    main()
