"""Deterministic scoring. Owner: Ian. See docs/CONTRACT.md.

Pure arithmetic, standard library only. No randomness, no clock, no network.
Same household in, same score out - judges will re-run this.

The LLM layer (api/main.py) NEVER touches anything in this file. It only
rewords explanation strings that were already computed here.
"""
from statistics import median

MODEL_VERSION = "corridor-credit-scoring-1.0"

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

# Frozen ordering from docs/CONTRACT.md. Also the deterministic tie-break order
# when two features have an identical weighted contribution.
FEATURE_ORDER = ("regularity", "median_inflow", "shock_recovery", "trend")


# ---------------------------------------------------------------- features

def regularity(inflows: list) -> float:
    """Share of months with a non-zero inflow."""
    if not inflows:
        return 0.0
    return sum(1 for v in inflows if v > 0) / len(inflows)


def raw_median_inflow(inflows: list) -> float:
    """Median of the non-zero inflows, in EGP. 0.0 if nothing ever arrived."""
    received = [v for v in inflows if v > 0]
    if not received:
        return 0.0
    return float(median(received))


def normalised_median(raw: float, corpus_min: float, corpus_max: float) -> float:
    """Min-max the household median across the whole dataset, clamped 0-1.

    A degenerate corpus (one household, or every median identical) has no
    spread to normalise against, so everyone sits mid-scale at 0.5.
    """
    if corpus_max <= corpus_min:
        return 0.5
    return _clamp((raw - corpus_min) / (corpus_max - corpus_min))


def shock_recovery(inflows: list) -> float:
    """How fast inflows climb back to the household's own median after a gap.

    Rules, fixed so the number is reproducible:
      - Leading zeros before the first ever transfer are not a shock, they are
        just a household that started receiving later. Skipped.
      - Consecutive zeros count as ONE gap.
      - Recovery lag k = months from the first zero of the gap to the first
        month at or above the household's own median. Next month -> k=1 -> 1.0,
        then 1/k decay: 0.50, 0.33, 0.25 ...
      - A gap that never recovers before the series ends scores 0.0.
      - Several gaps -> the mean of their scores.
      - No gaps at all -> 1.0.
    """
    own_median = raw_median_inflow(inflows)
    if own_median <= 0:
        return 0.0

    first_inflow = next((i for i, v in enumerate(inflows) if v > 0), None)
    if first_inflow is None:
        return 0.0

    scores = []
    i = first_inflow
    n = len(inflows)
    while i < n:
        if inflows[i] > 0:
            i += 1
            continue
        gap_start = i
        while i < n and inflows[i] == 0:  # consume the whole run of zeros
            i += 1
        recovered_at = next(
            (j for j in range(i, n) if inflows[j] >= own_median), None
        )
        if recovered_at is None:
            scores.append(0.0)
        else:
            scores.append(1.0 / (recovered_at - gap_start))

    if not scores:
        return 1.0
    return sum(scores) / len(scores)


def trend(inflows: list) -> float:
    """Second half against the first half, mapped onto 0-1 where 0.5 is flat.

    0.5 * (1 + (late - early) / (late + early)) is bounded by construction, so
    a household that doubles cannot run away with the score. Both halves empty
    (never received anything) is flat by definition.
    """
    if not inflows:
        return 0.5
    half = len(inflows) // 2
    early = _mean(inflows[:half])
    late = _mean(inflows[half:])
    if early + late == 0:
        return 0.5
    return _clamp(0.5 * (1 + (late - early) / (late + early)))


# ---------------------------------------------------------------- corpus

def corpus_median_bounds(households: list) -> tuple:
    """Min and max household median across the dataset. Computed once at startup."""
    medians = [raw_median_inflow(h.get("monthly_inflows_egp", [])) for h in households]
    medians = [m for m in medians if m > 0]
    if not medians:
        return (0.0, 0.0)
    return (min(medians), max(medians))


# ---------------------------------------------------------------- payload

def tier_for(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def build_products(score: int, raw_median: float) -> list:
    """Frozen names, order and count. Only detail and unlocked move.

    Consumer protection: nano-credit is capped at 60% of one month of median
    inflow, and we say so in the string because we say it on stage.
    """
    cap = int(round(0.6 * raw_median))
    return [
        {
            "name": "Auto-save on inflow",
            "detail": "5% swept on every transfer",
            "unlocked": True,
        },
        {
            "name": "Emergency nano-credit",
            "detail": f"Up to EGP {cap:,} (60% of one month of median inflow)",
            "unlocked": score >= 55,
        },
        {
            "name": "School-fee smoothing",
            "detail": "Term fees over 6 months",
            "unlocked": score >= 75,
        },
    ]


# Layer 1 explanation: deterministic templates. Ships first, never removed.
# Zero dependencies, zero latency, cannot fail. The optional Ollama rewrite in
# main.py is polish on top of these strings and falls back to them.
PHRASES_EN = {
    "regularity": "how regularly transfers arrive",
    "median_inflow": "the typical size of each transfer",
    "shock_recovery": "how quickly transfers recover after a missed month",
    "trend": "the direction of transfers over two years",
}

PHRASES_AR = {
    "regularity": "انتظام وصول التحويلات",
    "median_inflow": "قيمة التحويل المعتادة",
    "shock_recovery": "سرعة التعافي بعد شهر بلا تحويل",
    "trend": "اتجاه التحويلات خلال العامين الماضيين",
}


def explain(score: int, tier: str, strongest: str, weakest: str) -> tuple:
    """One sentence each, always present, naming the best and worst feature."""
    en = (
        f"A score of {score} (tier {tier}) is supported most by "
        f"{PHRASES_EN[strongest]}, and held back most by {PHRASES_EN[weakest]}."
    )
    ar = (
        f"أقوى ما يدعم الدرجة {score} (الفئة {tier}) هو {PHRASES_AR[strongest]}، "
        f"وأضعف عنصر فيها هو {PHRASES_AR[weakest]}."
    )
    return en, ar


def score_household(household: dict, corpus_min: float = 0.0,
                    corpus_max: float = 0.0) -> dict:
    """Full /score/{id} payload from docs/CONTRACT.md, in frozen key order."""
    inflows = household.get("monthly_inflows_egp", [])
    raw_median = raw_median_inflow(inflows)

    # Round to 2dp BEFORE weighting, so the four bars the judge sees on screen
    # add up by hand to the score printed next to them.
    values = {
        "regularity": round(regularity(inflows), 2),
        "median_inflow": round(normalised_median(raw_median, corpus_min, corpus_max), 2),
        "shock_recovery": round(shock_recovery(inflows), 2),
        "trend": round(trend(inflows), 2),
    }

    score = int(round(100 * sum(values[k] * WEIGHTS[k] for k in FEATURE_ORDER)))
    tier = tier_for(score)

    contributions = {k: values[k] * WEIGHTS[k] for k in FEATURE_ORDER}
    ranked = sorted(
        FEATURE_ORDER,
        key=lambda k: (-contributions[k], FEATURE_ORDER.index(k)),
    )
    strongest, weakest = ranked[0], ranked[-1]
    explanation_en, explanation_ar = explain(score, tier, strongest, weakest)

    return {
        "id": household["id"],
        "governorate": household.get("governorate", ""),
        "corridor": household.get("corridor", ""),
        "score": score,
        "tier": tier,
        "features": {
            k: {"value": values[k], "label": LABELS[k], "weight": WEIGHTS[k]}
            for k in FEATURE_ORDER
        },
        "products": build_products(score, raw_median),
        "explanation_en": explanation_en,
        "explanation_ar": explanation_ar,
    }


# ---------------------------------------------------------------- helpers

def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _mean(xs: list) -> float:
    if not xs:
        return 0.0
    return sum(xs) / len(xs)
