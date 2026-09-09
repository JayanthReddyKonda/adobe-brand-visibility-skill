# Brand AI-Readiness Audit — System Architecture

**Author:** Jayanth Reddy Konda  
**Version:** 3.0.0  
**Specification Compliance:** `agentskills.io` Standard & JSON Schema Draft-07  

---

## 1. Sensor-Brain Cognitive Orchestration Architecture

The suite implements a modular, specification-compliant architecture operating under two complementary execution modalities:

1. **Brain (Cognitive Agent):** An autonomous AI agent acts as the diagnostic reasoning engine, reading skill manifests (`SKILL.md`) and domain knowledge bases, ingesting empirical sensor telemetry via `orchestrator.py --telemetry`, applying the 6-Layer Causal DAG to isolate root causes and suppress downstream symptoms, classifying the business archetype (e-commerce, SaaS, publisher, local business), and synthesizing bespoke dual-track remediation.
2. **Sensors (Deterministic Scripts):** Pure Python 3.9+ standard library CLI utilities provide raw empirical measurements: RFC 9309 crawler matrices, Schema.org entity extraction, cross-page fact ledgers, external identity probing, Princeton KDD 2024 citability heuristics, and post-citation orientation scoring. Sensors output structured JSON telemetry with zero qualitative judgment.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              COGNITIVE AGENT & ORCHESTRATION ENGINE                     │
│  (audit-orchestrator: orchestrator.py / audit.py / SKILL.md)           │
│                                                                         │
│  1. Single-Pass Acquisition → web-scraper (acquire_inventory.py)        │
│  2. Offline Specialist Sensors → 6 Diagnostic check.py scripts          │
│  3. Multi-Signal Reasoning & Causal Clustering → causal_gate.py         │
│  4. Dual-Track Remediation → Technical fix + Creative fix               │
│  5. 6 Orthogonal Scores & Wilson 95% Confidence Intervals               │
│  6. Final Report Emission & Draft-07 Gate → validate_report.py          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼────────────────────────┐
           ▼                         ▼                        ▼
     Acquisition Engine       Diagnostic Skills         Validation Gate
     web-scraper              discoverability-audit     validate_report.py
     acquire_inventory.py     entity-content-audit      report-schema.json
     safe_fetch.py            fact-consistency-audit
                              corroboration-authority
                              geo-content-audit
                              engagement-context
```

### The Anti-Shortcut Directive
- **The AI Agent is the Brain:** It MUST ingest sensor telemetry via `orchestrator.py --telemetry`, reason over the measurements, apply 5-Whys causal analysis, classify business archetype, and author bespoke dual-track remediation customized to the brand's actual domain, products, and entity anchors.
- **The Scripts are Sensors:** They provide raw deterministic measurements. The headless baseline mode (`orchestrator.py --format json --baseline-only`) is strictly reserved for CI/CD automated test suites, NEVER for agent-to-user delivery.

---

## 2. The Layered Probability Model (The Master Formula)

Modern generative engines operate as multi-stage, partially observable probabilistic retrieval pipelines. The audit models generative visibility as a multiplicative chain:

```text
AI Visibility = Crawl Eligibility * Retrieval Eligibility * Content Citability * Entity Authority * Citation Fidelity
```

with an adjacent **Agentic Commerce Readiness** layer for transactional products and services.

### Methodological Rule: Prominence vs. Presence
In the canonical GEO paper (Aggarwal et al., KDD 2024), the documented "+40% visibility improvement" refers to a change in **Position-Adjusted Word Count (PAWC)** *among an already retrieved set of sources*. It is NOT a flat 40% increase in retrieval probability.

```text
PAWC(r) = sum(wc(s_i) * exp(-pos(s_i))) / sum(wc(s_j))
```

The audit measures citation prominence, citation position, and answer share rather than binary citation presence.

---

## 3. The 6 Orthogonal Scoring Dimensions

To avoid collapsing distinct technical vectors into a single misleading score, the audit evaluates six orthogonal dimensions:

1. **Crawlability Score (Weight: 20%):**
   - Deterministic HTTP 200 responses, RFC 9309 compliance (500 KiB cap, 5xx fail-closed).
   - Unrestricted permissions for AI search indexers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`).
2. **Retrieval Readiness (Weight: 20%):**
   - Main content extractability, Signal-to-Noise Ratio (SNR >= 0.12).
   - Content Availability Gap (CAG < 0.15), server-side rendering completeness.
3. **Citation Readiness (Weight: 20%):**
   - Atomic Fact-to-Token Ratio (FTR >= 0.080).
   - Evidence genre density (code, stats, definitions, comparisons).
   - Low hedge density (<= 1.2%) and BLUF top-30% placement.
4. **Entity / Authority Score (Weight: 15%):**
   - Machine-explicit Schema.org `@graph` Organization and Product nodes.
   - Authoritative `sameAs` density (>= 2 external authority links).
   - Cross-page first-party fact ledger consistency.
5. **Cross-Engine Visibility Score (Weight: 15%):**
   - Cross-Engine Citation Coverage (CECO across the Big 5 engines).
   - Statistical uncertainty bound by **Wilson 95% Confidence Intervals** (z = 1.96, n >= 10).
6. **Agentic Commerce Score (Weight: 10%):**
   - Clean float pricing, ISO 4217 currency validation.
   - Zero contradictions between HTML text and JSON-LD (`ProductConsistency = 1.0`).
   - Universal Commerce Protocol (UCP), Agent Payments (AP2), and Agent2Agent (A2A) readiness.

---

## 4. The Canonical 16-Defect Taxonomy & 6-Layer Causal DAG

Findings are categorized and gated through the Monotonic 6-Layer Causal DAG in `causal_gate.py` to isolate root causes and suppress symptomatic downstream noise:

```text
Layer 0: Network & Crawler Access (RFC 9309, HTTP 4xx/5xx)
    │
    ▼ (Blocks Layer 1-5 evaluation if AI_RETRIEVAL_BLOCKED)
Layer 1: Content Rendering & Delivery (CSR shell, SNR < 0.12, CAG > 0.15)
    │
    ▼ (Blocks Layer 4-5 citability evaluation if RENDERED_CONTENT_GAP)
Layer 2: Machine Entity Identity & Structured Data (Organization, sameAs, Schema)
    │
    ▼
Layer 3: Cross-Page Factual & Commercial Consistency (Fact ledger, trial terms)
    │
    ▼
Layer 4: Generative Content Citability (Princeton KDD 2024, BLUF, E-E-A-T)
    │
    ▼
Layer 5: Intent Handoff & Visitor Continuity (Orientation, CTA reachability)
```

### Keystone Root-Cause Suppression Invariants
1. **Layer 0 Block (`AI_RETRIEVAL_BLOCKED`):** If search retrieval crawlers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) are disallowed or pages return HTTP 4xx/5xx, all downstream defects across structured data, citability, factual consistency, and engagement are suppressed into the causal diagnostic record.
2. **Layer 1 Gap (`RENDERED_CONTENT_GAP`):** If initial HTML lacks body content (unrendered single-page application shell), factual contradictions and citability scores are suppressed until server-side rendering is restored.

### Hard Failures (HF-01 to HF-08) — Deterministic Blocker Gate
- `HF-01`: Target page unreachable or non-200 HTTP status.
- `HF-02`: Contradictory, missing, or conflicting canonical declarations (HTML vs HTTP Link header).
- `HF-03`: AI search retrieval crawler disallowed in `robots.txt`.
- `HF-04`: `noindex` directive active on indexable content (meta tag or `X-Robots-Tag`).
- `HF-05`: `nosnippet` or restrictive `max-snippet` active on core text.
- `HF-06`: Product price contradiction between visible HTML and JSON-LD `Offer.price`.
- `HF-07`: Critical factual claims exist solely in images/PDF/JS without equivalent HTML.
- `HF-08`: Structured data directly contradicts visible page content.

### High-Value Warnings (W-01 to W-08) — Probabilistic Quality Risks
- `W-01`: Initial HTML extraction deficit (SSR content gap).
- `W-02`: High-value claims lack independent source attribution.
- `W-03`: Commercial pricing, trial duration, or stock drift across routes.
- `W-04`: Brand entity discordance across Organization schema and external nodes.
- `W-05`: Excessive discovery depth (authoritative evidence requires > 3 hops).
- `W-06`: `llms.txt` manifest contains broken or non-canonical links.
- `W-07`: Low atomic fact density (FTR < 0.040).
- `W-08`: Cross-engine citation divergence (CECO < 0.50).

---

## 5. Multi-Archetype Answerability Architecture

`entity_content_check.py` evaluates commercial answerability across four distinct business archetypes rather than forcing a monolithic e-commerce model:

1. **E-Commerce Archetype:**
   - Evaluates `Product` and `Offer` schema nodes.
   - Inspects numeric `price`, ISO 4217 `priceCurrency`, `availability` (`InStock`), `hasMerchantReturnPolicy`, and `shippingDetails`.
2. **SaaS & Subscription Archetype:**
   - Evaluates structured pricing tables, tier names, monthly/annual billing cadences, cancellation terms, and interactive trial CTAs.
   - Validates trial length and commercial refund term consistency across landing pages and pricing routes.
3. **Professional & B2B Services Archetype:**
   - Evaluates explicit service definitions, named deliverables, engagement models (fixed fee, retainer, hourly), and verified contact channels (phone, email).
4. **Content & Publisher Archetype:**
   - Evaluates credentialed author attribution (`Person` schema, professional degrees/titles), publication timestamps, and citation references.

---

## 6. Security & SSRF Protection Architecture

The audit suite adheres to a zero-trust model when fetching external domains:
- **RFC 1918 Private Address Blocking:** Blocks `10.0.0.0/8`, `172.16.0.0/12`, `169.254.0.0/16`, `192.168.0.0/16`.
- **Loopback & Link-Local Blocking:** Blocks `127.0.0.0/8`, `::1`, `fe80::/10`.
- **IPv4-Mapped IPv6 Protection:** Disallows `::ffff:127.0.0.1` and encoded hexadecimal loopbacks.
- **Payload Limits:** Maximum fetch size capped at 2 MiB to prevent memory exhaustion / decompression bombs.
- **Timeout Bounds:** Bounded socket timeouts (5–10s) prevent hang conditions.

---

## 7. Grounded Verification & Epistemic Boundaries

To prevent misleading claims and preserve scientific integrity, the audit implements strict boundaries between static heuristics, declared metadata, and empirical evidence:

### 7.1 Explicit Evidence Classes (Authority & Corroboration)
The audit segregates identity and backlink evidence into two non-overlapping classes:
1. `declared_identity_nodes`: Outbound identity assertions declared by the site itself via Schema.org `sameAs` (e.g., Wikidata, Wikipedia, LinkedIn, X, Crunchbase). Verifies that these identity endpoints are live (HTTP 200) and resolve to authoritative third-party knowledge graphs.
2. `verified_candidate_backlinks`: Inbound citations from external third-party referring pages to the audited domain, verified via bounded, SSRF-safe HTTP probing.

> **Common Crawl CDX Technical Reality**: The Common Crawl CDX API indexes *crawled URLs*, timestamps, byte offsets, and MIME types. It does **not** index an inverted link graph (which URL links to which target). Truthful backlink discovery from Common Crawl requires petabytes of WARC graph extraction. The audit enforces an honest **bounded candidate backlink verification contract** (`--candidate-backlinks`) rather than feigning instant web-wide discovery.

### 7.2 Bounded Candidate Backlink Verification Contract
- **Input Contract:** Takes candidate referring URLs via `--candidate-backlinks "url1,url2"` or newline-delimited file.
- **SSRF Safe:** Strict IP resolution check against RFC 1918, loopbacks, link-local metadata addresses (`169.254.169.254`), and IPv6 private blocks prior to socket connection.
- **Resource Bounds:** Capped at 10 candidate URLs per audit, 5.0-second socket timeout, and 512 KiB streaming limit per response body.
- **Classification:** Categorizes referring domains by type (`academic_edu`, `government_gov`, `industry_news`, `standard_web`).

### 7.3 Dual-Track Engagement Auditing (Analytics Ingestion)
The audit separates static UX proxies from observed engagement outcomes:
- **Static UX Proxies:** Heuristic signals evaluated from raw HTML (H1 alignment, word count, CTA reachability in first 3 interactive elements, internal navigation scent).
- **Observed Engagement Outcomes:** Optional empirical ingestion via `--analytics <file.csv|file.json|inline>` containing `{route, ai_referral_sessions, bounce_rate, avg_dwell_time_seconds, primary_referrer}`.
- **Empirical Corroboration:** When analytics show bounce rate >= 60% and dwell time < 30s, static warnings are corroborated and elevated to `AI_REFERRAL_DISCONTINUITY` defects.
- **Heuristic Mitigation:** When analytics confirm healthy visitor retention (bounce <= 35%, dwell >= 60s), static heuristic defects are downgraded or suppressed with notes that empirical performance is satisfactory.
- **Heuristic-Only Limitation:** In the absence of analytics, reports explicitly declare findings as *unverified static UX proxies* that have not been calibrated against real user telemetry.

### 7.4 Deterministic Page-Level GEO Content Improvement Plans
Derived algorithmically from the 9 Princeton KDD 2024 / AutoGEO citability dimensions in `geo_content_check.py`:
- **Gap Analysis:** Identifies specific deficits on each audited page across causal mechanisms, statistical evidence, passage chunking, semantic tables, BLUF placement, hedge density, and quotation authority.
- **Structural Actions:** Actionable blueprints for adding responsive comparison tables, step-by-step ordered lists, and Q&A blocks with FAQPage JSON-LD.
- **Textual Modifications:** Prescriptive guidance to inject causal conjunctions (`because`, `therefore`, `enables`) and convert vague assertions into quantified metrics.
- **120–180 Word Passage Chunking Plan:** Reorganizes body content into standalone, self-contained semantic passages optimized for RAG chunk extraction.
- **Epistemic Qualification:** Every plan explicitly states that recommendations are static heuristic optimizations grounded in empirical GEO research, **not** live citation log measurements or guarantees of search engine ranking.

### 7.5 Empirical Evidence Genres & Standalone FAQ Deficit (Zhang et al. 2026)
Research across 21,143 empirical citations demonstrates that citation absorption is non-uniform across presentation structures:
- **High-Influence Genres:** Code blocks (+76.9%), Statistics (+61.6%), Definition copulas (+57.3%), Comparison tables (+55.3%), and Procedural steps (+41.2%).
- **Standalone FAQ Penalty (-5.7%):** Using isolated question-and-answer formats without empirical data, code, or tables reduces citation probability. The sensor flags `STANDALONE_FAQ_DEFICIT` to mandate multi-genre reinforcement.

### 7.6 Attention Primacy & Token Distribution
- **BLUF Top-30% Attention Primacy:** Grounded in Stanford ("Lost in the Middle") and Zyppy 2026 findings proving that 44.2% of citations occur in the top 30% / first 250 words of a document. Answers delayed beyond this threshold suffer 30–40% retrieval degradation.
- **Neural Perplexity Penalty:** Non-stopword token density exceeding 4.5% triggers `EXCESSIVE_KEYWORD_DENSITY`, reflecting the empirical -8.3% to -10% citation degradation caused by neural embedding reranker penalties on unnatural token repetition.

### 7.7 Post-Citation Intent Handoff & CTA Reachability Index
Evaluates the arrival experience of high-intent citation traffic:
- **Viewport Answer Anchoring:** The cited proposition must be visible within the top 600px viewport (first 150 words / 2 paragraphs) to prevent orientation shock and immediate bounce (`VIEWPORT_ANSWER_ABSENCE`).
- **CTA Reachability Index:** Quantifies transactional continuation accessibility:
  ```text
  Reachability Index = 1 / (1 + Preceding Interactive Elements)
  ```
  If the primary commercial action is delayed behind > 3 auxiliary header/nav links, the sensor flags `CTA_REACHABILITY_FRICTION`.
