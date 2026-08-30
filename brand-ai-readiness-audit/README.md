# Brand AI-Readiness & Visibility Marketplace

A production-grade, zero-trust marketplace of specialized AI-readiness auditors. This system replaces generic, superficial SEO scorecards with a forensic **Evidence Model** to diagnose why a brand is invisible, misrepresented, or abandoned by Generative AI assistants (like ChatGPT, Gemini, Copilot) and AI-referred visitors.

## 🏆 Evaluator's Guide (Adobe Round 3 Alignment)

This submission was aggressively engineered to meet and exceed the strict constraints of the Adobe University Hackathon (Round 3). 

### 1. Pure Python Standard Library
* **Zero `pip` dependencies.** No `requests`, no `beautifulsoup4`, no headless browsers.
* Parses complex HTML, sitemaps, and nested JSON-LD using custom subclasses of `html.parser.HTMLParser`.
* Handles HTTP/HTTPS, custom timeouts, and decompression natively via `urllib` and `gzip`.

### 2. Zero-Trust Security & Adversarial Resilience
* **SSRF Protection & DNS TOCTOU Defense:** A custom `safe_fetch.py` strictly blocks all RFC-1918, Link-Local, and Loopback IP resolutions. It uses a custom `HTTPConnection` class to pin resolved IPs and enforce URL bounds without globally patching the process, attempting to block DNS-rebinding Time-Of-Check-to-Time-Of-Use (TOCTOU) exploits.
* **Bounded Deadlines & Memory:** Attempts to ensure execution completes within the strict <5-minute limit, gracefully degrading to "partial" results rather than hanging. Implements bounded gzip decompression to prevent memory exhaustion exploits.

### 3. "God Tier" Exclusives (Beyond Generic SEO)
* **Generative Engine Optimization (GEO):** Evaluates pages for *Statistical Density* and *Tabular/List Data Extraction*—features theorized by early GEO research to increase LLM synthesis likelihood.
* **Variant-Aware Contradiction Engine:** Parses `sku` and `name` variants inside product ledgers to reduce false-positive pricing contradictions across multi-variant product pages.
* **Bounded Claim Corroboration:** Cross-references internal identity claims by resolving and parsing external authority links (e.g., social profiles via `sameAs`) in real-time.

---

## 🧠 The Marketplace Specialists & Architecture

This architecture utilizes a decentralized marketplace of 8 skills (1 entrypoint + 7 specialists) composed by a central entrypoint (`audit-orchestrator`). 

### 🛡️ Why 7 Specialists? (Genuine Separation of Concerns)
This architecture strictly enforces the **Principle of Least Privilege** and avoids artificial skill padding. 
- `corroboration-authority-audit` is the *only* skill allowed to make outbound network calls to 3rd-party domains, isolating SSRF risk. 
- `fact-consistency-audit` is the *only* skill that retains cross-page state (ledgering).
- `discoverability-audit` strictly focuses on crawler access rules (robots.txt, canonicals).
Decomposing the logic in this way ensures that if an agent wants to only check facts, it does not need to spin up the dangerous networking module.

### The Skills:
1. **`audit-orchestrator` (Entrypoint):** Coordinates the audit, enforces global time limits, executes the specialists, and synthesizes cross-skill findings to eliminate duplicate root causes.
2. **`discoverability-audit`:** Diagnoses AI-crawler accessibility, `robots.txt` parsing, Canonical/Hreflang validation, and `/llms.txt` proactive discovery.
3. **`entity-content-audit`:** Extracts structured JSON-LD. Evaluates if the AI can understand *Who* the brand is and *What* it sells.
4. **`fact-consistency-audit`:** Constructs a variant-aware temporal ledger of facts (prices, hours) across the domain to detect hallucination-inducing contradictions.
5. **`geo-content-audit`:** Evaluates text for Generative Engine Optimization (GEO) metrics, including statistical density and tabular extraction likelihood.
6. **`engagement-context-audit`:** Maps semantic page types to expected human intents, verifying that necessary UI elements exist for AI-referred traffic to prevent bounce.
7. **`corroboration-authority-audit`:** Performs bounded validation of external identity claims to strengthen entity identity and independent source corroboration.
8. **`assistant-representation-audit`:** (Optional Enrichment) Cross-checks observed external LLM citations against the brand's verified internal fact ledger.

---

## ⚙️ The Evidence Model vs. Legacy SEO

We strictly prohibit "cosmetic" SEO defects. Every finding must establish a defensible causal chain to an AI-retrieval failure.

* **Missing JSON-LD** is not flagged as a fatal error; it is a **Proactive Recommendation** to improve extraction confidence.
* **Missing `sameAs` links** are not fatal; they represent a **Claim Corroboration Gap**.
* Findings sharing the identical `cause_id` across 50 localized URLs are **synthesized by the orchestrator** into a single, high-signal finding to prevent JSON bloat.

---

## 🚀 Usage & Invocation

Execute the orchestrator. It will dynamically load all specialists and output a minimalist, schema-valid JSON report to `stdout`.

```bash
python3 skills/audit-orchestrator/scripts/orchestrator.py --site https://example.com --format json
```

## 🧪 Production-Grade Test Suite

The repository ships with a comprehensive adversarial test suite.

```bash
python3 test_suite.py
```

**Includes 38 Zero-Trust Adversarial Tests:**
1. **SSRF Redirect Bypasses:** Mocks a server returning HTTP 301 to `169.254.169.254`.
2. **Gzip Bomb Resilience:** Verifies memory-bounded decompression.
3. **Monotonic Deadline Exhaustion:** Simulates orchestrator timeouts under extreme latency.
4. **Hreflang ISO Poisoning:** Parses maliciously malformed region/language tags.
5. **Variant Ledger Contradictions:** Feeds overlapping SKU prices to prove the contradiction engine handles standard e-commerce architectures flawlessly.

---

## 📁 Repository Structure

```text
brand-ai-readiness-audit/
├── marketplace.json                # Master Marketplace Skills Manifest
├── README.md                       # Evaluator & Hackathon Documentation
├── LICENSE                         # Open-source MIT License
├── test_suite.py                   # 38-Test Automated Verification Suite
└── skills/
    ├── audit-orchestrator/         # Entrypoint Skill (Orchestrator)
    ├── discoverability-audit/      # Accessibility & Indexing check
    ├── entity-content-audit/       # Structured Knowledge check
    ├── fact-consistency-audit/     # Temporal Ledger & Contradiction check
    ├── corroboration-authority-audit/# E-E-A-T Claim check
    ├── engagement-context-audit/   # Visitor Orientation & Continuity check
    ├── geo-content-audit/          # Generative Engine Optimization check
    └── assistant-representation-audit/ # Output Enrichment layer
```
