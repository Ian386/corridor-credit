# Model card (demo artifact)

Owner: Dev C. One page. Judges love this and nobody builds it.

- **Purpose** Assess repayment capacity of remittance-receiving households.
- **Inputs** 24 months of inbound transfer amounts. No demographic inputs.
- **Explicitly excluded** Gender, age, religion, governorate. State this out loud.
- **Output** Score 0-100, tier A-D, four contributing factors with weights.
- **Human override** Any decline can be appealed to a human reviewer.
- **Consumer protection** Credit capped at 60% of one month's median inflow.
- **Known limitations** Trained on synthetic data. Not validated on real portfolios.
- **Scoring model** Deterministic arithmetic, no machine learning, no black box.
- **Explanation model** IBM Granite on local Ollama, Apache 2.0, offline, optional.
  It rewords an explanation the scorer already produced. It never sees the score.
- **Audit** Every request logged to `api/audit.log` as one JSON line with inputs,
  weights, output, model version and whether the explanation was Granite or template.
