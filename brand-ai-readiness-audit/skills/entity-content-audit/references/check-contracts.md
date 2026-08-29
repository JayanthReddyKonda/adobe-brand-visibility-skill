# Entity & Content Audit — Check Contracts

Every check in this skill states what it measures, what evidence is required,
and what does **not** constitute a defect. Findings are only emitted for
what is directly observable in the fetched initial HTML.

## Preconditions
Entity analysis needs real content. If the initial HTML carries too few
words to analyze (e.g. a CSR shell), the script returns
`status: "inconclusive"` with an explanatory error instead of guessing —
a rendering-gap finding belongs to `discoverability-audit`, and this skill
must not fabricate entity verdicts from an empty page.

## C1. Identity explicitness
- **Measures:** Whether a machine can determine **who** the site is from
  three signals: Organization/Brand JSON-LD, `og:site_name`, or an
  extractable `<title>` identity.
- **Defect:** All three absent → "Organization identity not machine-explicit",
  severity `medium`, confidence `medium` (a human may still infer identity;
  machines often cannot).
- **Not a defect:** Any one explicit signal present. Identity inferred only
  from imagery or logo files does not count (machines reading text cannot
  see it).

## C2. Product/offer extraction
- **Measures:** Presence and explicitness of product/offering entities
  (structured data first, then explicit markup).
- **Defect:** A detected product lacking explicit attributes (price,
  description) → `low`, confidence `high`.
- **Not a defect:** A site with no products (services, portfolios) —
  absence of a product entity on a non-commerce site is expected.

## C3. Claim completeness
- **Measures:** Whether the flagship entity carries attribute coverage
  (L2/L3 facts: what is offered, for whom, at what quality) in machine-
  readable form.
- **Defect:** Entity exists but claims are only implicit in prose.
- **Severity:** `low` to `medium` depending on how much a summarizing AI
  would have to guess.

## C4. sameAs corroboration (recommendation only)
- **Measures:** Presence of `sameAs` links on the Organization entity.
- **Never a defect by itself.** Missing `sameAs` without evidence of actual
  entity confusion is emitted as a **recommendation**, not a finding —
  absence of one optional property is not proof of disambiguation failure.
  Genuine ambiguity (competing entities sharing the name) would require
  corroborating evidence, which is the `corroboration-authority-audit`
  skill's job.

## Evidence standards
- Every finding quotes the observed state (which signals were present/absent).
- Confidence is stated per finding.
- The skill never infers facts from absent markup beyond what the check
  contract above explicitly licenses.
