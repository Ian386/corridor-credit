# CLAUDE.md - Corridor Credit

## Project
A 2 hour hackathon demo. Country: Egypt. Sector: Fintech.
We score a household's inbound remittance history and turn it into a credit
identity, then explain the decision in plain Arabic and English.

## Non-negotiables
- Total build time is 2 hours across 3 people. Optimise for demo, not production.
- No database. No authentication. No user accounts. No build tooling for the web app.
- No new dependencies beyond what is already in requirements.txt without asking.
- `docs/CONTRACT.md` defines the data schema and API. It is frozen. Do not change
  field names, types, or ordering. Other team members are coding against it right now.
- Deterministic output. Same household in, same score out. Judges will re-run it.

## Operating mode
Plan before code. State the plan in 5 bullets, wait for approval, then implement.
Work in small increments and stop for review after each file.
Do not refactor code you were not asked to touch.

## Stack
- API: Python 3, FastAPI, uvicorn. CORS wide open (demo only).
- Web: one `index.html`, vanilla JS, no framework, no npm.
- Data: plain JSON committed to the repo. No generation at runtime.
- LLM: Anthropic/watsonx call for the explanation string only. Never for scoring.

## Demo path that must never break
Open the page, pick household `EG-0007` (high score), read the explanation,
switch to `EG-0142` (low score), read the explanation. That is the whole demo.
If a change risks that path, do not make it.
