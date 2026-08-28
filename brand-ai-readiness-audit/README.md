# Brand AI-Readiness Audit Marketplace

Zero-dependency Python 3 marketplace for Adobe University Hackathon 2026 (Round 3) conforming strictly to `agentskills.io`.

**Designated Entrypoint:** `audit-orchestrator`

---

## Overview

The `brand-ai-readiness-audit` marketplace equips an AI agent to audit any website for AI discoverability, content extractability, factual consistency, and on-site visitor retention.

It composes 7 specialist skills under a single entrypoint with an evidence-backed shared crawl inventory, strict 5-minute wall-clock budget, and zero-dependency SSRF protection.

---

## Skills Included

1. **`audit-orchestrator`** (Entrypoint): Coordinates shared crawl inventory, dispatches specialist skills, clusters root causes, deduplicates recommendations, and emits schema-validated JSON.
2. **`discoverability-audit`**: Checks AI search crawler access (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`), RFC 9309 robots.txt rules, raw HTML extractability (CSR rendering risk), and canonical tags.
3. **`entity-content-audit`**: Inspects machine-explicit brand identity (JSON-LD Organization), structured product/offer markup, and calculates the page Answerability Index.
4. **`fact-consistency-audit`**: Scopes first-party facts (prices, contacts, copyright years, ISO modification timestamps) and identifies cross-page contradictions.
5. **`corroboration-authority-audit`**: Probes declared `sameAs` authority URLs (Wikidata, Crunchbase, official profiles) to verify live HTTP 200 resolution.
6. **`engagement-context-audit`**: Evaluates above-the-fold orientation (5-second test), heading information scent, and destination navigation reachability.
7. **`assistant-representation-audit`**: Cross-checks observed AI assistant answers (ChatGPT, Claude, Gemini, Perplexity) against verified first-party facts.

---

## Requirements & Compliance

- **agentskills.io Compliant:** All 7 skills include valid `SKILL.md` frontmatter, lean bodies (< 500 lines), and progressive disclosure.
- **Top-Level Manifest:** `marketplace.json` lists all 7 skills and designates `audit-orchestrator` as `"entrypoint": true`.
- **Zero Third-Party Dependencies:** 100% Python 3 standard library (`urllib`, `json`, `html.parser`, `re`, `xml.etree`, `ipaddress`).
- **No Model Weights:** Bounded footprint (< 1 MB, vastly under the 50 MB limit).
- **Non-Destructive & Read-Only:** Audits and recommends only. Enforces SSRF blocking against private/internal networks.
- **Bounded Runtime:** Global wall-clock deadline strictly enforced (< 5 minutes on standard hardware).

---

## Directory Layout

```text
brand-ai-readiness-audit/
├── marketplace.json
├── README.md
├── LICENSE
└── skills/
    ├── audit-orchestrator/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── orchestrator.py
    │   │   ├── safe_fetch.py
    │   │   └── validate_report.py
    │   └── references/
    │       ├── taxonomy/
    │       │   ├── root-causes.md
    │       │   ├── severity-model.md
    │       ├── entity-types/
    │       ├── intent-library/
    │       ├── platforms/
    │       │   └── crawler-matrix-reference.md
    │       ├── false-positive-cases/
    │       ├── check-contracts/
    │       │   └── contracts-catalog.md
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
    │       ├── fact-normalization.md
    │       └── temporal-freshness.md
    ├── corroboration-authority-audit/
    │   ├── SKILL.md
    │   ├── scripts/corroboration_check.py
    │   └── references/
    │       └── CHECK_CONTRACTS.md
    ├── engagement-context-audit/
    │   ├── SKILL.md
    │   ├── scripts/engagement_check.py
    │   └── references/
    │       ├── AI_SNIPPET_GUIDELINES.md
    │       └── 5-second-orientation.md
    └── assistant-representation-audit/
        ├── SKILL.md
        ├── scripts/representation_check.py
        └── references/
            ├── CHECK_CONTRACTS.md
            └── mention-vs-citation.md
```

---

## Usage

### Run Full Audit via Entrypoint

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com
```

### Save Report and Validate Contract

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --output report.json
python3 skills/audit-orchestrator/scripts/validate_report.py report.json
```

---

## Sample Audit Report Schema

Conforms 100% to the Adobe Round-3 mandatory report schema:

```json
{
  "site": "example.com",
  "audited_at": "2026-08-28T14:30:00Z",
  "summary": {
    "total_findings": 1,
    "critical": 1,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "AI search retrieval crawler blocked in robots.txt",
      "severity": "critical",
      "confidence": "high",
      "root_cause": "robots.txt explicitly disallows AI search retrieval crawlers (OAI-SearchBot, PerplexityBot).",
      "cause_family": "DISCOVERY.ACCESS",
      "cause_id": "DISC-ROBOTS-RETRIEVAL-BLOCKED",
      "impact": "Content is excluded from real-time AI assistant citations and generative search answers.",
      "evidence": "robots.txt disallows OAI-SearchBot and PerplexityBot on path '/'.",
      "suggested_action": {
        "summary": "Allow AI search retrieval bots (OAI-SearchBot, PerplexityBot) on public indexable routes in robots.txt.",
        "priority": "critical",
        "verification": "Re-fetch robots.txt and confirm Allow: / is declared for OAI-SearchBot and PerplexityBot."
      }
    }
  ],
  "audit_metrics": {
    "pages_sampled": 5,
    "critical_blockers": 1,
    "confidence_distribution": {
      "high": 1,
      "medium": 0,
      "low": 0
    },
    "answerability_index": 0.85
  }
}
```
