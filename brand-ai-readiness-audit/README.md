# Brand AI-Readiness Audit Marketplace

**Adobe University Hackathon 2026 — Round 3 Submission**  
**Specification:** [agentskills.io](https://agentskills.io) Compliant Multi-Skill Marketplace  
**Designated Entrypoint:** `skills/audit-orchestrator`

---

## Executive Summary

The **Brand AI-Readiness Audit Marketplace** is a zero-dependency, production-grade agentic auditing suite designed to evaluate why a brand is invisible, misrepresented, or experiencing high bounce rates across modern AI search engines (**ChatGPT Search**, **Claude Search**, **Perplexity AI**, and **Google AI Overviews**).

It composes **7 specialist skills** under a single entrypoint with an evidence-backed shared crawl inventory, strict 5-minute wall-clock execution budget, zero-dependency SSRF protection, causal root-cause attribution, and strict output schema validation.

```
                                  Target Website / URL
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
                Direct CLI Execution               Agent Harness Invocation
                        │                                     │
                        │                       [skills/audit-orchestrator/SKILL.md]
                        │                                     │
                        │                       ┌─────────────┴─────────────┐
                        │                       ▼                           ▼
                        │              Step 1: Inventory           Steps 2–7: Specialists
                        │             (acquire_inventory.py)      (discoverability, entity,
                        │                       │                  fact, corroboration,
                        │                       │                  engagement, rep.)
                        │                       └─────────────┬─────────────┘
                        │                                     │
                        ▼                                     ▼
             [orchestrator.py]                     Step 8: Synthesis Gate
             (Unified Pipeline)                    (synthesize_report.py)
                        │                                     │
                        └──────────────────┬──────────────────┘
                                           │
                                           ▼
                                 [validate_report.py]
                                           │
                                           ▼
                             Validated JSON Audit Report
```

---

## Quick Evaluation Commands

### 1. Run Complete Audit via Entrypoint (JSON Output)
```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://frescopa.coffee/ --format json
```

### 2. Validate Emitted Report Against Specification Schema
```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://frescopa.coffee/ --format json | python3 skills/audit-orchestrator/scripts/validate_report.py -
```

### 3. Run Step-by-Step Decoupled Agent Workflow
```bash
# Step 1: Acquire type-safe shared crawl inventory
python3 skills/audit-orchestrator/scripts/acquire_inventory.py --site https://frescopa.coffee/ --output /tmp/inv.json --format json

# Step 2: Access & Crawler Matrix Audit
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://frescopa.coffee/ --inventory /tmp/inv.json --format json > /tmp/disc.json

# Step 3: Entity Identity & Answerability Audit
python3 skills/entity-content-audit/scripts/entity_content_check.py --site https://frescopa.coffee/ --inventory /tmp/inv.json --format json > /tmp/entity.json

# Step 4: Fact Consistency & Lifecycle Audit
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://frescopa.coffee/ --inventory /tmp/inv.json --format json > /tmp/fact.json

# Step 5: Authority Link Verification
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://frescopa.coffee/ --inventory /tmp/inv.json --format json > /tmp/corr.json

# Step 6: Engagement & 5-Second Orientation Audit
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://frescopa.coffee/ --inventory /tmp/inv.json --format json > /tmp/eng.json

# Step 7: Synthesize All Specialist Findings into Final Validated Report
python3 skills/audit-orchestrator/scripts/synthesize_report.py \
  --site https://frescopa.coffee/ \
  --inventory /tmp/inv.json \
  --discoverability /tmp/disc.json \
  --entity /tmp/entity.json \
  --fact /tmp/fact.json \
  --corroboration /tmp/corr.json \
  --engagement /tmp/eng.json \
  --format json
```

### 4. Run With Optional AI Assistant Representation Cross-Check
```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py \
  --site https://frescopa.coffee/ \
  --with-representation \
  --responses path/to/observed_responses.json \
  --format json
```

---

## Marketplace Architecture & Skills Catalog

| Skill ID | Role | Key Diagnostic Checks | Primary Reference |
| :--- | :--- | :--- | :--- |
| **`audit-orchestrator`** | **Entrypoint** | Shared inventory acquisition, specialist dispatch, causal root-cause attribution, deduplication, schema validation gate. | `references/composition-guidelines.md` |
| **`discoverability-audit`** | Specialist | RFC 9309 crawler rules (retrieval vs. training bots), tokenized `noindex` directives, raw HTML rendering gaps (CSR), external canonicals. | `references/crawler-matrix-reference.md` |
| **`entity-content-audit`** | Specialist | Machine-explicit `Organization` identity, polymorphic structured data (`Product`, `Offer`), weighted **Answerability Index** (≥ 70%). | `references/structured-data-validation.md` |
| **`fact-consistency-audit`** | Specialist | Scoped fact ledger (`entity`, `currency`, `interval`), exact float price normalization, product lifecycle contradictions (discontinued vs current). | `references/multi-tier-pricing.md` |
| **`corroboration-authority-audit`** | Specialist | Live HTTP 200 validation for declared `sameAs` authority links (Wikidata, Crunchbase, official profiles) with timeout safeguards. | `references/identity-vs-claim.md` |
| **`engagement-context-audit`** | Specialist | Above-the-fold 4-question orientation test (5-second rule), heading information scent, navigation reachability, intent-to-landing match. | `references/5-second-orientation.md` |
| **`assistant-representation-audit`** | Specialist | Empirical cross-check of observed LLM responses against verified on-site facts using numerical price comparisons and citation tracking. | `references/mention-vs-citation.md` |

---

## Directory Layout (Flattened & Lowercase Standardized)

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
    │       ├── composition-guidelines.md
    │       ├── contracts-catalog.md
    │       ├── report-schema.json
    │       ├── report-schema.md
    │       ├── root-causes.md
    │       └── severity-model.md
    ├── discoverability-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── discoverability_check.py
    │   │   └── safe_fetch.py
    │   └── references/
    │       ├── crawler-matrix-reference.md
    │       ├── discoverability-contracts.md
    │       └── seo-foundations.md
    ├── entity-content-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── entity_content_check.py
    │   │   └── safe_fetch.py
    │   └── references/
    │       ├── entity-contracts.md
    │       ├── no-jsonld.md
    │       ├── organization.yaml
    │       ├── product.yaml
    │       └── structured-data-validation.md
    ├── fact-consistency-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── fact_consistency_check.py
    │   │   └── safe_fetch.py
    │   └── references/
    │       ├── entity-corroboration.md
    │       ├── fact-contracts.md
    │       ├── fact-normalization.md
    │       ├── freshness-checklist.md
    │       ├── multi-tier-pricing.md
    │       └── temporal-freshness.md
    ├── corroboration-authority-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── corroboration_check.py
    │   │   └── safe_fetch.py
    │   └── references/
    │       ├── corroboration-contracts.md
    │       └── identity-vs-claim.md
    ├── engagement-context-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── engagement_check.py
    │   │   └── safe_fetch.py
    │   └── references/
    │       ├── 5-second-orientation.md
    │       ├── ai-snippet-guidelines.md
    │       ├── engagement-contracts.md
    │       ├── engagement-rubric.md
    │       ├── pricing-comparison.yaml
    │       └── product-purchase.yaml
    └── assistant-representation-audit/
        ├── SKILL.md
        ├── scripts/
        │   ├── representation_check.py
        │   └── safe_fetch.py
        └── references/
            ├── mention-vs-citation.md
            └── representation-contracts.md

```

---

## Strict Evaluation Criteria & Compliance

### 1. Specification Compliance
- **Zero Third-Party Dependencies:** Implemented using 100% Python standard library (`urllib.request`, `http.client`, `sqlite3`, `html.parser`, `re`, `ipaddress`, `gzip`, `json`, `time`).
- **Lean `SKILL.md` (< 500 lines):** Every skill utilizes progressive disclosure (`scripts/` for deterministic logic, `references/` for domain decision tables).
- **Strict Case-Sensitivity:** All 57 files use consistent lowercase kebab-case naming for 100% Linux/Unix execution reliability.
- **Pure Dispatcher Orchestrator:** No duplicated domain knowledge in the orchestrator; specialist skills maintain exclusive ownership over their domain rules.

### 2. Output Schema Conformance (Adobe Round 3 Contract)
The output JSON strictly conforms to the official contract:
- **`site`** (string): Canonical audited host.
- **`audited_at`** (string): ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`).
- **`audit_status`** (enum: `"ok"`, `"partial"`, `"inconclusive"`).
- **`summary`** (object): Non-negative integer counts for `total_findings`, `critical`, `high`, `medium`, `low`.
- **`findings[]`** (array): Each finding containing `id`, `title`, `severity`, `category`, `root_cause`, `confidence`, `evidence`, and `suggested_action` (`summary`, `priority`, `verification`).
- **`proactive_actions[]`** (array): Deduplicated improvement suggestions.

### 3. False-Positive Control & Deterministic Guardrails
- **Tokenized Directive Parsing:** Replaces substring searches with tokenized parsing to prevent false alarms on directives like `max-image-preview:none`.
- **Interval & Currency Scoped Pricing:** Prices are keyed by `(entity, currency, interval)` so `$15/mo` vs `$150/yr` do not falsely contradict.
- **Crawler Role Separation:** Blocks on search retrieval bots (`OAI-SearchBot`) are flagged as `critical` defects, while foundation model training opt-outs (`GPTBot`) are classified as informational governance signals.
- **Content-Type Invariant:** Non-HTML resources (XML sitemaps, robots.txt, JSON, PDFs) are filtered out and never enter semantic or engagement audits.

### 4. Security & Performance Invariants
- **SSRF Defense:** Blocks DNS rebinding, loopback (`127.0.0.0/8`, `::1`), private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), cloud metadata (`169.254.169.254`), and multicast.
- **Zip-Bomb & Memory Protection:** Streaming bounded gzip decompression capping response payloads at 2 MB.
- **Global Time Budget:** Monotonic deadline management (`time.monotonic()`) guarantees full audit completion in under 300 seconds.
