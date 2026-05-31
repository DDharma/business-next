from __future__ import annotations

PRODUCT_HAS_COLUMN: dict[str, str] = {
    "personal_loan": "has_personal_loan",
    "credit_card": "has_credit_card",
    "home_loan": "has_home_loan",
}

TIER_PREFERENCE: dict[str, list[str]] = {
    "premium": ["home_loan", "personal_loan", "credit_card"],
    "high": ["personal_loan", "home_loan", "credit_card"],
    "mid": ["personal_loan", "credit_card", "savings_plus"],
    "low": ["savings_plus", "credit_card"],
}

SCORING_WEIGHTS: dict[str, float] = {
    "income_tier": 0.25,
    "salary_stability": 0.20,
    "balance_trend": 0.15,
    "no_existing": 0.15,
    "emi_signal": 0.10,
    "tenure": 0.10,
    "age_band": 0.05,
}

TIER_RAW: dict[str, float] = {
    "low": 30.0,
    "mid": 60.0,
    "high": 85.0,
    "premium": 100.0,
}

DEFAULT_TOP_N = 5
MAX_CANDIDATES = 80
TXN_WINDOW_DAYS = 180
TENURE_CAP_YEARS = 5.0
AGE_BAND_PEAK = 35
AGE_BAND_MIN = 28
AGE_BAND_MAX = 50

CHAT_TITLE_MAX_LEN = 80
SIDEBAR_CHAT_LIMIT = 50
