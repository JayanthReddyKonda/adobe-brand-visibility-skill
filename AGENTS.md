# AGENTS.md — Developer & AI Agent Instruction Manual

## 1. Project Mission & Overview

The **Brand AI-Readiness & Visibility Marketplace** is an autonomous multi-skill suite engineered for the Adobe University Hackathon 2026 (Round 3). Its mission is to automatically audit any brand website, diagnose why the brand is invisible, misrepresented, or experiencing high visitor bounce across generative AI search assistants (ChatGPT Search, Claude, Perplexity Pro, Google AI Overviews), and emit an evidence-backed, Draft-07 schema-validated audit report with dual-track remediation.

The marketplace conforms strictly to the **`agentskills.io`** standard and comprises **8 focused skills**:
- **`audit-orchestrator`** *(Marketplace Entrypoint)*: Master AI runbook coordinator; directs single-pass inventory acquisition, orchestrates specialist sensor execution, applies cognitive reasoning over multi-signal evidence, and enforces the Draft-07 JSON Schema gate.
- **`web-scraper`**: Autonomous, zero-dependency, SSRF-hardened web crawler and content extractor. Crawls websites, evaluates RFC 9309 robots.txt matrices across 16 AI retrieval & training bots, traverses XML sitemaps, flattens Schema.org JSON-LD graphs, extracts Trafilatura-grade clean Markdown with SNR scoring, scores commercial routes, and emits canonical site inventories (`inv.json`).
- **`discoverability-audit`**: Evaluates search retrieval access, crawler disallow rules, meta `noindex` directives, canonical consistency, and blank CSR/SPA shells.
- **`entity-content-audit`**: Extracts explicit Schema.org JSON-LD entities (`Organization`, `Product`, `@graph`) and scores commercial Answerability attribute completeness.
- **`fact-consistency-audit`**: Scopes first-party facts across multi-page inventories with global multi-currency normalization to isolate contradictory pricing, contacts, or lifecycle terms.
- **`corroboration-authority-audit`**: Validates external identity corroboration by probing declared `sameAs` authority links (Wikidata, LinkedIn, Wikipedia) with zero-trust SSRF sandboxing.
- **`geo-content-audit`**: Audits text based on empirical Generative Engine Optimization (Princeton KDD 2024 / CMU AutoGEO) research across all 9 citability vectors.
- **`engagement-context-audit`**: Evaluates post-citation visitor orientation and intent-handoff continuity with OpenGraph metadata fallbacks.

---

## 2. Strict Architectural Constraints & Invariants

Every agent or contributor working in this repository MUST preserve these non-negotiable rules:

1. **Zero Runtime Third-Party Dependencies:**
   - All runtime scripts under `src/skills/` MUST use pure Python 3.9+ standard library modules only (`urllib.parse`, `urllib.request`, `socket`, `html.parser`, `xml.etree.ElementTree`, `json`, `heapq`, `gzip`, `zlib`, `ast`, `re`, `argparse`).
   - Pip packages (Ruff, Flake8, MyPy, Pytest) are developer tooling ONLY and must NEVER be imported in production skill scripts.
2. **No Headless Browser Runtimes:**
   - Absolutely NO Playwright, Puppeteer, Selenium, or Chromium binaries. Everything must run lightweight, fast, and sandboxed.
3. **Zero-Trust SSRF Defense:**
   - Every outbound network request must resolve IP addresses before connecting and reject RFC 1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopbacks (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), cloud metadata (`169.254.169.254`), and IPv4-mapped IPv6 ranges.
4. **Twin Directory Invariant:**
   - `src/skills/` is the canonical source.
   - `.agents/skills/` must be 100% identical to `src/skills/`.
   - Always run `bash scripts/sync.sh` after modifying any skill.
5. **Clean Marketplace Root Packaging:**
   - Per `round3_PS.pdf`, the submission archive (`brand-ai-readiness-audit.zip`) must unpack to the single directory `brand-ai-readiness-audit/` containing ONLY:
     - `marketplace.json`
     - `README.md`
     - `LICENSE`
     - `skills/` (the 8 skill folders)
   - Archive size MUST be $\le 50\text{ MB}$ (current build is ~274 KB).
6. **Audit Execution Runtime Ceiling:**
   - The entire audit for a typical site MUST finish in $< 5\text{ minutes}$.

---

## 3. Tooling & Environment Setup

The repository uses standard Linux shell scripts and a local virtual environment for QA tooling:

```bash
# 1. Environment Activation (via .venv or uv)
source .venv/bin/activate
# or use uv directly:
# uv sync

# 2. Production QA Pipeline (MANDATORY BEFORE ANY COMMIT)
./scripts/qa_check.sh
# Runs:
# - Ruff Linter & Formatter (0 errors)
# - Flake8 Strict Style Checker (--max-line-length=140, 0 errors)
# - MyPy Static Type Checker across all 8 skills (0 errors)
# - JSON Schema & Draft-07 Manifest Integrity Check (0 errors)
# - Pytest Unit & Integration Test Suite (130+ tests, 100% green)

# 3. Synchronize Skills to .agents/skills/
./scripts/sync.sh

# 4. Build Marketplace Submission Zip
./scripts/build.sh
```

---

## 4. End-to-End Audit Execution Workflow

When an AI Agent is tasked with auditing a website (`--site <url>`), follow this 4-phase sequence:

### Phase 1: Pre-Flight & Normalization
Normalize URL to canonical domain (e.g., `https://example.com/`) and verify DNS reachability under SSRF policy.

### Phase 2: Unified Single-Pass Acquisition (NO 6x Redundant Crawling)
Run `web-scraper` once to acquire the target domain's full inventory into `inv.json`:
```bash
python3 skills/web-scraper/scripts/run_scraper.py \
  --site https://example.com \
  --output inv.json \
  --format json \
  --max-pages 15 \
  --timeout 30
```
*(Alternatively: `python3 skills/audit-orchestrator/scripts/acquire_inventory.py --site https://example.com --output inv.json --format json`)*

### Phase 3: Specialist Sensor Execution (Offline against `inv.json`)
Fan out `inv.json` across all 6 diagnostic tools sequentially or in parallel. Zero duplicate network requests:
```bash
# 1. Discoverability
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --format json

# 2. Entity Content & Schema.org
python3 skills/entity-content-audit/scripts/entity_content_check.py --site https://example.com --inventory inv.json --format json

# 3. Fact Consistency & Conflicts
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --format json

# 4. Authority & Corroboration
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --format json

# 5. Generative Engine Optimization (GEO)
python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --format json

# 6. Engagement & Context Continuity
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format json
```

### Phase 4: Cognitive Synthesis & Schema Validation Gate
1. Apply reasoning rules from `audit-orchestrator/references/audit-orchestrator-knowledge-base.md` to correlate cross-domain signals (e.g., low word count + missing schema + missing H1 = SPA rendering failure).
2. For each finding, generate **dual-track remediation**:
   - `technical_fix`: Exact code/markup snippet for developers.
   - `creative_fix`: Copy/UX guidelines for marketers and editors.
   - `verification`: Concrete verification test.
3. Validate the final output report against the Draft-07 schema gate:
```bash
python3 skills/audit-orchestrator/scripts/validate_report.py final_report.json
```

---

## 5. Dos and Don'ts for Agents

### DO:
- **DO** keep `SKILL.md` files concise and under 500 lines, pushing detailed checklists to `references/` and code to `scripts/`.
- **DO** ensure all Markdown references have clear Tables of Contents when exceeding 250 lines.
- **DO** run `./scripts/qa_check.sh` after modifying any code to ensure 0 lint, type, or test regressions.
- **DO** run `./scripts/sync.sh` whenever any skill file is modified.
- **DO** verify that `evidence` in audit findings can be safely parsed whether emitted as a string or a structured object.
- **DO** handle network timeouts and HTTP 4xx/5xx gracefully (fail-closed for 5xx robots.txt, fail-open for 404).

### DO NOT:
- **DO NOT** add any `pip` package dependency to any script in `src/skills/`.
- **DO NOT** create loose packages or scratch files at the marketplace root (`src/` or `build/brand-ai-readiness-audit/`).
- **DO NOT** execute crawling multiple times across specialist skills when `inv.json` is available.
- **DO NOT** modify live websites (the entire marketplace is strictly read-only and diagnostic).
- **DO NOT** check in `__pycache__` directories or `.pyc` files.
