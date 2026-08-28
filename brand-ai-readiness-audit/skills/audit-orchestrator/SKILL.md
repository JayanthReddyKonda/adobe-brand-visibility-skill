---
name: audit-orchestrator
description: Audit a website for AI discoverability and on-site engagement by composing the marketplace's specialist skills and emitting a single evidence-backed JSON report conforming to the required schema. Use when diagnosing why a brand is missing, stale, or misrepresented in AI assistants (ChatGPT, Claude, Gemini, Perplexity), or why visitors who arrive bounce.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
allowed-tools: Bash Read
metadata:
  role: entrypoint
  version: "1.0.0"
---

# Audit Orchestrator

The central entrypoint skill of the Brand AI-Readiness Audit Marketplace. It composes specialist skills, reconciles findings, deduplicates overlapping signals, assigns evidence-backed severity ratings, synthesizes proactive recommendations, and emits the final JSON audit report.

## When to use

- Perform a full AI discoverability and engagement audit for any given website domain or URL.
- Diagnose why an AI assistant cannot find, crawl, or accurately quote facts about a brand.
- Uncover why human visitors or AI search users bounce after arriving at a website.
- Validate an audit report against the official schema.

## Inputs

- **`site`** (string, required): The target domain or URL to audit (e.g., `example.com` or `https://example.com`).
- **`include_proactive`** (boolean, optional): Set to `false` to skip proactive improvement checks (default: enabled).

## Procedure

1. **Target Normalization**: Clean and validate the target domain/URL across platforms.
2. **Execute Specialist Skills**:
   - Invoke [`crawl-render-audit`](../crawl-render-audit/SKILL.md) to inspect bot access, SSR/CSR rendering gaps, and Schema.org JSON-LD.
   - Invoke [`freshness-corroboration`](../freshness-corroboration/SKILL.md) to check timestamps, staleness, and entity `sameAs` corroboration.
   - Invoke [`engagement-audit`](../engagement-audit/SKILL.md) to evaluate above-the-fold value props, heading structure, and summary readability.
3. **Reconcile & Deduplicate**:
   - Merge overlapping findings across skills according to [Composition Guidelines](references/COMPOSITION_GUIDELINES.md).
   - Reassign sequential IDs (`F-001`, `F-002`, ...).
4. **Calibrate Severity & Prioritize Actions**:
   - Map defects to `critical`, `high`, `medium`, `low` based on impact on AI citation and user engagement.
   - Ensure every finding includes concrete `evidence` and a mechanism-sound `suggested_action`.
5. **Synthesize Proactive Opportunities**:
   - Add high-value proactive suggestions (e.g., adding `llms.txt`, knowledge graph entity disambiguation) even if no explicit fatal defect was detected.
6. **Emit & Validate JSON Report**:
   - Generate the final JSON report matching the [Report Schema](references/REPORT_SCHEMA.md).
   - Verify compliance using the bundled validator script.
   - **Deliver ONLY the JSON report to the user** — output the raw JSON and nothing else: no prose, no commentary, no markdown code fence, no summaries, no file-saving message. Do not write a file unless the user explicitly asks.

## Output

Return ONLY a JSON report matching the required schema (no additional text before or after):

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "Robots.txt disallows AI search crawlers",
      "severity": "critical",
      "evidence": "robots.txt explicitly blocks User-agent: GPTBot and ClaudeBot.",
      "suggested_action": {
        "summary": "Allow verified AI search bots to crawl public content.",
        "priority": "critical"
      }
    }
  ]
}
```

## Gotchas

- **Do Not Modify Live Sites**: Audits are strictly read-only recommendations.
- **Do Not Guess Missing Schema**: Always inspect raw HTML and verify whether JSON-LD or microdata actually exists before claiming it is missing.
- **Deduplicate Findings**: If both crawl and freshness skills note missing brand metadata, consolidate into a single prioritized recommendation.

## Available scripts & references

- **`scripts/orchestrator.py`** — Runs full composed audit across all operating systems:
  ```bash
  python3 skills/audit-orchestrator/scripts/orchestrator.py --site example.com --output report.json
  ```
  *(On Windows, use `python` or `py`)*
- **`scripts/validate_report.py`** — Validates report against schema:
  ```bash
  python3 skills/audit-orchestrator/scripts/validate_report.py report.json
  ```
- **`references/REPORT_SCHEMA.json`** — Formal JSON schema definition.
- **`references/REPORT_SCHEMA.md`** — Field specifications and documentation.
- **`references/COMPOSITION_GUIDELINES.md`** — Reconciliation and severity scoring rules.
