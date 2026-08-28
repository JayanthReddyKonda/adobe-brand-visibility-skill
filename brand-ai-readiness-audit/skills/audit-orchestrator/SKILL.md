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

This is a **mandatory, ordered workflow**. You MUST load and run ALL THREE specialist skills before composing the report. Do not skip any specialist, do not reorder them, and do not emit the report until every checklist item below is complete and its findings have been collected.

> Progressive disclosure: agents do not auto-load every skill. The specialists below are NOT loaded into your context automatically — you must explicitly load each one's `SKILL.md` and run its bundled script as instructed. Verify each by running it and capturing its findings.

### Mandatory checklist (do all, in order)

- [ ] **Step 1 — Normalize target**: Clean and validate the target domain/URL. Determine the canonical `base_url`.
- [ ] **Step 2 — Load & run `crawl-render-audit`** (MANDATORY):
  - Load its instructions: read [`../crawl-render-audit/SKILL.md`](../crawl-render-audit/SKILL.md).
  - Execute its bundled script to inspect bot access, SSR/CSR rendering gaps, machine-readable content, and Schema.org JSON-LD:
    ```bash
    python3 skills/crawl-render-audit/scripts/crawl_render_check.py --site <base_url>
    ```
  - Collect all findings it returns. If it returns none, record that as a result (do not skip).
- [ ] **Step 3 — Load & run `freshness-corroboration`** (MANDATORY):
  - Load its instructions: read [`../freshness-corroboration/SKILL.md`](../freshness-corroboration/SKILL.md).
  - Execute its bundled script to check timestamps, staleness, cross-page consistency, and `sameAs` entity grounding:
    ```bash
    python3 skills/freshness-corroboration/scripts/freshness_check.py --site <base_url>
    ```
  - Collect all findings it returns. If it returns none, record that as a result (do not skip).
- [ ] **Step 4 — Load & run `engagement-audit`** (MANDATORY):
  - Load its instructions: read [`../engagement-audit/SKILL.md`](../engagement-audit/SKILL.md).
  - Execute its bundled script to evaluate above-the-fold orientation, heading hierarchy, information scent, and navigation:
    ```bash
    python3 skills/engagement-audit/scripts/engagement_check.py --site <base_url>
    ```
  - Collect all findings it returns. If it returns none, record that as a result (do not skip).
- [ ] **Step 5 — Proactive checks**: Run `proactive_checks` (llms.txt, sitemap) against the live site unless disabled.
- [ ] **Step 6 — Reconcile & deduplicate**: Merge overlapping findings across the three specialists according to [Composition Guidelines](references/COMPOSITION_GUIDELINES.md). Reassign sequential IDs (`F-001`, `F-002`, ...). Note any case where a specialist returned no findings so the report reflects a genuinely clean result, never fabricated findings.
- [ ] **Step 7 — Calibrate severity & prioritize**: Map defects to `critical`/`high`/`medium`/`low` based on impact on AI citation and user engagement. Ensure every finding includes concrete `evidence` and a mechanism-sound `suggested_action`.
- [ ] **Step 8 — Validation gate (MANDATORY, do not skip)**: Before emitting, validate the assembled report against the schema:
  ```bash
  python3 skills/audit-orchestrator/scripts/validate_report.py <report_file>
  ```
  If validation fails, fix the report and re-validate. Only proceed when it passes.
- [ ] **Step 9 — Emit**: Output ONLY the validated JSON report (see Output rule below).

## Output

Return ONLY a JSON report matching the required schema (no additional text before or after). The report must reflect output from ALL the mandatory specialist skills above; a finding of zero problems is a valid, truthful result only if every specialist genuinely returned nothing.

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
