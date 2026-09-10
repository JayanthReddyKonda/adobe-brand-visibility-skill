---
name: discoverability-audit
description: "Use when auditing whether AI retrieval engines like ChatGPT Search, Claude Search, Perplexity, and Google AI Overviews can crawl and index a website. Triggers on mentions of robots.txt, crawler access, AI bot blocking, searchbot permissions, noindex directives, canonical tags, or client-side rendering gaps. Evaluates RFC 9309 crawler matrices, meta directives, and raw HTML rendering completeness."
license: MIT
compatibility: ">=Python-3.9"
metadata:
  role: specialist
  parent: audit-orchestrator
  author: "Jayanth Reddy Konda"
allowed-tools:
  - Bash
  - Read
---

# Discoverability Audit Skill (Sensor-Brain Protocol)

| Component / Task | Execution Command | Output Contract | Role / Mode |
|---|---|---|---|
| **Offline Discoverability Sensor (Standard)** | `python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --format json` | `{status, findings, recommendations, coverage}` | Primary Offline Inspection |
| **State-Augmented Discoverability Audit** | `python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --state state.json --format json` | `{status, findings, recommendations, coverage}` | Multi-Turn Stateful Evaluation |
| **Direct Standalone Discoverability Probe** | `python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --format json` | `{status, findings, recommendations, coverage}` | Standalone Direct Probe |

> **Sensor-Brain Protocol Mandate:**
> - **Deterministic Read-Only Sensor:** `discoverability_check.py` is a pure measurement sensor. It inspects RFC 9309 crawler matrices across 16 AI retrieval and training bots, HTTP response codes, meta directives (`noindex`, `nofollow`, `noarchive`), canonical chains, XML sitemaps, and raw HTML extractability. It outputs observed empirical evidence without canned recommendation prose.
> - **Offline Sensor Execution:** Operates offline against the canonical `inv.json` site inventory. You must NEVER use built-in URL reading tools (`read_url_content`, `open_browser_url`) or issue redundant requests to the audited host.
> - **Cognitive Orchestrator:** The Master Orchestrator (`audit-orchestrator`) ingests this sensor's output, applies Layer 0 causal gating (suppressing downstream schema/GEO complaints if retrieval is blocked), simulates query strategies, and synthesizes bespoke dual-track fixes.

Evaluates the accessibility and indexing pipeline of a website for AI retrieval engines (ChatGPT Search, Claude Search, Perplexity AI, Google Search). Determines whether AI crawlers can fetch the site's content and whether initial HTML payloads carry extractable text.

---

> [!TIP]
> **Execution Context:** Assume your working directory is the repository root. All commands and file paths below are absolute relative to the root directory. Adapt shell commands (`python3`, `python`) to match your host operating system (Linux, macOS, or Windows). Always use forward slashes (`/`) for cross-platform file paths.

## Summary

Evaluates the technical discoverability and machine-readability pipeline of a brand website for AI retrieval engines. Deterministically audits 37 research checks across RFC 9309 crawler access rules, HTTP status barriers, meta robots directives, canonical fragmentation, XML sitemap indexation, and raw HTML extractability thresholds (< 25 words with mounting div containers).

## When to use

- Diagnose why AI search assistants (ChatGPT Search, Claude Search, Perplexity Pro, Google AI Overviews) cannot retrieve, crawl, or index a site's pages.
- Verify crawler access rules in `robots.txt`, distinguishing real-time retrieval bots (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) from training dataset collectors (`GPTBot`, `ClaudeBot`, `Google-Extended`).
- Detect client-side rendering (CSR) dependencies where primary text is missing from raw unrendered HTML.
- Validate canonical link consolidation, pagination loops, and noindex/noarchive directives.
- Deep-dive into specific routes flagged by orchestrator telemetry as blocked, unrendered, or canonical-mismatched.

---

## Inputs

- `--site <url>` (string, required): Target website URL or domain (e.g., `https://example.com`).
- `--inventory <path>` (string, optional): Path to pre-acquired canonical site inventory JSON payload (`inv.json`).
- `--state <path>` (string, optional): Path to global stateful knowledge graph JSON file.
- `--format <json|markdown>` (enum, optional, default: `json`): Machine-readable output serialization format.

---

## Component Architecture & File Inventory

Every script and reference in this skill serves a distinct diagnostic role:

| Path | Type | Purpose & Agent Calling Role |
|---|---|---|
| `scripts/discoverability_check.py` | Sensor Script | Core measurement sensor evaluating 37 discoverability checks across crawler access, HTTP headers, canonicals, sitemaps, and CSR extractability. |
| `references/checks.md` | Reference Catalogue | Full research specification covering checks A1-A5 (robots.txt matrix), B1-B5 (indexation & HTTP), C1-C6 (rendering & JS extractability), D1-D8 (XML sitemaps), and E1-E5 (encoding & syntax). |
| `references/knowledge-base.md` | Reference KB | Comprehensive technical reference on RFC 9309 longest-match precedence, user-agent matrix, CSR threshold heuristics, and international SEO. |
| `evals/evals.json` | Verification Fixtures | Test scenarios validating crawler matrix classification, noindex detection, and CSR gap identification. |

---

## Cognitive Integration with Suite Skills

| Skill | Relationship & Flow Direction |
|---|---|
| **`web-scraper`** | Upstream provider. Crawls target site under zero-trust SSRF safety and emits `inv.json` containing robots.txt rules, HTTP status codes, and raw HTML bodies. |
| **`audit-orchestrator`** | Master coordinator. Ingests discoverability telemetry; executes Layer 0 / Layer 1 Causal DAG suppression (preempts downstream entity/citability claims when retrieval is blocked); synthesizes Draft-07 report. |
| **`entity-content-audit`** | Sibling sensor. When discoverability identifies unrendered JavaScript shells (< 25 words), downstream entity extraction is flagged as unhydrated. |
| **`geo-content-audit`** | Sibling sensor. When robots.txt blocks AI search retrieval crawlers (`OAI-SearchBot`, `Claude-SearchBot`), citability scoring is suppressed on blocked routes. |

---

## References & Documentation Library

Load these resources as needed during discoverability checks:

### Core Knowledge Base & Check Catalogue (Load First — MANDATORY)
- [37 Discoverability Checks Reference](references/checks.md): Full research specification covering A1-A5 (robots.txt matrix), B1-B5 (indexation & HTTP directives), C1-C6 (rendering & JS extractability), D1-D8 (XML sitemaps & DTD protection), and E1-E5 (encoding & syntax).
- [Discoverability Knowledge Base](references/knowledge-base.md): AI crawler user-agent rules (RFC 9309), meta robots directives, canonical tag logic, raw HTML extractability thresholds, and International SEO & Localization architecture (Section 7).

## Procedure

### Step 1: Read Domain Knowledge Base & Checks (MANDATORY)

Read the specialist reference files using your native file reading capabilities (do NOT use bash `cat`):
- `skills/discoverability-audit/references/checks.md`
- `skills/discoverability-audit/references/knowledge-base.md`

### Step 2: Execution Command

Execute the deterministic extraction script using the shared inventory and `--format json`:

```bash
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory inv.json --format json
```

Direct standalone execution:
```bash
python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --format json
```

---

### Step 3: Decision Protocol & Check Logic

1. **HTTP Status Verification (`DISCOVERY.ACCESS.AI_RETRIEVAL_BLOCKED`):**
   - If root landing URL returns HTTP 4xx or 5xx: report `critical` severity.
   - If network is unreachable or DNS fails: return `status: "inconclusive"`. Never report an unreachable target as clean.
2. **RFC 9309 Crawler Matrix Analysis:**
   - **Retrieval Crawlers** (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `anthropic-ai`): Disallow rule -> `critical` / `high` finding (`AI_RETRIEVAL_BLOCKED`).
   - **Training Bots** (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`): Disallow rule -> `info` / `low` observation under training governance (never a critical retrieval failure).
   - **Precedence Rule:** Specific user-agent groups take strict precedence over wildcard `User-agent: *` groups.
3. **Noindex & Directive Analysis (`DISCOVERY.ACCESS.NOINDEX_EXCLUSION`):**
   - Check `<meta name="robots">` and `X-Robots-Tag` headers across all crawled pages. Presence of `noindex` or `none` on public commercial routes -> `critical` finding.
4. **Canonical Consolidation (`DISCOVERY.DISCOVERY_PATH.CANONICAL_FRAGMENTATION`):**
   - If `<link rel="canonical">` points to an external un-audited host -> `medium` finding.
5. **Initial HTML Extractability (`DISCOVERY.REPRESENTATION_AVAILABILITY.RENDERED_CONTENT_GAP`):**
   - If visible text in raw HTML < 25 words and an unrendered SPA root (`<div id="root|app">`) is present -> `high` severity rendering risk indicator. Computes `average_page_snr` (and legacy `signal_to_noise_ratio`) metrics to evaluate raw text-to-code density.

6. **Internationalization & Hreflang Validation (`DISCOVERY.HREFLANG.INVALID_TARGET`):**
   - Validates `<link rel="alternate" hreflang="...">` declarations across all crawled routes against ISO 639-1 / ISO 3166-1 standards and checks for broken target URLs.
7. **Machine Discoverability Manifests (`DISCOVERY.MANIFEST.MACHINE_READABLE_ABSENT`):**
   - Evaluates `/llms.txt`, `/pricing.md`, `ai-plugin.json`, and `security.txt` availability, emitting proactive recommendations for missing manifests.

---

## Output Format

Emits strictly valid JSON matching the schema with zero prose commentary:
`{status, findings[], recommendations[], observations[], coverage{}, limitations[]}`.
All string fields in emitted findings and recommendations must be clean, single-line or semicolon-delimited (` ; `), containing zero escaped literal newlines (`\n\n`) and zero raw Markdown tables.

---

## Gotchas & Error Handling

- Do NOT flag training bot blocks (`GPTBot`, `ClaudeBot`) as critical AI search failures.
- Do NOT flag missing `llms.txt` as a defect (it is an optional discovery enhancement file).
- Do NOT report missing structured data in this skill (owned by `entity-content-audit`).
- **robots.txt 404 = allow-all:** An absent robots.txt file means all bots are permitted under RFC 9309. Never flag absence as a crawler block.
- **robots.txt 5xx = fail-closed:** A server error on robots.txt must be treated as `Disallow: /` for all bots.
- **Network unreachable is `inconclusive`:** If DNS fails or the connection times out, return `status: "inconclusive"`. Never report an unreachable target as a passing clean score.

---

## Security & SSRF Policy

Operates offline against canonical `inv.json`. All network fetch operations, pre-connect DNS resolution, and zero-trust SSRF sandboxing are enforced centrally by `web-scraper` (`safe_fetch.py`) and coordinated under the master suite policy in `audit-orchestrator`.
