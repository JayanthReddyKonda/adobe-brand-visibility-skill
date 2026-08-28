---
name: entity-content-audit
description: >
  Entity & content understanding layer. Determines whether an AI system can
  understand WHO the brand is and WHAT it offers: organization identity
  explicitness, structured schema (JSON-LD), and the Answerability Engine
  measuring material attribute completeness per page type.
---
# Entity & Content Audit

## When to use
- A brand is described vaguely or misattributed by AI assistants.
- Products, pricing, or services exist on the site but are omitted from AI answers.
- Assess whether identity, offer facts, and material attributes are machine-explicit.

## Inputs
- **`--site`** (string, required): Target domain or URL.
- **`--inventory`** (string, optional): Shared site inventory snapshot JSON from `audit-orchestrator`.

## Procedure
1. Fetch and parse the landing page with SSRF-safe networking; require ≥50 words of initial-HTML text.
2. Extract Organization/Brand structured data (name, logo, sameAs, legalName) from JSON-LD and OpenGraph tags.
3. Identity explicitness check: if no machine-explicit identity exists, report a medium-severity finding.
4. Offer extractability: extract Product, Offer, and Service schema objects. Incomplete product schema (missing price, availability, or description) is reported as a finding. Absence of structured data is a recommendation.
5. **Answerability Engine**: For each sampled page type (product, pricing, service, location, documentation, contact), evaluate coverage of required material factual attributes.
6. Calculate overall `answerability_index` across sampled pages.

## Do NOT flag
- Absence of structured data as an automatic critical defect (it is an extractability recommendation).
- Rendered CSR shells as missing identity (return `inconclusive`).

## Output
JSON: `{status, findings[], recommendations[], observations[], entity_snapshot{}, coverage{}, limitations[]}`.

## Scripts
```bash
python3 skills/entity-content-audit/scripts/entity_content_check.py --site <url> [--inventory <file.json>]
```

## Security & SSRF Policy
Enforces IP filtering, redirect limits, and response byte caps (HTML: 2 MB). All fetched data is treated as untrusted.
