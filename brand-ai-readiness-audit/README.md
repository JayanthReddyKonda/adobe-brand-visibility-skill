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
    ├── discoverability-audit/            # [SPECIALIST] Crawler access, content availability, structured data
    │   ├── SKILL.md
    │   └── scripts/discoverability_check.py
    ├── entity-content-audit/             # [SPECIALIST] Entity identity clarity & offer extractability
    │   ├── SKILL.md
    │   └── scripts/entity_content_check.py
    ├── fact-consistency-audit/           # [SPECIALIST] Freshness signals & cross-page fact consistency
    │   ├── SKILL.md
    │   ├── scripts/fact_consistency_check.py
    │   └── references/{FRESHNESS_CHECKLIST.md, ENTITY_CORROBORATION.md}
    ├── corroboration-authority-audit/    # [SPECIALIST] Authority-link verification & entity corroboration
    │   ├── SKILL.md
    │   └── scripts/corroboration_check.py
    ├── engagement-context-audit/         # [SPECIALIST] Orientation, hierarchy, journey continuity
    │   ├── SKILL.md
    │   ├── scripts/engagement_check.py
    │   └── references/{ENGAGEMENT_RUBRIC.md, AI_SNIPPET_GUIDELINES.md}
    └── assistant-representation-audit/   # [OPT-IN] Observed AI representation vs first-party facts
        ├── SKILL.md
        └── scripts/representation_check.py
```

## Skills

| Skill | Role |
|---|---|
| `audit-orchestrator` *(entrypoint)* | Runs the full lifecycle: loads **all five** core specialists (mandatory checklist), deduplicates overlapping findings, calibrates severity & confidence, adds proactive opportunities, validates, and emits the report. Bundles the CLI runner and schema validator. |
| `discoverability-audit` | Can retrieval systems access the content? Crawler access, content availability in initial HTML, structured data. |
| `entity-content-audit` | Is the entity and its offer extractable? Identity clarity, attribute coverage, answerability of key facts. |
| `fact-consistency-audit` | Are facts current and self-consistent? Freshness signals, cross-page contradictions, corroboration metadata. |
| `corroboration-authority-audit` | Do declared authority links (sameAs, profiles) resolve and corroborate the entity? |
| `engagement-context-audit` | Does the journey survive the AI referral? Orientation, heading hierarchy, navigation discoverability, context continuity. |
| `assistant-representation-audit` *(opt-in)* | What do assistants actually say? Compares observed AI responses against first-party facts (requires observed outputs or API access). |

Every specialist records its execution status (`ok` / `failed` / `not_run`) in the report; tool failure is never misread as "no findings". Proactive improvements (e.g. `llms.txt`) are reported separately as `proactive_actions`, never as defects.

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
