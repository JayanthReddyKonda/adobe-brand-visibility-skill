---
name: corroboration-authority-audit
description: >
  Cross-web authority & corroboration layer. Verifies that the identity links
  a site declares (sameAs profile URLs) actually resolve, and surfaces
  corroboration gaps as recommendations. A declared authority link that is
  provably broken (HTTP error/redirect) is a finding; absence of links is
  never a defect. Use when assessing whether AI systems can verify brand
  identity against independent authorities.
---
# Corroboration & Authority Audit

## When to use
- Verify that declared sameAs / authority links are live and canonical.
- Assess whether a machine can corroborate the brand entity against
  independent sources (Wikidata, registries, official profiles).

## Inputs
- **`site`** (string, required): target domain or URL.

## Procedure
1. Fetch homepage and extract `sameAs` URLs from all JSON-LD blocks.
2. HEAD-probe each link (fall back to GET). Record HTTP status and final URL.
3. Unreachable probes are **inconclusive** — never claims.
4. Links returning 3xx/4xx/5xx are a medium, high-confidence finding:
   declared corroboration is broken.
5. No sameAs links at all → a recommendation explaining that this is a gap,
   not a proven ambiguity.

## Output
JSON: `{status, findings[], recommendations[], links_checked[]}`.

## Scripts
- `scripts/corroboration_check.py --site <url>`

## Gotchas
- Never equate "missing sameAs" with "entity ambiguity" — ambiguity requires
  evidence of competing entities, which this layer does not assert.