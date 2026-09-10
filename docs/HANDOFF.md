# Master Agent Handover & Project Knowledge Base

**Author:** Jayanth Reddy Konda  
**Version:** 2.1.0 (Production SOTA Release)  
**Project:** Brand AI-Readiness & Generative Engine Optimization (GEO/AEO) Audit Suite  
**Target Audience:** Incoming Autonomous AI Agent taking over project stewardship  
**Status:** 100% OPERATIONAL — 263/263 TESTS + 29 SUBTESTS GREEN — 0 LINT DEFECTS — PURE PYTHON STANDARD LIBRARY  

---

## 1. Executive Orientation for the Incoming Agent

Welcome, Agent. You are taking over stewardship of the **Brand AI-Readiness & Generative Engine Optimization (GEO/AEO) Audit Suite**, submitted for the Adobe Hackathon Round 3.

### The Core Problem Statement
Traditional SEO optimizes for keyword rank across 10 organic blue links. However, generative engines (ChatGPT Search, Perplexity AI, Claude, Google AI Overviews) generate synthesized answers with selective citations. Brands are experiencing an "organic disconnection": ranking #1 on Google no longer guarantees AI visibility, and conversely, unranked long-tail pages frequently secure top AI citations.

This codebase delivers an end-to-end audit skill that evaluates any brand's website for AI readiness, identifies deterministic crawl and entity defects, measures content citability and answer absorption, scores autonomous agent commerce readiness, and produces a Draft-07 schema-validated audit report with dual-track remediation.

### The Non-Negotiable Evaluator Constraints (`resources/round3_PS.pdf`)
To maintain a 100/100 evaluation score, you MUST preserve these strict rules:
1. **Zero External Dependencies:** 100% pure Python standard library (`urllib.request`, `html.parser`, `re`, `json`, `math`, `datetime`, `subprocess`, `ssl`, `socket`). No `pip` packages (`requests`, `beautifulsoup4`, `playwright`, `pydantic`).
2. **Single Entrypoint Architecture:** Exactly 1 entrypoint orchestrator (`audit-orchestrator`) coordinating 7 specialist skills (including dedicated `web-scraper`) defined in `marketplace.json` conforming to the `agentskills.io` standard (8 skills total).
3. **Draft-07 JSON Schema Gate:** Final audit report MUST strictly validate against `report-schema.json` with support for both string and structured evidence objects, dual-track remediation (`technical_fix`, `creative_fix`, `verification`), and proactive actions.
4. **Recommend-Only Mandate:** Never execute mutating operations on the target domain; recommend fixes with `technical_fix` and `creative_fix`.
5. **Zero Emojis Policy:** Absolute zero emojis in any markdown documentation across all skills and docs.
6. **Package Ceiling:** Zip size must stay <= 50 MB (current build is ~490 KB).
7. **Time Ceiling:** Audit execution must complete in < 5 minutes (test suite runs in ~45s, live audits finish in < 3s).

---

## 2. Codebase Directory & Capabilities Map

The codebase exists in two synchronized representations:
- `src/skills/`: The primary canonical source codebase.
- `.agents/skills/`: The runtime agent marketplace environment.
- **Rule:** Any change made in `src/skills/` MUST be mirrored to `.agents/skills/` (`python scripts/sync.py` or `./scripts/sync.sh`).

```
adobe-brand-visibility-skill/
├── marketplace.json                 # Standard marketplace manifest (1 entrypoint + 7 specialists)
├── src/skills/                      # Source skills directory (8 skills total)
│   ├── audit-orchestrator/          # Entrypoint coordinator & report synthesis
│   │   ├── SKILL.md                 # Orchestrator runbook & synthesis guidelines
│   │   ├── scripts/                 # orchestrator.py, audit.py, assemble_report.py, causal_gate.py, validate_report.py
│   │   └── references/              # report-schema.json, knowledge-base.md, checks.md, checks.json
│   ├── web-scraper/                 # Autonomous crawler, RFC 9309 matrices, markdown & JSON-LD
│   │   ├── SKILL.md                 # Scraper runbook & CLI guidelines
│   │   ├── scripts/safe_fetch.py    # Canonical zero-trust SSRF fetcher
│   │   ├── scripts/acquire_inventory.py # Canonical inventory acquisition crawler
│   │   ├── scripts/run_scraper.py   # CLI entrypoint with JSON & MD table outputs
│   │   └── scripts/crawler/         # 16 pure-Python modules (policy, fetch, robots, sitemap, etc.)
│   ├── discoverability-audit/       # RFC 9309, AI bots, SNR, nosnippet (HF-03, HF-04, HF-05)
│   ├── entity-content-audit/        # Schema.org @graph, sameAs, ISO 4217, product consistency (HF-06)
│   ├── fact-consistency-audit/      # Cross-page contradiction ledger, price drift (W-03)
│   ├── corroboration-authority-audit/# Zero-trust linkbacks, 57% off-site footprint (W-04)
│   ├── geo-content-audit/           # Evidence genres, hedge lexicon, FTR, BLUF, Wilson CIs (TX01-TX06)
│   └── engagement-context-audit/    # Post-citation intent handoff, value CTAs, /pricing.md
├── tests/                           # Pure stdlib + pytest suite (unit/, integration/, system/)
├── docs/                            # High-level knowledge base and architectural docs
├── resources/                       # Unabridged research papers, PDFs, cloned repos, and specs
└── scripts/
    ├── qa_check.sh                  # Full production pipeline (Ruff, Flake8, MyPy, Schema, Pytest)
    ├── build.py                     # Cross-platform package builder (pure Python)
    ├── sync.py                      # Cross-platform src/ to .agents/ mirror (pure Python)
    ├── build.sh                     # POSIX shell forwarder to build.py
    └── sync.sh                      # POSIX shell forwarder to sync.py
```

---

## 3. High-Level Skill Responsibilities

### 1. `audit-orchestrator` (The Master Coordinator)
- **Role:** Coordinates the audit runbook and synthesizes diagnostic reports.
- **Key Tools:**
  - `orchestrator.py`: Master CLI pipeline executing single-pass crawl, offline sensor fan-out, causal DAG synthesis, and proactive actions. Supports `--telemetry` mode for AI agent cognitive reasoning.
  - `audit.py`: Multi-pass execution engine coordinating collection, agent review finalization, and validation.
  - `assemble_report.py`: Assembles candidate finding objects into Draft-07 schema compliance with dual-track remediation.
  - `causal_gate.py`: 6-Layer Causal DAG enforcing deterministic suppression of downstream symptoms when upstream blockers exist. Supports bidirectional taxonomy aliases.
  - `validate_report.py`: Strict Draft-07 JSON schema validator enforcing required fields and locked enums.
- **Cognitive Responsibility:** The agent synthesizes specialist telemetry, deduplicates overlapping findings, calculates the 6 Orthogonal Scores, maps root causes to the 16-Defect Matrix, and outputs the final report.
- **Sensor-Brain Architecture:** The Python scripts are deterministic telemetry sensors providing empirical measurements. The AI agent is the Cognitive Reasoning Brain that reasons over telemetry, applies the 6-Layer Causal DAG, classifies business archetypes, and synthesizes bespoke dual-track remediation. The agent must NEVER simply run orchestrator.py --format json and forward the output.

### 2. `web-scraper` (Single-Pass Crawler & Content Extractor)
- **Role:** Autonomous, zero-dependency web crawler and AI content extractor.
- **Key Tools:**
  - `safe_fetch.py`: Canonical zero-trust SSRF protection blocking private RFC-1918, link-local, and loopback IP addresses.
  - `acquire_inventory.py`: Canonical crawler generating `inv.json` with page classifications, HTML, clean text, and robots directives.
  - `run_scraper.py`: Production CLI with JSON output (`inv.json`) and clean terminal Markdown tables.
  - `crawler/`: 16 pure-Python modules implementing RFC 9309 robots matrices across 16 AI retrieval and training bots, recursive sitemap parsing, clean Markdown extraction with SNR scoring, Schema.org JSON-LD graph flattening, and zero-trust SSRF defense.
- **Enriched Acquisition Signals:** Streaming parser extracts interactive CTAs (`ctas`), internationalization (`hreflangs`), publication and modification dates (`dates`), edge HTTP directives (`x_robots_tag`, HTTP `Link` canonicals), structured contact channels (`contact_info`), social authority profiles (`social_links`), author attribution (`authors`), and AI discovery manifests (`/llms.txt`, `/pricing.md`, `/.well-known/ai-plugin.json`, `/.well-known/security.txt`).

### 3. `discoverability-audit` (Crawl & Index Eligibility)
- **Evaluates:** RFC 9309 rules (500 KiB cap `CR04`, 5xx fail-closed `CR05`), AI search indexers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) vs. training bots (`GPTBot`, `ClaudeBot`), Signal-to-Noise Ratio (`RD02`, `SNR >= 0.12`), edge-level `X-Robots-Tag` headers, HTTP canonical conflicts, hreflang tag validation, and machine discoverability manifests.

### 4. `entity-content-audit` (Machine-Explicit Identity & Commerce)
- **Evaluates:** Schema.org JSON-LD `@graph` structures (`Organization`, `Product`, `Offer`), authoritative `sameAs` density (>= 2 nodes `SC01`), sameAs social authority corroboration (`MISSING_SAMEAS_VERIFICATION`), clean float pricing without currency symbols, 3-letter ISO 4217 currencies (`SC02`), 60-day freshness (`SC03`), HTML vs. JSON-LD product consistency (`HF-06`), structured contact channel verification, and multi-archetype answerability (SaaS, E-commerce, Services, Content).

### 5. `fact-consistency-audit` (Truth & Grounding Ledger)
- **Evaluates:** Multi-page numerical and factual drift. Constructs cross-page fact ledgers (prices, emails, phone numbers, copyright dates) and detects conflicting commercial terms and trial durations (`CONFLICTING_COMMERCIAL_TERMS`) that trigger LLM hallucination and purchase distrust.

### 6. `corroboration-authority-audit` (External Identity & Third-Party Footprint)
- **Evaluates:** Zero-trust HTTP linkback verification. Confirms that external `sameAs` targets (Wikidata, Wikipedia, LinkedIn, GitHub) resolve to verified brand entities. Detects `UNLINKED_KNOWLEDGE_GRAPH_ANCHOR` when official channels exist on-site but are omitted from structured data. Enforces an 8.0s hard cumulative deadline on external probes.
- **57% Off-Site Footprint Sensor:** Probes for brand footprint across top third-party citation hubs (Reddit, Wikipedia, YouTube, LinkedIn, Trustpilot, G2).

### 7. `geo-content-audit` (Generative Citability & Absorption)
- **Evaluates:** Evidence genre detection (Code +76.9%, Stats +61.6%, Definitions +57.3%, Comparisons +55.3%), Hyland hedge lexicon density (<= 1.2%), Atomic Fact-to-Token Ratio (FTR >= 0.080), BLUF top-30% positioning, credentialed author attribution (`PROACTIVE.GEO.CREDENTIALED_AUTHOR_ATTRIBUTION.001`), commercial CTA intrusion detection (`COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT`), and Wilson 95% Confidence Intervals.

### 8. `engagement-context-audit` (Intent Handoff & Autonomous Buying)
- **Evaluates:** Post-citation user orientation, first-3-elements CTA reachability from structured inventory CTAs, viewport answer anchoring, ARI cognitive readability, and machine-readable pricing manifests (`/pricing.md` or `/pricing.txt`) for autonomous purchasing agents.

---

## 4. Execution Interfaces & Operational Runbooks

### Interface 1: AI Agent Cognitive Pipeline (`orchestrator.py --telemetry` & `--review`)
Primary entrypoint for AI agents. Acquires inventory and collects empirical telemetry for cognitive synthesis:
```bash
# 1. Acquire site inventory (single-pass, SSRF-safe)
python3 src/skills/audit-orchestrator/scripts/acquire_inventory.py --site https://example.com --output inv.json --format json

# 2. Collect aggregated sensor telemetry for AI agent reasoning
python3 src/skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --telemetry

# 3. Ingest agent review findings into unified causal DAG report synthesis
python3 src/skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --inventory inv.json --review review.json --output report.json
```
The AI agent reasons over the telemetry, applies the 6-Layer Causal DAG, classifies the business archetype, authors bespoke dual-track remediation into `review.json`, and synthesizes a schema-validated report with cryptographic provenance (`run_manifest`).

### Interface 1b: Headless CI/CD Baseline Runner (Automated Testing ONLY)
```bash
# NOT for AI agent use — reserved for automated test suites
python3 src/skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --format json --baseline-only
```

### Interface 2: Contract-Driven Multi-Pass Audit Engine (`audit.py`)
Multi-pass orchestration isolating bounded evidence collection, semantic agent review, and Draft-07 schema validation:
```bash
# 1. Bounded single-pass collection & baseline report emission (bounded to 160s)
python3 src/skills/audit-orchestrator/scripts/audit.py collect https://example.com --out output/audit

# 2. Agent semantic finalization composing collected evidence with review.json
python3 src/skills/audit-orchestrator/scripts/audit.py finalize --bundle output/audit/bundle.json --review output/audit/review.json --out output/audit/final-report.json

# 3. Validate final report against Draft-07 schema and consistency invariants
python3 src/skills/audit-orchestrator/scripts/audit.py validate output/audit/final-report.json
```

### Interface 3: Modular Specialist Sensor Invocations
Each sensor runs completely offline against `inv.json` with self-resolving path discovery (`SCRAPER_DIR`):
```bash
# 1. Acquire canonical site inventory via single-pass web scraper
python3 src/skills/web-scraper/scripts/acquire_inventory.py --site https://example.com --output inv.json --format json

# 2. Execute specialist sensors against inv.json
python3 src/skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --format json
python3 src/skills/entity-content-audit/scripts/entity_content_check.py --site https://example.com --inventory inv.json --format json
python3 src/skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --format json
python3 src/skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --format json
python3 src/skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --format json
python3 src/skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format json

# 3. Validate output report against Draft-07 schema gate
python3 src/skills/audit-orchestrator/scripts/validate_report.py final_report.json
```

---

## 5. Specialist Sensor Interface Contract

Every diagnostic sensor implements the standard programmatic interface:
```python
def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None) -> Dict[str, Any]:
    """Execute diagnostic sensor against inventory.
    
    Returns:
        Dict matching {"status": "ok"|"inconclusive", "findings": [...], "recommendations": [...]}
    """
```

### Finding Object Invariants
Every emitted finding must strictly provide:
- `id` *(string)*: Unique defect identifier (e.g., `F-001`).
- `cause_id` *(string)*: Root cause key matching `knowledge-base.md`.
- `title` *(string)*: Clean descriptive defect title.
- `category` *(string)*: Functional audit domain.
- `severity` *(enum)*: Strictly `"critical" | "high" | "medium" | "low"`.
- `confidence` *(enum)*: Strictly `"high" | "medium" | "low"`.
- `evidence` *(string | object)*: Concise diagnostic proof without synthetic fabrication.
- `suggested_action` *(object)*: Actionable mitigation with required `"summary"` and `"priority"`, plus `"technical_fix"`, `"creative_fix"`, and `"verification"`.

---

## 6. Critical Environment Quirks & Watch-Outs for the Agent

1. **The Twin Directory Invariant:**
   - `src/skills/` is the canonical source of truth; `.agents/skills/` is the generated runtime mirror.
   - Always run `python scripts/build.py && python scripts/sync.py` after any modification.
2. **Canonical Import Resolution:**
   - `safe_fetch.py` and `acquire_inventory.py` reside canonically in `src/skills/web-scraper/scripts/`.
   - Never re-create duplicate shims in specialist skills; sensors resolve `SCRAPER_DIR` dynamically.
3. **The `validate_report.py` Strictness:**
   - `report-schema.json` has `additionalProperties: false` enabled on every object level. Unrecognized keys will trigger schema validation failure.
4. **Pure Python Standard Library Invariant:**
   - Never import runtime `pip` packages. All runtime scripts must execute on vanilla Python 3.9+.
5. **Frozen Vendor Directory:**
   - Never modify, format, or lint files in `resources/`. Target tools strictly to `src/` and `tests/`.

---

## 7. Developer QA Pipeline & Verification Commands

All modifications must pass the complete QA suite before declaring work complete:
```bash
# 1. Full Production QA Pipeline (Ruff, Flake8, MyPy, Draft-07 Schema, Pytest)
./scripts/qa_check.sh

# 2. Package Build & Marketplace Compliance Validation (cross-platform)
python scripts/build.py
python tests/validate_package.py brand-ai-readiness-audit.zip

# 3. Synchronize Runtime Mirror (cross-platform)
python scripts/sync.py

# 4. Full Test Suite
pytest tests/ -q
```

---

## 8. Strategic Roadmap for Further Perfection

1. **Live AI Search Probes (Optional API Extension):**
   - Provide an optional CLI mode (`--live-probe`) connecting to Perplexity Sonar API or OpenAI Search API to compare theoretical citability against live citation events.
2. **Deep Graph Web Traversal (WebWalker ACL 2025):**
   - Extend `acquire_inventory.py` with multi-hop graph depth tracking (`DiscoveryDepth` and `EvidenceReachability`) across hierarchical routes.
3. **Automated Remediation Patch Generator:**
   - Provide a script that emits ready-to-apply `.patch` diffs or JSON-LD snippets that webmasters can paste directly into their CMS.
