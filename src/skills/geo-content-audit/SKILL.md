---
name: geo-content-audit
description: "Use when auditing web content for Generative Engine Optimization (GEO) and LLM citation selection based on Princeton KDD 2024 and AutoGEO research. Triggers on requests regarding GEO, Generative Engine Optimization, AI citation probability, answer engine optimization, causal conjunctions, statistical evidence density, or passage chunking to maximize ChatGPT, Perplexity, and Claude citations."
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

# Generative Engine Optimization (GEO) Audit Skill (Sensor-Brain Protocol)

| Component / Task | Execution Command | Output Contract | Role / Mode |
|---|---|---|---|
| **Offline GEO & Citability Sensor (Standard)** | `python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --format json` | `{status, findings, recommendations, page_improvement_plans}` | Primary Offline Inspection |
| **State-Augmented GEO Audit** | `python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --state state.json --format json` | `{status, findings, recommendations, page_improvement_plans}` | Multi-Turn Stateful Evaluation |
| **Direct Standalone GEO Probe** | `python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --format json` | `{status, findings, recommendations, page_improvement_plans}` | Standalone Direct Probe |

> **Sensor-Brain Protocol Mandate:**
> - **Deterministic Read-Only Sensor:** `geo_content_check.py` measures text quotability, answer density, heading/chunk alignment, statistical metrics, attributed quotes, and causal conjunction density across the 9 empirical Princeton KDD 2024 / AutoGEO vectors. It generates deterministic `page_improvement_plans` with 120–180 word passage chunking models without calling LLMs.
> - **Offline Sensor Execution:** Operates offline against the canonical `inv.json` site inventory. You must NEVER use built-in URL reading tools (`read_url_content`, `open_browser_url`) or issue redundant requests to the audited host.
> - **Cognitive Orchestrator:** The Master Orchestrator (`audit-orchestrator`) ingests citability metrics, executes simulated assistant query strategies, and synthesizes bespoke, information-dense passage chunking and explanatory rewrites.

Evaluates HTML content for AI citation and retrieval-augmented generation (RAG) extractability based on empirical Generative Engine Optimization research (Aggarwal et al., Princeton KDD 2024, arXiv:2311.09735; and Wu et al., CMU AutoGEO, arXiv:2510.11438 preprint). Determines whether content provides the causal mechanisms, statistical evidence, and structured definitions required for LLM citation.

---

> [!TIP]
> **Execution Context:** DO NOT assume your working directory contains a `skills/` folder directly. The marketplace may be installed in a nested directory like `.agents/skills/` or `src/skills/`. Resolve the root path before running commands. Always adapt shell commands (`python3`, `python`) to match your host operating system and use forward slashes (`/`) for cross-platform file paths.

## Summary

Audits website content against empirical Generative Engine Optimization (GEO) and retrieval-augmented generation (RAG) extractability benchmarks. Scores 9 empirical vectors (Princeton KDD 2024 and AutoGEO): in-depth causal mechanisms (+28% preference), statistical evidence density (+40% lift), attributed expert quotations (+40.9% lift), BLUF top-30% placement, standalone FAQ penalties (-5.7%), keyword stuffing perplexity degradation, and generates actionable page improvement plans.

## When to use

- AI search assistants (ChatGPT Search, Perplexity Pro, Claude) fail to cite, quote, or summarize a brand's product, feature, or service pages.
- Marketing copy relies on superficial superlative assertions rather than mechanistic explanations ("how" and "why" causal conjunctions).
- Content is buried or structured poorly for retrieval-augmented generation chunking windows (120–180 words).
- Detect standalone FAQ penalties where questions are answered without supporting empirical evidence (code, stats, comparison tables).
- Identify excessive keyword density (> 4.5%) degrading neural embedding perplexity in generative models.
- Deep-dive into citability scores and retrieve deterministic `page_improvement_plans` for specific key landing pages.

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
| `scripts/geo_content_check.py` | Sensor Script | Core measurement sensor evaluating 9 Princeton KDD 2024 / AutoGEO vectors, calculating citability scores, and synthesizing deterministic `page_improvement_plans`. |
| `references/checks.md` | Reference Catalogue | Research specifications covering checks N1-N15 (self-contained answers, answer-first positioning, numbers vs vague claims, attribution, quotations, and fluency). |
| `references/knowledge-base.md` | Reference KB | Benchmark reference covering Princeton KDD 2024 lifts, 134-167 word chunking math, causal conjunction cheatsheets, comparison table patterns, and AI writing detection. |
| `evals/evals.json` | Verification Fixtures | Test scenarios validating causal conjunction scoring, statistical density detection, standalone FAQ penalties, and page improvement plan generation. |

---

## Cognitive Integration with Suite Skills

| Skill | Relationship & Flow Direction |
|---|---|
| **`web-scraper`** | Upstream provider. Provides clean Trafilatura-grade markdown and DOM blocks from `inv.json` for passage chunking. |
| **`audit-orchestrator`** | Master coordinator. Ingests citability vectors, maps findings across the 6-Layer Causal DAG, and synthesizes engine-specific citation guidance (ChatGPT, Claude, Perplexity, Google AIO). |
| **`discoverability-audit`** | Preempting sensor. If AI retrieval bots are blocked in robots.txt or pages require client-side JS, citability complaints on those routes are suppressed as symptoms of Layer 0/1. |
| **`engagement-context-audit`** | Downstream bridge. High-probability citation passages identified by GEO must match above-the-fold viewport content to prevent referral bounce. |

---

## References & Documentation Library

Load these resources as needed during GEO content checks:

### Core Knowledge Base & Check Catalogue (Load First — MANDATORY)
- [GEO & Content Quality Checks Reference](references/checks.md): Research specifications covering N1-N15 (self-contained answers, answer-first positioning, numbers vs vague claims, attribution, quotations, and fluency).
- [GEO Content Knowledge Base](references/knowledge-base.md): Princeton KDD 2024 / AutoGEO benchmarks, 134–167 word optimal chunk scoring, causal conjunction cheatsheets, comparison table patterns, and AI Writing Detection & Natural Content Patterns (Section 9).


### Mandatory Domain Invariants & Non-Fabrication Rules
1. **Zero Synthetic Fabrication:** Never invent numbers, metrics, statistics, customer testimonials, quotes, credentials, or third-party sources to satisfy a GEO recommendation.
2. **Preserve Factual Qualifiers:** When restructuring answers or passages, preserve all caveats, scope limitations, pricing conditions, and geographic qualifiers.
3. **Grounded Answer Extraction:** Extract actual answer gaps from observed content (e.g. replacing a vague marketing superlative with an existing supported specification).
4. **No Guaranteed Uplift:** Empirical GEO vectors improve machine readability and selection probability, but cannot promise guaranteed ranking or citation.

---

## Procedure

### Step 1: Read Domain Knowledge Base & Checks (MANDATORY)

Read the specialist reference files using your native file reading capabilities (do NOT use bash `cat`):
- `skills/geo-content-audit/references/knowledge-base.md`
- `skills/geo-content-audit/references/checks.md`

### Step 2: Execution Command

Execute the deterministic GEO evaluation script using the shared inventory and `--format json`:

```bash
python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory inv.json --format json
```

Direct standalone execution:
```bash
python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --format json
```

---

### Step 3: Decision Protocol & Check Logic

1. **In-Depth Causal Mechanisms (`CONTENT.SHALLOW_COVERAGE.MISSING_IN_DEPTH_MECHANISMS`):**
   - Evaluates content pages (`product_detail`, `article`, `pricing`) for word-bounded causal conjunctions ('how', 'why', 'because', 'therefore', 'allows', 'enables', 'results in').
   - If depth score < 2 on a substantive page: emit a finding (`MISSING_IN_DEPTH_MECHANISMS`, Severity: `medium`, Confidence: `high`).
   - *Rationale (Princeton KDD 2024):* Generative engines strongly prefer sources providing explanatory mechanisms over surface-level marketing statements (+28% selection preference).

2. **Quantifiable Evidence Density (`CONTENT.RETRIEVAL_OPTIMIZATION.LACK_OF_SPECIFIC_EVIDENCE`):**
   - Scans text for numerical metrics, percentages, dollar figures, and dates.
   - If a substantive page lacks specific statistical evidence: emit a proactive **recommendation** (`priority: low`).
   - *Rationale (Princeton KDD 2024):* Adding verifiable numbers and statistics increases LLM citation likelihood by **+40%**.

3. **Semantic Structure & Answer Blocks (Advisory GEO):**
   - For product pages: flags absence of semantic `<table>` and `<ul>`/`<ol>` elements as an advisory extractability recommendation.
   - For informational/article pages: flags absence of question-oriented headings (`<h2>What is...</h2>`, `<h2>How does...</h2>`) as a recommendation to adopt FAQ/direct answer formatting.

4. **Zhang et al. 2026 Evidence Genres & Standalone FAQ Deficit (`CONTENT.STANDALONE_FAQ_DEFICIT`):**
   - Audits the 5 high-influence evidence genres: Code (+76.9%), Statistics (+61.6%), Definition Copulas (+57.3%), Comparison Tables (+55.3%), and Procedural Steps (+41.2%).
   - Flags `STANDALONE_FAQ_DEFICIT` (Severity: `medium`, Confidence: `high`) when pages use isolated Q&A/FAQ format without supporting empirical evidence (code, stats, or comparison tables), which research proves incurs an empirical -5.7% citation penalty.

5. **Keyword Stuffing & Neural Perplexity Degradation (`CONTENT.KEYWORD_STUFFING_DEGRADATION.EXCESSIVE_KEYWORD_DENSITY`):**
   - Evaluates non-stopword token frequencies across substantive pages (>= 150 words).
   - If any individual content word exceeds 4.5% term frequency, emits `EXCESSIVE_KEYWORD_DENSITY` (Severity: `medium`, Confidence: `high`).
   - *Rationale:* Unnatural keyword repetition degrades neural embedding perplexity and incurs an empirical -8.3% to -10% citation degradation in LLMs.

6. **BLUF Top-30% Attention Primacy (`CONTENT.CONTEXT_PLACEMENT_DEGRADATION`):**
   - Verifies whether core definitional propositions or commercial answers are stated in the top 30% / first 250 words of content.
   - If missing on substantive content, emits `CONTEXT_PLACEMENT_DEGRADATION` (Severity: `medium`, Confidence: `high`).
   - *Rationale (Stanford "Lost in the Middle", Liu et al. 2023):* Research indicates a disproportionate share of citations occur in the top portion of content; middle-buried answers may experience lower retrieval recall.

7. **Attributed Expert Quotations (`PROACTIVE.GEO.ATTRIBUTED_EXPERT_QUOTES.001`):**
   - Checks for quotations attributed to named domain authorities or credentialed specialists (Dr., PhD, MD, Professor, Chief Scientist).
   - *Rationale (Princeton KDD 2024):* Attributed Quotations yield the single highest citation lift (+40.9% PAWC boost) among all tested optimization vectors.

8. **Deterministic Page-Level Content Improvement Plans (`page_improvement_plans`):**
   - For each substantive evaluated page, derives a deterministic, actionable remediation plan:
     * Current dimension scores across Answer Block Quality, Self-Containment, Mechanistic Depth, Statistical Density, Table/List Formatting, Hedge Control, and FTR.
     * Evidence genres analysis, attributed quotation coverage, BLUF placement, and keyword density diagnostics.
     * Concrete gap analysis benchmarking against empirical thresholds (e.g., FTR >= 0.080, hedge density <= 0.5%, depth score >= 3, max keyword density <= 4.0%).
     * Prioritized action tracks: `immediate_structural_actions`, `textual_modifications`, and `passage_chunking_plan` (120–180 word modular sections).
     * Mandatory epistemic qualification on every plan.

9. **Credentialed Author Attribution (`PROACTIVE.GEO.CREDENTIALED_AUTHOR_ATTRIBUTION.001`):**
   - Scans declared authors in metadata for academic and professional credentials (MD, PhD, Lead Architect, Chief Scientist, Senior Director). Emits proactive E-E-A-T recommendation when credentialed attribution can maximize Claude and Perplexity trust.

10. **Commercial CTA Intrusion in Informational Content (`COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT`):**
    - Flags informational or educational guides containing >= 4 commercial conversion CTAs (`is_commercial_cta`), which degrades LLM citation probability due to commercial intent penalties.

---

## Output Format

Emits strictly valid JSON matching the schema with zero prose commentary:
`{status, findings[], recommendations[], observations[], page_improvement_plans[], coverage{}, limitations[]}`.
All string fields in emitted findings, recommendations, and improvement plans must be clean, single-line or semicolon-delimited (` ; `), containing zero escaped literal newlines (`\n\n`) and zero raw Markdown tables.

---

## Gotchas & Error Handling

- **Static Heuristics vs Live Citations:** Citability scores and improvement plans are derived deterministically from empirical static text heuristics (Princeton KDD 2024, AutoGEO, C-SEO Bench). They evaluate linguistic and informational citability readiness, not live search engine citation logs or dynamic LLM inference results.
- **Do NOT flag transactional pages** (login, cart, checkout, account settings) for lack of explanatory mechanisms or statistics.
- **Do NOT flag short contact pages** with standard headers as shallow content.
- **Do NOT emit heuristic tag absence** (e.g. missing `<table>`) as a defect finding; tag absence is strictly a proactive recommendation.
- **Score thresholds are soft signals:** A depth score < 2 on a single page is a finding; it is not a guarantee the page will be excluded from AI citations.

---

## Security & SSRF Policy

Operates offline against canonical `inv.json`. All network fetch operations, pre-connect DNS resolution, and zero-trust SSRF sandboxing are enforced centrally by `web-scraper` (`safe_fetch.py`) and coordinated under the master suite policy in `audit-orchestrator`.
