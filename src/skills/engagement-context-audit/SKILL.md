---
name: engagement-context-audit
description: "Use when evaluating visitor orientation, information scent, and intent-handoff continuity for traffic arriving from AI search citations. Triggers on mentions of visitor bounce, information scent, H1 alignment, CTA reachability, post-citation continuity, landing page orientation, or AI referral drop-off. Evaluates above-the-fold clarity, heading scent, and destination friction."
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

# Engagement & Context Continuity Audit Skill (Sensor-Brain Protocol)

| Component / Task | Execution Command | Output Contract | Role / Mode |
|---|---|---|---|
| **Offline Engagement Sensor (Standard)** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format json` | `{status, findings, recommendations, engagement_mode, coverage}` | Primary Offline Inspection |
| **Target Route Engagement Audit** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --url https://example.com/pricing` | `{status, page_metrics, findings, recommendations}` | Single-Route Engagement Audit |
| **Simulated Referral Query Scent Test** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --referrer-query "cloud backup enterprise pricing"` | `{status, referrer_query, evaluations}` | Intent-to-Landing Scent Test |
| **Above-the-Fold Viewport Only** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --viewport-only` | `{status, viewport_records, average_cta_reachability, ...}` | Fast Viewport & CTA Inspection |
| **First-Party Analytics Corroboration** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --analytics analytics.json --format json` | `{status, findings, recommendations, engagement_mode, analytics_summary}` | Dual-Track Empirical Audit |
| **State-Augmented Engagement Audit** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --state state.json --format json` | `{status, findings, recommendations, engagement_mode, coverage}` | Multi-Turn Stateful Evaluation |
| **Direct Standalone Engagement Probe** | `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --format json` | `{status, findings, recommendations, engagement_mode, coverage}` | Standalone Direct Probe |

> **Sensor-Brain Protocol Mandate:**
> - **Clean Skill Isolation:** This skill is strictly isolated to post-citation visitor orientation, information scent, and intent-handoff continuity. Only this skill invokes `scripts/engagement_check.py`.
> - **Helper Sensor (Problem Telemetry Only):** `engagement_check.py` is an empirical helper sensor. It measures orientation proxies, H1 semantic scent, viewport answer anchoring, and CTA reachability friction. When supplied with `--analytics`, it correlates static UX friction against observed bounce rate and dwell time data. It reports only objective layout measurements and friction points without doing the cognitive work.
> - **LLM Cognitive Discovery & Generation:** The AI Agent is the reasoning brain. In addition to reviewing automated UX friction scores, the agent directly inspects `inv.json` (evaluating hero H1 scent against common referral queries, inspecting buttons for missing text labels or inert `#` targets, identifying visual clipping/layout friction) and `telemetry.json`. The agent discovers and authors its OWN bespoke engagement findings, proactive actions, and dual-track suggestions (H1 rewrites, accessible CTA targets, viewport answer anchoring) in addition to what the script detected.

Evaluates the above-the-fold visitor experience, heading information scent, destination reachability, and intent continuity for visitors referred from AI search answers. Detects content and navigation friction that causes visitor bounce.

---

> [!TIP]
> **Execution Context:** DO NOT assume your working directory contains a `skills/` folder directly. The marketplace may be installed in a nested directory like `.agents/skills/` or `src/skills/`. Resolve the root path before running commands. Always adapt shell commands (`python3`, `python`) to match your host operating system and use forward slashes (`/`) for cross-platform file paths.

## Summary

Evaluates visitor orientation, information scent, and intent-handoff continuity for traffic arriving from AI search citations (ChatGPT Search, Claude, Perplexity Pro). Evaluates the 4-question orientation test above the fold, H1 semantic intent alignment, viewport answer anchoring (top 600px), destination navigation reachability, and conversion CTA proximity. Supports dual-track cross-correlation when first-party web analytics are provided.

## When to use

- AI-referred visitors experience high bounce rates or immediate drop-off after clicking citations.
- Evaluate whether landing pages immediately answer the 4-question orientation test (What is this? Who is it for? Why is it relevant? What can I do next?).
- Audit heading hierarchies and navigation reachability to core brand destinations (Pricing, Products, Documentation, Contact).
- Diagnose generic H1 tags ("Welcome", "Home") that break semantic information scent.
- Detect buried conversion actions preceded by excessive auxiliary interactive elements (Reachability Index).
- Correlate static UX friction with first-party traffic data via `--analytics`.

---

## Inputs

- `--site <url>` (string, required): Target website URL or domain (e.g., `https://example.com`).
- `--inventory <path>` (string, optional): Path to pre-acquired canonical site inventory JSON payload (`inv.json`).
- `--url <route>` (string, optional): Target URL route to scope engagement and continuity evaluation.
- `--referrer-query <query>` (string, optional): Simulate AI search citation referral query and test intent-to-landing scent and missing query terms.
- `--viewport-only` (flag, optional): Inspect strictly above-the-fold viewport elements and CTA reachability across routes.
- `--state <path>` (string, optional): Path to global stateful knowledge graph JSON file.
- `--analytics <path_or_json>` (string, optional): Path to first-party web analytics JSON/CSV file or raw JSON string with route-level bounce/dwell data.
- `--format <json|markdown>` (enum, optional, default: `json`): Machine-readable output serialization format.

---

## Component Architecture & File Inventory

Every script and reference in this skill serves a distinct diagnostic role:

| Path | Type | Purpose & Agent Calling Role |
|---|---|---|
| `scripts/engagement_check.py` | Sensor Script | Core measurement sensor evaluating 4-question orientation, H1 information scent, viewport answer anchoring, CTA reachability, and analytics correlation. |
| `references/checks.md` | Reference Catalogue | Research specifications covering checks I1-I2 (deep-link stability and parameter probes) and J1-J10 (identity, navigability, prominence, conversion friction, recovery). |
| `references/knowledge-base.md` | Reference KB | Comprehensive SXO guide covering intent handoffs, entity-to-H1 scent rules, CTA reachability index formula, and first-party analytics ingestion schemas. |
| `evals/evals.json` | Verification Fixtures | Test scenarios validating low information scent detection, CTA reachability index calculations, and analytics cross-correlation. |

---

## Cognitive Integration with Suite Skills

| Skill | Relationship & Flow Direction |
|---|---|
| **`web-scraper`** | Upstream provider. Provides DOM elements, H1/H2 tags, interactive elements, and body text via `inv.json`. |
| **`audit-orchestrator`** | Master coordinator. Ingests engagement telemetry; correlates orientation friction against Layer 5 intent handoffs; gates synthesis via `causal_gate.py`. |
| **`geo-content-audit`** | Sibling sensor. Matches top cited claims from GEO against viewport content to detect orientation shock (`VIEWPORT_ANSWER_ABSENCE`). |
| **`entity-content-audit`** | Sibling sensor. Entity names established in Schema.org must be anchored in hero headings to maintain information scent (`LOW_INFORMATION_SCENT`). |

---

## References & Documentation Library

Load these resources as needed during engagement context checks:

### Core Knowledge Base & Check Catalogue (Load First)
- [Bridge & Engagement Checks Reference](references/checks.md): Research specifications covering I1-I2 (deep-link stability and parameter probes) and J1-J10 (identity, navigability, prominence, conversion friction, and recovery).
- [Engagement Context Knowledge Base](references/knowledge-base.md): Master knowledge base covering state and validation protocols (Checks I1-I2, J1-J10), Section 4 intent-handoff structure specifications, entity-to-H1 information scent evaluation, commercial intent CTA reachability, first-party analytics ingestion, and post-referral bounce prevention.


### Mandatory Domain Invariants & Evidence Rules
1. **Deep-Link Continuity (I1):** Deep links must preserve the same core content unit upon fresh, unauthenticated reload. Query URLs are valid candidates.
2. **Inert Parameter Probes (I2):** Parameter probes must compare baseline/probe/baseline responses; dynamic variation or personalization is not a defect.
3. **404 Recovery Affordances (J9):** 404 error pages must inventory navigation and recovery links in raw source HTML.
4. **Single Band Precedence:** Issues providing dual benefits (e.g. discoverability and engagement) receive one highest justified severity band, never additive scores.

---

## Procedure

### Step 1: Read Domain Knowledge Base & Reference Files (MANDATORY)

Read the specialist reference files using your native file reading capabilities (do NOT use bash `cat`):
- `skills/engagement-context-audit/references/knowledge-base.md` (Sections 1–9, Intent Handoff & SXO Rubrics)
- `skills/engagement-context-audit/references/checks.md`

### Step 2: Execution Command

Execute the engagement and intent continuity script with `--format json`:

```bash
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format json
```

Specialist forensic options:
```bash
# Simulate AI search referral query to evaluate intent scent and landing alignment
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --referrer-query "best enterprise security software"

# Inspect strictly above-the-fold viewport elements (top 600px / 150w) and CTA reachability
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --viewport-only

# Scope continuity evaluation to specific target route
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --url https://example.com/landing

# Correlate heuristic UX friction with first-party route analytics
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --analytics analytics.json --format json

# Emit readable markdown summary
python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory inv.json --format markdown
```

---

### Step 3: Decision Protocol & Check Logic

1. **Multi-Signal 5-Second Orientation (`EXPERIENCE.CONTINUITY.LOW_INFORMATION_SCENT`):**
   - If a content-bearing page lacks an `<h1>`, lacks descriptive subheadings (`<h2>`), AND has an uninformative `<title>` -> flag `LOW_INFORMATION_SCENT` (Severity: `medium`).
   - If an `<h1>` exists but consists of generic filler ("Welcome", "Home", "Main Page") -> flag `LOW_INFORMATION_SCENT` (Severity: `low`).
   - **Do NOT flag 0 H1 as a high/medium bounce defect** if `<title>` and hero copy clearly orient the visitor.
2. **Destination Reachability (`EXPERIENCE.CONTINUITY.DESTINATION_NAVIGATION_FRICTION`):**
   - Flag when a landing page has fewer than 3 navigation links and omits discoverable pathways to core brand destinations (Pricing, Products, Documentation, Contact).
3. **Intent-to-Landing Match (`EXPERIENCE.CONTINUITY.INTENT_TO_LANDING_MISMATCH`):**
   - Flag when a specialized landing route (e.g. `/pricing`) fails to expose core expected commercial answers (price figures, plan tiers, starting ranges) above the fold.
4. **Viewport Answer Anchoring (`EXPERIENCE.CONTINUITY.VIEWPORT_ANSWER_ABSENCE`):**
   - Evaluates whether the top 600px viewport (first 2 paragraphs / first 150 words) anchors the specific core propositions (prices, product functionality, direct definitions).
   - If decorative banners push answers below the fold, flag `VIEWPORT_ANSWER_ABSENCE` (Severity: `medium`, Confidence: `high`).
5. **CTA Reachability Index & Commercial Continuity (`EXPERIENCE.CONTINUITY.CTA_REACHABILITY_FRICTION`):**
   - Evaluates the order of interactive DOM elements and structured action items (`ctas` and `nav_link_texts` from inventory).
   - If the first commercial conversion action ('Buy', 'Start Free Trial', 'Contact Sales', 'Book Demo') is preceded by more than 3 auxiliary interactive elements, flag `CTA_REACHABILITY_FRICTION` (Reachability Index = 1 / (1 + preceding)). Ensures visitors arriving from AI search citations can convert without cognitive navigation friction.
6. **First-Party Analytics Cross-Correlation (Dual-Track Evaluation):**
   - **Empirical Corroboration:** When analytics are ingested and a static UX defect aligns with high bounce rate (>= 60%) or low dwell time (<= 20s), elevate confidence and severity to `high`.
   - **Static Flag Mitigation:** When observed user retention is healthy (bounce rate <= 35%, dwell time >= 60s), downgrade static heuristic severity to `low` or informational.
   - **AI Referral Discontinuity:** When AI referral cohort bounce rate exceeds organic search baseline by >= 25%, flag `AI_REFERRAL_DISCONTINUITY` as a high-severity intent mismatch.
   - **Heuristic-Only Fallback:** When analytics are omitted, operate with explicit limitations stating findings are structural proxies, not verified visitor abandonment.

---

## Output Format

Emits strictly valid JSON matching the schema with zero prose commentary:
`{status, engagement_mode, analytics_summary, findings[], recommendations[], observations[], coverage{}, limitations[]}`.
All string fields in emitted findings and recommendations must be clean, single-line or semicolon-delimited (` ; `), containing zero escaped literal newlines (`\n\n`) and zero raw Markdown tables.

---

## Gotchas & Error Handling

- **Static Proxies vs Observed Outcomes:** Static DOM indicators (missing H1, buried CTA) are structural friction proxies. Without first-party analytics, do not claim visitors are provably bouncing in the wild.
- **Healthy Analytics Override:** Never escalate a missing H1 or layout warning to critical/high if first-party analytics prove 75% scroll depth and low bounce rates.
- **AI Buying Agent Manifest:** Absence of `/pricing.md` is an advisory recommendation (`PROACTIVE.ENGAGEMENT.AGENT_PRICING_MANIFEST.001`), not a critical site defect.
- **Generic H1 threshold:** An H1 of "Welcome" or "Home" triggers `LOW_INFORMATION_SCENT` at severity `low` only. It is NOT a `high` defect without analytics corroboration of actual bounce.
- **Single-page scope:** This sensor evaluates individual page orientation signals, not site-wide user journey funnels. Do not make cross-page funnel abandonment claims from page-level DOM data.

---

## Security & SSRF Policy

Operates offline against canonical `inv.json`. All network fetch operations, pre-connect DNS resolution, and zero-trust SSRF sandboxing are enforced centrally by `web-scraper` (`safe_fetch.py`) and coordinated under the master suite policy in `audit-orchestrator`.
