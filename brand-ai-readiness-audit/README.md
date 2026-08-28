# Brand AI-Readiness Audit Marketplace

[agentskills.io](https://agentskills.io)-compliant multi-skill marketplace built for **Adobe University Hackathon 2026 — Round 3**. It audits any website for:

- **AI Discoverability** — how assistants (ChatGPT, Claude, Gemini, Perplexity) crawl, extract, corroborate, and cite brand facts.
- **On-Site Engagement** — how visitors orient, navigate, and convert after landing.

The entrypoint skill emits a single, schema-compliant JSON report — **presented to the user as raw JSON and nothing else**. A file is written only on explicit request.

## Structure

```text
brand-ai-readiness-audit/
├── marketplace.json                      # Manifest: skills + designated entrypoint
├── README.md
└── skills/
    ├── audit-orchestrator/               # [ENTRYPOINT] Composes specialists, reconciles & emits report
    │   ├── SKILL.md
    │   ├── scripts/{orchestrator.py, validate_report.py}
    │   └── references/{REPORT_SCHEMA.json, REPORT_SCHEMA.md, COMPOSITION_GUIDELINES.md}
    ├── crawl-render-audit/               # [SPECIALIST] Bot access, SSR/CSR gaps, Schema.org JSON-LD
    │   ├── SKILL.md
    │   ├── scripts/crawl_render_check.py
    │   └── references/{CRAWL_RENDER_CHECKLIST.md, STRUCTURED_DATA_SPECS.md, AI_BOT_POLICIES.md}
    ├── freshness-corroboration/          # [SPECIALIST] Staleness, consistency, sameAs entity grounding
    │   ├── SKILL.md
    │   ├── scripts/freshness_check.py
    │   └── references/{FRESHNESS_CHECKLIST.md, ENTITY_CORROBORATION.md}
    └── engagement-audit/                 # [SPECIALIST] Heading hierarchy, navigation, AI-summary readiness
        ├── SKILL.md
        ├── scripts/engagement_check.py
        └── references/{ENGAGEMENT_RUBRIC.md, AI_SNIPPET_GUIDELINES.md}
```

## Skills

| Skill | Role |
|---|---|
| `audit-orchestrator` *(entrypoint)* | Runs the full lifecycle: loads **all three** specialists (mandatory checklist), deduplicates overlapping findings, calibrates severity, adds proactive opportunities, validates, and emits the report. Bundles the CLI runner and schema validator. |
| `crawl-render-audit` | Machine readability: `robots.txt` AI-bot directives (`GPTBot`, `ClaudeBot`, …), client-side-rendering gaps, facts locked in images, JSON-LD structured data. |
| `freshness-corroboration` | Temporal trust: stale dates/copyrights, cross-page contradictions, missing `sameAs` corroboration (Wikidata, social profiles). |
| `engagement-audit` | Visitor orientation & extractability: above-the-fold value proposition, `H1`–`H3` hierarchy, navigation health, AI-summarizer signal-to-noise. |

## Usage

```bash
# Full composed audit — report printed to stdout as JSON
python3 skills/audit-orchestrator/scripts/orchestrator.py --site example.com

# Optional: write the report to a file
python3 skills/audit-orchestrator/scripts/orchestrator.py --site example.com --output report.json

# Validate a report against the schema
python3 skills/audit-orchestrator/scripts/validate_report.py report.json
```

In a compatible agent client, prompt naturally — e.g. *"Audit https://example.com for AI discoverability and engagement"* — and the entrypoint skill activates via description matching and returns the JSON report as its only output.

## Report Format

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": { "total_findings": 4, "critical": 1, "high": 2, "medium": 1, "low": 0 },
  "findings": [
    {
      "id": "F-001",
      "title": "AI crawlers disallowed in robots.txt",
      "severity": "critical",
      "evidence": "robots.txt explicitly disallows GPTBot and ClaudeBot across all paths.",
      "suggested_action": {
        "summary": "Update robots.txt to permit verified AI search bots.",
        "priority": "critical"
      }
    }
  ]
}
```

## Design Principles

- **Read-only**: audits never modify live sites or take destructive actions.
- **Evidence-backed**: every finding cites verifiable evidence; nothing is synthesized — clean sites yield zero findings.
- **Deterministic composition**: the orchestrator must load and run all specialist skills and pass schema validation before emitting.
- **Zero-dependency core**: standard-library Python 3 only (`urllib`, `html.parser`, `json`, `re`, `xml.etree`) for cross-platform portability.
- **Progressive disclosure**: compact declarative `SKILL.md` files; deep criteria in `references/`, deterministic checks in `scripts/`.
