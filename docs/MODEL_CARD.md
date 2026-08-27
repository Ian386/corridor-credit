# Model card (demo artifact)

Owner: Dev C. One page. Judges love this and nobody builds it.

- **Purpose** Assess repayment capacity of remittance-receiving households.
- **Inputs** 24 months of inbound transfer amounts. No demographic inputs.
- **Explicitly excluded** Gender, age, religion, governorate. State this out loud.
- **Output** Score 0-100, tier A-D, four contributing factors with weights.
- **Human override** Any decline can be appealed to a human reviewer.
- **Consumer protection** Credit capped at 60% of one month's median inflow.
- **Known limitations** Trained on synthetic data. Not validated on real portfolios.
- **Audit** Every request logged with inputs, weights, output and model version.
