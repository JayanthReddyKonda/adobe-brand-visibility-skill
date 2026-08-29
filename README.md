# Brand AI-Readiness & Search Visibility Audit System

An enterprise-grade, zero-dependency Python intelligence system and agentic audit marketplace designed to evaluate, diagnose, and optimize website visibility across modern AI search engines (**ChatGPT Search**, **Claude Search**, **Perplexity AI**, and **Google AI Overviews**).

Conforms strictly to the [`agentskills.io`](https://agentskills.io) multi-skill marketplace specification with 7 specialized diagnostic skills, an entrypoint orchestrator, zero-dependency SQLite telemetry persistence, and an exhaustive 29-test unit and benchmark evaluation suite.

---

## Table of Contents

1. [Problem Statement & Background](#problem-statement--background)
2. [Architectural Blueprint](#architectural-blueprint)
3. [The 7 Diagnostic Specialist Skills](#the-7-diagnostic-specialist-skills)
4. [Quickstart & CLI Reference](#quickstart--cli-reference)
   - [Direct Orchestrated Audit](#1-direct-orchestrated-audit)
   - [Decoupled Multi-Skill Agent Workflow](#2-decoupled-multi-skill-agent-workflow)
   - [SQLite Telemetry & Trend Tracking](#3-sqlite-telemetry--trend-tracking)
   - [AI Assistant Output Verification](#4-ai-assistant-output-verification)
5. [Causal Failure Taxonomy](#causal-failure-taxonomy)
6. [The Mathematical Answerability Engine](#the-mathematical-answerability-engine)
7. [False-Positive Protection & Scoping Guardrails](#false-positive-protection--scoping-guardrails)
8. [Security & SSRF Defense Model](#security--ssrf-defense-model)
9. [Testing & Evaluation Benchmarks](#testing--evaluation-benchmarks)
10. [Repository Structure](#repository-structure)

---

## Problem Statement & Background

Traditional Search Engine Optimization (SEO) focused on keyword matching, backlink authority, and PageRank. Modern AI Search Assistants (SearchGPT, Claude, Perplexity, Gemini) function fundamentally differently:

1. **Direct Retrieval & Extraction:** AI retrieval crawlers fetch raw HTML payloads and require instant semantic extractability without rendering complex JavaScript client-side applications.
2. **Entity & Structured Data Grounding:** Machine-explicit JSON-LD schemas (`Organization`, `Product`, `Offer`) allow LLMs to build verified entity knowledge graphs rather than guessing from unorganized body copy.
3. **Fact Consistency & Hallucination Resistance:** Contradictory prices, obsolete product listings, or mismatched commercial terms across secondary pages confuse AI retrieval models, leading to citation suppression or empirical price hallucinations.
4. **Context Continuity & 5-Second Orientation:** AI search visitors land directly on specific deep routes. If the page lacks clear heading information scent, immediate value proposition, or related navigation paths, bounce rates spike.

This system provides automated, evidence-backed diagnostic audits that uncover the exact technical and architectural root causes behind AI visibility suppression.

---

## Architectural Blueprint

```
                                  Target Website / URL
                                           │
                                           ▼
                       [Step 1: Shared Inventory Acquisition]
                       (acquire_inventory.py - 60s max budget)
                         - Homepage discovery & status
                         - robots.txt & RFC 9309 rule parsing
                         - XML sitemaps & sitemap indexes
                         - Type-safe HTML page inventory
                                           │
                        ┌──────────────────┴──────────────────┐
                        │                                     │
                        ▼                                     ▼
             [Autonomous Agent Harness]               [Direct Pipeline CLI]
            (Invokes Skills Sequentially)             (orchestrator.py CLI)
                        │                                     │
       ┌────────────────┼────────────────┬────────────────────┼────────────────┐
       ▼                ▼                ▼                    ▼                ▼
[discoverability]   [entity]           [fact]          [corroboration]   [engagement]
 - AI bot matrix    - JSON-LD Org      - Scoped ledger   - sameAs check   - 5-sec scent
 - noindex tokens   - Answerability    - Price float     - HTTP 200       - Reachability
 - CSR empty DOM    - Product schema   - Lifecycle stat  - Dead anchors   - Intent route
       │                │                │                    │                │
       └────────────────┼────────────────┴────────────────────┼────────────────┘
                        │
                        ▼ (Optional Layer)
           [assistant-representation]
            - Empirical claim verification
            - Price conflict detection
            - Citation link tracking
                        │
                        ▼
            [Step 8: Master Evidence Synthesis Gate]
             (synthesize_report.py / orchestrator.py)
              - Multi-locale finding deduplication
              - Causal failure taxonomy mapping
              - Proactive recommendation ranking
              - Strict Schema Validation Gate (validate_report.py)
                        │
                        ▼
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
[JSON Report Output]            [SQLite Audit Database]
(stdout / file.json)            (audits, specialist_runs, findings)
```

---

## The 7 Diagnostic Specialist Skills

| Skill Directory | Role | Core Responsibility |
| :--- | :--- | :--- |
| **`skills/audit-orchestrator`** | Entrypoint | Coordinates crawl acquisition, dispatches specialist diagnostics, reconciles multi-signal evidence, maps root causes, validates output schema, and persists relational history to SQLite. |
| **`skills/discoverability-audit`** | Specialist | Evaluates search engine accessibility, robots.txt AI-crawler rules (differentiating retrieval vs training bots), tokenized `noindex` directives, raw HTML rendering gaps (CSR), and external canonical links. |
| **`skills/entity-content-audit`** | Specialist | Validates machine-explicit `Organization` identity, polymorphic structured data (`Product`, `Offer`), and calculates the weighted **Answerability Index** across page archetypes. |
| **`skills/fact-consistency-audit`** | Specialist | Constructs an entity-scoped fact ledger, performs exact decimal float price comparisons (`$49.99` vs `€1.250,50` vs `₹5,499.00`), and flags product lifecycle contradictions (discontinued vs current). |
| **`skills/corroboration-authority-audit`** | Specialist | Verifies external authority anchors by probing declared `sameAs` identity links (Wikidata, Crunchbase, Wikipedia, social profiles) for live HTTP 200 responses. |
| **`skills/engagement-context-audit`** | Specialist | Audits above-the-fold 5-second visitor orientation, heading information scent, navigation reachability, and intent-to-landing match to minimize AI-referred bounce rates. |
| **`skills/assistant-representation-audit`** | Specialist (Enrichment) | Cross-checks empirical LLM responses against verified on-site facts to detect pricing hallucinations, unsupported claims, and citation drop-offs. |

---

## Quickstart & CLI Reference

### 1. Direct Orchestrated Audit

Run a full audit against any domain in one command:
```bash
# Emit strictly validated JSON to stdout
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py --site https://frescopa.coffee/ --format json

# Save report to a file
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py --site https://frescopa.coffee/ --output report.json --format json

# Format human-readable Markdown summary
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py --site https://frescopa.coffee/ --format markdown
```

### 2. Decoupled Multi-Skill Agent Workflow

When executed by an AI agent harness (e.g. Google Antigravity, Claude, AutoGen, Swarm), each specialist skill is executed independently and aggregated via the synthesis gate:

```bash
# 1. Acquire shared crawl inventory
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/acquire_inventory.py   --site https://frescopa.coffee/   --output /tmp/inventory.json   --format json

# 2. Run Discoverability Specialist
python3 brand-ai-readiness-audit/skills/discoverability-audit/scripts/discoverability_check.py   --site https://frescopa.coffee/   --inventory /tmp/inventory.json   --format json > /tmp/disc.json

# 3. Run Entity & Content Specialist
python3 brand-ai-readiness-audit/skills/entity-content-audit/scripts/entity_content_check.py   --site https://frescopa.coffee/   --inventory /tmp/inventory.json   --format json > /tmp/entity.json

# 4. Run Fact Consistency Specialist
python3 brand-ai-readiness-audit/skills/fact-consistency-audit/scripts/fact_consistency_check.py   --site https://frescopa.coffee/   --inventory /tmp/inventory.json   --format json > /tmp/fact.json

# 5. Run Corroboration & Authority Specialist
python3 brand-ai-readiness-audit/skills/corroboration-authority-audit/scripts/corroboration_check.py   --site https://frescopa.coffee/   --inventory /tmp/inventory.json   --format json > /tmp/corr.json

# 6. Run Engagement & Continuity Specialist
python3 brand-ai-readiness-audit/skills/engagement-context-audit/scripts/engagement_check.py   --site https://frescopa.coffee/   --inventory /tmp/inventory.json   --format json > /tmp/eng.json

# 7. Synthesize into Master Report
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/synthesize_report.py   --site https://frescopa.coffee/   --inventory /tmp/inventory.json   --discoverability /tmp/disc.json   --entity /tmp/entity.json   --fact /tmp/fact.json   --corroboration /tmp/corr.json   --engagement /tmp/eng.json   --format json
```

### 3. SQLite Telemetry & Trend Tracking

Record audit history, trace individual specialist executions, and track domain improvements over time without any third-party databases:

```bash
# Run audit and persist to SQLite database
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py   --site https://frescopa.coffee/   --db audit_history.db   --format json

# View historical audit summary list
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/audit_db.py --db audit_history.db --list

# Inspect complete relational trace for a specific audit ID
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/audit_db.py --db audit_history.db --details 1

# Calculate domain visibility & defect trends over time
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/audit_db.py --db audit_history.db --trend frescopa.coffee
```

### 4. AI Assistant Output Verification

Cross-check actual logged answers from ChatGPT, Claude, Gemini, or Perplexity against ground-truth website facts:

```bash
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py   --site https://frescopa.coffee/   --with-representation   --responses sample_observations.json   --format json
```

---

## Causal Failure Taxonomy

Every audit finding is assigned an architectural root-cause code under a standardized 11-family taxonomy:

```
CAUSAL TAXONOMY HIERARCHY
├── DISCOVERY
│   ├── DISCOVERY.ACCESS
│   │   ├── AI_RETRIEVAL_BLOCKED         (Critical: AI search bot disallowed in robots.txt)
│   │   ├── NOINDEX_EXCLUSION            (Critical: noindex/none directive on public route)
│   │   └── TARGET_UNREACHABLE           (Critical: Root landing URL returns 4xx/5xx)
│   ├── DISCOVERY.DISCOVERY_PATH
│   │   └── CANONICAL_FRAGMENTATION      (Medium: Canonical tag points to external host)
│   └── DISCOVERY.REPRESENTATION_AVAILABILITY
│       └── RENDERED_CONTENT_GAP         (High: Initial raw HTML is empty CSR SPA root)
├── ENTITY
│   ├── ENTITY.IDENTITY
│   │   └── MATERIAL_ENTITY_AMBIGUITY    (Medium: No machine-explicit Organization block)
│   ├── ENTITY.STRUCTURED_DATA
│   │   └── INVALID_STRUCTURED_MARKUP    (Low/Medium: Broken JSON-LD syntax)
│   └── ENTITY.ANSWERABILITY
│       └── LOW_ANSWERABILITY_SCORE      (Medium: Material page attributes < 70% complete)
├── FACT
│   ├── FACT.CONSISTENCY
│   │   └── FIRST_PARTY_FACT_CONFLICT    (High: Different prices on same entity across pages)
│   └── FACT.LIFECYCLE
│       └── DISCONTINUED_VS_CURRENT_CONFLICT (High: Obsolete item advertised as active)
├── AUTHORITY
│   └── AUTHORITY.IDENTITY_CORROBORATION
│       └── BROKEN_AUTHORITY_ANCHOR      (Medium: Declared sameAs profile returns 4xx/5xx)
├── EXPERIENCE
│   └── EXPERIENCE.CONTINUITY
│       ├── LOW_INFORMATION_SCENT        (Medium: Generic H1 or missing page title context)
│       ├── DESTINATION_NAVIGATION_FRICTION (Medium: No internal links to key destinations)
│       └── INTENT_TO_LANDING_MISMATCH   (Medium: Pricing landing page omits prices)
└── REPRESENTATION
    └── REPRESENTATION.ACCURACY
        ├── AI_FACT_CONFLICT             (High: Assistant asserts incorrect commercial terms)
        └── AI_CITATION_GAP              (Info: Brand mentioned without source link citation)
```

---

## The Mathematical Answerability Engine

The `entity-content-audit` skill implements a deterministic, weighted **Answerability Index** that measures whether an AI assistant has sufficient structured material data to answer commercial search questions.

$$	ext{Answerability Score} = rac{\sum_{i} w_i \cdot \mathbb{I}(	ext{attribute}_i 	ext{ present})}{\sum_{i} w_i}$$

### Archetype Weighting Matrices

- **Product Detail Pages:** Product Name ($0.30$), Price ($0.25$), Stock Availability ($0.25$), Specifications ($0.20$).
- **Pricing & Tier Pages:** Tier Names ($0.35$), Numerical Prices ($0.35$), Feature Matrix ($0.30$).
- **Subscription Pages:** Plan Description ($0.35$), Selection Options ($0.35$), Call-to-Action ($0.30$).
- **Contact & Support Pages:** Email Channel ($0.40$), Phone Channel ($0.30$), Location/Form ($0.30$).

Pages scoring below $0.70$ ($70\%$) trigger a `LOW_ANSWERABILITY_SCORE` diagnostic finding with explicit lists of missing attributes.

---

## False-Positive Protection & Scoping Guardrails

1. **Interval-Aware Price Scoping:** Prices are keyed by `(entity, currency, interval)`. A SaaS product offering `$15/mo` and `$150/yr` is recognized as two distinct billing tiers and will **never** trigger a false price contradiction.
2. **Tokenized Directive Parsing:** Directives in `<meta name="robots">` are parsed via token delimiters (`[,;\s]+`). `max-image-preview:none` is isolated and will **never** trigger a false `noindex` alert.
3. **Training vs Retrieval Bot Separation:** Disallowing foundation training scrapers (`GPTBot`, `ClaudeBot`, `CCBot`) is treated as intentional data governance (`info` observation). Only blocks on real-time search retrieval crawlers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) trigger `critical` defects.
4. **Strict Content-Type Separation:** XML sitemaps, robots.txt, and JSON feeds are classified as infrastructure assets and **never** enter semantic or visitor engagement checks.
5. **Contact Page Semantics:** Universal contact headlines ("Contact us", "Get in touch", "Contáctenos", "お問い合わせ") are recognized as semantically complete.

---

## Security & SSRF Defense Model

Every audit treats fetched external web content as **untrusted data**:
- **Prompt Injection Defense:** External page titles, headings, meta tags, and robots.txt content are treated strictly as data payloads and never executed as agent instructions.
- **SSRF Defense:** Every URL and redirect target is resolved to its IP address and verified against private spaces:
  - Loopback (`127.0.0.0/8`, `::1`)
  - Private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Cloud Metadata (`169.254.169.254`, `169.254.0.0/16`)
  - Multicast & Reserved subnets (`224.0.0.0/4`, `240.0.0.0/4`)
- **Bounded Payload Memory:** Response streams are strictly bounded (HTML $\le 2$ MB, robots.txt $\le 512$ KB) with bounded gzip decompression to prevent zip-bomb exploits.
- **Monotonic Deadline:** Audits enforce a strict global wall-clock limit of 300 seconds using `time.monotonic()`.

---

## Testing & Evaluation Benchmarks

The codebase includes an enterprise-grade automated test suite and local evaluation benchmark fixtures:

```bash
# Run 29 Unit Tests across all 7 layers
python3 test_suite.py

# Run 7 Evaluation Benchmark Fixtures (100% Precision & Recall)
python3 evals_local/run_evals.py
```

### Test Suite Coverage Breakdown

```text
.............................
Ran 29 tests in 0.170s

OK
=== Running Brand AI-Readiness Evaluation Benchmark Suite ===
  [PASS] crawler-blocked: correctly flagged OAI-SearchBot/PerplexityBot as AI_RETRIEVAL_BLOCKED.
  [PASS] conflicting-prices: correctly detected FIRST_PARTY_FACT_CONFLICT on Velocity X9.
  [PASS] csr-rendering: correctly flagged empty client-side root as RENDERED_CONTENT_GAP.
  [PASS] clean-site: verified 0 false positive critical/high defects.
  [PASS] multi-tier-pricing: verified zero false positive price conflicts on distinct billing intervals.
  [PASS] discontinued-lifecycle: correctly detected DISCONTINUED_VS_CURRENT_CONFLICT.
  [PASS] tokenized-noindex: verified zero false positives on max-image-preview:none directives.

All 7 evaluation benchmark tests PASSED (100% precision & recall on standard fixtures).
```

---

## Repository Structure

```text
brand-ai-readiness-audit/
├── marketplace.json                # Master Marketplace Skills Manifest
├── README.md                       # Evaluator & Hackathon Documentation
├── LICENSE                         # Open-source MIT License
├── test_suite.py                   # 29-Test Automated Verification Suite
├── evals_local/                    # Evaluation Benchmark Fixtures
│   ├── run_evals.py                # Benchmark Runner
│   └── fixtures/                   # Standard Test Site Inventories
├── .agents/skills/                 # Synchronized Agent Directory
└── brand-ai-readiness-audit/skills/
    ├── audit-orchestrator/         # Entrypoint Skill
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
    ├── entity-content-audit/
    ├── fact-consistency-audit/
    ├── corroboration-authority-audit/
    ├── engagement-context-audit/
    └── assistant-representation-audit/
```
