# Brand AI-Readiness Audit — System Architecture

**Author:** Jayanth Reddy Konda  
**Version:** 3.0.0  
**Specification Compliance:** `agentskills.io` Standard & JSON Schema Draft-07  

---

## 1. The Core Architectural Philosophy: The AI Agent IS the Orchestrator

This system implements a **True Agentic Marketplace**. There is no monolithic master Python runner in `src/` that conceals decision logic in procedural code. 

The AI Agent acts as the cognitive engine:
1. The AI reads each skill's `SKILL.md` and domain knowledge bases to understand decision boundaries.
2. The AI invokes pure-Python deterministic sensor scripts via CLI to gather telemetry.
3. The AI applies multi-signal cognitive reasoning to diagnose root causes, deduplicate findings, and map evidence.
4. The AI synthesizes the final report and validates it against the Draft-07 schema gate.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI AGENT (Reasoner)                           │
│                                                                         │
│  1. Reads SKILL.md files & Knowledge Bases                             │
│  2. Executes web-scraper (run_scraper.py) → Canonical inv.json snapshot │
│  3. Executes Specialist Diagnostic Scripts → Collects pure telemetry   │
│  4. Applies Multi-Signal Reasoning → Root-causes defects (HF-01 to W-08)│
│  5. Computes 6 Orthogonal Scores & Wilson 95% Confidence Intervals      │
│  6. Generates Final JSON Report → Validates with validate_report.py     │
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

### Two-Layer Separation of Concerns
- **AI Cognitive Layer (`SKILL.md`, Knowledge Bases):** Responsible for judgment, causal inference, dual-track remediation, and qualitative synthesis. Never executes unvalidated HTTP requests directly.
- **Deterministic Sensor Layer (`_check.py`, `safe_fetch.py`):** Responsible for raw data extraction, RFC parsing, DOM evaluation, and mathematical calculations. Completely isolated, testable with unit tests, and 100% pure Python standard library.

---

## 2. The Layered Probability Model (The Master Formula)

Modern generative engines operate as multi-stage, partially observable probabilistic retrieval pipelines. The audit models generative visibility as a multiplicative chain:

$$\boxed{ \text{AI Visibility} \approx \text{Crawl Eligibility} \times \text{Retrieval Eligibility} \times \text{Content Citability} \times \text{Entity/Source Authority} \times \text{Citation Fidelity} }$$

with an adjacent **Agentic Commerce Readiness** layer for transactional products and services.

### Methodological Rule: Prominence vs. Presence
In the canonical GEO paper (Aggarwal et al., KDD 2024), the documented "+40% visibility improvement" refers to a change in **Position-Adjusted Word Count (PAWC)** *among an already retrieved set of sources*. It is NOT a flat 40% increase in retrieval probability.

$$\text{PAWC}(r) = \frac{\sum_{s_i \in S_c} wc(s_i) e^{-pos(s_i)}}{\sum_j wc(s_j)}$$

The audit measures citation prominence, citation position, and answer share rather than binary citation presence.

---

## 3. The 6 Orthogonal Scoring Dimensions

To avoid collapsing distinct technical vectors into a single misleading score, the audit evaluates six orthogonal dimensions:

1. **Crawlability Score (Weight: 20%):**
   - Deterministic HTTP 200 responses, RFC 9309 compliance (500 KiB cap, 5xx fail-closed).
   - Unrestricted permissions for AI search indexers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`).
2. **Retrieval Readiness (Weight: 20%):**
   - Main content extractability, Signal-to-Noise Ratio ($\text{SNR} \ge 0.12$).
   - Content Availability Gap ($\text{CAG} < 0.15$), server-side rendering completeness.
3. **Citation Readiness (Weight: 20%):**
   - Atomic Fact-to-Token Ratio ($\text{FTR} \ge 0.080$).
   - Evidence genre density (code, stats, definitions, comparisons).
   - Low hedge density ($\le 1.2\%$) and BLUF top-30% placement.
4. **Entity / Authority Score (Weight: 15%):**
   - Machine-explicit Schema.org `@graph` Organization and Product nodes.
   - Authoritative `sameAs` density ($\ge 2$ external authority links).
   - Cross-page first-party fact ledger consistency.
5. **Cross-Engine Visibility Score (Weight: 15%):**
   - Cross-Engine Citation Coverage ($\text{CECO}$ across the Big 5 engines).
   - Statistical uncertainty bound by **Wilson 95% Confidence Intervals** ($z=1.96, n \ge 10$).
6. **Agentic Commerce Score (Weight: 10%):**
   - Clean float pricing, ISO 4217 currency validation.
   - Zero contradictions between HTML text and JSON-LD (`ProductConsistency = 1.0`).
   - Universal Commerce Protocol (UCP), Agent Payments (AP2), and Agent2Agent (A2A) readiness.

---

## 4. The Canonical 16-Defect Taxonomy

Findings must be classified into the canonical defect taxonomy:

### Hard Failures (HF-01 to HF-08) — Deterministic Blocker Gate
- `HF-01`: Target page unreachable or non-200 HTTP status.
- `HF-02`: Contradictory, missing, or conflicting canonical declarations.
- `HF-03`: AI search retrieval crawler disallowed in `robots.txt`.
- `HF-04`: `noindex` directive active on indexable content.
- `HF-05`: `nosnippet` or restrictive `max-snippet` active on core text.
- `HF-06`: Product price contradiction between visible HTML and JSON-LD `Offer.price`.
- `HF-07`: Critical factual claims exist solely in images/PDF/JS without equivalent HTML.
- `HF-08`: Structured data directly contradicts visible page content.

### High-Value Warnings (W-01 to W-08) — Probabilistic Quality Risks
- `W-01`: Initial HTML extraction deficit (SSR content gap).
- `W-02`: High-value claims lack independent source attribution.
- `W-03`: Commercial pricing or stock drift across routes.
- `W-04`: Brand entity discordance across Organization schema and external nodes.
- `W-05`: Excessive discovery depth (authoritative evidence requires > 3 hops).
- `W-06`: `llms.txt` manifest contains broken or non-canonical links.
- `W-07`: Low atomic fact density ($\text{FTR} < 0.040$).
- `W-08`: Cross-engine citation divergence ($\text{CECO} < 0.50$).

---

## 5. Security & SSRF Protection Architecture

The audit suite adheres to a zero-trust model when fetching external domains:
- **RFC 1918 Private Address Blocking:** Blocks `10.0.0.0/8`, `172.16.0.0/12`, `169.254.0.0/16`, `192.168.0.0/16`.
- **Loopback & Link-Local Blocking:** Blocks `127.0.0.0/8`, `::1`, `fe80::/10`.
- **IPv4-Mapped IPv6 Protection:** Disallows `::ffff:127.0.0.1` and encoded hexadecimal loopbacks.
- **Payload Limits:** Maximum fetch size capped at 2 MiB to prevent memory exhaustion / decompression bombs.
- **Timeout Bounds:** Bounded socket timeouts (5–10s) prevent hang conditions.

---

## 6. Grounded Verification & Epistemic Boundaries

To prevent misleading claims and preserve scientific integrity, the audit implements strict boundaries between static heuristics, declared metadata, and empirical evidence:

### 6.1 Explicit Evidence Classes (Authority & Corroboration)
The audit segregates identity and backlink evidence into two non-overlapping classes:
1. `declared_identity_nodes`: Outbound identity assertions declared by the site itself via Schema.org `sameAs` (e.g., Wikidata, Wikipedia, LinkedIn, X, Crunchbase). Verifies that these identity endpoints are live (HTTP 200) and resolve to authoritative third-party knowledge graphs.
2. `verified_candidate_backlinks`: Inbound citations from external third-party referring pages to the audited domain, verified via bounded, SSRF-safe HTTP probing.

> **Common Crawl CDX Technical Reality**: The Common Crawl CDX API indexes *crawled URLs*, timestamps, byte offsets, and MIME types. It does **not** index an inverted link graph (which URL links to which target). Truthful backlink discovery from Common Crawl requires petabytes of WARC graph extraction. The audit enforces an honest **bounded candidate backlink verification contract** (`--candidate-backlinks`) rather than feigning instant web-wide discovery.

### 6.2 Bounded Candidate Backlink Verification Contract
- **Input Contract:** Takes candidate referring URLs via `--candidate-backlinks "url1,url2"` or newline-delimited file.
- **SSRF Safe:** Strict IP resolution check against RFC 1918, loopbacks, link-local metadata addresses (`169.254.169.254`), and IPv6 private blocks prior to socket connection.
- **Resource Bounds:** Capped at 10 candidate URLs per audit, 5.0-second socket timeout, and 512 KiB streaming limit per response body.
- **Classification:** Categorizes referring domains by type (`academic_edu`, `government_gov`, `industry_news`, `standard_web`).

### 6.3 Dual-Track Engagement Auditing (Analytics Ingestion)
The audit separates static UX proxies from observed engagement outcomes:
- **Static UX Proxies:** Heuristic signals evaluated from raw HTML (H1 alignment, word count, CTA reachability in first 3 interactive elements, internal navigation scent).
- **Observed Engagement Outcomes:** Optional empirical ingestion via `--analytics <file.csv|file.json|inline>` containing `{route, ai_referral_sessions, bounce_rate, avg_dwell_time_seconds, primary_referrer}`.
- **Empirical Corroboration:** When analytics show bounce rate $\ge 60\%$ and dwell time $< 30$s, static warnings are corroborated and elevated to `AI_REFERRAL_DISCONTINUITY` defects.
- **Heuristic Mitigation:** When analytics confirm healthy visitor retention (bounce $\le 35\%$, dwell $\ge 60$s), static heuristic defects are downgraded or suppressed with notes that empirical performance is satisfactory.
- **Heuristic-Only Limitation:** In the absence of analytics, reports explicitly declare findings as *unverified static UX proxies* that have not been calibrated against real user telemetry.

### 6.4 Deterministic Page-Level GEO Content Improvement Plans
Derived algorithmically from the 9 Princeton KDD 2024 / AutoGEO citability dimensions in `geo_content_check.py`:
- **Gap Analysis:** Identifies specific deficits on each audited page across causal mechanisms, statistical evidence, passage chunking, semantic tables, BLUF placement, hedge density, and quotation authority.
- **Structural Actions:** Actionable blueprints for adding responsive comparison tables, step-by-step ordered lists, and Q&A blocks with FAQPage JSON-LD.
- **Textual Modifications:** Prescriptive guidance to inject causal conjunctions (`because`, `therefore`, `enables`) and convert vague assertions into quantified metrics.
- **120–180 Word Passage Chunking Plan:** Reorganizes body content into standalone, self-contained semantic passages optimized for RAG chunk extraction.
- **Epistemic Qualification:** Every plan explicitly states that recommendations are static heuristic optimizations grounded in empirical GEO research, **not** live citation log measurements or guarantees of search engine ranking.

### 6.5 Empirical Evidence Genres & Standalone FAQ Deficit (Zhang et al. 2026)
Research across 21,143 empirical citations demonstrates that citation absorption is non-uniform across presentation structures:
- **High-Influence Genres:** Code blocks (+76.9%), Statistics (+61.6%), Definition copulas (+57.3%), Comparison tables (+55.3%), and Procedural steps (+41.2%).
- **Standalone FAQ Penalty (-5.7%):** Using isolated question-and-answer formats without empirical data, code, or tables reduces citation probability. The sensor flags `STANDALONE_FAQ_DEFICIT` to mandate multi-genre reinforcement.

### 6.6 Attention Primacy & Token Distribution
- **BLUF Top-30% Attention Primacy:** Grounded in Stanford ("Lost in the Middle") and Zyppy 2026 findings proving that 44.2% of citations occur in the top 30% / first 250 words of a document. Answers delayed beyond this threshold suffer 30–40% retrieval degradation.
- **Neural Perplexity Penalty:** Non-stopword token density exceeding 4.5% triggers `EXCESSIVE_KEYWORD_DENSITY`, reflecting the empirical -8.3% to -10% citation degradation caused by neural embedding reranker penalties on unnatural token repetition.

### 6.7 Post-Citation Intent Handoff & CTA Reachability Index
Evaluates the arrival experience of high-intent citation traffic:
- **Viewport Answer Anchoring:** The cited proposition must be visible within the top 600px viewport (first 150 words / 2 paragraphs) to prevent orientation shock and immediate bounce (`VIEWPORT_ANSWER_ABSENCE`).
- **CTA Reachability Index:** Quantifies transactional continuation accessibility:
  $$\text{Reachability Index} = \frac{1}{1 + \text{Preceding Interactive Elements}}$$
  If the primary commercial action is delayed behind $>3$ auxiliary header/nav links, the sensor flags `CTA_REACHABILITY_FRICTION`.


