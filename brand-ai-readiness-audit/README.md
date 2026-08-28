# Brand AI-Readiness Audit

Zero-dependency Python 3 marketplace for Adobe University Hackathon 2026 (Round 3) conforming to `agentskills.io`.

Entrypoint: `audit-orchestrator`

## Overview

The `audit-orchestrator` skill audits any domain for AI-readiness across search crawlers and AI assistants (ChatGPT, Claude, Gemini, Perplexity). It creates a shared site inventory and runs specialist skills against a consistent evidence snapshot.

## Skills Included

- **audit-orchestrator**: Entrypoint orchestrator that manages shared crawl inventory, runs specialists, clusters root causes, and emits schema-validated JSON.
- **discoverability-audit**: Checks AI crawler access (robots.txt rules for GPTBot, PerplexityBot, etc.), HTML extractability, and canonical tags.
- **entity-content-audit**: Verifies brand entity identity, schema markup (JSON-LD), and content answerability.
- **fact-consistency-audit**: Identifies stale facts, cross-page factual contradictions, and missing citations.
- **corroboration-authority-audit**: Resolves sameAs/social links and validates external authority sources.
- **engagement-context-audit**: Evaluates structural headings, orientation, and user journey continuity for AI referral traffic.
- **assistant-representation-audit**: Opt-in audit to check observed AI assistant outputs against on-site brand facts.

## Requirements & Compliance

- Entrypoint: `audit-orchestrator` defined in `marketplace.json`
- Dependencies: Python 3 standard library only (`urllib`, `json`, `html.parser`, `re`, `xml.etree`)
- Non-interactive: Standard CLI flags
- Output: Standard JSON emitted to stdout
- Validation: Schema-validated via `validate_report.py`

## Project Structure

```text
brand-ai-readiness-audit/
├── marketplace.json
├── README.md
└── skills/
    ├── audit-orchestrator/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── orchestrator.py
    │   │   └── validate_report.py
    │   └── references/
    │       ├── COMPOSITION_GUIDELINES.md
    │       ├── REPORT_SCHEMA.json
    │       └── REPORT_SCHEMA.md
    ├── discoverability-audit/
    │   ├── SKILL.md
    │   ├── scripts/discoverability_check.py
    │   └── references/
    │       ├── CHECK_CONTRACTS.md
    │       └── seo-foundations.md
    ├── entity-content-audit/
    │   ├── SKILL.md
    │   ├── scripts/entity_content_check.py
    │   └── references/
    │       ├── CHECK_CONTRACTS.md
    │       └── structured-data-validation.md
    ├── fact-consistency-audit/
    │   ├── SKILL.md
    │   ├── scripts/fact_consistency_check.py
    │   └── references/
    │       ├── ENTITY_CORROBORATION.md
    │       └── FRESHNESS_CHECKLIST.md
    ├── corroboration-authority-audit/
    │   ├── SKILL.md
    │   ├── scripts/corroboration_check.py
    │   └── references/CHECK_CONTRACTS.md
    ├── engagement-context-audit/
    │   ├── SKILL.md
    │   ├── scripts/engagement_check.py
    │   └── references/
    │       ├── AI_SNIPPET_GUIDELINES.md
    │       └── ENGAGEMENT_RUBRIC.md
    └── assistant-representation-audit/
        ├── SKILL.md
        ├── scripts/representation_check.py
        └── references/
            ├── CHECK_CONTRACTS.md
            └── mention-vs-citation.md
```

## Usage

### Run Full Audit

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com
```

### Save Report to File

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --output report.json
```

### Validate Report Schema

```bash
python3 skills/audit-orchestrator/scripts/validate_report.py report.json
```

### Run Individual Specialist

```bash
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com
```

## Output Format

The orchestrator outputs schema-validated JSON with the following structure:

```json
{
  "site": "example.com",
  "audited_at": "2026-08-28T12:00:00Z",
  "summary": {
    "total_findings": 1,
    "critical": 1,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "specialists": {
    "discoverability-audit": { "status": "ok" },
    "entity-content-audit": { "status": "ok" },
    "fact-consistency-audit": { "status": "ok" },
    "corroboration-authority-audit": { "status": "ok" },
    "engagement-context-audit": { "status": "ok" }
  },
  "findings": [
    {
      "id": "F-001",
      "title": "AI search crawler blocked by robots.txt",
      "severity": "critical",
      "evidence": "robots.txt contains Disallow: / for Google-Extended",
      "suggested_action": {
        "summary": "Narrow or remove Google-Extended disallow rule",
        "priority": "critical"
      }
    }
  ],
  "diagnostic_dimensions": {
    "crawlability": 80.0,
    "entity_clarity": 100.0,
    "fact_integrity": 100.0,
    "citation_readiness": 100.0,
    "context_continuity": 90.0
  }
}
```
