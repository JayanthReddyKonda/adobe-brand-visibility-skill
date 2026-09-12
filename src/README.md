# Brand AI-Readiness & Visibility Marketplace

**Author:** Jayanth Reddy Konda
**Version:** 2.1.0
**Specification Compliance:** `agentskills.io` Standard & JSON Schema Draft-07

---

## 1. The Problem

Traditional SEO optimizes for keyword rank across 10 organic blue links. Generative AI search engines (ChatGPT Search, Claude, Perplexity, Google AI Overviews) have fundamentally changed discovery: they synthesize answers from multiple sources and selectively cite content based on structural quality, factual density, and machine-readable entity clarity — not page rank.

Brands face an **AI Visibility Gap**: ranking #1 on Google no longer guarantees AI citation, and conversely, unranked long-tail pages frequently secure top AI citations. Sites that lack machine-explicit structured data, causal depth in content, or proper crawler permissions are invisible to generative engines.

This marketplace diagnoses exactly why a website is invisible, misrepresented, or losing visitors across AI search assistants, and provides actionable dual-track remediation (technical code fixes + creative content fixes).

---

## 2. The Sensor-Brain Architecture

This marketplace implements a **Sensor-Brain Cognitive Orchestration Architecture** that separates deterministic measurement from intelligent reasoning:

```
+-------------------------------------------------------------------------+
|                    BRAIN: AI AGENT (Cognitive Reasoning)                 |
|                                                                         |
|  - Reads sensor telemetry and applies 6-Layer Causal DAG               |
|  - Classifies business archetype (e-commerce, SaaS, publisher, local)  |
|  - Performs 5-Whys root-cause analysis across domain signals            |
|  - Authors bespoke dual-track remediation (technical + creative)        |
|  - Validates and delivers Draft-07 schema-compliant report             |
+-------------------------------------------------------------------------+
                                    |
                    Empirical Telemetry (Structured JSON)
                                    |
+-------------------------------------------------------------------------+
|                 SENSORS: Deterministic Python Scripts                    |
|                                                                         |
|  - Single-pass SSRF-safe crawl and inventory acquisition               |
|  - RFC 9309 crawler permission matrix across 16 AI bots               |
|  - Schema.org JSON-LD entity extraction and answerability scoring      |
|  - Cross-page fact ledger and pricing contradiction detection          |
|  - External identity corroboration via zero-trust probing              |
|  - Princeton KDD 2024 citability heuristics and statistical density   |
|  - Post-citation visitor orientation and CTA reachability scoring     |
+-------------------------------------------------------------------------+
```

**Why this matters:** The AI agent is the diagnostic brain, not a copy-paster. The Python scripts are precision measurement instruments that provide empirical telemetry. The agent reasons over that telemetry to produce a contextualized, archetype-aware diagnosis that no deterministic script can generate alone.

---

## 3. The 8 Skills

The marketplace decomposes into **1 entrypoint coordinator** and **7 specialist diagnostic sensors** (8 skills total):

| Skill | Role | What It Measures |
|---|---|---|
| **`audit-orchestrator`** | Entrypoint Coordinator | Orchestrates single-pass crawl, fans out to all sensors, aggregates telemetry, gates findings through the 6-Layer Causal DAG, and validates the final report against Draft-07 schema. |
| **`web-scraper`** | Acquisition Engine | Crawls websites under zero-trust SSRF protection, parses RFC 9309 robots.txt across 16 AI bots, extracts clean markdown with SNR scoring, flattens Schema.org JSON-LD graphs, and emits canonical site inventories (`inv.json`). |
| **`discoverability-audit`** | Crawlability Sensor | Evaluates whether AI retrieval bots (OAI-SearchBot, Claude-SearchBot, PerplexityBot) can crawl and index the site. Detects robots.txt blocks, noindex directives, canonical fragmentation, and client-side rendering gaps. |
| **`entity-content-audit`** | Entity Identity Sensor | Extracts Schema.org JSON-LD entities (Organization, Product, Offer) and scores answerability attribute completeness. Detects missing brand identity, incomplete pricing, and stale schema. |
| **`fact-consistency-audit`** | Fact Ledger Sensor | Builds a cross-page fact ledger (prices, contacts, copyright dates) and diffs first-party claims to isolate verified contradictions that trigger LLM hallucination. |
| **`corroboration-authority-audit`** | Authority Sensor | Probes declared sameAs identity links (Wikidata, LinkedIn, Wikipedia) under zero-trust SSRF to verify external entity corroboration. |
| **`geo-content-audit`** | Citability Sensor | Audits content against Princeton KDD 2024 and AutoGEO research across 9 citability vectors: BLUF primacy, statistical density, causal depth, passage chunking, and evidence genre distribution. |
| **`engagement-context-audit`** | Orientation Sensor | Evaluates post-citation visitor experience: heading information scent, above-the-fold CTA reachability, and intent-handoff continuity for AI-referred traffic. |

---

## 4. How It Works

### Step 1: Single-Pass Acquisition
The orchestrator invokes `web-scraper` to crawl the target site once under SSRF protection, extracting HTML, robots.txt matrices, clean markdown, and JSON-LD into a canonical site inventory (`inv.json`). Crawling is never repeated.

### Step 2: Offline Sensor Fan-Out
All 6 specialist sensors run offline against `inv.json` with zero additional network overhead, producing structured empirical measurements.

### Step 3: Cognitive Synthesis (The AI Agent)
The AI agent ingests sensor telemetry via `orchestrator.py --telemetry`, then:
- Applies the **6-Layer Causal DAG** to suppress downstream symptoms when upstream blockers exist (e.g., if robots.txt blocks crawlers, suppress content citability findings)
- Classifies the **business archetype** (e-commerce, SaaS, publisher, local business) to reweight priorities
- Authors **bespoke dual-track remediation**: copy-pasteable technical fixes (code/config/Schema.org JSON-LD) and actionable creative fixes (content/UX guidance grounded in GEO research)

### Step 4: Schema Validation Gate
The final report validates against a strict Draft-07 JSON schema, ensuring every finding has evidence, dual-track remediation, and correct severity classification.

---

## 5. Use Cases

### Use Case 1: Full AI Readiness Audit
> "Audit `https://brand.com` for AI search visibility across ChatGPT, Claude, and Perplexity."

The agent acquires site inventory, runs all 6 sensors, reasons over the telemetry, and delivers an executive diagnostic briefing with a validated JSON report containing prioritized findings and dual-track remediation.

### Use Case 2: Diagnose AI Invisibility
> "Why is our brand never cited by ChatGPT Search or Perplexity even though we rank #1 on Google?"

The agent identifies the root causes: perhaps robots.txt blocks AI retrieval bots (Layer 0), or the site lacks Schema.org Organization markup (Layer 2), or the content has low causal depth and no statistical evidence (Layer 4).

### Use Case 3: Fix High AI Referral Bounce Rates
> "AI search sends traffic to our site but visitors bounce within 5 seconds."

The engagement sensor detects heading scent mismatches, delayed CTA placement, and viewport answer absence. The agent provides specific H1 rewrites, above-the-fold restructuring, and CTA repositioning guidance.

### Use Case 4: E-Commerce AI Commerce Readiness
> "Prepare our product catalog for autonomous AI purchasing agents (Google AI Mode, ChatGPT Checkout)."

The entity sensor evaluates Product/Offer schema completeness, pricing consistency, and ISO 4217 compliance. The agent recommends Universal Commerce Protocol (UCP) manifest deployment and machine-readable pricing manifests.

---

## 6. Execution Interfaces

### Primary: AI Agent Cognitive Pipeline
```bash
# 1. Acquire site inventory (single-pass, SSRF-safe)
python3 skills/web-scraper/scripts/acquire_inventory.py --site https://example.com --output inv.json --format json

# 2. Collect empirical telemetry from all sensors
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --telemetry

# 3. Ingest agent review findings into unified causal DAG report synthesis
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --review review.json --output report.json
```
The AI agent reasons over the telemetry, consults domain knowledge bases, authors refined findings into `review.json`, and synthesizes the final report with cryptographic provenance (`run_manifest`).


### Automated CI/CD Pipeline
```bash
# Headless baseline report for automated testing (NOT for agent use)
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --format json --baseline-only
```

### Modular Sensor Invocation
```bash
# Run individual sensors against pre-acquired inventory
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --format json
python3 skills/entity-content-audit/scripts/entity_content_check.py --site https://example.com --inventory inv.json --format json
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --format json
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --format json
python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --format json
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format json

# Validate report against Draft-07 schema
python3 skills/audit-orchestrator/scripts/validate_report.py < report.json
```

---

## 7. Output Report Schema

Every report emitted by the audit conforms to Draft-07 JSON Schema:

```json
{
  "site": "https://example.com",
  "audited_at": "2026-09-02T12:00:00Z",
  "audit_status": "complete",
  "summary": {
    "total_findings": 2,
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "findings": [{
      "id": "finding-1",
      "title": "AI Search Crawlers Blocked in robots.txt",
      "severity": "high",
      "category": "discoverability",
      "root_cause": "robots.txt explicitly disallows OAI-SearchBot and PerplexityBot.",
      "evidence": {
        "summary": "Disallow: / found for OAI-SearchBot and PerplexityBot.",
        "scope": "robots.txt",
        "sources": [{"url": "https://example.com/robots.txt", "type": "robots_txt", "observation": "Disallow: /"}]
      },
      "suggested_action": {
        "summary": "Allow AI search retrieval bots in robots.txt.",
        "priority": "high",
        "technical_fix": "Add User-agent: OAI-SearchBot ; Allow: / to robots.txt.",
        "creative_fix": "Update AI governance disclosures to clarify retrieval access is permitted.",
        "verification": "Fetch robots.txt with User-Agent: OAI-SearchBot and verify Allow: /."
      }
    }
  ],
  "proactive_actions": []
}
```

---

## 8. Technical Constraints

- **Zero Runtime Dependencies:** Pure Python 3.9+ standard library only. No pip packages at runtime.
- **Zero-Trust SSRF Protection:** All network operations flow through `safe_fetch.py` with pre-socket IP validation against RFC 1918, loopback, link-local, and cloud metadata subnets.
- **Single-Pass Acquisition:** The site is crawled exactly once. All sensors run offline against the cached inventory.
- **Read-Only Execution:** Only GET and HEAD requests. Zero state-changing operations on target domains.
- **Bounded Execution:** Full audit completes in under 5 minutes with strict wall-clock timeouts.
- **Package Size:** Distribution zip is under 1 MB (well within the 50 MB ceiling).

---

## 9. Research Foundation

The audit methodology is grounded in peer-reviewed academic research:

- **Aggarwal et al. (ACM SIGKDD 2024):** "GEO: Generative Engine Optimization" — the foundational mathematical model of generative search, 10,000-query GEO-bench, and empirical lift table (quotations +40.9%, statistics +30.6%).
- **Zhang, He, Yao (2026):** "From Citation Selection to Citation Absorption" — 21,143 citations, evidence-genre lift analysis (code +76.9%, statistics +61.6%, standalone FAQ -5.7% penalty).
- **Tian et al. (2026):** "Citation Failure Modes in GEO" — 5-stage failure taxonomy explaining why 43% of topically relevant pages receive zero citations.
- **Liu et al. (Stanford, TACL 2024):** "Lost in the Middle" — U-shaped attention curve proving BLUF primacy (44.2% of citations from top 30% of content).
- **Omniscient Digital (2026):** 57% of branded AI citations come from third-party sources, not the brand's own website.
