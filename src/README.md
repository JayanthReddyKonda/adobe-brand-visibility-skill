# Brand AI-Readiness, Generative Engine Optimization (GEO) & Visibility Suite

**Author:** Jayanth Reddy Konda
**Version:** 2.1.0
**Standard Compliance:** `agentskills.io` Standard & JSON Schema Draft-07

---

## 1. Executive Overview: The Generative Search Transition

Traditional search engine optimization (SEO) focuses on keyword rankings across ten organic blue links. Generative AI search engines—including ChatGPT Search, Claude Search, Perplexity Pro, and Google AI Overviews—have fundamentally shifted discovery: they synthesize direct answers from distributed web sources, selectively citing content based on structural answerability, causal depth, factual consensus, and machine-explicit entity clarity rather than traditional domain authority alone.

This creates the **AI Visibility Gap**: brands ranking #1 on traditional search engines frequently suffer from complete omission, brand hallucination, or inaccurate pricing citations in generative answer engines. Conversely, high-density informational content with precise Schema.org JSON-LD structured data and strong factual grounding frequently captures top AI citations.

The **Brand AI-Readiness Suite** is a production multi-skill diagnostic system. It empowers AI coding agents and engineering teams to audit any website, isolate why it is invisible or misrepresented across generative search engines, diagnose post-citation visitor drop-off, and deliver schema-validated reports with dual-track remediation (patch-applicable technical code diffs and research-backed creative copy rewrites).

---

## 2. Sensor-Brain Cognitive Orchestration Architecture

The suite operates on a **Sensor-Brain Cognitive Architecture** that decouples empirical measurement from contextual reasoning:

```
+-------------------------------------------------------------------------+
|                    BRAIN: AI AGENT (Cognitive Reasoning)                 |
|                                                                         |
|  - Deeply inspects site inventory (inv.json) and telemetry grid        |
|  - Enforces 6-Layer Causal DAG to suppress downstream symptoms          |
|  - Grounds findings in target business archetype (E-Comm, SaaS, etc.)  |
|  - Authors bespoke dual-track remediations (technical patch + copy)     |
|  - Ranks findings by needle-moving impact with explicit justification   |
|  - Validates and emits Draft-07 schema-compliant report JSON            |
+-------------------------------------------------------------------------+
                                    |
                    Empirical Telemetry (Structured JSON)
                                    |
+-------------------------------------------------------------------------+
|                 SENSORS: Deterministic Python Core                       |
|                                                                         |
|  - Single-pass zero-trust SSRF crawl & content acquisition (safe_fetch) |
|  - RFC 9309 crawler permission matrix across 16 AI retrieval bots       |
|  - Schema.org JSON-LD entity graph & answerability attribute scoring    |
|  - Multi-attribute first-party fact ledger & contradiction detection   |
|  - External identity link corroboration (Wikidata, LinkedIn, Wikipedia) |
|  - Princeton KDD 2024 citability heuristics & statistical density      |
|  - Post-citation visitor orientation & interactive CTA reachability     |
+-------------------------------------------------------------------------+
```

### The Diagnostic Advantage
Deterministic scripts provide rapid, reproducible, and verifiable telemetry without hallucination. However, script heuristics cannot understand nuanced brand voice, complex commercial journeys, or architectural subtleties. The AI Agent acts as the cognitive diagnostic brain: it inspects the raw inventory and telemetry grid, applies causal reasoning, contextualizes findings to the specific business model, and authors customized remediations that resolve root causes rather than surface symptoms.

---

## 3. The Multi-Skill Portfolio

The suite decomposes into one master coordinator and seven specialist diagnostic modules (eight skills total):

| Skill | Role | Primary Telemetry & Diagnostic Capabilities |
| :--- | :--- | :--- |
| **`audit-orchestrator`** | Master Coordinator | Orchestrates single-pass inventory acquisition, fans out offline sensor diagnostics, resolves causal dependencies via the 6-Layer Causal DAG, prioritizes findings, and validates output against Draft-07 JSON Schema. |
| **`web-scraper`** | Acquisition Engine | Crawls websites under zero-trust SSRF protection, audits RFC 9309 robots.txt permissions across 16 AI retrieval bots, extracts clean markdown with Signal-to-Noise Ratio (SNR) scoring, and emits the canonical inventory (`inv.json`). |
| **`discoverability-audit`** | Indexation Sensor | Audits crawler access barriers, meta robots directives, canonical tag consistency, hreflang validity, machine-readable `/llms.txt` manifests, and client-side JavaScript rendering copy vacuums. |
| **`entity-content-audit`** | Structured Data Sensor | Extracts Schema.org JSON-LD graphs (Organization, Product, Offer, SoftwareApplication, LocalBusiness) and evaluates the 7-attribute commercial answerability index (pricing, availability, specifications, currency). |
| **`fact-consistency-audit`** | Fact Consensus Sensor | Constructs a cross-page first-party fact ledger (pricing, product specifications, contact details, dates) and detects internal contradictions that trigger generative hallucination or model consensus penalties. |
| **`corroboration-authority-audit`** | Identity Anchor Sensor | Probes declared `sameAs` identity anchors (Wikidata, LinkedIn, Wikipedia, Crunchbase) under zero-trust SSRF sandboxing to verify external knowledge graph corroboration. |
| **`geo-content-audit`** | Citability Sensor | Evaluates content against Princeton KDD 2024 and AutoGEO benchmarks across nine vectors: BLUF answer primacy, statistical evidence density, causal conjunction depth, and 134-167 word passage chunking. |
| **`engagement-context-audit`** | Post-Citation UX Sensor | Evaluates the 5-second orientation test, above-the-fold value proposition visibility, H1 conversational information scent, interactive CTA reachability, and authentication flow integrity for AI-referred traffic. |

---

## 4. End-to-End Operational Workflow

1. **Single-Pass Acquisition:** `web-scraper` fetches target routes under strict SSRF protection, caching raw HTML, headers, markdown, and structured data into a canonical site inventory (`inv.json`). Target servers are crawled exactly once.
2. **Offline Sensor Fan-Out:** Specialist sensors execute offline against `inv.json`, generating structured empirical telemetry with zero redundant network latency.
3. **Cognitive AI Synthesis:** The AI Agent ingests sensor telemetry via `orchestrator.py --telemetry`, applies the 6-Layer Causal DAG to eliminate downstream symptom duplicates, contextualizes findings to the target website's business archetype, and authors bespoke dual-track remediations.
4. **Draft-07 Schema Validation Gate:** Output reports are strictly validated against `report-schema.json`, ensuring every finding provides verifiable evidence, mechanism-sound root-cause explanation, and copy-pasteable technical and creative fixes.

---

## 5. Primary Use Cases

### Use Case 1: End-to-End Enterprise Brand AI-Readiness & Retrieval Architecture Audit
**Objective:** Complete diagnostic evaluation of enterprise digital presence across generative engines (ChatGPT Search, Claude Search, Perplexity, and Google AI Overviews), resolving indexation barriers and entity ambiguity.

**Auditor Prompt:**
```text
Audit https://example.com for comprehensive Brand AI-Readiness, Generative Engine Optimization (GEO), and Cross-Engine Citability across ChatGPT Search, Claude Search, Perplexity, and Google AI Overviews. Inspect the single-pass inventory and empirical telemetry to determine why AI engines omit or misrepresent our brand. Evaluate robots.txt access across all 16 AI crawler user-agents, raw HTML extractability for client-side JavaScript rendering gaps, and Schema.org JSON-LD graph completeness (Organization, Product, Offer, and PriceSpecification). Apply causal root-cause analysis to author bespoke, priority-ranked findings with copy-pasteable technical code fixes and creative content remediations. Verify all findings against actual page evidence before outputting the final report as clean, schema-validated JSON.
```

**Diagnostic Coverage:**
- **Retrieval & Rendering (Layers 0 & 1):** Uncovers edge WAF blocks, restrictive robots.txt user-agent policies, and single-page application (SPA) client-side rendering gaps that leave AI crawlers with empty DOM shells.
- **Entity Identity & Knowledge Graph (Layers 2 & 4):** Evaluates whether Schema.org graphs declare complete organizational stewardship and external authority anchors (Wikidata, LinkedIn).
- **Deliverables:** A Draft-07 schema-compliant report featuring prioritized findings (`F-001`, `F-002`...), copy-pasteable JSON-LD patches, and forward-looking proactive improvements (e.g. authoritative `/llms.txt` manifests).

---

### Use Case 2: Post-Citation Visitor Orientation & Intent-Handoff Friction Diagnosis
**Objective:** Diagnose and eliminate immediate visitor drop-off for referral traffic arriving from generative AI answer citations.

**Auditor Prompt:**
```text
Audit https://example.com for brand AI-readiness, post-citation visitor retention, and intent-handoff continuity. Focus on why visitors referred from generative AI answers immediately bounce: evaluate the 5-second orientation test, above-the-fold value proposition clarity, H1 information scent alignment with conversational search queries, and CTA reachability friction. Cross-reference empirical telemetry with the raw page inventory to detect inert interactive elements (buttons or links pointing to '#'), gated location pathways, or displaced core propositions. Synthesize priority-ordered findings and dual-track remediations that eliminate bounce friction, and emit the verified report as schema-compliant JSON.
```

**Diagnostic Coverage:**
- **Information Scent Alignment:** Tests whether landing page H1 headings and opening propositions preserve contextual continuity from the AI assistant's cited answer.
- **The 5-Second Orientation Test:** Inspects above-the-fold viewport content to confirm the primary answer proposition appears within the first 250 visible words without requiring scroll or interaction.
- **Conversion Journey Continuity:** Evaluates primary calls to action, account registration pathways, and shopping cart triggers to isolate inert anchor links (`href='#'`), inaccessible dialogs, or form-gated discovery friction that trap both human visitors and autonomous purchasing agents (OpenAI Operator, Google Jarvis).
- **Deliverables:** Precise H1 headline revisions, semantic viewport restructuring guidelines, and actionable CTA destination fixes.

---

### Use Case 3: Generative Engine Optimization (GEO) & Factual Consensus Audit
**Objective:** Maximize AI citation frequency and eliminate hallucination risks by aligning content with empirical GEO research and auditing first-party factual consistency.

**Auditor Prompt:**
```text
Conduct an in-depth Generative Engine Optimization (GEO) and commercial answerability audit for https://example.com. Evaluate content against generative citation criteria: measure statistical evidence density, BLUF (Bottom Line Up Front) answer structuring, causal conjunction depth, and 134-167 word passage chunking for LLM RAG absorption. Construct a first-party cross-page fact ledger to isolate contradictory pricing, availability, or legacy claims that trigger LLM hallucinations or citation suppression. Propose forward-looking proactive improvements tailored specifically to the site's business archetype, such as authoritative /llms.txt manifests and machine-readable pricing schemas. Deliver fully verified, priority-ordered findings in clean JSON.
```

**Diagnostic Coverage:**
- **Princeton KDD 2024 Citability Heuristics:** Audits content for empirical citation drivers: quotation addition (+40.9% lift), statistical evidence density (+40.0% lift), causal conjunction depth (+28.2% lift), and elimination of unsupported promotional fluff.
- **First-Party Fact Consensus Ledger:** Cross-references pricing tiers, cancellation policies, product specifications, and legal entity names across all crawled routes to detect internal discrepancies that cause AI models to lose consensus confidence.
- **Archetype-Tailored Architecture:** Synthesizes proactive recommendations matching the organization's business model (e.g. un-gated `/pricing.md` manifests for SaaS, Universal Commerce Protocol readiness for E-Commerce).
- **Deliverables:** Concrete copywriting diffs replacing vague claims with attributed data, modular passage restructuring plans, and first-party fact reconciliations.

---

## 6. Execution Interfaces

### AI Agent Cognitive Workflow (Standard)
```bash
# 1. Single-pass inventory acquisition (SSRF-safe crawl)
python3 skills/web-scraper/scripts/acquire_inventory.py --site https://example.com --output inv.json --format json

# 2. Extract empirical telemetry across all diagnostic sensors
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --telemetry > telemetry.json

# 3. Ingest agent review findings and emit schema-validated deliverable report
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --review review.json --clean --include-scores --output report.json
```

### Automated CI/CD Headless Verification
```bash
# Deterministic baseline execution for automated test pipelines
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --format json --baseline-only
```

### Modular Sensor Probing
```bash
# Targeted sensor execution against pre-crawled inventory
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --format json
python3 skills/entity-content-audit/scripts/entity_content_check.py --site https://example.com --inventory inv.json --format json
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --format json
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --format json
python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --format json
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format json

# Validate any report against Draft-07 schema
python3 skills/audit-orchestrator/scripts/validate_report.py report.json
```

---

## 7. Output Report Structure

Every final report conforms to Draft-07 JSON Schema with priority-ranked findings and clear epistemic scoring:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "schema_version": "1.0.0",
  "site": "https://example.com",
  "audited_at": "2026-09-13T12:00:00Z",
  "audit_status": "complete",
  "summary": {
    "total_findings": 2,
    "critical": 1,
    "high": 1,
    "medium": 0,
    "low": 0,
    "detected_archetype": "ecommerce"
  },
  "findings": [
    {
      "id": "F-001",
      "cause_id": "INCOMPLETE_OFFER_ATTRIBUTES",
      "title": "Incomplete commercial subscription terms across affected routes",
      "severity": "critical",
      "category": "entity_content",
      "root_cause": "The subscription offering advertises promotional discounts without disclosing standard recurring monthly rates or cancellation terms in machine-readable markup.",
      "confidence": "high",
      "scope": "https://example.com",
      "evidence": {
        "summary": "Subscription page lacks standard recurring price and cancellation policy terms in Schema.org Offer.",
        "sources": [
          {
            "url": "https://example.com/subscription",
            "type": "structured_data",
            "observation": "Missing priceCurrency, recurring price specification, and cancellation terms."
          }
        ]
      },
      "impact": "Generative search assistants cannot answer purchase inquiries or quote accurate pricing, excluding the brand from conversational commerce.",
      "suggested_action": {
        "summary": "Embed Schema.org Offer with explicit recurring billing terms and cancellation policy.",
        "priority": "critical",
        "technical_fix": "Add Schema.org Offer with price, priceCurrency, and explicit recurring billing terms to /subscription head JSON-LD.",
        "creative_fix": "Display standard recurring rate clearly beneath promotional pricing in semantic HTML.",
        "verification": "Inspect /subscription markup with Schema.org Validator to confirm complete Offer properties."
      },
      "affected_urls": [
        "https://example.com/subscription"
      ]
    }
  ],
  "proactive_actions": [
    {
      "id": "P-001",
      "title": "Deploy Machine-Readable /llms.txt Manifest",
      "summary": "Deploy an authoritative /llms.txt manifest providing executive BLUF summaries and clean markdown links for generative search assistants.",
      "priority": "low",
      "category": "discoverability",
      "technical_fix": "Serve /llms.txt with Content-Type: text/plain linking to core guide routes.",
      "creative_fix": "Author first-100-word executive overviews for each core product offering.",
      "verification": "Request GET /llms.txt and verify HTTP 200 with text/plain content."
    }
  ],
  "archetype": "ecommerce",
  "readiness": {
    "composite_score": 78.5,
    "grade": "B",
    "score_scope": "Observed static inventory and specialist telemetry; heuristic citation-readiness proxy, not live provider ranking or citation measurement."
  }
}
```

---

## 8. Engineering Standards & Operational Invariants

- **Zero Third-Party Runtime Dependencies:** All runtime logic across all eight skills uses strictly the Python 3.9+ standard library (`urllib`, `socket`, `html.parser`, `xml.etree.ElementTree`, `json`, `re`, `argparse`, `math`).
- **Zero-Trust SSRF Protection:** All outbound network operations flow through `safe_fetch.py`, performing pre-socket DNS resolution and immediately aborting on private (RFC 1918), loopback, link-local (`169.254.0.0/16`), cloud metadata (`169.254.169.254`), and CGNAT subnets.
- **Single-Pass Acquisition Architecture:** Target websites are crawled strictly once. All six specialist sensors operate offline against `inv.json`, ensuring zero redundant network traffic.
- **Deterministic Execution:** Sensor measurements execute via deterministic static analysis without non-deterministic scraping or browser simulation.
- **Zero Headless Browsers:** Eliminates Playwright, Puppeteer, Selenium, and Chromium binaries. The entire audit suite executes in under five minutes with low resource consumption.
- **Compact Package Footprint:** The complete distribution package is approximately 0.4 MB, easily deployable in any enterprise environment.

---

## 9. Academic Research Foundations

The diagnostic rules and scoring vectors in this suite are grounded directly in peer-reviewed academic literature:

- **Aggarwal et al. (ACM SIGKDD 2024):** "GEO: Generative Engine Optimization" — Established the empirical lift framework for generative citations: quotations (+40.9%), statistics (+30.6%), and technical fluency.
- **Zhang, He, Yao (2026):** "From Citation Selection to Citation Absorption" — Analyzed 21,143 generative engine citations, documenting source absorption rates and content genre optimization.
- **Tian et al. (2026):** "Citation Failure Modes in GEO" — Categorized the five-stage failure taxonomy explaining why relevant web pages fail to be selected by generative answer engines.
- **Liu et al. (Stanford, TACL 2024):** "Lost in the Middle: How Language Models Use Long Contexts" — Demonstrated the U-shaped attention distribution in LLMs, proving the necessity of Bottom Line Up Front (BLUF) answer placement.
- **RFC 9309:** Robots Exclusion Protocol standard compliance for autonomous AI retrieval crawlers and search indexers.

