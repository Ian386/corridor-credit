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
