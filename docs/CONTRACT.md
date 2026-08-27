# FROZEN CONTRACT

Do not change anything in this file without all three team members agreeing.

## Household record (data/households.json)

An array of objects:

```json
{
  "id": "EG-0007",
  "governorate": "Sharqia",
  "corridor": "KSA-EGY",
  "receiver_since": "2021-03",
  "monthly_inflows_egp": [4100, 4200, 0, 4150, 4400]
}
```

- `id` : string, format `EG-####`, unique, stable.
- `monthly_inflows_egp` : exactly 24 numbers, oldest first. `0` means no transfer.
- `corridor` : one of `KSA-EGY`, `UAE-EGY`, `KWT-EGY`, `QAT-EGY`.

## Scoring API

`GET http://localhost:8000/households`

```json
[{ "id": "EG-0007", "governorate": "Sharqia", "corridor": "KSA-EGY" }]
```

`GET http://localhost:8000/score/{id}`

```json
{
  "id": "EG-0007",
  "score": 78,
  "tier": "B",
  "features": {
    "regularity":      { "value": 0.92, "label": "Inflow regularity",  "weight": 0.35 },
    "median_inflow":   { "value": 0.71, "label": "Typical monthly amount", "weight": 0.20 },
    "shock_recovery":  { "value": 0.84, "label": "Recovery after a missed month", "weight": 0.25 },
    "trend":           { "value": 0.55, "label": "Direction over 24 months", "weight": 0.20 }
  },
  "products": [
    { "name": "Auto-save on inflow", "detail": "5% swept on every transfer", "unlocked": true },
    { "name": "Emergency nano-credit", "detail": "Up to EGP 3,000", "unlocked": true },
    { "name": "School-fee smoothing", "detail": "Term fees over 6 months", "unlocked": false }
  ],
  "explanation_en": "Transfers arrive nearly every month and recover quickly after a gap.",
  "explanation_ar": "التحويلات تصل كل شهر تقريبا وتعود بسرعة بعد أي انقطاع."
}
```

Rules:
- Every `features` value is normalised 0.0 to 1.0. The UI renders them as bars.
- `tier` is A (80+), B (60-79), C (40-59), D (below 40).
- `score` is an integer 0 to 100.
- Both explanation strings are always present. Never null, never empty.
- On unknown id, return HTTP 404 with `{"error": "unknown household"}`.

## Fixture

`fixtures/mock_response.json` is a valid `/score/{id}` response.
The web app must work against this file alone, with the API switched off.
