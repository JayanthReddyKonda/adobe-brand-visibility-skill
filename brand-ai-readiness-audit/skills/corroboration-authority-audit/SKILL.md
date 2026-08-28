---
name: corroboration-authority-audit
description: >
  Cross-web authority & corroboration layer. Distinguishes identity link verification
  (verifying declared sameAs URLs resolve with HTTP 200) from external claim
  corroboration. A declared authority link that is provably broken (4xx/5xx) is a
  finding; absence of links is a recommendation.
---
# Corroboration & Authority Audit

## When to use
- Verify that declared sameAs / authority links (Wikidata, Crunchbase, official profiles) are live and accessible.
- Distinguish between identity link resolution and third-party claim corroboration.
- Assess whether AI search engines can corroborate the brand entity against independent databases.

## Inputs
- **`--site`** (string, required): Target domain or URL.
- **`--inventory`** (string, optional): Shared site inventory snapshot JSON from `audit-orchestrator`.

## Procedure
1. Extract `sameAs` URLs from Organization JSON-LD blocks on the landing page.
2. Safe probe each authority URL with SSRF protection (validating target IP and restricting redirects).
3. Unreachable probes (network timeout) are marked as **inconclusive**, never defects.
4. Broken links (HTTP 404, 410, 500, 502, 503) are reported as medium-severity findings (broken authority claim).
5. If no sameAs links exist, emit a proactive recommendation to declare authoritative profiles.

## Output
JSON: `{status, findings[], recommendations[], observations[], coverage{}, limitations[]}`.

## Scripts
```bash
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site <url> [--inventory <file.json>]
```

## Security & SSRF Policy
All external authority probes validate target host IPs against private CIDR blocks and enforce a 512 KB response byte limit.
