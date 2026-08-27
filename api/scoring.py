"""Deterministic scoring. Owner: Ian. See docs/CONTRACT.md."""

WEIGHTS = {
    "regularity": 0.35,
    "median_inflow": 0.20,
    "shock_recovery": 0.25,
    "trend": 0.20,
}

LABELS = {
    "regularity": "Inflow regularity",
    "median_inflow": "Typical monthly amount",
    "shock_recovery": "Recovery after a missed month",
    "trend": "Direction over 24 months",
}


def score_household(household: dict) -> dict:
    """TODO: return the full /score/{id} payload from docs/CONTRACT.md."""
    raise NotImplementedError
