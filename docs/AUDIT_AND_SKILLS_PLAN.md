# Brand AI-Readiness Audit — Skills, References, Evals & Scripts Plan

**Specification Standard:** `agentskills.io` Standard and JSON Schema Draft-07  
**Architecture:** Sensor-Brain Cognitive Orchestration Architecture  
**Status:** Canonical Engineering & Operational Plan  

---

## 1. Executive Summary & The Sensor-Brain Paradigm

This plan specifies the architecture, verification procedures, and operational contracts across all eight skills in the Adobe Brand Visibility and AI-Readiness suite.

### The Sensor-Brain Paradigm: Anti-Copy-Paster Directive
A common failure mode in AI agent tooling is creating monolithic scripts that generate pre-canned, generic audit reports, reducing the AI agent to a passive copy-paster. This architecture strictly prohibits that anti-pattern through the **Sensor-Brain Separation of Concerns**:

```text
+-------------------------------------------------------------------------+
|                        COGNITIVE REASONING AGENT                        |
|                                                                         |
|  - Archetype Contextualization (e-commerce, SaaS, publisher, local)     |
|  - 6-Layer Causal DAG Synthesis (root-cause isolation, symptom masking) |
|  - 5-Whys Qualitative Root Cause Analysis                               |
|  - Bespoke Dual-Track Remediation (technical code + creative copy)      |
|  - Forward-Looking Strategic Recommendations (UCP, llms.txt, pricing.md)|
|  - Draft-07 Final Report Assembly and Validation Gate                   |
+-------------------------------------------------------------------------+
                                    |
                    Empirical Telemetry (JSON Contract)
                                    v
+-------------------------------------------------------------------------+
|                      DETERMINISTIC SENSOR LAYER                         |
|                                                                         |
|  - Single-Pass Crawl & Inventory Acquisition (web-scraper)              |
|  - RFC 9309 16-Bot Matrix & HTML SNR Evaluation (discoverability)       |
|  - Schema.org Graph Parsing & Answerability Extraction (entity-content) |
|  - Cross-Page Fact Ledger & Price Variance Detection (fact-consistency) |
|  - Zero-Trust SSRF External sameAs Link Probing (corroboration)         |
|  - Princeton KDD 2024 Citability & Statistical Density (geo-content)    |
|  - 5-Second Orientation, Heading Scent & CTA Reach (engagement-context) |
+-------------------------------------------------------------------------+
```

1. **Deterministic Sensors (`_check.py`, `safe_fetch.py`, `acquire_inventory.py`):**
   - Pure Python 3.9+ standard library with zero runtime third-party dependencies.
   - Strictly gather empirical evidence, extract DOM/HTTP metrics, and output deterministic measurements.
   - Never generate hallucinated marketing prose, speculate on business intent, or bypass SSRF boundaries.
2. **Cognitive Agent Brain (`SKILL.md`, `knowledge-base.md`, `orchestrator.py --telemetry`):**
   - Ingests aggregated sensor telemetry via `orchestrator.py --telemetry`.
   - Analyzes business archetype, evaluates business impact, resolves causal dependencies, and synthesizes customized dual-track remediation actions.
   - Emits a strictly validated Draft-07 JSON deliverable alongside an executive briefing.

---

## 2. Portfolio Topology & Mutation Boundaries

| Directory | Role | Mutation Policy | Prohibitions |
| :--- | :--- | :--- | :--- |
| `src/skills/` | Canonical Source of Truth | Author all production code, manifests, and references here. | No pip runtime packages. Python stdlib only. |
| `tests/` | Test Suite & Fixtures | Unit, integration, system, fixture, and validator tests. | No production logic in test helpers. |
| `.agents/skills/` | Agent Runtime Mirror | Read-only. Generated via `scripts/sync.py`. | Never edit directly. |
| `resources/` | External Vendor References | Frozen reference repositories. | Never edit, format, or lint. |
| `docs/` | Architecture & Documentation | Engineering manuals and architecture specifications. | Zero emojis and zero LaTeX syntax. |
| `scripts/` | Automation & Tooling | Packaging (`build.py`), syncing (`sync.py`), QA (`qa_check.sh`). | Keep executable and cross-platform. |
| `build/` | Staging Distribution | Generated build directory. | Never commit manual files. |

---

## 3. Skill-by-Skill Audit Plan, References, Evals & Scripts

### 3.1 `audit-orchestrator` (Master Coordinator & Synthesis Engine)
- **Role:** Entrypoint skill. Coordinates the 7 specialist skills, runs the single-pass acquisition pipeline, aggregates telemetry, gates findings through the 6-Layer Causal DAG, and enforces Draft-07 JSON schema compliance.
- **Scripts:**
  - `orchestrator.py`: Main orchestration CLI supporting `--telemetry` (for AI agents), `--baseline-only` (for headless CI testing), `--deliverable`, and full causal report synthesis.
  - `plan.py`: Remediation readiness calculator and mathematical priority ranking index:
    `priority_index = 5 * severity + (6 - difficulty)`
  - `bundle_context.py`: Site-specific context compiler extracting relevant knowledge base sections based on detected archetype and signals.
  - `causal_gate.py`: 6-Layer Causal DAG enforcing deterministic suppression of downstream symptoms when upstream blockers exist.
  - `validate_report.py`: Strict Draft-07 schema validator verifying output integrity.
- **References:**
  - `checks.json`: Master 134-check domain catalogue with activation criteria, severity bands, and V/C/E/X remedy levels.
  - `checks.md`: Master markdown catalogue documenting all 134 diagnostic procedures.
  - `core-synthesis-digest.md`: High-density briefing covering the 6-Layer Causal DAG, scoring weights, and Princeton GEO heuristics.
  - `knowledge-base.md`: Unified master reference containing 26 core sections including the 17 root causes, Draft-07 contracts, epistemic reasoning policy, zero-trust SSRF policy, normalized vocabulary, and detection feasibility scales.
  - `report-schema.json`: Production Draft-07 report schema.
  - `telemetry-schema.json`: Schema for empirical sensor telemetry.
- **Evals (`evals/evals.json`):**
  - Eval 1: Full-site audit against live target emitting schema-valid Draft-07 report with dual-track remediation.
  - Eval 2: Offline deterministic audit using pre-acquired `inv.json` executing within bounded time limits without network overhead.

### 3.2 `web-scraper` (Single-Pass Acquisition & SSRF Engine)
- **Role:** Safely fetches, parses, and structures site inventories under zero-trust pre-socket SSRF protection.
- **Scripts:**
  - `safe_fetch.py`: Socket-level pre-connect DNS TOCTOU resolution, subnet blocklists, bounded redirects (max 5), and hard size caps.
  - `acquire_inventory.py`: Single-pass crawler orchestrating RFC 9309 robots.txt evaluation, sitemap discovery, page fetching, Trafilatura-grade HTML extraction, JSON-LD parsing, and CLI interface.
  - `crawler/`: 16 pure-Python modules implementing RFC 9309 robots matrices across 16 AI retrieval and training bots, recursive sitemap parsing, clean Markdown extraction with SNR scoring, Schema.org JSON-LD graph flattening, streaming HTML parsing, and zero-trust SSRF defense.
- **Enriched Acquisition Contract:**
  - Extracts interactive CTAs (`ctas`) with commercial intent classification (`is_commercial_cta`).
  - Captures internationalization tags (`hreflangs`) and edge HTTP headers (`x_robots_tag`, HTTP `Link` canonicals).
  - Extracts temporal freshness timestamps (`dates`: published, modified, Last-Modified) and author metadata.
  - Harvests RFC-compliant emails and phone numbers (`contact_info`) and external social links (`social_links`).
  - Probes machine discoverability endpoints: `/llms.txt`, `/pricing.md`, `/.well-known/ai-plugin.json`, `/.well-known/security.txt`.
- **References:**
  - `bot-registry.json`: Authoritative registry of 16 AI crawler user agents, provider roles (retrieval vs training), and capabilities.
  - `knowledge-base.md`: Complete crawler matrix rules, RFC 9309 longest-match semantics, Trafilatura-grade SNR extraction, and SSRF subnet tables.
- **Evals (`evals/evals.json`):**
  - Eval 1: Multi-page crawl emitting standard `inv.json` site inventory with robots, sitemap, and parsed page records.
  - Eval 2: SSRF defense rejection of private IP ranges, loopback, and cloud metadata targets.

### 3.3 `discoverability-audit` (Crawlability & Rendering Sensor)
- **Role:** Evaluates whether AI retrieval engines can access, parse, and index target web pages.
- **Scripts:**
  - `discoverability_check.py`: Evaluates RFC 9309 crawler permissions across 16 AI bots, meta robots noindex directives, edge `X-Robots-Tag` headers, canonical tag validity (HTML vs HTTP headers), hreflang consistency, machine discoverability manifests, and raw HTML rendering completeness (Client-Side Rendering detection).
- **References:**
  - `checks.md`: Domain checks A1 through H4 covering crawler access, headers, canonicals, and rendering.
  - `knowledge-base.md`: Comprehensive discoverability rules, bot distinction matrices, and rendering gap thresholds.
- **Evals (`evals/evals.json`):**
  - Eval 1: Detection of AI retrieval crawler blocking in `robots.txt`.
  - Eval 2: Identification of unrendered client-side rendering (CSR) single-page application shells.

### 3.4 `entity-content-audit` (Structured Data & Answerability Sensor)
- **Role:** Audits machine-explicit Schema.org structured data, entity disambiguation, and commercial answerability.
- **Scripts:**
  - `entity_content_check.py`: Extracts and validates Schema.org JSON-LD graphs (`Organization`, `Product`, `Offer`, `WebSite`), cross-references on-page social links against `sameAs` arrays to detect `MISSING_SAMEAS_VERIFICATION`, verifies structured contact channels, and evaluates commercial answerability across SaaS, e-commerce, services, and content archetypes.
- **References:**
  - `checks.md`: Domain checks E1 through E7 covering entity definitions, pricing transparency, and schema completeness.
  - `knowledge-base.md`: Unified knowledge base incorporating Organization and Product schema specifications, primary surfaces, volatility indicators, verification conditions, and master linked graph templates.
- **Evals (`evals/evals.json`):**
  - Eval 1: Identification of missing machine-explicit `Organization` structured data on homepage.
  - Eval 2: Validation of complete e-commerce `Product` and `Offer` schema attributes.

### 3.5 `fact-consistency-audit` (Cross-Page Fact Ledger Sensor)
- **Role:** Detects cross-page factual contradictions, pricing discrepancies, and stale content drift.
- **Scripts:**
  - `fact_consistency_check.py`: Builds a multi-page fact ledger (scoped prices, contact emails, phone numbers, copyright dates, trial durations), detects `CONFLICTING_COMMERCIAL_TERMS`, and diffs first-party claims to isolate verified internal contradictions.
- **References:**
  - `checks.md`: Domain checks covering factual accuracy, price consistency, and temporal freshness.
  - `knowledge-base.md`: Scoped fact extraction rules, price normalization algorithms, and tolerance thresholds.
- **Evals (`evals/evals.json`):**
  - Eval 1: Isolation of contradictory prices for the same product across different site routes.
  - Eval 2: Detection of legacy copyright dates and outdated contact information.

### 3.6 `corroboration-authority-audit` (External Identity Corroboration Sensor)
- **Role:** Verifies declared external identity links (`sameAs`) and independent third-party knowledge graph anchors.
- **Scripts:**
  - `corroboration_check.py`: Probes declared `sameAs` URLs (Wikidata, Wikipedia, LinkedIn, Crunchbase) under zero-trust SSRF sandboxing with an 8.0s hard cumulative deadline, flags `UNLINKED_KNOWLEDGE_GRAPH_ANCHOR` when verified brand assets exist on-site but are omitted from structured data, and verifies candidate backlinks.
- **References:**
  - `checks.md`: Domain checks BC1 through PP7 covering brand corroboration and portfolio proof.
  - `knowledge-base.md`: Tier-1 authority node evaluation criteria, anchor reachability rules, and backlink verification bounds.
- **Evals (`evals/evals.json`):**
  - Eval 1: Probing declared `sameAs` links to verify HTTP 200 reachability and entity presence.
  - Eval 2: Rejection of non-HTTPS or private-network authority links by SSRF filters.

### 3.7 `geo-content-audit` (Generative Engine Optimization Sensor)
- **Role:** Audits web content against Princeton KDD 2024 and AutoGEO generative engine optimization research to maximize AI citation probability.
- **Scripts:**
  - `geo_content_check.py`: Evaluates content citability heuristics: Bottom Line Up Front (BLUF) lead paragraphs, statistical evidence density, quotation ratios, causal conjunction frequency, passage chunking, credentialed author attribution (`PROACTIVE.GEO.CREDENTIALED_AUTHOR_ATTRIBUTION.001`), and commercial CTA intrusion (`COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT`).
- **References:**
  - `checks.md`: Domain checks N1 through N15 covering Princeton GEO dimensions.
  - `knowledge-base.md`: Research synthesis, 9 GEO optimization vectors, PAWC visibility formulas, and AI writing pattern guardrails.
- **Evals (`evals/evals.json`):**
  - Eval 1: Detection of low statistical density and absent BLUF lead answers in informational content.
  - Eval 2: Evaluation of passage self-containment and quotation attribution.

### 3.8 `engagement-context-audit` (Post-Citation Visitor Continuity Sensor)
- **Role:** Evaluates visitor orientation, information scent, and intent-handoff continuity for traffic arriving from AI search engine citations.
- **Scripts:**
  - `engagement_check.py`: Evaluates 5-second orientation, heading information scent, viewport answer anchoring, ARI cognitive readability, CTA reachability from structured inventory CTAs, navigation friction, and optional first-party analytics cross-correlation.
- **References:**
  - `checks.md`: Domain checks I1-I2 (deep-link stability) and J1-J10 (identity, navigability, prominence, conversion friction, recovery).
  - `knowledge-base.md`: Unified knowledge base incorporating Section 4 intent-handoff specifications (pricing comparison and product purchase), heading scent matrix, and dual-track analytics evaluation.
- **Evals (`evals/evals.json`):**
  - Eval 1: Detection of low information scent or generic H1 headings on primary content pages.
  - Eval 2: Verification of pricing intent alignment and visible commercial terms on pricing routes.

---

## 4. Verification & QA Pipeline Protocol

All code modifications must pass the four-tier verification suite before deployment:

```bash
# 1. Package Hygiene & Integrity Validator
python -m unittest tests/validate_package.py

# 2. Marketplace Distribution Packaging & Zip Validation
python scripts/build.py
python tests/validate_package.py brand-ai-readiness-audit.zip

# 3. Cross-Check Reference Join (134/134 Checks)
python scripts/cross_check_references.py

# 4. Full Pytest Test Suite
pytest tests/ -q

# 5. Mirror Synchronization
python scripts/sync.py
```

### Invariant Checks Verified:
1. Pure Python 3.9+ standard library exclusively across `src/skills/` (zero pip runtime dependencies).
2. Immutable vendor references in `resources/` remain untouched and untracked.
3. Distribution zip `brand-ai-readiness-audit.zip` packages cleanly into a single root folder with size <= 50 MB.
4. All 134 checks join with zero orphans between `checks.json` and all `checks.md` reference files.
5. All relative markdown links resolve to existing files within the package.
6. Zero emojis and zero LaTeX formatting across all markdown documents, manifests, and knowledge bases.
