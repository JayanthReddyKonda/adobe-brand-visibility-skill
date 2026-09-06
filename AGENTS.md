# AGENTS.md — Developer & AI Agent Operating Specification

Autonomous multi-skill diagnostic engine engineered for the Adobe University Hackathon 2026 (Round 3). Audits brand websites for Generative Engine Optimization (GEO), Answer Engine Optimization (AEO), and LLM citation readiness (ChatGPT Search, Claude, Perplexity Pro, Google AI Overviews), emitting Draft-07 schema-validated reports with dual-track remediation.

---

## 1. Directory Topology & Mutation Boundaries

Strict directory roles must be respected. Violating these boundaries causes build drift, test contamination, and package corruption.

| Path | Purpose | Mutation Rules | Prohibited Actions |
| :--- | :--- | :--- | :--- |
| **`src/skills/`** | **Canonical Source of Truth** | All runtime code, manifests, and references MUST be authored here. | Never write external dependencies or developer tooling imports here. |
| **`tests/`** | **Test Suite & Fixtures** | Tiered tests (`unit/`, `integration/`, `system/`), fixtures, helpers. | Do not put runtime skill logic in test helpers. |
| **`.agents/skills/`** | **Runtime Agent Mirror** | **READ-ONLY / GENERATED**. Synced from `src/skills/` via `scripts/sync.sh`. | **NEVER edit directly.** Direct edits are overwritten on sync. |
| **`resources/`** | **External Vendor References** | **FROZEN / READ-ONLY**. Contains research papers and reference repos. | **NEVER run formatters (`ruff`), linters, or edits here.** |
| **`build/`** | **Packaging Staging** | **GENERATED**. Managed by `scripts/build.sh`. | Never commit manual files to `build/`. |

### Repository Synchronization
Always mirror `src/` to `.agents/` after any edit:
```bash
./scripts/sync.sh
```

---

## 2. Non-Negotiable Architectural Invariants

1. **Zero Runtime Dependencies:**
   - All runtime scripts in `src/skills/` MUST use Python 3.9+ standard library ONLY (`urllib`, `socket`, `html.parser`, `xml.etree.ElementTree`, `json`, `heapq`, `gzip`, `zlib`, `re`, `argparse`).
   - Pip tools (`pytest`, `ruff`, `flake8`, `mypy`) are developer tooling only. No third-party packages in production execution.
2. **No Headless Browsers:**
   - Absolutely NO Playwright, Puppeteer, Selenium, or Chromium binaries. Execution must remain sub-second, lightweight, and deterministic.
3. **Zero-Trust SSRF Protection:**
   - All outbound requests must resolve target IPs before socket creation and immediately abort on RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopbacks (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), carrier-grade NAT (`100.64.0.0/10`), AWS/GCP metadata (`169.254.169.254`), and IPv4-mapped IPv6 ranges.
4. **Single-Pass Acquisition (Zero Redundant Crawls):**
   - Web crawling is strictly performed once by `web-scraper` (or `acquire_inventory.py`) emitting `inv.json`. All downstream diagnostic sensors run offline against `inv.json`.
5. **Clean Marketplace Distribution:**
   - `brand-ai-readiness-audit.zip` unpacks into a single root folder `brand-ai-readiness-audit/` containing ONLY:
     - `marketplace.json`
     - `README.md`
     - `LICENSE`
     - `skills/` (the 8 skill folders)
   - Final archive size MUST be <= 50 MB (current artifact is ~274 KB).
6. **Execution Ceiling:**
   - Complete multi-skill audit for any standard domain must finish in < 5 minutes.

---

## 3. Specialist Skills Catalog

| Skill Name | Role | Primary Sensor Output |
| :--- | :--- | :--- |
| **`audit-orchestrator`** | Entrypoint & Coordinator | Master runbook, single-pass crawl dispatch, cross-signal synthesis, Draft-07 schema gate. |
| **`web-scraper`** | Crawler & Extractor | SSRF-safe crawler, RFC 9309 (16 AI bots), Trafilatura markdown, JSON-LD extraction, `inv.json`. |
| **`discoverability-audit`** | Search Engine Retrieval | Crawler rules, meta `noindex`, canonical mismatch, blank SPA/CSR shell detection. |
| **`entity-content-audit`** | Entity Identity & Schema.org | Machine-explicit `Organization`, `Product`, `@graph` completeness, commercial Answerability. |
| **`fact-consistency-audit`** | Factual Ledger & Drift | Multi-page contradiction detection, cross-currency pricing divergence, stale contact terms. |
| **`corroboration-authority-audit`** | Identity Corroboration | Probes declared `sameAs` authority links (Wikidata, Wikipedia, LinkedIn) under SSRF guard. |
| **`geo-content-audit`** | Citation Probability | Princeton KDD 2024 / CMU AutoGEO citability metrics across all 9 empirical vectors. |
| **`engagement-context-audit`** | Post-Citation Continuity | Visitor orientation, Entity-to-H1 alignment, CTA proximity, and intent-handoff friction. |

---

## 4. Common Defect Prevention & Anti-Pattern Matrix

This matrix governs recurring implementation and automation errors. Follow these exact patterns:

| Defect Class | Root Cause | Mandatory Guardrail / Resolution |
| :--- | :--- | :--- |
| **Dirty git diff in `resources/`** | Running formatters across repository root (`ruff check --fix .`). | **Target strictly `src/` and `tests/`**. `resources/` contains immutable third-party repos. If touched, revert immediately: `git checkout -- resources/`. |
| **Manual drift in `.agents/`** | Editing files directly under `.agents/skills/`. | **Edit `src/skills/` exclusively**. Run `./scripts/sync.sh` to mirror changes. |
| **`TypeError: stat: path should be string...`** | Sensor `audit(base, domain, inv)` called with dict in legacy `responses_file` positional slot. | Guard sensor signatures: if `isinstance(responses_file, dict)`, assign `inv = responses_file; responses_file = None`. Use `isinstance(arg, (str, bytes, os.PathLike))` before `os.path.exists()`. |
| **Schema validation error on `proactive_actions`** | Missing required fields in action dictionary or test fixtures. | Every action item MUST provide all 4 fields: `"id"`, `"title"`, `"summary"`, and `"priority"`. |
| **Schema validation error on root status** | Emitting `"ok"` or `"inconclusive"` at report root. | Root status must strictly be one of: `"complete"`, `"partial"`, or `"failed"`. |
| **False-negative finding suppression** | Suppressing entity schema defects when HTML `<title>` or OpenGraph tags exist. | Machine search engines require explicit Schema.org JSON-LD. Never suppress `MATERIAL_ENTITY_AMBIGUITY` just because HTML title tags are present. |
| **Sensor crash on empty crawl** | Target site unreachable or empty inventory passed. | Sensors must gracefully return `{"status": "inconclusive", "findings": [], "recommendations": []}`. Tests must accept `["ok", "inconclusive"]`. |
| **Terminal / subagent hanging** | Shell blocked on interactive process or background command. | Avoid persistent interactive shells. Run standalone commands with timeout or use direct file inspection. |

---

## 5. Specialist Sensor Interface Contract

Every sensor script (`*_check.py`):
```bash
python3 <skill_script>.py --site <url> [--inventory <inv.json>] [--state <state.json>] [--format json]
```

### Python API Signature
```python
def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None) -> Dict[str, Any]:
    """Execute diagnostic sensor against inventory.
    
    Returns:
        Dict matching {"status": "ok"|"inconclusive", "findings": [...], "recommendations": [...]}
    """
```

### Finding Object Structure
Every finding in `findings` must strictly provide:
- `id` *(string)*: Unique defect identifier (e.g., `AI_RETRIEVAL_BLOCKED`, `MATERIAL_ENTITY_AMBIGUITY`).
- `cause_id` *(string)*: Root cause key matching `audit-orchestrator-knowledge-base.md`.
- `category` *(string)*: Functional audit domain.
- `severity` *(enum)*: Strictly `"critical" | "high" | "medium" | "low"`.
- `confidence` *(enum)*: Strictly `"high" | "medium" | "low"`.
- `evidence` *(string | object)*: Concise diagnostic proof (`summary`, `scope`, `sources`).
- `suggested_action` *(object)*: Actionable mitigation with required `"summary"` and `"priority"`, plus `"technical_fix"`, `"creative_fix"`, and `"verification"`.

---

## 6. Draft-07 Report Schema Gate Invariants

All reports processed by `validate_report.py` must satisfy `report-schema.json`:

1. **Root Status:** Must be one of `["complete", "partial", "failed"]`.
2. **Proactive Actions:** Array elements must have `id`, `title`, `summary`, and `priority` (`"critical" | "high" | "medium" | "low"`).
3. **Summary Counts:** Non-negative integers for `total_findings`, `critical`, `high`, `medium`, and `low`.
4. **No Disallowed Additional Properties:** Strict validation is enforced on root and summary blocks. Do not introduce unauthorized top-level keys.

---

## 7. QA Pipeline & Verification Commands

All changes must pass the full QA verification suite prior to commit:

```bash
# 1. Run Complete Quality Assurance Suite
./scripts/qa_check.sh

# 2. Individual Scoped Checks (DO NOT run on repo root)
ruff check src/ tests/
flake8 src/ tests/ --max-line-length=140 --ignore=E402,E501,W503
mypy src/
pytest tests/ -q

# 3. Synchronize Runtime Mirror
./scripts/sync.sh

# 4. Build Marketplace Distribution Zip
./scripts/build.sh
```

---

## 8. Agent Behavioral Rules

### Mandatory:
- Author code strictly under `src/skills/` and tests under `tests/`.
- Run `./scripts/sync.sh` immediately after altering skill logic or manifests.
- Keep `SKILL.md` documents concise and below 500 lines; place extended tables in `references/`.
- Validate that helper functions accommodate argument inversion (e.g., `is_allowed(bot, url)` and `is_allowed(url, bot)`).
- Provide dual-track remediation (both `technical_fix` and `creative_fix`) for every diagnostic finding.

### Strictly Forbidden:
- **DO NOT** edit files inside `.agents/` or `build/` directly.
- **DO NOT** modify, format, or lint files in `resources/`.
- **DO NOT** import runtime `pip` packages in `src/skills/`.
- **DO NOT** execute redundant network crawls across sensors when `inv.json` exists.
- **DO NOT** commit cache files (`__pycache__`, `*.pyc`).
