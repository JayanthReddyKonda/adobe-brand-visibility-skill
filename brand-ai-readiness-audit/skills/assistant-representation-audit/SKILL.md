---
name: assistant-representation-audit
description: >
  Assistant representation layer (optional enrichment). Cross-checks OBSERVED
  assistant responses (supplied as JSON via --responses or --observations)
  against the brand's first-party fact snapshot, detecting factual conflicts
  such as wrong prices, plus observational signals (mentions without citations).
---
# Assistant Representation Audit

## When to use
- Cross-check recorded assistant answers (ChatGPT, Claude, Gemini, Perplexity) against verified first-party facts.
- Inspect whether an AI assistant quotes outdated pricing, conflicting brand names, or incorrect specifications.
- Generate a site-side baseline fact snapshot for external evaluation.

## Inputs
- **`--site`** (string, required): Target domain or URL.
- **`--responses` / `--observations`** (string, optional): Path to JSON file of observed responses (`assistant`, `prompt`, `mentioned`, `cited`, `claims[]{fact, topic}`).
- **`--inventory`** (string, optional): Shared site inventory snapshot JSON from `audit-orchestrator`.

## Procedure
1. Build the first-party fact snapshot from the landing page (visible prices, years, title, word count) with SSRF safety.
2. If `--responses` is provided, cross-check observed claims:
   - Identify unmentioned or uncited signals as observational notes (not site defects).
   - Flag conflicting prices and claims as high-severity representation conflict findings.
3. If no responses file is provided, emit the baseline snapshot and a recommendation to supply observed response data.

## Output
JSON: `{status, findings[], recommendations[], observational_notes[], coverage{}}`.

## Scripts
```bash
python3 skills/assistant-representation-audit/scripts/representation_check.py --site <url> [--responses file.json]
```

## Security & SSRF Policy
All requests enforce private IP filtering, redirect limits, and response byte caps (HTML: 2 MB). All fetched data is treated as untrusted.
