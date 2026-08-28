# CORRIDOR CREDIT - BACKEND TASK BRIEF

## 1. THE SITUATION

We are three developers at an IBM developer event in a 2 hour hackathon. The
brief was: pick an African country, pick a sector, build a solution. We chose
Egypt, fintech, and a product called Corridor Credit.

This is a DEMO, not a product. Optimise every decision for "works on stage in
90 seconds", never for scale, security, or extensibility. Code that is elegant
but unfinished loses. Code that is crude and running wins.

## 2. THE PROBLEM WE ARE SOLVING

Egypt received a record ~$47 billion in remittances in the fiscal year ending
June 2026, mostly from Egyptians working in the Gulf. Around 78% of Egyptian
adults now hold an active financial account, so basic access is largely solved.

The unsolved problem is what happens to that money after it lands. A household
can receive steady, reliable transfers for five years and remain completely
invisible to a lender, because inbound remittances do not build a credit file.
Meanwhile SME and consumer lending keeps flowing to borrowers who already have
collateral, so the households generating Egypt's largest stable hard-currency
inflow get none of the credit benefit of it.

Corridor Credit is a consent-based scoring layer. A household shares its
transfer history, we read the STABILITY of those inflows rather than the size,
and that stability becomes a portable financial identity that unlocks savings,
nano-credit, and school-fee smoothing. Crucially, every decision comes with a
plain-language reason in Arabic and English, because a score you cannot
challenge is not financial inclusion.

The pitch line: Egypt already moves the money. We make the money count as proof.

## 3. WHAT THE JUDGES WILL ACTUALLY SEE

The entire demo is two clicks:
  1. Open the web page, select household EG-0007. Steady sender. Score ~78,
     tier B. Four feature bars. Read the Arabic explanation out loud.
  2. Switch to household EG-0142. Same total money, erratic arrival. Score ~41,
     tier D. Same four bars, visibly different shape. Read that explanation.

If any change you make risks that path, do not make the change. The explanation
is the money shot, not the number.

## 4. THE TEAM, WORKING IN PARALLEL RIGHT NOW

- Dev B owns web/index.html. They are already coding against
  fixtures/mock_response.json and will point at my live API when I say it is up.
  I must not change any field name, type, nesting, or ordering in the response.
- Dev C owns data/generate.py and will commit data/households.json shortly,
  then moves to the deck. I must NOT block waiting on that file.
- I own api/ only. Do not create, edit, or delete anything outside api/, except
  the doc cleanup in section 10.

## 5. MY TASK

Implement two endpoints, plus the scoring logic behind them.

GET /households
  -> [{ "id": "EG-0007", "governorate": "Sharqia", "corridor": "KSA-EGY" }, ...]

GET /score/{id}
  -> the full payload defined in docs/CONTRACT.md. Read that file. It is frozen.
     Unknown id returns HTTP 404 with {"error": "unknown household"}.

Data source: data/households.json. Each record has `monthly_inflows_egp`, an
array of exactly 24 numbers, oldest first, where 0 means no transfer arrived
that month. If that file is missing or empty, fall back to serving
fixtures/mock_response.json so the API is never down. Log a warning when you do.

## 6. SCORING SPEC (api/scoring.py)

Pure arithmetic. Four features, each normalised to 0.0 - 1.0.

1. regularity
   Share of the 24 months with a non-zero inflow. Simple ratio.

2. median_inflow
   Median of the non-zero inflows, min-max normalised across ALL households in
   the dataset, clamped to 0.0 - 1.0. Compute the min and max once at startup.

3. shock_recovery
   How fast inflows return to the household's own median after a zero month.
   1.0 if recovery happens the next month, decaying toward 0.0 the longer it
   takes. Return 1.0 when there are no zero months at all.

4. trend
   Mean of the last 12 months versus the mean of the first 12, mapped onto
   0.0 - 1.0 where 0.5 means flat. Clamp the extremes.

Weights: regularity 0.35, shock_recovery 0.25, median_inflow 0.20, trend 0.20.

score = round(100 * sum(value * weight))
tier  = A if >=80, B if >=60, C if >=40, else D

Product unlocking:
  Auto-save on inflow    -> always unlocked
  Emergency nano-credit  -> unlocked when score >= 55
  School-fee smoothing   -> unlocked when score >= 75

Consumer protection rule, and state it in the payload detail string: nano-credit
is capped at 60% of one month's median inflow. We say this on stage.

## 7. THE EXPLANATION LAYER

Two strings, explanation_en and explanation_ar. Both are ALWAYS present, never
null, never empty. One sentence each. They must name the strongest feature and
the weakest feature, so the user learns what to improve.

Build it in two layers, in this order:

Layer 1, ship this FIRST and never remove it:
  A deterministic template. Pick the highest-weighted-contribution feature and
  the lowest, slot them into pre-written English and Arabic sentence templates.
  Zero dependencies, zero latency, cannot fail. Write the Arabic templates as
  simple Modern Standard Arabic. A native speaker on our team will review them.

Layer 2, only after Layer 1 is committed and working:
  Optional local LLM rewrite for a more natural sentence, via Ollama.
    - Endpoint: http://localhost:11434/api/generate
    - Model: granite4.2:3b   (IBM Granite, Apache 2.0, running locally)
      If that tag is unavailable, fall back to granite4.1:8b, then to
      whatever `ollama list` shows. Read the model name from an env var
      GRANITE_MODEL with a default, so we can swap it without a code change.
    - Hard timeout: 3 seconds.
    - Wrap the whole call in try/except. ANY error, timeout, refused
      connection, malformed output, or empty string falls back silently to the
      Layer 1 template. The demo must run identically with Ollama switched off.
    - Enable it with an env var USE_LLM=1, default OFF.

The LLM NEVER touches the score. It only rewords an explanation we already
computed. Say that clearly in a code comment, because a judge will ask.

## 8. AUDIT LOG (our open-source answer to model governance)

Every /score call appends one JSON line to api/audit.log:
  timestamp, household id, the four raw feature values, the weights used,
  the final score, the tier, the model version string, and whether the LLM
  layer was used or fell back.

Keep it to about 15 lines of code. It exists so we can open the file on stage
and say "every decision is reproducible and auditable by the regulator".

## 9. HARD CONSTRAINTS

- Fully open source. No proprietary SaaS, no API keys, no hosted inference.
- Deterministic. Identical input always yields identical output. Judges re-run.
- No database, no auth, no caching layer, no ORM, no async workers.
- Dependencies: fastapi and uvicorn only. Standard library for everything else.
  No pandas, no numpy, no scikit-learn. Ask me before adding anything.
- CORS stays wide open. This is a demo.
- Everything runs offline. Assume venue wifi will fail, because it will.

## 10. DOC CLEANUP

Remove all watsonx, watsonx.governance, watsonx.data and Hyper Protect
references from README.md, CLAUDE.md, docs/DEMO_SCRIPT.md and
docs/MODEL_CARD.md. Replace with: local Ollama running IBM Granite under
Apache 2.0, plus the JSON audit log and the model card as the governance story.
Do not restructure those files, just swap the stack references.

## 11. HOW TO WORK

Plan first. Give me exactly 5 bullets covering your approach plus any ambiguity
or contradiction you find in this brief. Then STOP and wait for my approval.

After approval:
  Step 1  Implement api/scoring.py in full. Stop for my review.
  Step 2  Implement api/main.py wiring the endpoints. Stop for my review.
  Step 3  Add the Layer 2 Ollama call and the audit log. Stop.
  Step 4  Do the doc cleanup.

Do not refactor code you were not asked to touch. Do not add tests unless I ask.

## 12. DEFINITION OF DONE

Run the server and show me the literal terminal output for:

  curl -s localhost:8000/health
  curl -s localhost:8000/households | head -c 300
  curl -s localhost:8000/score/EG-0007
  curl -s localhost:8000/score/EG-0142
  curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/score/EG-9999

I need to paste the EG-0007 response to Dev B as proof the contract holds, so
give it to me as raw JSON I can copy in one block.