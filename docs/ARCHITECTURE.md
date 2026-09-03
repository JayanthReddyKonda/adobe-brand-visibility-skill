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
│  2. Executes acquire_inventory.py → Builds typed page inventory         │
│  3. Executes 6 Specialist Diagnostic Scripts → Collects pure telemetry   │
│  4. Applies Multi-Signal Reasoning → Root-causes defects (HF-01 to W-08)│
│  5. Computes 6 Orthogonal Scores & Wilson 95% Confidence Intervals      │
│  6. Generates Final JSON Report → Validates with validate_report.py     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼────────────────────────┐
           ▼                         ▼                        ▼
     Orchestration Tools      6 Specialist Skills       Validation Gate
     acquire_inventory.py     discoverability-audit     validate_report.py
     safe_fetch.py            entity-content-audit      report-schema.json
                              fact-consistency-audit
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
