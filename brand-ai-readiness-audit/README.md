# Brand AI-Readiness & Visibility Marketplace

A comprehensive, zero-trust marketplace of specialized AI-readiness auditors. This system replaces generic, superficial SEO scorecards with a forensic **Stateful Knowledge Graph Architecture** to diagnose why a brand is invisible, misrepresented, or abandoned by Generative AI assistants (like ChatGPT, Gemini, Copilot) and AI-referred visitors.

## 🏆 Evaluator's Guide (Adobe Round 3 Alignment)

This submission was aggressively engineered to meet and exceed the strict constraints of the Adobe University Hackathon (Round 3). 

### 1. Pure Python Standard Library
* **Zero `pip` dependencies.** No `requests`, no `beautifulsoup4`, no headless browsers.
* Parses complex HTML, sitemaps, and nested JSON-LD using custom subclasses of `html.parser.HTMLParser`.
* Handles HTTP/HTTPS, custom timeouts, and decompression natively via `urllib` and `gzip`.

### 2. Zero-Trust Security & Adversarial Resilience
* **SSRF Protection & DNS TOCTOU Defense:** A custom `safe_fetch.py` strictly blocks all RFC-1918, Link-Local, Loopback, and IPv4-mapped IPv6 resolutions (e.g. `::ffff:127.0.0.1`). It uses a custom `HTTPConnection` class to pin resolved IPs and enforce URL bounds without globally patching the process, attempting to block DNS-rebinding Time-Of-Check-to-Time-Of-Use (TOCTOU) exploits.
* **Bounded Deadlines & Memory:** Ensures execution completes within the strict global time limit, gracefully degrading to "partial" results rather than hanging. Implements bounded gzip decompression to prevent memory exhaustion exploits.

### 3. "God Tier" Exclusives (Beyond Generic SEO)
* **Semantic GEO (AutoGEO Research):** Evaluates text for Generative Engine Optimization (GEO) metrics using proven research dimensions. We discarded primitive HTML tag counting (`<table>`, `<ul>`) in favor of evaluating "In-Depth Mechanisms" (causal conjunctions) and "Specific Evidence" (digits/substantiation).
* **Context-Window Retrieval (C-SEO Bench):** Explicitly evaluates Title tags and Canonical URLs based on research proving that traditional SEO retrieval signals dictate LLM context-window placement.
* **Information Scent Anchoring:** Validates that the Canonical Entity extracted from the Knowledge Graph perfectly matches the anchor text used in the `<h1>` tag, measuring true semantic orientation for AI-referred visitors.

---

## 🧠 The Marketplace Specialists & Architecture

This architecture utilizes a decentralized marketplace of 7 skills (1 entrypoint + 6 specialists) composed by a central entrypoint (`audit-orchestrator`). 

### 🛡️ The Stateful Knowledge Graph
Instead of executing sequential, disconnected heuristic scans, the orchestrator constructs and passes an atomic, concurrency-safe `state.json` contract across the exact causal execution pipeline: `Discoverability -> Entity -> Fact -> Corroboration -> GEO -> Engagement`.

### The Skills:
1. **`audit-orchestrator` (Entrypoint):** Coordinates the audit, enforces global time limits, manages the Stateful Knowledge Graph, executes the specialists, and synthesizes findings into a strict schema-compliant public JSON report.
2. **`discoverability-audit`:** Diagnoses AI-crawler accessibility, `robots.txt` parsing, Canonical URL routing, and `/llms.txt` proactive discovery.
3. **`entity-content-audit`:** Extracts structured JSON-LD and raw HTML semantics. Evaluates if the AI can understand *Who* the brand is and *What* it sells, seeding the Knowledge Graph.
4. **`fact-consistency-audit`:** Cross-references pricing, contact, and lifecycle facts across the internal graph to detect contradiction-inducing fragmentation. (Also integrates representation verification).
5. **`corroboration-authority-audit`:** Performs bounded validation of external identity claims by resolving declared authority links (`sameAs`) in real-time.
6. **`geo-content-audit`:** Evaluates text for Generative Engine Optimization (GEO) dimensions: Causal Mechanisms and Specific Evidence.
7. **`engagement-context-audit`:** Maps semantic page types to expected human intents, verifying Information Scent continuity (Entity-to-Heading anchoring) to prevent AI-referred bounce.

---

## ⚙️ The Evidence Model vs. Legacy SEO

We strictly prohibit "cosmetic" SEO defects. Every finding must establish a defensible causal chain to an AI-retrieval failure.

* **No Heuristic Defects:** Heuristics (like missing `<table>` tags or missing `<h1>` tags) do NOT alone trigger defect-level findings. They are reported strictly as proactive recommendations.
* **Schema Contract Rigidity:** Findings are strictly delineated into `technical_fix` and `creative_fix` pathways to address root causes systematically.
* **Inconclusive Parsers:** Parsing failures (e.g. malformed HTML) safely degrade to an `inconclusive` status, preventing empty states from hallucinating successful audits.

---

## 🚀 Usage & Invocation

Execute the orchestrator. It will dynamically load all specialists and output a minimalist, schema-valid JSON report to `stdout`.

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com
```

## 📁 Repository Structure

```text
brand-ai-readiness-audit/           # Main Hackathon Submission Payload
├── marketplace.json                # Master Marketplace Skills Manifest
├── README.md                       # Evaluator & Hackathon Documentation
├── LICENSE                         # Open-source MIT License
└── skills/
    ├── audit-orchestrator/         # Entrypoint Skill (Orchestrator)
    ├── discoverability-audit/      # Accessibility & Indexing check
    ├── entity-content-audit/       # Structured Knowledge check
    ├── fact-consistency-audit/     # Temporal Ledger & Contradiction check
    ├── corroboration-authority-audit/# E-E-A-T Claim check
    ├── engagement-context-audit/   # Visitor Orientation & Continuity check
    └── geo-content-audit/          # Generative Engine Optimization check
```

## Note on Architectural Duplication
Per the strict `agentskills.io` portability specification, each skill MUST be fully self-contained without relying on cross-directory dependencies (such as a shared core library). For this reason, helper modules like `safe_fetch.py` and `fact_extractor.py` are deliberately duplicated into each skill's `scripts/` directory to ensure each skill can be extracted and run in total isolation.
