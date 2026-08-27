"""Layer 2 explanation polish. Owner: Ian. Optional, off by default.

THE LLM NEVER TOUCHES THE SCORE. A judge will ask this, so it is worth saying
plainly: scoring.py has already computed the score, the tier, the four feature
values and a complete pair of explanation sentences before anything here runs.
This module only rewords sentences that already exist. If it is switched off,
times out, refuses the connection, or returns rubbish, the demo runs
identically on the Layer 1 templates.

Local IBM Granite via Ollama. No API key, no hosted inference, works offline.
"""
import json
import os
import urllib.error
import urllib.request

# 127.0.0.1, not localhost: on Windows localhost is dual-stack, so a dead
# Ollama costs the IPv6 attempt AND the IPv4 attempt, doubling the wait.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
GRANITE_MODEL = os.environ.get("GRANITE_MODEL", "granite4.2:3b")
TIMEOUT_SECONDS = 3

# Circuit breaker. If Ollama is not answering we stop asking, so a switched-off
# model costs the demo one slow call, not one slow call per click.
MAX_FAILURES = 2
_failures = 0

PROMPT = """You rewrite one-sentence credit explanations for a bank customer in Egypt.

Rewrite each sentence below so it sounds natural and human. Keep the meaning,
the numbers and the named strengths and weaknesses exactly as they are. Do not
add advice, do not add numbers, do not flatter. One sentence each.

English: {en}
Arabic: {ar}

Reply with only this JSON object and nothing else:
{{"en": "<rewritten English>", "ar": "<rewritten Arabic>"}}"""


def enabled() -> bool:
    return os.environ.get("USE_LLM", "0") == "1"


def rewrite(explanation_en: str, explanation_ar: str) -> tuple:
    """Return (en, ar, used_llm). Any failure at all returns the inputs unchanged."""
    global _failures
    if not enabled() or _failures >= MAX_FAILURES:
        return explanation_en, explanation_ar, False

    body = json.dumps({
        "model": GRANITE_MODEL,
        "prompt": PROMPT.format(en=explanation_en, ar=explanation_ar),
        "stream": False,
        # Greedy decoding: as close to reproducible as a local model gets.
        "options": {"temperature": 0, "seed": 0},
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = json.loads(resp.read().decode("utf-8")).get("response", "")

        # Granite sometimes wraps the JSON in prose or a code fence. Take the
        # outermost braces and give up quietly if that is not valid JSON.
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            _failures += 1
            return explanation_en, explanation_ar, False
        out = json.loads(raw[start:end + 1])

        en = str(out.get("en", "")).strip()
        ar = str(out.get("ar", "")).strip()
        if not en or not ar:
            _failures += 1
            return explanation_en, explanation_ar, False
        _failures = 0
        return en, ar, True

    except (urllib.error.URLError, OSError, ValueError, TypeError, KeyError):
        # Timeout, connection refused, Ollama not installed, malformed output.
        # Silent by design: the stage must never see a stack trace.
        _failures += 1
        return explanation_en, explanation_ar, False
