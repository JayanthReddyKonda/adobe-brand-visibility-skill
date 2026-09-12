---
name: fact-consistency-audit
description: "Use when detecting cross-page factual contradictions, pricing discrepancies, outdated contact information, or legacy content drift across a website. Triggers on mentions of fact conflicts, pricing inconsistencies, hallucination risks, outdated copyright dates, or stale content. Constructs a multi-attribute first-party fact ledger to isolate verified contradictions."
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

# Fact Consistency & Lifecycle Audit Skill (Sensor-Brain Protocol)

| Component / Task | Execution Command | Output Contract | Role / Mode |
|---|---|---|---|
| **Offline Fact Ledger Sensor (Standard)** | `python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --format json` | `{status, findings, recommendations, coverage}` | Primary Offline Inspection |
| **Observed Assistant Hallucination Cross-Check** | `python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --responses assistant_outputs.json --format json` | `{status, findings, recommendations, coverage}` | AI Search Hallucination Verification |
| **State-Augmented Fact Audit** | `python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --state state.json --format json` | `{status, findings, recommendations, coverage}` | Multi-Turn Stateful Evaluation |
| **Direct Standalone Fact Probe** | `python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --format json` | `{status, findings, recommendations, coverage}` | Standalone Direct Probe |

> **Sensor-Brain Protocol Mandate:**
> - **Deterministic Read-Only Sensor:** `fact_consistency_check.py` constructs a normalized first-party fact ledger across all crawled routes, isolating strictly scoped commercial and operational attributes (prices, specs, contact info). When provided with observed AI assistant outputs (`--responses`), it detects discrepancies between first-party truth and AI hallucinated answers. It does not guess which conflicting first-party fact is true.
> - **Offline Sensor Execution:** Operates offline against the canonical `inv.json` site inventory. You must NEVER use built-in URL reading tools (`read_url_content`, `open_browser_url`) or issue redundant requests to the audited host.
> - **Cognitive Orchestrator:** The Master Orchestrator (`audit-orchestrator`) ingests detected contradictions, applies epistemic falsification (ruling out billing cycles or feature tiering), and synthesizes a single-source-of-truth factual reconciliation runbook.

Constructs a multi-attribute first-party fact ledger across sampled website pages. Detects verified commercial contradictions, product lifecycle conflicts (discontinued vs current), and legacy fact propagation.

---

> [!TIP]
> **Execution Context:** Assume your working directory is the repository root. All commands and file paths below are absolute relative to the root directory. Adapt shell commands (`python3`, `python`) to match your host operating system (Linux, macOS, or Windows). Always use forward slashes (`/`) for cross-platform file paths.

## Summary

Constructs a multi-attribute first-party fact ledger across website pages to detect cross-page factual contradictions, pricing discrepancies, outdated contact information, and legacy content drift. Isolates strictly scoped commercial attributes (entity, variant, currency, billing cycle) and optionally cross-references target facts against observed generative AI assistant outputs to identify citation hallucination risks.

## When to use

- AI search assistants (ChatGPT Search, Claude, Perplexity) hallucinate incorrect prices, features, or discontinued status for brand offerings.
- Verify that prices, specifications, and commercial terms are consistent across all first-party brand pages (e.g. `/pricing` vs `/features` vs product landing pages).
- Detect when obsolete or discontinued products are erroneously advertised as active or in-stock on secondary routes.
- Identify legacy brand slogans, obsolete contact details, or multi-year outdated copyright notices across unmaintained templates.
- Cross-check observed AI assistant responses (`--responses`) against first-party site inventory to isolate factual hallucinations.

---

## Inputs

- `--site <url>` (string, required): Target website URL or domain (e.g., `https://example.com`).
- `--inventory <path>` (string, optional): Path to pre-acquired canonical site inventory JSON payload (`inv.json`).
- `--state <path>` (string, optional): Path to global stateful knowledge graph JSON file.
- `--responses <path>` / `--observations <path>` (string, optional): Path to JSON file of observed AI assistant outputs to cross-check against site facts.
- `--format <json|markdown>` (enum, optional, default: `json`): Machine-readable output serialization format.

---

## Component Architecture & File Inventory

Every script and reference in this skill serves a distinct diagnostic role:

| Path | Type | Purpose & Agent Calling Role |
|---|---|---|
| `scripts/fact_consistency_check.py` | Sensor Script | Core measurement sensor extracting scoped facts, matching price intervals, isolating lifecycle conflicts, and cross-checking AI assistant responses. |
| `references/checks.md` | Reference Catalogue | Research specifications covering claim verification, date staleness, price consistency, and lifecycle contradictions. |
| `references/knowledge-base.md` | Reference KB | Comprehensive guide covering scoped entity extraction rules, price interval matching, product lifecycle drift detection, and first-party ledger construction. |
| `evals/evals.json` | Verification Fixtures | Test scenarios validating scoped price conflicts, discontinued vs current lifecycle detection, and copyright drift. |

---

## Cognitive Integration with Suite Skills

| Skill | Relationship & Flow Direction |
|---|---|
| **`web-scraper`** | Upstream provider. Provides canonical `inv.json` with multi-page text bodies and Schema.org offers. |
| **`audit-orchestrator`** | Master coordinator. Ingests fact consistency telemetry, applies Layer 3 Causal DAG evaluation, and synthesizes single-source-of-truth reconciliation runbooks. |
| **`entity-content-audit`** | Sibling sensor. Provides structured entities (Product, Offer, PriceSpecification) to correlate against visible DOM text assertions. |
| **`discoverability-audit`** | Preempting sensor. If routes are blocked or unrendered, fact extraction on those routes is skipped or flagged as inconclusive. |

---

## References & Documentation Library

Load these resources as needed during factual consistency checks:

### Core Knowledge Base & Check Catalogue (Load First)
- [Fact & Consistency Checks Reference](references/checks.md): Research specifications covering claim verification, date staleness, and cross-page consistency.
- [Fact Consistency Knowledge Base](references/knowledge-base.md): Scoped entity extraction rules, price interval matching, product lifecycle drift detection, and first-party ledger construction.


### Mandatory Domain Invariants & Evidence Rules
1. **Two Incompatible Assertions Rule:** Every contradiction finding MUST cite two exact incompatible assertions from collected inventory, identifying both artifacts (`artifact`), locators (`locator`), and verbatim quotes (`quote`). Never hypothesize a conflict without dual proof.
2. **Scope Binding:** Bind claims strictly to entity, variant, locale, currency, effective period, and source before comparison. Do NOT compare annual billing to monthly billing or different regional currencies.
3. **Paraphrases Are Not Contradictions:** Semantic restatements, marketing variations, and differing detail levels are not factual contradictions.
4. **Historical Truth Limits:** An older date alone does not establish staleness without verified historical evidence of an update.

---

## Procedure

### Step 1: Read Domain Knowledge Base & Reference Files (MANDATORY)

Read the specialist reference files using your native file reading capabilities (do NOT use bash `cat`):
- `skills/fact-consistency-audit/references/knowledge-base.md`
- `skills/fact-consistency-audit/references/checks.md`

### Step 2: Execution Command

Execute the fact ledger and consistency script with `--format json`:

```bash
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory inv.json --format json
```

Direct standalone execution:
```bash
python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --format json
```

---

### Step 3: Decision Protocol & Check Logic

1. **Scoped Price Contradictions (`FACT.CONSISTENCY.FIRST_PARTY_FACT_CONFLICT`):**
   - Flag a defect ONLY when two or more first-party pages state conflicting prices for the **same scoped entity** (e.g. "Velocity X9" is USD 5,499 on `/product/x9` but USD 4,999 on `/promo`).
   - **Do NOT compare distinct tiers:** A USD 10 Starter Plan and USD 50 Pro Plan share the attribute `price` but possess different entity scopes.
2. **Product Lifecycle Conflicts (`FACT.LIFECYCLE.DISCONTINUED_VS_CURRENT_CONFLICT`):**
   - Flag when a product is marked as `discontinued` or `out of production` on one page but listed as `in_stock` or `current` on another (Severity: `high`).
3. **Legacy Fact Propagation (`FACT.FRESHNESS.LEGACY_FACT_PROPAGATION`):**
   - Flag when copyright years differ by >= 2 years across active pages (e.g. 2022 on one route vs 2026 on another), indicating unmaintained legacy templates.
4. **Commercial Trial Terms Consistency (`CONFLICTING_COMMERCIAL_TERMS`):**
   - Flag when different trial durations (e.g. 14-day free trial on homepage vs 30-day trial on pricing route) are advertised across pages for the same product line (Severity: `high`).

---

## Output Format

Emits strictly valid JSON matching the schema with zero prose commentary:
`{status, findings[], recommendations[], coverage{}, limitations[]}`.
All string fields in emitted findings and recommendations must be clean, single-line or semicolon-delimited (` ; `), containing zero escaped literal newlines (`\n\n`) and zero raw Markdown tables.

---

## Gotchas & Error Handling

- **Strict Entity & Scope Matching:** Only flag price conflicts when facts share the identical entity, currency, billing interval, and product variant.
- **Tiered Pricing Tables:** Do not flag multiple distinct price tiers (e.g. Starter USD 49 vs Pro USD 99) on the same page as a factual conflict.
- **Footer Copyright Drift:** Varying copyright years across page templates should be emitted as a freshness recommendation, not a critical defect.
- **Currency & Billing Cycle Matching:** A price of USD 49/mo and USD 490/yr for the same tier is NOT a conflict; they represent different billing intervals. Only flag when currency, tier scope, and billing interval are identical but values differ.
- **Single-Page Evidence:** A contradiction must be observed across at least two distinct page URLs; a single page cannot contradict itself in this audit's scope.

---

## Security & SSRF Policy

Operates offline against canonical `inv.json`. All network fetch operations, pre-connect DNS resolution, and zero-trust SSRF sandboxing are enforced centrally by `web-scraper` (`safe_fetch.py`) and coordinated under the master suite policy in `audit-orchestrator`.
