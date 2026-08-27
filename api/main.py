"""FastAPI app. Owner: Ian. Keep CORS open, this is a demo.

Data is loaded once at startup, including the min/max used to normalise
median_inflow across the dataset. If data/households.json lands after the
server is already running, restart the server.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Works whether you launch as `uvicorn main:app` from api/ or
# `uvicorn api.main:app` from the repo root. On stage, both should work.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm  # noqa: E402
import scoring  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("corridor-credit")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "households.json"
FIXTURE_FILE = ROOT / "fixtures" / "mock_response.json"
AUDIT_FILE = Path(__file__).resolve().parent / "audit.log"

app = FastAPI(title="Corridor Credit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load():
    """Load households, or fall back to the fixture so the API is never down.

    Returns (households, corpus_min, corpus_max, fixture_or_None). When the
    fixture is in play we serve it verbatim for its own id and 404 everything
    else - we do not invent households.
    """
    try:
        records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        records = []
        log.warning("could not read %s (%s)", DATA_FILE, exc)

    if records:
        lo, hi = scoring.corpus_median_bounds(records)
        log.info("loaded %d households, median range %.0f-%.0f EGP",
                 len(records), lo, hi)
        return records, lo, hi, None

    log.warning("data/households.json missing or empty - serving %s instead. "
                "Only the fixture household is available.", FIXTURE_FILE.name)
    fixture = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    return [], 0.0, 0.0, fixture


HOUSEHOLDS, CORPUS_MIN, CORPUS_MAX, FIXTURE = _load()
BY_ID = {h["id"]: h for h in HOUSEHOLDS}


@app.get("/health")
def health():
    return {
        "ok": True,
        "households": len(BY_ID) if not FIXTURE else 1,
        "source": "fixture" if FIXTURE else "data",
    }


@app.get("/households")
def households():
    """Picker list for the web app. Frozen keys: id, governorate, corridor."""
    if FIXTURE:
        source = [FIXTURE]
    else:
        source = HOUSEHOLDS
    return [
        {
            "id": h["id"],
            "governorate": h.get("governorate", ""),
            "corridor": h.get("corridor", ""),
        }
        for h in source
    ]


@app.get("/score/{household_id}")
def score(household_id: str):
    """Full payload from docs/CONTRACT.md.

    Returned as a plain dict on purpose - no response_model, because Pydantic
    would reorder and strip keys and the contract freezes field ordering.
    """
    if FIXTURE:
        if household_id == FIXTURE["id"]:
            # No audit line here on purpose. The fixture was hand-written, not
            # computed, so logging it would put a row in audit.log that nothing
            # can reproduce - and reproducibility is the whole claim.
            # Copy, so the shared fixture dict is never mutated in place.
            return {**FIXTURE, "llm_used": False}
        return _unknown()

    household = BY_ID.get(household_id)
    if household is None:
        return _unknown()

    payload = scoring.score_household(household, CORPUS_MIN, CORPUS_MAX)

    # Layer 2, optional: reword the two sentences only. The score, tier,
    # features and products above are already final and are never sent to,
    # or read back from, the model.
    payload["explanation_en"], payload["explanation_ar"], used_llm = llm.rewrite(
        payload["explanation_en"], payload["explanation_ar"]
    )
    # Appended after explanation_ar, so nothing in the frozen ordering shifts.
    # web/index.html reads this to label the explanation Granite or template.
    payload["llm_used"] = used_llm
    _audit(payload, "granite" if used_llm else
           ("fallback" if llm.enabled() else "off"))
    return payload


def _audit(payload: dict, llm_state: str):
    """One JSON line per scored decision. Open it on stage: every decision here
    is reproducible from the features and weights recorded next to it."""
    line = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "id": payload["id"],
        "features": {k: f["value"] for k, f in payload["features"].items()},
        "weights": scoring.WEIGHTS,
        "score": payload["score"],
        "tier": payload["tier"],
        "model_version": scoring.MODEL_VERSION,
        "llm": llm_state,  # granite | fallback | off
    }
    try:
        with AUDIT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError as exc:  # never let logging break a demo response
        log.warning("audit write failed: %s", exc)


def _unknown():
    # Not HTTPException: that emits {"detail": ...} and the contract says
    # {"error": ...}.
    return JSONResponse(status_code=404, content={"error": "unknown household"})
