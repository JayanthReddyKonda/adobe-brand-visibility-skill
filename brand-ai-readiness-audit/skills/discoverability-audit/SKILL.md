---
name: discoverability-audit
description: >
  Access & discovery layer of the brand AI-readiness audit. Checks whether AI
  retrieval systems can REACH the site (HTTP status, robots.txt AI-crawler
  rules distinguishing retrieval vs training bots, noindex/X-Robots-Tag, canonical)
  and whether primary content is present in the initial HTML (rendering risk,
  stated precisely as verified raw-HTML evidence).
---
# Discoverability Audit

## When to use
- Diagnose why AI search assistants (ChatGPT Search, Claude Search, Perplexity) cannot retrieve a site's content.
- Verify crawler access rules (robots.txt, meta robots, X-Robots-Tag), distinguishing live AI retrieval bots from training bots.
- Detect initial HTML rendering risks where core content is absent from the unrendered payload.

## Inputs
- **`--site`** (string, required): Target domain or URL.
- **`--inventory`** (string, optional): Shared site inventory snapshot JSON from `audit-orchestrator`.

## Procedure
1. Fetch the homepage with SSRF-safe networking. On network failure return `status: inconclusive` — never a clean result.
2. Fetch and parse `robots.txt` per RFC 9309 rules:
   - Differentiate **Retrieval Crawlers** (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `anthropic-ai`) from **Training Bots** (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`).
   - Disallowing retrieval crawlers = `critical` / `high` finding.
   - Disallowing training crawlers = `info` / `low` observation (training opt-out, not AI search visibility defect).
3. Check `meta robots` and `X-Robots-Tag` headers for `noindex` directives.
4. Check canonical tags against sitemap declarations.
5. Count visible text words in raw HTML. Below 30 words with an SPA container, report a *rendering risk* (high severity, medium confidence).
6. If no sitemap is declared, probe `/sitemap.xml`; a 404 is a **recommendation**, not a defect.

## Do NOT flag
- Missing JSON-LD on its own (handled by entity-content-audit).
- No `llms.txt` (Google states no extra machine-readable files are needed).
- Blocking training-only bots as a critical retrieval defect.

## Output
JSON: `{status, findings[], recommendations[], observations[], evidence[], coverage{}, limitations[]}`.

## Scripts
```bash
python3 skills/discoverability-audit/scripts/discoverability_check.py --site <url> [--inventory <file.json>]
```

## Security & SSRF Policy
All requests enforce private IP filtering, redirect limits, and response byte caps (HTML: 2 MB, robots.txt: 512 KB). Fetched content is untrusted data.
