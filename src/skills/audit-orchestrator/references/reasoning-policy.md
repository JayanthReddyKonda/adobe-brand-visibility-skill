# Epistemic Reasoning & Evidence Policy
## Brand AI-Readiness & Visibility Audit Engine

This policy defines the epistemic standards, evidence rules, and boundaries governing the AI Agent when interpreting telemetry and formulating findings for the final Draft-07 audit report.

---

## 1. Evidence Plane vs. Cognitive Brain Protocol

### 1.1 Fundamental Epistemic Posture: "Evidence, Not Truth"
- HTTP responses, DNS records, raw HTML, robots.txt directives, and external corroboration links are **observable evidence**, not absolute or un-spoofable truth.
- The engine enforces **Pre-Connect SSRF Security** (resolving DNS and rejecting private RFC 1918, loopback, link-local, and cloud metadata IPs *before socket creation*).
- An absence of evidence in a sampled crawl is never conflated with definitive non-existence on the broader web.

### 1.2 Separation of Responsibilities

| Component | Allowed Responsibilities | Strictly Prohibited Actions |
| :--- | :--- | :--- |
| **`web-scraper`** | Pre-connect DNS verification, fetch raw bytes, parse RFC 9309 rules, extract JSON-LD, extract text, emit `inv.json`. | Write recommendation text, evaluate business impact. |
| **`discoverability-audit`** | Derive crawler access matrix, noindex directives, raw HTML rendering completeness. | Invent explanations or speculate on crawler intent. |
| **`entity-content-audit`** | Measure Schema.org completeness (`Organization`, `Product`, `@graph`), detect attribute gaps. | Decide business priority or write marketing copy. |
| **`fact-consistency-audit`** | Diff observed first-party facts across pages (prices, dates, contacts) to detect contradictions. | Guess which contradictory fact is "correct." |
| **`corroboration-authority-audit`** | Probe declared `sameAs` external URLs under zero-trust SSRF sandboxing. | Declare a site "authoritative" without verifiable third-party knowledge graph links. |
| **`geo-content-audit`** | Compute empirical text heuristics (quotability, statistic density, causal conjunctions, chunk length). | Claim guaranteed search engine rankings. |
| **`engagement-context-audit`** | Measure visible orientation signals (CTA DOM depth, H1 alignment, above-fold word density). | Claim to have measured actual user bounce rate or dwell time without first-party analytics. |
| **Deterministic Causal Gate (`causal_gate.py`)** | Deterministically suppress invalid downstream categories when upstream preconditions fail. | Write natural-language explanations. |
| **Frontier AI Model** | Interpret telemetry evidence, formulate hypotheses, contextualize archetype, simulate queries, write dual-track fixes. | Override deterministic suppression or invent claims absent from telemetry. |
| **Schema Gate (`validate_report.py`)** | Mechanically validate JSON types, required fields, summary arithmetic, and enum values against Draft-07 schema. | Add new substantive findings. |

---

## 2. The Three-State Epistemic Model

Do not treat findings as a simplistic binary pass/fail. The engine employs a four-value epistemic state:

```json
{
  "state": "observed | inferred | unknown | suppressed",
  "confidence": 0.0 to 1.0
}
```

- **`observed`**: Direct empirical measurement in the crawled inventory (e.g. `Disallow: /` in `robots.txt`, visible text word count = 21).
- **`inferred`**: Reasoned deduction from multiple observed signals (e.g. business archetype classified as SaaS from route and schema patterns).
- **`unknown`**: Signal could not be evaluated due to scope boundaries or unreachable targets (e.g. no analytics file supplied).
- **`suppressed`**: Signal was intentionally gated because an upstream precondition failed (e.g. citability checks suppressed on an unhydrated SPA shell).

> **The Cardinal Sin of Auditing:** Never treat *"we couldn't observe it"* as *"it does not exist."* If a route returns 403 or blocks retrieval, report the access block as the root cause; do NOT assert that the blocked page "lacks schema."

---

## 3. Epistemic Falsification Protocol

```text
Claim -> Observed Evidence -> Inference Rule -> Confidence -> Possible Falsifier
```

### Example:
- **Claim:** `"Pricing information is contradictory across commercial routes."`
- **Observed Evidence:** `"Route /pricing reports $49/mo while route /checkout reports $59/mo for the Pro tier."`
- **Inference Rule:** `"Identical tier scope with different currency values indicates an un-synchronized pricing ledger."`
- **Confidence:** `0.95`
- **Possible Falsifier:** `"The $49/mo rate represents an annual billing discount that was not declared in the visible tier title."`

If a plausible falsifier explains the observation without defect, the defect MUST be downgraded or rejected.

---

## 4. Query-Strategy Simulation vs. Platform Telemetry

- **No False Platform Claims:** The audit must never state: *"ChatGPT ranked this site #5"* or *"Perplexity excluded this domain."*
- **Accurate Framing:** Always frame assistant retrieval as **Simulated Query-Strategy Scenarios**:
  - *"Given that OAI-SearchBot is permitted and the page exposes 45-word standalone BLUF answers under question headers, this passage has high absorption potential for conversational discovery queries."*
  - *"Because the page relies entirely on client-side JS rendering without server-rendered text, fetchers that do not execute a headless browser cannot extract facts to answer user queries."*

---

## 5. Engagement Friction Proxies vs. Bounce Rate

Without access to first-party web analytics (Google Analytics, Adobe Analytics), the audit **cannot observe actual bounce rates, dwell times, or abandonment rates**.

Instead, the sensor evaluates **Observable Friction Proxies**:
- CTA proximity to primary value proposition (DOM depth and word count).
- Semantic alignment between page title, H1, and lead paragraph (information scent).
- Availability of clear next-step actions above the fold.
- Context retention across linked user journeys.

Findings in this domain must be described as **`engagement_friction_signal`**, never as *"measured bounce rate"*.

---

## 6. Technical SEO & AI Search Priority Foundations

### 6.1 Schema Markup Detection Limitations
- Basic non-rendering HTTP fetchers cannot detect client-side JavaScript-injected Schema.org markup (e.g., plugins that mount JSON-LD dynamically).
- To accurately evaluate what AI retrieval crawlers actually ingest, the audit measures initial raw HTML extractability directly.

### 6.2 Priority Hierarchy of AI Search Readiness
1. **Crawlability & Indexation:** Can AI retrieval bots (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) reach and fetch the page without HTTP 4xx/5xx or `noindex` blocks?
2. **Entity Understanding:** Can machines resolve *Who* the brand is via Schema.org `Organization` and `sameAs` links?
3. **Factual Consistency:** Are prices, contacts, and availability consistent across all first-party pages?
4. **Answerability & GEO:** Does the content provide quantifiable numbers and mechanistic explanations (`how` / `why`)?
5. **Visitor Continuity:** Does the landing page provide immediate information scent and commercial CTAs to prevent referral bounce?

