# Brand AI-Readiness & Search Visibility Suite

An `agentskills.io`-compliant multi-skill marketplace for auditing websites across AI search engines, generative retrieval assistants (ChatGPT Search, Claude Search, Perplexity, Google AI Overviews), and on-site post-citation engagement.

---

## 1. Multi-Skill Portfolio

The suite decomposes into one designated entrypoint skill and seven specialist modules (eight skills total):

| Skill | Role | Core Responsibility |
| :--- | :--- | :--- |
| **`audit-orchestrator`** | Master Entrypoint | Coordinates single-pass crawling, fans out offline sensor diagnostics, resolves causal dependencies via a 6-layer causal DAG, ranks findings by priority, and emits a Draft-07 schema-validated report. |
| **`web-scraper`** | Acquisition Engine | Crawls websites under zero-trust SSRF protection, audits RFC 9309 crawler permissions across 16 AI retrieval bots, extracts clean markdown with signal-to-noise ratio scoring, and saves canonical inventory (`inv.json`). |
| **`discoverability-audit`** | Indexation Sensor | Audits crawler access barriers, robots.txt directives, canonical tag consistency, sitemap coverage, machine-readable `/llms.txt` manifests, and client-side JavaScript rendering copy vacuums. |
| **`entity-content-audit`** | Structured Data Sensor | Extracts Schema.org JSON-LD graphs (Organization, Product, Offer, SoftwareApplication, LocalBusiness) and evaluates the 7-attribute commercial answerability index (pricing, availability, specifications, currency). |
| **`fact-consistency-audit`** | Fact Consensus Sensor | Constructs a cross-page first-party fact ledger (pricing, product specifications, contact details, dates) and detects internal contradictions that cause LLM hallucination and consensus penalties. |
| **`corroboration-authority-audit`** | Identity Anchor Sensor | Probes declared `sameAs` identity anchors (Wikidata, LinkedIn, Wikipedia, Crunchbase) under zero-trust SSRF sandboxing to verify external knowledge graph corroboration. |
| **`geo-content-audit`** | Citability Sensor | Evaluates content against generative citation criteria across nine vectors: bottom-line-up-front (BLUF) answer primacy, statistical evidence density, causal conjunction depth, and 134-167 word passage chunking. |
| **`engagement-context-audit`** | Post-Citation UX Sensor | Evaluates the 5-second orientation test, above-the-fold value proposition visibility, H1 conversational information scent, interactive CTA reachability, and authentication flow integrity for AI-referred traffic. |

---

## 2. How the Entrypoint Composes the Skills

The entrypoint (`audit-orchestrator`) coordinates the marketplace through a 4-stage pipeline that decouples deterministic empirical measurement from cognitive reasoning (Sensor-Brain Architecture):

```
Target Website URL
       |
       v
[ Stage 1: Single-Pass Acquisition (`web-scraper`) ]
       |  SSRF-safe crawl: fetches HTML, headers, markdown, metadata
       v
Canonical Inventory (`inv.json`)
       |
       +-----------------------+-----------------------+
       |                       |                       |
[ Stage 2: Offline Diagnostic Sensor Fan-Out (Parallel Execution) ]
  - `discoverability-audit`       - `entity-content-audit`
  - `fact-consistency-audit`     - `corroboration-authority-audit`
  - `geo-content-audit`           - `engagement-context-audit`
       |                       |                       |
       +-----------------------+-----------------------+
       |
       v
Empirical Telemetry Grid (`telemetry.json`)
       |
       v
[ Stage 3: Monotonic 6-Layer Causal DAG Synthesis ]
       |  Layer 0: Infrastructure & Network
       |  Layer 1: Crawl & Rendering (Robots, JS CSR Gaps)
       |  Layer 2: Entity & Structured Data (Schema.org JSON-LD)
       |  Layer 3: Content Structure & Citability (BLUF, Evidence)
       |  Layer 4: Factual Consistency & Knowledge Graph Anchors
       |  Layer 5: Post-Citation Engagement & Intent Handoff
       |  * Eliminates downstream symptom duplicates (e.g. CSR gap suppresses missing schema)
       v
[ Stage 4: Schema Validation & Report Emission ]
       |  Strict validation against Draft-07 JSON schema (`report-schema.json`)
       v
Final Audit Deliverable (`report.json`)
```

### Sensor-Brain Decoupling
- **Sensors (Deterministic Python Stdlib):** The 6 specialist diagnostic sensors and `web-scraper` run deterministically against `inv.json`. They produce raw, verifiable measurements without LLM hallucination or external network overhead.
- **Brain (AI Coding Agent):** When invoked in an agentic loop, the AI agent ingests `telemetry.json`, walks the 6-layer causal DAG, contextualizes findings to the specific business archetype (E-commerce, SaaS, Media, Local), and authors bespoke dual-track remediations (copy-pasteable technical code diffs and creative copy rewrites).
- **Headless Baseline:** For automated CI/CD pipelines, `orchestrator.py` can run in `--baseline-only` mode to assemble a fully valid, deterministic report without requiring an active agent.

---

## 3. Primary Use Cases

### Use Case 1: End-to-End Enterprise Brand AI-Readiness Audit
```text
Audit https://example.com for comprehensive Brand AI-Readiness, Generative Engine Optimization (GEO), and Cross-Engine Citability across ChatGPT Search, Claude Search, Perplexity, and Google AI Overviews. Inspect the single-pass inventory and empirical telemetry to determine why AI engines omit or misrepresent our brand. Evaluate robots.txt access across all 16 AI crawler user-agents, raw HTML extractability for client-side JavaScript rendering gaps, and Schema.org JSON-LD graph completeness. Apply causal root-cause analysis to author bespoke, priority-ranked findings with copy-pasteable technical code fixes and creative content remediations. Verify all findings against actual page evidence before outputting the final report as clean, schema-validated JSON.
```

### Use Case 2: Post-Citation Visitor Retention & Intent-Handoff Friction
```text
Audit https://example.com for brand AI-readiness, post-citation visitor retention, and intent-handoff continuity. Focus on why visitors referred from generative AI answers immediately bounce: evaluate the 5-second orientation test, above-the-fold value proposition clarity, H1 information scent alignment with conversational search queries, and CTA reachability friction. Cross-reference empirical telemetry with the raw page inventory to detect inert interactive elements (buttons or links pointing to '#'), gated location pathways, or displaced core propositions. Synthesize priority-ordered findings and dual-track remediations that eliminate bounce friction, and emit the verified report as schema-compliant JSON.
```

### Use Case 3: Generative Citability & Factual Consensus Audit
```text
Conduct an in-depth Generative Engine Optimization (GEO) and commercial answerability audit for https://example.com. Evaluate content against generative citation criteria: measure statistical evidence density, BLUF (Bottom Line Up Front) answer structuring, causal conjunction depth, and 134-167 word passage chunking for LLM RAG absorption. Construct a first-party cross-page fact ledger to isolate contradictory pricing, availability, or legacy claims that trigger LLM hallucinations or citation suppression. Propose forward-looking proactive improvements tailored specifically to the site's business archetype, such as authoritative /llms.txt manifests and machine-readable pricing schemas. Deliver fully verified, priority-ordered findings in clean JSON.
```

---

## 4. Scope & Guardrails

- **Recommend-Only & Non-Destructive:** The suite audits and reports. No skill modifies a live website, accesses authenticated areas, or executes destructive actions.
- **Zero Third-Party Runtime Dependencies:** All runtime logic across all 8 skills relies exclusively on the Python 3.9+ standard library (`urllib`, `socket`, `html.parser`, `xml.etree.ElementTree`, `json`, `re`, `argparse`, `math`).
- **Zero-Trust SSRF Protection:** Outbound network requests pass through `safe_fetch.py` with pre-socket DNS resolution, rejecting private (RFC 1918), loopback, link-local (`169.254.0.0/16`), cloud metadata (`169.254.169.254`), and carrier-grade NAT IPs.
- **Single-Pass Acquisition:** Target sites are crawled once. Sensors execute offline against `inv.json` with zero redundant network overhead.
- **Zero Headless Browsers:** No Playwright, Puppeteer, Selenium, or Chromium dependencies.
