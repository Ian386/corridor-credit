# Full Names
Ian Ndolo Mwau
Tyrese Muigai
Francis Kimani

# Collaborators Git Usernames

ian386
Muigaihacks
ChaserFrank


# Corridor Credit

Egypt receives a record volume of remittances every year, and the households
receiving that money still cannot get a loan, because inbound transfers do not
build a credit file. Corridor Credit is a consent-based scoring layer that turns
remittance and wallet history into a portable financial identity.

Built at the IBM developer event. 2 hour build.

## Run it

Terminal 1 (API):
    cd api
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Optional, natural-language explanations via local IBM Granite (Apache 2.0):
    ollama pull granite4.2:3b
    USE_LLM=1 GRANITE_MODEL=granite4.2:3b uvicorn main:app --port 8000
    # off by default. If Ollama is not running, explanations fall back to the
    # built-in template and the demo is unchanged.

Terminal 2 (web):
    cd web
    python3 -m http.server 5500
    # open http://localhost:5500

## Who owns what

| Area              | Path        | Owner |
|-------------------|-------------|-------|
| Scoring + API     | `api/`      | Ian   |
| Single screen UI  | `web/`      | Dev B |
| Synthetic data    | `data/`     | Dev C |
| Deck + demo       | `docs/`     | Dev C |

Rules:
1. `docs/CONTRACT.md` is frozen. Changing it needs all three to agree out loud.
2. Only touch your own directory. Merge conflicts kill hackathon teams.
3. Feature freeze at T+1:30. After that, fixes only.
