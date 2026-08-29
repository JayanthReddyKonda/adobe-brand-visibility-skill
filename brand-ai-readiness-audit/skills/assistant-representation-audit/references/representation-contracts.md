# Assistant Representation — Check Contracts

This skill is an **optional enrichment layer**: it compares observed AI
assistant responses against the brand's first-party fact base. It must work
with zero API access — when no observations are supplied, it reports
`status: "not_observed"` and produces NO findings.

## CHECK 1: Claim accuracy cross-check

- **Measures**: Factual claims in supplied AI responses (price, specs,
  availability, category) vs the fact ledger built from the site.
- **Evidence required**: A supplied observation file (`--observations file.json`)
  containing assistant responses plus the site fact ledger.
- **Defect**: A specific value conflict (AI says ₹4,999; site says ₹5,499).
- **NOT a defect**: Vague or hedged responses; absence of the brand from a
  response (that is a visibility outcome, not a representation error).
- **Severity conditions**: high for material factual conflicts (price,
  availability, safety-relevant specs); medium for secondary attributes.
- **Confidence**: high only when both sources are explicit and dated;
  otherwise medium/low.

## CHECK 2: Unsupported claim detection

- **Measures**: Claims in AI responses that no first-party source supports.
- **Defect**: A specific, falsifiable claim about the brand with no site
  corroboration (candidate hallucination condition).
- **NOT a defect**: General industry statements, opinions, competitor claims.
- **Framing**: Reported as "hallucination *conditions*", never as
  "the AI will hallucinate".

## Stochastic discipline

Never conclude from a single response. When multiple runs per platform are
supplied, compute per-platform rates (mention, citation, claim accuracy) and
report platforms separately — do not collapse them into one universal score.
