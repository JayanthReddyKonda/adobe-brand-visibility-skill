---
name: discoverability-audit
description: >
  Access & discovery layer of the brand AI-readiness audit. Checks whether AI
  retrieval systems can REACH the site (HTTP status, robots.txt AI-crawler
  rules, noindex/X-Robots-Tag, canonical) and whether primary content is
  present in the initial HTML (rendering risk, stated precisely as verified
  raw-HTML evidence, never claiming a render was performed). Use when
  diagnosing why AI assistants cannot retrieve or index a brand's pages.
---
# Discoverability Audit

## When to use
- Diagnose why AI assistants or search systems cannot retrieve a site's content.
- Verify crawler access rules (robots.txt, meta robots, X-Robots-Tag) for AI user-agents.
- Detect rendering risk: primary content absent from the initial HTML response.

## Inputs
- **`site`** (string, required): target domain or URL.

## Procedure
1. Fetch the homepage (L1 evidence: direct HTTP). On network failure return
   `status: inconclusive` — never a clean result.
2. Fetch and parse `robots.txt`. Report only **explicit** blanket
   `Disallow: /` rules for known AI crawler user-agents. Absence of a rule
   means allowed; do not infer blocks.
3. Check `meta robots` and the `X-Robots-Tag` header for `noindex`.
4. Check the canonical link; report only a homepage canonical that points
   elsewhere (medium, high confidence).
5. Count visible text words in the **raw HTML response only**. Below 30
   words, report a *rendering risk* (high, medium confidence) — phrased as a
   risk because systems that render JS may still succeed. Never claim
   "crawlers cannot render JS" as fact.
6. If no sitemap is declared in robots.txt, probe `/sitemap.xml`; a 404 is a
   **recommendation**, not a defect.

## Do NOT flag
- Missing JSON-LD on its own (see entity-content-audit).
- No `llms.txt` (Google states no extra machine-readable files are needed).
- JavaScript rendering choice per se — only missing content in the initial HTML.

## Output
JSON: `{status, findings[], recommendations[], evidence[]}`. Findings use the
rich model: `category, title, severity, confidence, root_cause, impact,
evidence, suggested_action{summary, priority, verification}`.

## Scripts
- `scripts/discoverability_check.py --site <url>`

## Gotchas
- Network-unreachable targets must return `inconclusive`, not zero findings.
- Only flag robots blocks you can quote verbatim from the fetched robots.txt.

## References
- Read `references/CHECK_CONTRACTS.md` before writing or judging any finding —
  it defines exactly what each check measures, what counts as a defect, and
  what does not.