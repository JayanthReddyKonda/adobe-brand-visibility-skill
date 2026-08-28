# Brand AI-Readiness Audit Marketplace

Zero-dependency Python 3 marketplace for Adobe University Hackathon 2026 (Round 3) conforming strictly to `agentskills.io`.

**Designated Entrypoint:** `audit-orchestrator`

---

## Overview

The `brand-ai-readiness-audit` marketplace equips an AI agent to audit any website for AI discoverability, content extractability, factual consistency, and on-site visitor retention.

It composes 7 specialist skills under a single entrypoint with an evidence-backed shared crawl inventory, strict 5-minute wall-clock budget, zero-dependency SSRF protection, and zero-dependency SQLite persistence.

---

## Skills Included

1. **`audit-orchestrator`** (Entrypoint): Coordinates shared crawl inventory acquisition, dispatches specialist skills with dedicated sub-budgets, clusters root causes into a unified causal taxonomy, deduplicates recommendations, provides zero-dependency SQLite run logging, and emits strictly validated schema JSON or Markdown.
2. **`discoverability-audit`**: Checks AI search crawler access (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`), RFC 9309 robots.txt rules, raw HTML extractability (CSR rendering risk), `X-Robots-Tag` headers, and canonical tags.
3. **`entity-content-audit`**: Inspects machine-explicit brand identity (JSON-LD Organization), structured product/offer markup (supporting array `@type`), and calculates the mathematically reproducible weighted Answerability Index.
4. **`fact-consistency-audit`**: Scopes first-party facts (prices, contacts, copyright years, ISO modification timestamps) and identifies cross-page contradictions without false positives across distinct pricing tiers or non-overlapping contexts.
5. **`corroboration-authority-audit`**: Probes declared `sameAs` authority URLs (Wikidata, Crunchbase, official profiles, supporting `@id` objects) to verify live HTTP 200 resolution.
6. **`engagement-context-audit`**: Evaluates above-the-fold orientation (4-question 5-second test), heading information scent, link anchor text discoverability, and destination navigation reachability.
7. **`assistant-representation-audit`**: Cross-checks observed AI assistant answers (ChatGPT, Claude, Gemini, Perplexity) against verified first-party facts using numerical float comparisons.

---

## Requirements & Compliance

- **agentskills.io Compliant:** All 7 skills include valid `SKILL.md` frontmatter, lean bodies (< 500 lines), and progressive disclosure.
- **Top-Level Manifest:** `marketplace.json` lists all 7 skills and designates `audit-orchestrator` as `"entrypoint": true`.
- **Zero Third-Party Dependencies:** 100% Python 3 standard library (`urllib`, `sqlite3`, `json`, `html.parser`, `re`, `xml.etree`, `ipaddress`, `gzip`).
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
    │   │   ├── acquire_inventory.py
    │   │   ├── audit_db.py
    │   │   ├── orchestrator.py
    │   │   ├── safe_fetch.py
    │   │   ├── synthesize_report.py
    │   │   └── validate_report.py
    │   └── references/
    │       ├── check-contracts/
    │       │   └── contracts-catalog.md
    │       ├── entity-types/
    │       │   ├── organization.yaml
    │       │   └── product.yaml
    │       ├── false-positive-cases/
    │       │   ├── multi-tier-pricing.md
    │       │   └── no-jsonld.md
    │       ├── intent-library/
    │       │   ├── pricing-comparison.yaml
    │       │   └── product-purchase.yaml
    │       ├── platforms/
    │       │   └── crawler-matrix-reference.md
    │       ├── taxonomy/
    │       │   ├── root-causes.md
    │       │   └── severity-model.md
    │       ├── COMPOSITION_GUIDELINES.md
    │       ├── REPORT_SCHEMA.json
    │       └── REPORT_SCHEMA.md
    ├── discoverability-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── discoverability_check.py
    │   └── references/
    │       ├── CHECK_CONTRACTS.md
    │       └── seo-foundations.md
    ├── entity-content-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── entity_content_check.py
    │   └── references/
    │       ├── CHECK_CONTRACTS.md
    │       └── structured-data-validation.md
    ├── fact-consistency-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── fact_consistency_check.py
    │   └── references/
    │       ├── ENTITY_CORROBORATION.md
    │       ├── FRESHNESS_CHECKLIST.md
    │       ├── fact-normalization.md
    │       └── temporal-freshness.md
    ├── corroboration-authority-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── corroboration_check.py
    │   └── references/
    │       ├── CHECK_CONTRACTS.md
    │       └── identity-vs-claim.md
    ├── engagement-context-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── engagement_check.py
    │   └── references/
    │       ├── 5-second-orientation.md
    │       ├── AI_SNIPPET_GUIDELINES.md
    │       └── ENGAGEMENT_RUBRIC.md
    └── assistant-representation-audit/
        ├── SKILL.md
        ├── scripts/
        │   └── representation_check.py
        └── references/
            ├── CHECK_CONTRACTS.md
            └── mention-vs-citation.md
```

---

## Usage

### 1. Run Complete Audit via Entrypoint (JSON Output)

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --format json
```

### 2. Run Audit with Markdown Output & SQLite Storage

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --format markdown --db audits.db
```

### 3. Step-by-Step Shared Inventory Pipeline

```bash
# Step 1: Acquire Shared Site Inventory (< 60s)
python3 skills/audit-orchestrator/scripts/acquire_inventory.py --site https://example.com --output /tmp/inv.json

# Step 2: Run Specialists using Shared Inventory
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory /tmp/inv.json --format json > /tmp/d.json
python3 skills/entity-content-audit/scripts/entity_content_check.py --site https://example.com --inventory /tmp/inv.json --format json > /tmp/e.json
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory /tmp/inv.json --format json > /tmp/f.json
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory /tmp/inv.json --format json > /tmp/c.json
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory /tmp/inv.json --format json > /tmp/eng.json

# Step 3: Synthesize and Validate Master Report
python3 skills/audit-orchestrator/scripts/synthesize_report.py \
  --site https://example.com \
  --inventory /tmp/inv.json \
  --discoverability /tmp/d.json \
  --entity /tmp/e.json \
  --fact /tmp/f.json \
  --corroboration /tmp/c.json \
  --engagement /tmp/eng.json \
  --db audits.db \
  --format json
```

### 4. Validate Audit Report

```bash
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
      "cause_id": "AI_RETRIEVAL_BLOCKED",
      "impact": "Content is excluded from real-time AI assistant citations and generative search answers.",
      "evidence": "robots.txt disallows OAI-SearchBot and PerplexityBot on path '/'.",
      "suggested_action": {
        "summary": "Allow AI search retrieval bots in robots.txt while maintaining training crawler restrictions if desired.",
        "priority": "critical",
        "verification": "Inspect robots.txt to confirm Allow or absence of Disallow for OAI-SearchBot and PerplexityBot."
      }
    }
  ],
  "audit_metrics": {
    "execution_time_seconds": 12.4,
    "html_pages_sampled": 8,
    "sitemaps_processed": 1,
    "urls_discovered": 45,
    "page_types_covered": {
      "homepage": 1,
      "product": 3,
      "pricing": 1,
      "about": 1,
      "contact": 1,
      "documentation": 1
    },
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
