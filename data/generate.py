"""Synthetic household generator. Owner: Dev C.

Writes data/households.json per docs/CONTRACT.md.
Use a fixed random seed so the demo is reproducible.

Must produce a visible spread:
  - ~20% very regular senders (these should score A)
  - ~50% regular with one or two gaps (B / C)
  - ~30% irregular or declining (D)

Guarantee EG-0007 is a strong household and EG-0142 is a weak one.
Those two ids are hardcoded in the demo script.
"""

import json
import os
import random

random.seed(42)  # Deterministic seed for reproducible scoring and demos

CORRIDORS = ["KSA-EGY", "UAE-EGY", "KWT-EGY", "QAT-EGY"]
GOVERNORATES = [
    "Cairo", "Alexandria", "Giza", "Sharqia", "Asyut",
    "Aswan", "Luxor", "Mansoura", "Tanta", "Suez",
    "Ismailia", "Beni Suef", "Minya", "Qena", "Sohag"
]

def gen_receiver_since():
    year = random.choice([2019, 2020, 2021, 2022, 2023])
    month = f"{random.randint(1, 12):02d}"
    return f"{year}-{month}"

def gen_household(idx: int) -> dict:
    hh_id = f"EG-{idx:04d}"
    corridor = random.choice(CORRIDORS)
    gov = random.choice(GOVERNORATES)
    receiver_since = gen_receiver_since()
    
    # Base monthly remittance: 3,000 to 18,000 EGP
    base_inflow = random.randint(3500, 15000)
    profile_roll = random.random()

    inflows = []
    for m in range(24):
        if profile_roll > 0.80:
            # ~20% Tier A: Very regular, 0 or 1 gap total, slight upward trend
            val = base_inflow * (1 + random.gauss(0, 0.08)) * (1 + 0.006 * m)
            if random.random() < 0.04:
                val = 0
        elif profile_roll > 0.30:
            # ~50% Tier B / C: Regular with 1–3 gaps, stable or mild trend
            val = base_inflow * (1 + random.gauss(0, 0.25))
            if random.random() < 0.16:
                val = 0
        else:
            # ~30% Tier D: Irregular, multi-month gaps, or declining
            if random.random() > 0.45:
                val = base_inflow * (1 + random.gauss(0, 0.40)) * (1 - 0.015 * m)
            else:
                val = 0
        inflows.append(max(0, int(round(val))))

    return {
        "id": hh_id,
        "governorate": gov,
        "corridor": corridor,
        "receiver_since": receiver_since,
        "monthly_inflows_egp": inflows
    }

# Hardcode demo hero households from CONTRACT.md and DEMO_SCRIPT.md
def demo_hero_steady() -> dict:
    """EG-0007: Steady KSA corridor household. Target Score ~78 (Tier B)."""
    base = 4200
    inflows = [int(round(base * (1 + random.gauss(0, 0.06)))) for _ in range(24)]
    inflows[6] = 0  # 1 gap at month 6 that recovers immediately
    inflows[7] = 4300
    return {
        "id": "EG-0007",
        "governorate": "Sharqia",
        "corridor": "KSA-EGY",
        "receiver_since": "2021-03",
        "monthly_inflows_egp": inflows
    }

def demo_hero_erratic() -> dict:
    """EG-0142: Erratic UAE corridor household with large gaps. Target Score ~41 (Tier C/D)."""
    inflows = [0] * 24
    # Only 10 months of inflows, irregular arrival
    active_months = [0, 1, 4, 7, 8, 12, 16, 17, 21, 23]
    for m in active_months:
        inflows[m] = random.randint(8000, 12000)
    return {
        "id": "EG-0142",
        "governorate": "Asyut",
        "corridor": "UAE-EGY",
        "receiver_since": "2022-08",
        "monthly_inflows_egp": inflows
    }

if __name__ == "__main__":
    records = []
    for i in range(1, 501):
        if i == 7:
            records.append(demo_hero_steady())
        elif i == 142:
            records.append(demo_hero_erratic())
        else:
            records.append(gen_household(i))

    out_path = os.path.join(os.path.dirname(__file__), "households.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(records)} households in {out_path}")

