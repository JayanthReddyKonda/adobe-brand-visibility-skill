# AGENTS.md — Developer & AI Coding Agent Operating Specification

Operating specification and engineering manual for AI coding assistants and developers building, modifying, testing, and packaging the Adobe Brand Visibility & AI-Readiness multi-skill suite.

---

## 1. Core Engineering Principles (Coding Guidelines)

### 1. Think Before Coding
- **Don't assume. Don't hide confusion. Surface tradeoffs.**
- Before implementing, state assumptions explicitly. If multiple interpretations exist, present them.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what is confusing, and ask.

### 2. Simplicity First
- **Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked.
- No abstractions for single-use code.
- No unnecessary "flexibility" or "configurability".
- No error handling for impossible scenarios.
- If 50 lines solves it cleanly, do not write 200 lines. Ask: *"Would a senior engineer say this is overcomplicated?"*

### 3. Surgical Changes
- **Touch only what you must. Clean up only your own mess.**
- When editing existing code, do not "improve" adjacent code, comments, or formatting.
- Do not refactor things that are not broken.
- Match existing style.
- When your changes create unused imports, variables, or functions, remove them immediately.
- The test: Every changed line must trace directly to the requested task.

### 4. Goal-Driven Execution
- **Define success criteria. Loop until verified.**
- Transform tasks into verifiable milestones (reproduce issue -> implement surgical fix -> verify with automated tests).
- Run linting, typing, and test suites after changes before declaring completion.

---

## 2. Directory Topology & Mutation Boundaries

Strict directory boundaries must be maintained to prevent build contamination and test drift:

| Directory / File | Role | Modification Policy | Prohibitions |
| :--- | :--- | :--- | :--- |
| **`src/skills/`** | **Canonical Source of Truth** | All runtime code, skill manifests (`SKILL.md`), schemas, and references must be authored here. | Never import third-party pip packages here. Python stdlib only. |
| **`tests/`** | **Test Suite & Fixtures** | Unit, integration, and system tests. | Do not put runtime production logic in test helpers. |
| **`.agents/skills/`** | **Runtime Agent Mirror** | **READ-ONLY / GENERATED**. Synced from `src/skills/` via `scripts/sync.sh`. | **NEVER edit directly.** Direct edits will be overwritten on sync. |
| **`resources/`** | **External Vendor References** | **FROZEN / READ-ONLY**. Reference repos and research papers. | **NEVER edit, format, or lint files here.** |
| **`build/`** | **Packaging Staging** | **GENERATED**. Managed by `scripts/build.sh`. | Never commit manual files to `build/`. |

### Build & Repository Synchronization
Always build the distribution package and mirror `src/` to `.agents/` after any edit:
```bash
./scripts/build.sh
./scripts/sync.sh
```

---

## 3. Product Architecture & Production Invariants

When modifying or adding code to `src/skills/`, adhere strictly to these architectural constraints:

1. **Zero Runtime Dependencies:**
   - All runtime scripts inside `src/skills/` must use Python 3.9+ standard library ONLY (`urllib`, `socket`, `html.parser`, `xml.etree.ElementTree`, `json`, `heapq`, `gzip`, `zlib`, `re`, `argparse`).
   - Pip packages (`pytest`, `ruff`, `flake8`, `mypy`) are strictly developer tooling and must never be imported in `src/skills/`.
2. **No Headless Browsers:**
   - Zero Playwright, Puppeteer, Selenium, or Chromium binaries. Sensor analysis must remain lightweight, fast (< 5 min), and deterministic.
3. **Zero-Trust SSRF Protection:**
   - All network calls in runtime crawlers must validate and resolve target IPs before socket creation. Abort immediately on private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), metadata (`169.254.169.254`), and carrier-grade NAT subnets.
4. **Single-Pass Acquisition Architecture:**
   - Crawling is performed strictly once by `acquire_inventory.py` / `web-scraper`, saving `inv.json`. All diagnostic sensors run offline against `inv.json`.
5. **Draft-07 Schema Compliance:**
   - Output reports from `orchestrator.py` must validate cleanly against `src/skills/audit-orchestrator/references/report-schema.json`.
   - Every item in `proactive_actions` must have all 4 required fields: `id`, `title`, `summary`, and `priority` (`critical` | `high` | `medium` | `low`).
   - Summary block counts must be non-negative integers.
   - Clean string values: no literal escaped newlines (`\n\n`), no raw Markdown tables, and no raw HTML markup inside JSON string properties (`technical_fix`, `creative_fix`, `evidence`, `summary`).
6. **Marketplace Distribution Standard:**
   - The distribution package `brand-ai-readiness-audit.zip` must unpack into a single root folder `brand-ai-readiness-audit/` containing `marketplace.json`, `README.md`, `LICENSE`, and `skills/` (the 8 skill folders).
   - Package size must remain <= 50 MB (current build is ~330 KB).

---

## 4. Specialist Skills Architecture

The suite consists of 8 modular skills coordinated by `audit-orchestrator`:

| Skill Name | Functional Domain | Primary Sensor Script |
| :--- | :--- | :--- |
| **`audit-orchestrator`** | Master Runbook & Synthesis | `src/skills/audit-orchestrator/scripts/orchestrator.py` |
| **`web-scraper`** | SSRF Crawler & Extraction | `src/skills/web-scraper/scripts/acquire_inventory.py` |
| **`discoverability-audit`** | Search Engine & Bot Retrieval | `src/skills/discoverability-audit/scripts/discoverability_check.py` |
| **`entity-content-audit`** | Schema.org & Entity Identity | `src/skills/entity-content-audit/scripts/entity_content_check.py` |
| **`fact-consistency-audit`** | Cross-Page Consistency & Drift | `src/skills/fact-consistency-audit/scripts/fact_consistency_check.py` |
| **`corroboration-authority-audit`**| Identity Corroboration & Links | `src/skills/corroboration-authority-audit/scripts/corroboration_check.py` |
| **`geo-content-audit`** | Citation Probability (GEO/AEO) | `src/skills/geo-content-audit/scripts/geo_content_check.py` |
| **`engagement-context-audit`** | Post-Citation Continuity & Scent | `src/skills/engagement-context-audit/scripts/engagement_check.py` |

### Specialist Sensor Interface Contract
Every sensor script implements the standard interface:
```python
def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None) -> Dict[str, Any]:
    """Execute diagnostic sensor against inventory.
    
    Returns:
        Dict matching {"status": "ok"|"inconclusive", "findings": [...], "recommendations": [...]}
    """
```

### Finding Object Invariants
Every finding emitted into `findings` must strictly provide:
- `id` *(string)*: Unique defect identifier (e.g., `F-001`).
- `cause_id` *(string)*: Root cause key matching `knowledge-base.md`.
- `title` *(string)*: Clean descriptive defect title.
- `category` *(string)*: Functional audit domain.
- `severity` *(enum)*: Strictly `"critical" | "high" | "medium" | "low"`.
- `confidence` *(enum)*: Strictly `"high" | "medium" | "low"`.
- `evidence` *(string | object)*: Concise diagnostic proof without synthetic fabrication.
- `suggested_action` *(object)*: Actionable mitigation with required `"summary"` and `"priority"`, plus `"technical_fix"`, `"creative_fix"`, and `"verification"`.

---

## 5. Common Defect Prevention & Anti-Pattern Matrix

| Defect Class | Root Cause | Mandatory Guardrail / Resolution |
| :--- | :--- | :--- |
| **Dirty git diff in `resources/`** | Running formatters across repository root (`ruff check --fix .`). | **Target strictly `src/` and `tests/`**. `resources/` contains immutable third-party repos. If touched, revert immediately: `git checkout -- resources/`. |
| **Manual drift in `.agents/`** | Editing files directly under `.agents/skills/`. | **Edit `src/skills/` exclusively**. Run `./scripts/build.sh` then `./scripts/sync.sh` to mirror changes. |
| **`TypeError: stat: path should be string...`** | Sensor `audit(base, domain, inv)` called with dict in legacy `responses_file` positional slot. | Guard sensor signatures: if `isinstance(responses_file, dict)`, assign `inv = responses_file; responses_file = None`. Use `isinstance(arg, (str, bytes, os.PathLike))` before `os.path.exists()`. |
| **Schema validation error on `proactive_actions`** | Missing required fields in action dictionary or test fixtures. | Every action item MUST provide all 4 fields: `"id"`, `"title"`, `"summary"`, and `"priority"`. |
| **Schema validation error on root status** | Emitting `"ok"` or `"inconclusive"` at report root. | Root status must strictly be one of: `"complete"`, `"partial"`, or `"failed"`. |
| **False-negative finding suppression** | Suppressing entity schema defects when HTML `<title>` or OpenGraph tags exist. | Machine search engines require explicit Schema.org JSON-LD. Never suppress `MATERIAL_ENTITY_AMBIGUITY` just because HTML title tags are present. |
| **Sensor crash on empty crawl** | Target site unreachable or empty inventory passed. | Sensors must gracefully return `{"status": "inconclusive", "findings": [], "recommendations": []}`. Tests must accept `["ok", "inconclusive"]`. |
| **Terminal / subshell hanging** | Shell blocked on interactive process or background command expecting EOF. | Always pass `< /dev/null` for command execution. Never leave interactive background shells running. |

---

## 6. Developer QA Pipeline & Verification Commands

All modifications must pass the complete QA suite before declaring work complete:

```bash
# 1. Complete Quality Assurance Suite
./scripts/qa_check.sh

# 2. Individual Scoped Checks (DO NOT run on repo root)
ruff check src/ tests/
flake8 src/ tests/ --max-line-length=140 --ignore=E402,E501,W503
MYPYPATH=src/skills:src/skills/audit-orchestrator/scripts:src/skills/web-scraper/scripts:src/skills/discoverability-audit/scripts:src/skills/entity-content-audit/scripts:src/skills/fact-consistency-audit/scripts:src/skills/corroboration-authority-audit/scripts:src/skills/geo-content-audit/scripts:src/skills/engagement-context-audit/scripts mypy --ignore-missing-imports src/
pytest tests/ -q

# 3. Build Marketplace Distribution Zip
./scripts/build.sh

# 4. Synchronize Runtime Mirror
./scripts/sync.sh
```

---

## 7. AI Coding Agent Operational Directives

### Mandatory Workflow:
- Author code strictly under `src/skills/` and tests under `tests/`.
- Immediately run `./scripts/build.sh` followed by `./scripts/sync.sh` after altering skill logic or manifests.
- Keep `SKILL.md` documents concise and structured according to the 14-section Production Standard Order. Extended reference material belongs in `references/`.
- Maintain unified knowledge bases per skill: avoid fragmented satellite files that cause context fatigue.
- Zero-LaTeX Markdown Standard: format all math, algorithms, and logic relations as clean plain text or unicode (no `$`, `$$`, `\frac{}{}`, `\sum`, `\text{}`).
- Tool-Agnostic File Reading: In skill runbooks, instruct agents to use native file-reading tools; never embed shell `cat` commands.
- Transparent Pair Programming: Communicate directly, clearly, and concisely with the user as a senior software engineer. State assumptions, surface tradeoffs, and verify implementations with automated tests.

### Strictly Forbidden:
- **DO NOT** edit files inside `.agents/` or `build/` directly.
- **DO NOT** modify, format, or lint files in `resources/`.
- **DO NOT** import runtime `pip` packages in `src/skills/`.
- **DO NOT** leave unresolved background processes running.
- **DO NOT** commit cache files (`__pycache__`, `*.pyc`).
