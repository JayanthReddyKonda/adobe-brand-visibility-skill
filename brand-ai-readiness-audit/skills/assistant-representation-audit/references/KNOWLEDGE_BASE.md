# ASSISTANT-REPRESENTATION-AUDIT KNOWLEDGE BASE

This document contains all mandatory rules, schemas, and taxonomies required for this skill.



========================================================================
=== SOURCE FILE: representation-contracts.md ===
========================================================================

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


========================================================================
=== SOURCE FILE: mention-vs-citation.md ===
========================================================================

# Mention vs Citation (assistant-representation reference)

Internal reference clarifying how AI representation is measured. It deliberately
keeps separate concepts that are easy to conflate, and it refuses to collapse
representation into a single opaque "AI visibility" number.

## Mention ≠ Citation

These are distinct outcomes and must not be merged:

- **Mention** — a brand name surfaced in an AI answer's text.
- **Citation** — an explicit source/link the AI attributes the claim to.
- **Claim accuracy** — whether the surfaced claim is factually correct about
  the brand.

A domain can be cited without the brand being explicitly mentioned, and a brand
can be mentioned without a citable source. Each is recorded independently:

```json
{ "mentioned": true, "cited": true, "claim_accuracy": "accurate" }
```

Never collapse into `AI visibility = 1`.

## Topic and fact coverage

AI retrieval often fans a query out into related subtopics and supporting facts
before composing an answer. So representation depends less on matching one exact
phrase and more on whether the site supports the underlying topics and facts a
multi-step retrieval process may need.

- We inspect a site's own content for *topic coverage* and *answerability*.
- We do NOT assert "missing topic = invisibility." We assert the defensible
  version: "Important adjacent topic is not supported by first-party content,
  reducing the site's ability to serve relevant information for that intent
  cluster." That is a content **opportunity**, not a defect verdict.

## Source corroboration framing

Where competitors are supplied (or derived from public search), a citation-
source gap is reported only as the defensible claim:

> "Important category claims have weak independent corroboration compared with
> competing entities."

not as "you need backlinks." We do not pretend to have any commercial prompt
corpus; coverage is derived from first-party content + public signals + any
supplied competitor set.

## What this skill verifies in this marketplace build

- The orchestrator's entity layer (entity-content-audit) establishes the brand
  entity and its first-party facts.
- This skill can consume a supplied corpus of third-party mentions/citations to
  report mention-vs-citation vs claim-accuracy.
- When no external corpus is provided, it reports `inconclusive` rather than
  inventing representation data — absence of evidence is never recorded as a
  clean or negative claim.
