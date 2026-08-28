# Brand AI-Readiness Audit Marketplace

A modular, multi-skill AI agent marketplace built in the standard [agentskills.io](https://agentskills.io) format for **Adobe University Hackathon 2026**.

This marketplace automatically audits any website for both **off-site AI discoverability** (how search assistants like ChatGPT, Claude, Gemini, and Perplexity crawl, extract, corroborate, and cite brand facts) and **on-site engagement** (how human visitors orient, navigate, and convert once they land), producing an evidence-backed audit report with prioritized recommendations and proactive improvements.

---

## Marketplace Structure

```text
brand-ai-readiness-audit/
├── marketplace.json                        # Marketplace manifest listing all skills & designating entrypoint
├── README.md                               # Marketplace documentation and architecture guide
└── skills/
    ├── audit-orchestrator/                 # [ENTRYPOINT] Composes specialist skills & emits final report
    │   ├── SKILL.md                        # Orchestration procedure, reconciliation, and output formatting
    │   ├── scripts/
    │   │   ├── orchestrator.py             # CLI runner to execute sub-audits, aggregate & emit report
    │   │   └── validate_report.py          # Strict JSON schema validator for audit reports
    │   └── references/
    │       ├── REPORT_SCHEMA.json          # Formal JSON schema definition for final report
    │       ├── REPORT_SCHEMA.md            # Detailed schema specification and field rules
    │       └── COMPOSITION_GUIDELINES.md   # Rules for deduplication, priority scoring & proactive actions
    │
    ├── crawl-render-audit/                 # [SPECIALIST] Crawlability, JS rendering & structured data
    │   ├── SKILL.md                        # Crawl barriers, bot access, SSR/CSR gaps & JSON-LD schemas
    │   ├── scripts/
    │   │   └── crawl_render_check.py       # Diagnostic script inspecting robots.txt, HTML/DOM, and JSON-LD
    │   └── references/
    │       ├── CRAWL_RENDER_CHECKLIST.md   # Step-by-step checklist for crawl & render failure modes
    │       ├── STRUCTURED_DATA_SPECS.md    # Schema.org best practices (Organization, Product, FAQ, Article)
    │       └── AI_BOT_POLICIES.md          # User-agents & crawler policies (GPTBot, ClaudeBot, etc.)
    │
    ├── freshness-corroboration/            # [SPECIALIST] Temporal signals, fact consistency & entity grounding
    │   ├── SKILL.md                        # Staleness audit, cross-page consistency, Wikidata / sameAs links
    │   ├── scripts/
    │   │   └── freshness_check.py          # Script checking copyright years, modified dates, and entity links
    │   └── references/
    │       ├── FRESHNESS_CHECKLIST.md      # Temporal decay, update cadence, and stale claims detection
    │       └── ENTITY_CORROBORATION.md     # Knowledge graph grounding, NAP consistency & disambiguation
    │
    └── engagement-audit/                   # [SPECIALIST] On-site orientation, information scent & summaries
        ├── SKILL.md                        # Above-the-fold clarity, heading structure, and summary readiness
        ├── scripts/
        │   └── engagement_check.py         # Script evaluating heading hierarchy, navigation & text density
        └── references/
            ├── ENGAGEMENT_RUBRIC.md        # Orientation, bounce prevention, and navigation heuristics
            └── AI_SNIPPET_GUIDELINES.md    # Assistant and email AI summary extractability rules
```

---

## Skills Breakdown & Separation of Concerns

### 1. `audit-orchestrator` (Entrypoint)
- **Role**: Coordinates the entire audit lifecycle. Receives the target domain/URL, invokes specialist skills, reconciles findings, deduplicates overlapping signals, computes composite severity counts, generates proactive enhancements beyond raw defects, and outputs the final JSON report.
- **Tools**: Bundled with `orchestrator.py` (CLI runner) and `validate_report.py` (strict schema validator).

### 2. `crawl-render-audit` (Discoverability Specialist)
- **Role**: Audits technical access and machine readability. Evaluates `robots.txt` directives for AI bots (e.g., `GPTBot`, `ClaudeBot`, `PerplexityBot`), checks for SSR vs CSR rendering gaps (ensuring core text exists in raw HTML), detects facts trapped in un-annotated images or non-text elements, and verifies Schema.org JSON-LD structured data.

### 3. `freshness-corroboration` (Trust & Accuracy Specialist)
- **Role**: Audits temporal freshness and factual trustworthiness. Identifies stale dates, outdated copyright notices, contradictory claims across pages, and lack of external entity corroboration (such as missing `sameAs` links to Wikidata, Crunchbase, or official social profiles).

### 4. `engagement-audit` (On-Site & Summary Specialist)
- **Role**: Audits visitor experience and AI summary extractability. Assesses above-the-fold value proposition clarity, heading hierarchy (`H1` to `H3` logical flow), navigation health, and signal-to-noise ratio for AI summarizers (such as email and assistant briefers).

---

## Audit Report Schema

The entrypoint skill outputs a JSON report conforming to the required schema:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 4,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "AI crawlers disallowed in robots.txt",
      "severity": "critical",
      "evidence": "robots.txt explicitly disallows GPTBot and ClaudeBot across all paths.",
      "suggested_action": {
        "summary": "Update robots.txt to permit indexing by verified AI search bots.",
        "priority": "critical"
      }
    }
  ]
}
```

---

## Guardrails & Principles

- **Read-Only / Recommend-Only**: Never alters live websites or executes destructive actions.
- **Robots.txt & Sandbox Safe**: Strictly respects crawler policies and operates cleanly in offline or sandboxed environments.
- **Progressive Disclosure**: Keeps main `SKILL.md` files compact and declarative, delegating detailed reference criteria to `references/` and deterministic checks to `scripts/`.
- **Zero-Dependency Python Core**: All bundled scripts rely on standard Python 3 libraries (`urllib`, `html.parser`, `json`, `re`, `xml.etree.ElementTree`) for maximum cross-environment portability.
