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
| **`tests/`** | **Test Suite & Fixtures** | Unit (`tests/unit/`), integration (`tests/integration/`), system (`tests/system/`), fixtures (`tests/fixtures/`), and helpers (`tests/helpers/`). | Do not put runtime production logic in test helpers. Do not place re-export forwarders in root `tests/`. |
| **`.agents/skills/`** | **Runtime Agent Mirror** | **READ-ONLY / GENERATED**. Synced from `src/skills/` via `python scripts/sync.py`. | **NEVER edit directly.** Direct edits will be overwritten on sync. |
| **`resources/`** | **External Vendor References** | **FROZEN / READ-ONLY**. Reference repos and research papers. | **NEVER edit, format, or lint files here.** |
| **`docs/`** | **Architecture & Documentation** | System architecture, research syntheses, runbooks, and handoff guides. | Must remain zero-emoji and zero-LaTeX. |
| **`scripts/`** | **Automation & Tooling** | Build packaging (`build.py` / `build.sh`), runtime sync (`sync.py` / `sync.sh`), and QA verification (`qa_check.sh`). | Keep cross-platform compatible. |
| **`build/`** | **Packaging Staging** | **GENERATED**. Managed by `python scripts/build.py`. | Never commit manual files to `build/`. |

### Build & Repository Synchronization

Always build the distribution package and mirror `src/` to `.agents/` after any edit:

```bash
# Cross-platform (recommended)
python scripts/build.py
python scripts/sync.py

# POSIX shell (Linux/macOS only)
./scripts/build.sh
./scripts/sync.sh
```

---

## 3. Product Architecture & Production Invariants

When modifying or adding code to `src/skills/`, adhere strictly to these architectural constraints:

1. **Zero Runtime Dependencies:**
   - All runtime scripts inside `src/skills/` must use Python 3.9+ standard library ONLY (`urllib`, `socket`, `html.parser`, `xml.etree.ElementTree`, `json`, `heapq`, `gzip`, `zlib`, `re`, `argparse`, `math`, `time`).
   - Pip packages (`pytest`, `ruff`, `flake8`, `mypy`) are strictly developer tooling and must never be imported in `src/skills/`.
2. **No Headless Browsers:**
   - Zero Playwright, Puppeteer, Selenium, or Chromium binaries. Sensor analysis must remain lightweight, fast (< 5 min), and deterministic.
3. **Zero-Trust SSRF Protection:**
   - All network operations must flow through [`src/skills/web-scraper/scripts/safe_fetch.py`](file:///home/jayanth/CODE/projects/adobe-brand-visibility-skill/src/skills/web-scraper/scripts/safe_fetch.py).
   - Target IPs are resolved and validated before socket creation. Immediate abort on private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), cloud metadata (`169.254.169.254`), and carrier-grade NAT subnets.
4. **Single-Pass Acquisition Architecture:**
   - Crawling is performed strictly once by `web-scraper` (`acquire_inventory.py` / `run_scraper.py`), saving `inv.json`. All diagnostic sensors run offline against `inv.json` with zero redundant network overhead.
5. **Canonical Import Resolution:**
   - Specialist sensors locate the canonical `safe_fetch.py` dynamically via self-resolving path discovery:

     ```python
     SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
     SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
     for _p in (SCRIPT_DIR, SCRAPER_DIR):
         if os.path.isdir(_p) and _p not in sys.path:
             sys.path.insert(0, _p)
     ```

   - Never duplicate `safe_fetch.py` or create local shims.
6. **Draft-07 Schema Compliance:**
   - Output reports from `orchestrator.py` must validate cleanly against `src/skills/audit-orchestrator/references/report-schema.json`.
   - Every item in `proactive_actions` must provide all 4 required fields: `id`, `title`, `summary`, and `priority` (`critical` | `high` | `medium` | `low`).
   - Summary block counts must be non-negative integers.
   - Clean string values: no literal escaped newlines (`\n\n`), no raw Markdown tables, and no raw HTML markup inside JSON string properties (`technical_fix`, `creative_fix`, `evidence`, `summary`).
7. **Marketplace Distribution Standard:**
   - The distribution package `brand-ai-readiness-audit.zip` must unpack into a single root folder `brand-ai-readiness-audit/` containing `marketplace.json`, `README.md`, `LICENSE`, and `skills/` (the 8 skill folders).
   - Package size must remain <= 50 MB (current build is ~0.5 MB).
8. **Zero-Emoji & Zero-LaTeX Documentation Standard:**
   - Absolute zero emojis across all skill manifests, knowledge bases, docstrings, and markdown documentation.
   - Zero raw LaTeX mathematical syntax (no `\$`, `\$\$`, `\frac{}{}`, `\sum`). Format all math and formulas as clean plain text or unicode.
9. **Sensor-Brain Architecture & Anti-Shortcut Directive:**
   - Diagnostic scripts inside `src/skills/` are deterministic telemetry sensors providing raw empirical measurements.
   - The AI agent is the Cognitive Reasoning Brain: it must ingest empirical telemetry via `orchestrator.py --telemetry`, apply the 6-Layer Causal DAG, contextualize by business archetype, and author bespoke dual-track remediations.
   - The baseline runner (`orchestrator.py --format json` / `--baseline-only`) is strictly reserved for headless CI/CD automated test suites and must never be blindly forwarded to the user.

---

## 4. Skills Portfolio & Sensor Interface Contract

The suite consists of 8 modular skills coordinated by `audit-orchestrator`:

- **`audit-orchestrator`**: Master coordinator, causal synthesis, and Draft-07 report emission (`orchestrator.py`, `audit.py`, `assemble_report.py`, `causal_gate.py`, `validate_report.py`). Supports `--telemetry` mode for AI agent cognitive synthesis and `--baseline-only` for automated CI/CD.
- **`web-scraper`**: Single-pass acquisition and zero-trust SSRF fetcher (`safe_fetch.py`, `acquire_inventory.py`, `crawler/`).
- **Specialist Diagnostic Sensors (6)**: `discoverability-audit`, `entity-content-audit`, `fact-consistency-audit`, `corroboration-authority-audit`, `geo-content-audit`, `engagement-context-audit`.

### Sensor Programmatic Interface Contract

Every sensor script implements the standard interface:

```python
def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None) -> Dict[str, Any]:
    """Execute diagnostic sensor against inventory.
    
    Returns:
        Dict matching {"status": "ok"|"inconclusive", "findings": [...], "recommendations": [...]}
    """
```

### Knowledge Base & Check Catalogue Standard

- Every skill maintains its domain knowledge base strictly at `references/knowledge-base.md`. Never introduce fragmented satellite knowledge bases.
- The master 134-check catalogue lives in `src/skills/audit-orchestrator/references/checks.md` and `checks.json`, with domain subsets maintained in each specialist skill's `references/checks.md`.
- Architectural overviews, research citations, and handoff guides belong strictly in `docs/`.

---

## 5. Common Defect Prevention & Anti-Pattern Matrix

| Defect Class | Root Cause | Mandatory Guardrail / Resolution |
| :--- | :--- | :--- |
| **Agent Copy-Paste Anti-Pattern** | Blindly executing baseline runner (`orchestrator.py --format json`) and forwarding raw output to user. | **Enforce Anti-Shortcut Directive**. The agent is the diagnostic brain. Acquire inventory, collect telemetry via `--telemetry`, apply the 6-Layer Causal DAG, contextualize by business archetype, and author bespoke dual-track remediations. |
| **Dirty git diff in `resources/`** | Running formatters across repository root (`ruff check --fix .`). | **Target strictly `src/` and `tests/`**. `resources/` contains immutable third-party repos. If touched, revert immediately: `git checkout -- resources/`. |
| **Manual drift in `.agents/`** | Editing files directly under `.agents/skills/`. | **Edit `src/skills/` exclusively**. Run `python scripts/build.py` then `python scripts/sync.py` to mirror changes. |
| **Missing `safe_fetch` in sensors** | Direct execution without scraper on `sys.path`. | Sensor scripts must include `SCRAPER_DIR` in `sys.path` via dynamic relative path resolution. Never re-introduce duplicate shims. |
| **`TypeError: stat: path should be string...`** | Sensor `audit(base, domain, inv)` called with dict in legacy `responses_file` positional slot. | Guard sensor signatures: if `isinstance(responses_file, dict)`, assign `inv = responses_file; responses_file = None`. Use `isinstance(arg, (str, bytes, os.PathLike))` before `os.path.exists()`. |
| **Schema validation error on `proactive_actions`** | Missing required fields in action dictionary or test fixtures. | Every action item MUST provide all 4 fields: `"id"`, `"title"`, `"summary"`, and `"priority"`. |
| **Schema validation error on root status** | Emitting `"ok"` or `"inconclusive"` at report root. | Root status must strictly be one of: `"complete"`, `"partial"`, or `"failed"`. |
| **False-negative finding suppression** | Suppressing entity schema defects when HTML `<title>` or OpenGraph tags exist. | Machine search engines require explicit Schema.org JSON-LD. Never suppress `MATERIAL_ENTITY_AMBIGUITY` just because HTML title tags are present. |
| **Sensor crash on empty crawl** | Target site unreachable or empty inventory passed. | Sensors must gracefully return `{"status": "inconclusive", "findings": [], "recommendations": []}`. Tests must accept `["ok", "inconclusive"]`. |
| **Terminal / subshell hanging** | Shell blocked on interactive process or background command expecting EOF. | Always pass `< /dev/null` for command execution. Never leave interactive background shells running. |
| **Redundant test forwarders** | Placing stub test files in root `tests/` that forward to `tests/unit/`. | All test modules live natively under `tests/unit/`, `tests/integration/`, or `tests/system/`. |

---

## 6. Developer QA Pipeline & Verification Commands

All modifications must pass the complete QA suite before declaring work complete:

```bash
# 1. Complete Quality Assurance Suite (Ruff, Flake8, MyPy, Schemas, Pytest)
./scripts/qa_check.sh

# 2. Individual Scoped Checks (DO NOT run on repo root)
ruff check src/ tests/
flake8 src/ tests/ --max-line-length=140 --ignore=E402,E501,W503
MYPYPATH=src/skills:src/skills/audit-orchestrator/scripts:src/skills/web-scraper/scripts:src/skills/discoverability-audit/scripts:src/skills/entity-content-audit/scripts:src/skills/fact-consistency-audit/scripts:src/skills/corroboration-authority-audit/scripts:src/skills/geo-content-audit/scripts:src/skills/engagement-context-audit/scripts mypy --ignore-missing-imports src/
pytest tests/ -q

# 3. Build Marketplace Distribution Zip & Validate Package (cross-platform)
python scripts/build.py
python tests/validate_package.py brand-ai-readiness-audit.zip

# 4. Synchronize Runtime Mirror (cross-platform)
python scripts/sync.py

# POSIX shell alternatives (Linux/macOS)
./scripts/build.sh
./scripts/sync.sh
```

---

## 7. AI Coding Agent Operational Directives

### Mandatory Workflow

- Author code strictly under `src/skills/` and tests under `tests/`.
- Immediately run `python scripts/build.py` followed by `python scripts/sync.py` (or `./scripts/build.sh` and `./scripts/sync.sh`) after altering skill logic or manifests.
- Keep `SKILL.md` documents concise and structured according to the 14-section Production Standard Order. Extended reference material belongs in `references/`.
- Maintain unified knowledge bases per skill: avoid fragmented satellite files that cause context fatigue.
- Zero-LaTeX Markdown Standard: format all math, algorithms, and logic relations as clean plain text or unicode (no `\$`, `\$\$`, `\frac{}{}`, `\sum`, `\text{}`).
- Zero-Emoji Documentation Standard: never introduce emojis into manifests, knowledge bases, docstrings, or markdown files.
- Tool-Agnostic File Reading: In skill runbooks, instruct agents to use native file-reading tools; never embed shell `cat` commands.
- Transparent Pair Programming: Communicate directly, clearly, and concisely with the user as a senior software engineer. State assumptions, surface tradeoffs, and verify implementations with automated tests.

### Strictly Forbidden

- **DO NOT** edit files inside `.agents/` or `build/` directly.
- **DO NOT** modify, format, or lint files in `resources/`.
- **DO NOT** import runtime `pip` packages in `src/skills/`.
- **DO NOT** re-introduce duplicate shims (e.g. `safe_fetch.py` or `acquire_inventory.py`).
- **DO NOT** leave unresolved background processes running.
- **DO NOT** commit cache files (`__pycache__`, `*.pyc`).
