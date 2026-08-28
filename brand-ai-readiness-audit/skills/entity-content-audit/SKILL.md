---
name: entity-content-audit
description: >
  Entity & content understanding layer. Determines whether a machine could
  understand WHO the brand is and WHAT it offers: organization identity
  explicitness, product/offer extractability, and attribute (claim)
  completeness. Absence of structured data is never a defect by itself; only
  measured understanding gaps are reported. Use when a brand is misquoted,
  miscategorized, or omitted by AI assistants despite being crawlable.
---
# Entity & Content Audit

## When to use
- A brand is described vaguely or misattributed by AI assistants.
- Products/offers exist on the site but never appear in AI answers.
- Assess whether identity and offer facts are machine-explicit.

## Inputs
- **`site`** (string, required): target domain or URL.

## Procedure
1. Fetch the homepage; require ≥50 words of initial-HTML text. Below that,
   return `inconclusive` and defer to discoverability-audit (rendering risk).
2. Extract an entity snapshot: Organization/Brand JSON-LD (name, logo,
   sameAs, @type), og:site_name, `<title>`, Product objects with offers.
3. **Identity check**: if no explicit name/logo/type from any metadata source,
   report a medium finding (medium confidence) — machines must infer identity
   from prose.
4. **Offer check**: if no Product structured data exists, emit a
   *recommendation* (never a defect). Note whether price-like strings exist
   in prose — facts present but not extractable.
5. **Claim completeness**: for each structured Product found, report missing
   material attributes (price, description, availability) as low-severity,
   high-confidence findings.
6. Defer sameAs detail to corroboration-authority-audit; emit its
   recommendation here only as a note.

## Do NOT flag
- Missing JSON-LD where identity is otherwise explicit in metadata.
- Multiple H1s, missing nav, copyright years (other layers own those, with evidence).

## Output
JSON: `{status, findings[], recommendations[], entity, products_found, words}`.
Findings use the rich model (category/confidence/root_cause/impact/verification).

## Scripts
- `scripts/entity_content_check.py --site <url>`

## Gotchas
- If the page is a CSR shell, entity analysis is meaningless — return
  `inconclusive` rather than "no identity found".