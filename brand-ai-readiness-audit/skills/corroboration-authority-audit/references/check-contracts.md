# Corroboration & Authority — Check Contracts

Every check in this skill follows this contract. Findings are only emitted
when the DEFECT conditions are met with direct evidence; everything else is
either INCONCLUSIVE or a proactive recommendation.

## CHECK 1: Outbound corroboration links

- **Measures**: Whether the site links out to authoritative third-party
  sources (standards bodies, registries, publications) that support its claims.
- **Evidence required**: Anchor inventory of fetched page(s).
- **Defect**: Site makes strong factual claims ("award-winning", "#1",
  certifications) with zero outbound or citation support.
- **NOT a defect**: Few outbound links on a page that makes few factual claims.
  Marketing pages legitimately link sparingly.
- **Severity conditions**: high only when specific unsupported factual claims
  are extractable from the text; otherwise low / recommendation.
- **Remediation**: Add citations or evidence pages behind the claims.

## CHECK 2: Identity consistency for corroboration

- **Measures**: Whether the site's name, domain, and profile references are
  coherent enough for third parties to corroborate the entity.
- **Evidence required**: Title/org extraction across home + internal pages.
- **Defect**: Verified contradiction (e.g., different organization names
  presented as canonical on different first-party pages).
- **NOT a defect**: Missing `sameAs`, missing social links, or a single
  organization name that merely varies in formatting (e.g. "Acme" vs "Acme Inc").
- **Severity conditions**: medium for verified contradictions; missing links
  are never findings.
- **Remediation**: Standardize the canonical entity name and add `sameAs`.

## Evidence hierarchy

Findings here rely on Levels 1–3 (direct HTTP/DOM, structured data, cross-page
first-party). Level 6 (heuristic inference) never produces high severity.
