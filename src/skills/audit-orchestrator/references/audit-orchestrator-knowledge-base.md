# AUDIT-ORCHESTRATOR KNOWLEDGE BASE

## Table of Contents

- [Causal Taxonomy Hierarchy](#causal-taxonomy-hierarchy)
- [Root Cause Reference Table](#root-cause-reference-table)
- [1. `AI_RETRIEVAL_BLOCKED`](#1-ai-retrieval-blocked)
- [2. `RENDERED_CONTENT_GAP`](#2-rendered-content-gap)
- [3. `MATERIAL_ENTITY_AMBIGUITY`](#3-material-entity-ambiguity)
- [4. `FIRST_PARTY_FACT_CONFLICT`](#4-first-party-fact-conflict)
- [5. `BROKEN_AUTHORITY_ANCHOR`](#5-broken-authority-anchor)
- [5b. `CANDIDATE_BACKLINK_UNREACHABLE`](#5b-candidate-backlink-unreachable)
- [6. `INTENT_TO_LANDING_MISMATCH`](#6-intent-to-landing-mismatch)
- [7. `LOW_INFORMATION_SCENT`](#7-low-information-scent)
- [7b. `AI_REFERRAL_DISCONTINUITY`](#7b-ai-referral-discontinuity)
- [8. `AI_FACT_CONFLICT`](#8-ai-fact-conflict)
- [9. `MISSING_IN_DEPTH_MECHANISMS`](#9-missing-in-depth-mechanisms)
- [Top-Level Fields](#top-level-fields)
- [Summary Object](#summary-object)
- [Finding Object](#finding-object)
  - [Suggested Action Object](#suggested-action-object)
- [Root Cause Object](#root-cause-object)
- [Example Clean Production Report](#example-clean-production-report)
- [Severity Rubric](#severity-rubric)
- [Confidence Model](#confidence-model)
- [1. Specialist Responsibilities](#1-specialist-responsibilities)
- [2. Global Wall-Clock Deadline (< 5 Minutes)](#2-global-wall-clock-deadline-5-minutes)
- [3. SSRF Protection & Bounded Streaming](#3-ssrf-protection-bounded-streaming)
- [4. Crawler Matrix Semantics](#4-crawler-matrix-semantics)
- [5. Eligibility Gate & Deduplication](#5-eligibility-gate-deduplication)
- [6. Taxonomy-Driven Root-Cause Clustering](#6-taxonomy-driven-root-cause-clustering)
- [7. Objective Audit Metrics](#7-objective-audit-metrics)
- [1. Specialist Status Contract](#1-specialist-status-contract)
- [2. Public Report Contract](#2-public-report-contract)
  - [2.1 Finding Contract](#21-finding-contract)
- [3. Internal Shared State Contract](#3-internal-shared-state-contract)
- [4. No Heuristic Defects Rule](#4-no-heuristic-defects-rule)
- [8. Scoring Model v2 & Composite GEO Score](#8-scoring-model-v2--composite-geo-score)
- [9. Machine-Readable `GEO-AUDIT-META` Specification](#9-machine-readable-geo-audit-meta-specification)
- [10. The Canonical 16-Defect Matrix (HF-01 to HF-08 and W-01 to W-08)](#10-the-canonical-16-defect-matrix-hf-01-to-hf-08-and-w-01-to-w-08)
- [11. The 6 Orthogonal Scoring Dimensions & Statistical Formulation](#11-the-6-orthogonal-scoring-dimensions--statistical-formulation)
- [12. Causal Dependency Graph (DAG) & The Keystone Defect Rule](#12-causal-dependency-graph-dag--the-keystone-defect-rule)
- [13. Epistemic Falsification & Disambiguation Protocol](#13-epistemic-falsification--disambiguation-protocol-anti-hallucination-gates)
- [14. The 5-Step Cognitive Synthesis Protocol](#14-the-5-step-cognitive-synthesis-protocol-from-sensors-to-diagnostic-judgment)
- [15. Multi-Engine Retrieval Simulation Matrix](#15-multi-engine-retrieval-simulation-matrix)
- [17. Effort-vs-Impact Executive Prioritization Matrix](#17-effort-vs-impact-executive-prioritization-matrix)
- [18. State-of-the-Art Generative Engine Optimization (GEO) Benchmarks](#18-state-of-the-art-generative-engine-optimization-geo-benchmarks)
- [19. Multiplicative Layered Probability Model & Advanced Citability Framework](#19-multiplicative-layered-probability-model--advanced-citability-framework)
- [20. Citation Absorption & Structural Feature Engineering (GEO-SFE)](#20-citation-absorption--structural-feature-engineering-geo-sfe)
- [21. Archetype Dynamic Adaptation & Query-Strategy Profiles](#21-archetype-dynamic-adaptation--query-strategy-profiles)

---

This document contains all mandatory rules, schemas, and taxonomies required for this skill.

---

## Unified Causal Failure Taxonomy for AI Brand Visibility

This document establishes the canonical root-cause classification across all skills in the Brand AI-Readiness Audit Marketplace.
Findings represent authentic **causal failure modes**, not superficial HTML checklist violations.

---

## Causal Taxonomy Hierarchy

```text
AUDIT TAXONOMY
│
├── DISCOVERY
│   ├── ACCESS
│   │   ├── AI_RETRIEVAL_BLOCKED            (robots.txt blocks AI search retrieval bots: OAI-SearchBot, PerplexityBot)
│   │   ├── NOINDEX_EXCLUSION               (noindex directive prevents indexing of public content)
│   │   └── WAF_BOT_CHALLENGE               (Edge WAF / firewall rejects AI crawler User-Agents)
│   ├── DISCOVERY_PATH
│   │   ├── CANONICAL_FRAGMENTATION         (Canonical consolidation points away from indexable content)
│   │   ├── ORPHANED_CONTENT_PATH           (Critical pages unlinked from site navigation or sitemaps)
│   │   └── LOCALE_MISCONFIGURATION         (Invalid hreflang codes causing regional surfacing errors)
│   │   └── SITEMAP_INDEXING_GAP            (Absence of sitemap for large multi-page catalog)
│   └── REPRESENTATION_AVAILABILITY
│       └── RENDERED_CONTENT_GAP            (Core textual content omitted from initial raw HTML payload)
│
├── ENTITY
│   ├── IDENTITY
│   │   ├── MATERIAL_ENTITY_AMBIGUITY       (Brand or organization entity cannot be resolved unambiguously)
│   │   └── WEAK_IDENTITY_SIGNALS           (Absence of structured machine-explicit Organization markup)
│   └── ANSWERABILITY
│       ├── MISSING_MATERIAL_FACT           (Material commercial fact missing from specialized landing page)
│       ├── INCOMPLETE_OFFER_ATTRIBUTES     (Product schema omits price, availability, or specifications)
│       └── WEAK_ANSWER_SURFACE             (Page fails to provide direct answers to high-intent queries)
│
├── FACT
│   ├── CONSISTENCY
│   │   ├── FIRST_PARTY_FACT_CONFLICT       (Contradictory values published for identical scoped entity)
│   │   └── CONFLICTING_COMMERCIAL_TERMS    (Discrepancy between on-page price and structured schema price)
│   ├── FRESHNESS
│   │   ├── LEGACY_FACT_PROPAGATION         (Retired taglines or outdated brand claims persist across pages)
│   │   └── STALE_AUTHORITATIVE_FACT        (Absence of currency signals / multi-year stale copyright dates)
│   └── LIFECYCLE
│       └── DISCONTINUED_VS_CURRENT_CONFLICT (Discontinued model marketed as active or in-stock)
│
├── AUTHORITY
│   ├── IDENTITY_CORROBORATION
│   │   ├── BROKEN_AUTHORITY_ANCHOR         (Declared sameAs profile URL returns 4xx/5xx HTTP error)
│   │   ├── CIRCULAR_SAMEAS_SELF_REFERENCE  (sameAs points to alternate mirror domains rather than 3rd-party knowledge graph)
│   │   └── CANDIDATE_BACKLINK_UNREACHABLE  (Candidate backlink from referring domain returns 4xx/5xx or is unreachable)
│   ├── CLAIM_CORROBORATION
│   │   └── CLAIM_CORROBORATION_GAP         (Material factual assertions lack external verification)
│   └── PROVENANCE_AND_RIGHTS
│       └── UNVERIFIED_CONTENT_RIGHTS       (Media/streaming/catalog lacks machine-verifiable licensing disclosures)
│
├── EXPERIENCE
│   └── CONTINUITY
│       ├── INTENT_TO_LANDING_MISMATCH      (Landing page fails to retain referral query intent)
│       ├── LOW_INFORMATION_SCENT           (Headline / hero uses vague filler lacking descriptive nouns)
│       ├── VIEWPORT_ANSWER_ABSENCE         (Core cited proposition missing from top 600px viewport, triggering orientation shock)
│       ├── CTA_REACHABILITY_FRICTION       (First commercial continuation action delayed behind >3 auxiliary interactive links)
│       ├── DESTINATION_NAVIGATION_FRICTION (Absence of semantic navigation to key brand destinations)
│       └── AI_REFERRAL_DISCONTINUITY       (First-party analytics confirm excessive bounce on AI search traffic)
│
├── CONTENT
│   ├── SHALLOW_COVERAGE
│   │   ├── MISSING_IN_DEPTH_MECHANISMS     (Content lacks explanatory mechanisms 'how' and 'why' prioritized by generative search)
│   │   └── STANDALONE_FAQ_DEFICIT          (Isolated Q&A format lacking empirical code/statistics/tables, incurring -5.7% penalty)
│   ├── RETRIEVAL_OPTIMIZATION
│   │   ├── LACK_OF_SPECIFIC_EVIDENCE       (Content lacks concrete statistics, numbers, or verifiable metrics)
│   │   └── EXCESSIVE_KEYWORD_DENSITY       (Term frequency >4.5% degrading neural embedding perplexity by -8.3% to -10%)
│   └── CONTEXT_PLACEMENT
│       └── CONTEXT_PLACEMENT_DEGRADATION   (Primary answer delayed beyond top 30% / first 250 words; Lost in the Middle)
│
└── REPRESENTATION
    └── ACCURACY
        ├── AI_FACT_CONFLICT                (Observed AI assistant quotes facts contradicting site reality)
        ├── AI_UNSUPPORTED_CLAIM            (Observed AI assistant makes ungrounded assertions)
        └── AI_CITATION_GAP                 (Brand mentioned in AI answer without source citation link)
```

---

## Root Cause Reference Table

| Cause Family | Cause ID | Description | Default Severity |
| :--- | :--- | :--- | :--- |
| `DISCOVERY.ACCESS` | `AI_RETRIEVAL_BLOCKED` | robots.txt blocks AI search retrieval crawlers (`OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot`). | `critical` / `high` |
| `DISCOVERY.ACCESS` | `NOINDEX_EXCLUSION` | Meta robots or headers exclude public content from AI ingestion. | `critical` |
| `DISCOVERY.ACCESS` | `ROBOTS_5XX_FAIL_CLOSED` | robots.txt returns HTTP 5xx causing fail-closed block of all AI crawlers. | `critical` |
| `DISCOVERY.ACCESS` | `ROBOTS_TXT_OVERSIZED` | robots.txt exceeds 500 KiB RFC 9309 ceiling resulting in truncated directive processing. | `medium` |
| `DISCOVERY.ACCESS` | `NOSNIPPET_ON_CORE_CONTENT` | Meta nosnippet directive prevents generative answer engine extraction. | `high` |
| `DISCOVERY.DISCOVERY_PATH` | `CANONICAL_FRAGMENTATION` | Canonical URL consolidates onto a different un-audited host. | `medium` |
| `DISCOVERY.DISCOVERY_PATH` | `LOCALE_MISCONFIGURATION` | Hreflang language/country code misconfiguration causing cross-regional routing failure. | `medium` |
| `DISCOVERY.REPRESENTATION_AVAILABILITY` | `RENDERED_CONTENT_GAP` | Primary copy missing from raw HTML (client-side rendering dependency). | `high` |
| `ENTITY.IDENTITY` | `MATERIAL_ENTITY_AMBIGUITY` | Brand entity is missing machine-explicit Organization identity. | `medium` |
| `ENTITY.ANSWERABILITY` | `INCOMPLETE_OFFER_ATTRIBUTES` | Product/Offer schema omits required commercial fields (price, availability). | `low` |
| `ENTITY.ANSWERABILITY` | `ATTRIBUTE_INCOMPLETENESS` | Product/Offer schema omits required commercial attributes (price, currency, availability). | `low` |
| `ENTITY.ANSWERABILITY` | `MISSING_MATERIAL_FACT` | Page type missing core factual attributes expected for user query answerability. | `low` |
| `ENTITY.ANSWERABILITY` | `COMMERCIAL_PRODUCT_DATA_CONTRADICTION` | Discrepancy between on-page visible price and JSON-LD structured schema price. | `high` |
| `ENTITY.STRUCTURE` | `SCHEMA_DEPRECATION` | Outdated Schema.org types or deprecated properties degrade machine extraction. | `low` |
| `ENTITY.STRUCTURE` | `SCHEMA_PRICE_FORMAT_INVALID` | Schema price contains unparsed currency symbols or string format rather than clean float. | `low` |
| `FACT.CONSISTENCY` | `FIRST_PARTY_FACT_CONFLICT` | Conflicting prices or specifications published for the same product/plan across pages. | `high` |
| `FACT.FRESHNESS` | `LEGACY_FACT_PROPAGATION` | Outdated slogans, legacy pricing, or stale copyright years persist across pages. | `medium` |
| `FACT.LIFECYCLE` | `DISCONTINUED_VS_CURRENT_CONFLICT` | Discontinued product marketed as active or in-stock on secondary pages. | `high` |
| `FACT.CONSISTENCY` | `AI_FACT_CONFLICT` | Observed AI assistant quotes pricing or facts contradicting on-site reality. | `high` |
| `AUTHORITY.IDENTITY_CORROBORATION` | `BROKEN_AUTHORITY_ANCHOR` | Declared sameAs profile URL returns 4xx/5xx HTTP error. | `medium` |
| `AUTHORITY.IDENTITY_CORROBORATION` | `CIRCULAR_SAMEAS_SELF_REFERENCE` | sameAs points to internal mirrors/redirects rather than external authority knowledge graphs. | `medium` |
| `AUTHORITY.IDENTITY_CORROBORATION` | `CANDIDATE_BACKLINK_UNREACHABLE` | Candidate backlink from referring domain returns 4xx/5xx or is unreachable. | `medium` |
| `AUTHORITY.CLAIM_CORROBORATION` | `CLAIM_CORROBORATION_GAP` | Material factual assertions lack external verification or corroboration. | `low` |
| `EXPERIENCE.CONTINUITY` | `INTENT_TO_LANDING_MISMATCH` | Landing page omits answers to referral query intent above the fold. | `medium` |
| `EXPERIENCE.CONTINUITY` | `LOW_INFORMATION_SCENT` | Primary H1 uses generic filler words ("Welcome", "Home") lacking information scent. | `low` |
| `EXPERIENCE.CONTINUITY` | `VIEWPORT_ANSWER_ABSENCE` | Core cited proposition missing from top 600px viewport, triggering orientation shock. | `medium` |
| `EXPERIENCE.CONTINUITY` | `CTA_REACHABILITY_FRICTION` | Commercial continuation CTA delayed behind >3 auxiliary interactive elements. | `medium` |
| `EXPERIENCE.CONTINUITY` | `AI_REFERRAL_DISCONTINUITY` | First-party analytics confirm excessive bounce (>= 60%) and low dwell (< 30s) on AI search traffic. | `high` |
| `EXPERIENCE.CONTINUITY` | `DESTINATION_NAVIGATION_FRICTION` | Landing page lacks navigation links to core brand destinations. | `medium` |
| `EXPERIENCE.CONTINUITY` | `AGENT_INTERACTION_BARRIER` | Conversion action requires multi-step interactive friction blocking autonomous agent task completion. | `medium` |
| `CONTENT.SHALLOW_COVERAGE` | `MISSING_IN_DEPTH_MECHANISMS` | Content lacks explanatory mechanisms ('how' and 'why') prioritized by generative search. | `medium` |
| `CONTENT.SHALLOW_COVERAGE` | `STANDALONE_FAQ_DEFICIT` | Standalone FAQ format without empirical code, statistics, or comparison tables (-5.7% penalty). | `medium` |
| `CONTENT.RETRIEVAL_OPTIMIZATION` | `LACK_OF_SPECIFIC_EVIDENCE` | Content lacks concrete statistics, numbers, or verifiable metrics. | `low` |
| `CONTENT.KEYWORD_STUFFING_DEGRADATION` | `EXCESSIVE_KEYWORD_DENSITY` | Term frequency >4.5% degrading neural embedding perplexity (-8.3% to -10% citation degradation). | `medium` |
| `CONTENT.CONTEXT_PLACEMENT_DEGRADATION` | `CONTEXT_PLACEMENT_DEGRADATION` | Primary answer delayed beyond top 30% / first 250 words (Stanford 'Lost in the Middle'). | `medium` |
| `CONTENT.CITABILITY` | `LOW_CITABILITY_SCORE` | Composite citability index falls below benchmark threshold for LLM selection. | `medium` |
| `CONTENT.INFORMATION_DENSITY` | `LOW_FACT_TO_TOKEN_RATIO` | Atomic Fact-to-Token Ratio (FTR < 0.040) indicates thin, non-citable marketing copy. | `medium` |
| `CONTENT.LINGUISTIC` | `EXCESSIVE_HEDGE_LANGUAGE` | High frequency of epistemic hedge words (>1.5%) conveys speculative low confidence. | `low` |
| `CONTENT.FRESHNESS` | `CONTENT_RECENCY_DEFICIT` | Core substantive content lacks recent modification signals (>365 days stale). | `low` |

---

## Audit Check Contracts Catalog

Formal contracts defining inputs, evidence criteria, decision boundaries, and remediation rules across all marketplace skills.

---

## 1. `AI_RETRIEVAL_BLOCKED`
- **Skill:** `discoverability-audit`
- **Family:** `DISCOVERY.ACCESS`
- **Purpose:** Ensure AI search retrieval crawlers can access public content.
- **Input:** Parsed `robots.txt` rules per RFC 9309.
- **Decision:** Finding triggered IF `robots_access(rules, bot, "/") == "disallow"` for ANY retrieval bot (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`).
- **Exclusion:** Training-only bots (`GPTBot`, `Google-Extended`) trigger informational observations, NOT this defect.
- **Severity:** `critical` (if OAI-SearchBot / PerplexityBot blocked) or `high`.
- **Confidence:** `high`.
- **Remediation:** Remove blanket `Disallow: /` for AI search retrieval crawlers.
- **Verification:** Re-fetch `robots.txt` and verify retrieval bots are permitted.

---

## 2. `RENDERED_CONTENT_GAP`
- **Skill:** `discoverability-audit`
- **Family:** `DISCOVERY.REPRESENTATION_AVAILABILITY`
- **Purpose:** Detect heavy client-side rendering where bots see empty shells.
- **Input:** Raw HTTP response body vs rendered DOM snapshot.
- **Decision:** Finding triggered IF text delta > 70% or raw word count < 50 while rendered > 250 words.
- **Exclusion:** Single-page applications with prerendered meta tags and server-side hydration.
- **Severity:** `high`.
- **Confidence:** `high`.
- **Remediation:** Implement server-side rendering (SSR) or dynamic prerendering for bots.
- **Verification:** Verify raw HTML response contains visible body copy.

---

## 3. `MATERIAL_ENTITY_AMBIGUITY`
- **Skill:** `entity-content-audit`
- **Family:** `ENTITY.IDENTITY`
- **Purpose:** Ensure machines can unambiguously identify the publishing organization.
- **Input:** JSON-LD scripts extracted from homepage / root.
- **Decision:** Finding triggered IF no `Organization` or `Brand` schema is found, or if `name` / `url` is missing.
- **Exclusion:** Sub-pages inheriting root Organization schema via reverse linkage.
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Add canonical `Organization` JSON-LD schema with `name`, `url`, `logo`, and `sameAs`.
- **Verification:** Validate JSON-LD with Schema.org validator.

---

## 4. `FIRST_PARTY_FACT_CONFLICT`
- **Skill:** `fact-consistency-audit`
- **Family:** `FACT.CONSISTENCY`
- **Purpose:** Prevent hallucinations caused by contradictory facts published across different pages.
- **Input:** Fact ledger compiled from crawled page bodies and structured data.
- **Decision:** Finding triggered IF identical entity attribute (e.g. price) has conflicting values across 2+ pages.
- **Exclusion:** Explicitly marked tier differences or historical changelogs.
- **Severity:** `high`.
- **Confidence:** `high`.
- **Remediation:** Align factual claims across all site pages or mark historical data with deprecation notices.
- **Verification:** Re-crawl affected URLs and confirm identical pricing.

---

## 5. `BROKEN_AUTHORITY_ANCHOR`
- **Skill:** `corroboration-authority-audit`
- **Family:** `AUTHORITY.IDENTITY_CORROBORATION`
- **Purpose:** Verify declared external authority profiles are live and accessible.
- **Input:** Extracted `sameAs` URLs from Organization schema.
- **Decision:** Finding triggered IF probe returns HTTP 4xx or 5xx error.
- **Exclusion:** Unreachable / timeout probes are marked `inconclusive`, not broken.
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Update dead sameAs URLs to active canonical profile URLs.
- **Verification:** Send HEAD request to all sameAs URLs and confirm HTTP 200.

---

## 5b. `CANDIDATE_BACKLINK_UNREACHABLE`
- **Skill:** `corroboration-authority-audit`
- **Family:** `AUTHORITY.IDENTITY_CORROBORATION`
- **Purpose:** Verify external candidate backlink sources citing the brand domain are live and reachable.
- **Input:** Provided candidate backlink URLs via `--candidate-backlinks`.
- **Decision:** Finding triggered IF candidate backlink probe returns HTTP 4xx or 5xx error, or fails to fetch.
- **Exclusion:** URLs blocked by SSRF protections are marked rejected, not broken.
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Update or remove unreachable referring source URLs from backlink rosters.
- **Verification:** Re-probe referring URLs under SSRF-safe HTTP streaming.

---

## 6. `INTENT_TO_LANDING_MISMATCH`
- **Skill:** `engagement-context-audit`
- **Family:** `EXPERIENCE.CONTINUITY`
- **Purpose:** Prevent visitor bounce caused by landing pages that fail to retain referral query intent.
- **Input:** Landing page hero content vs expected page-type intent facts.
- **Decision:** Finding triggered IF specialized landing route (e.g. `/pricing` or `/products/x`) lacks expected core facts above the fold.
- **Exclusion:** Do NOT report if page clearly states relevant entity name and primary offering details.
- **Severity:** `medium`.
- **Confidence:** `medium`.
- **Remediation:** Present core answer facts (pricing, features, specifications) above the fold on the landing page.
- **Verification:** Inspect landing viewport to confirm key value answers are visible within 5 seconds.

---

## 7. `LOW_INFORMATION_SCENT`
- **Skill:** `engagement-context-audit`
- **Family:** `EXPERIENCE.CONTINUITY`
- **Purpose:** Prevent visitor bounce caused by low-information landing page headlines.
- **Input:** Primary `<h1>` text content.
- **Decision:** Finding triggered IF H1 is in `["welcome", "home", "homepage", "untitled", "index", "hello"]` or ≤ 1 word.
- **Exclusion:** Do NOT report if H1 contains concrete brand or offering names.
- **Severity:** `low`.
- **Confidence:** `high`.
- **Remediation:** Revise H1 to clearly state the product name or core value proposition.
- **Verification:** Confirm updated H1 contains descriptive nouns and value verbs.

---

## 7b. `AI_REFERRAL_DISCONTINUITY`
- **Skill:** `engagement-context-audit`
- **Family:** `EXPERIENCE.CONTINUITY`
- **Purpose:** Detect severe post-citation drop-off where AI search referrals bounce immediately due to orientation failure.
- **Input:** First-party analytics records ingested via `--analytics`.
- **Decision:** Finding triggered IF an AI referral source on a route exhibits bounce rate >= 60% and dwell time < 30 seconds.
- **Exclusion:** Do NOT trigger if total route sessions < 5 (insufficient sample size).
- **Severity:** `high`.
- **Confidence:** `high`.
- **Remediation:** Align page H1, value proposition, and primary CTAs directly with the answering AI engine's query intent.
- **Verification:** Re-check analytics telemetry after 7 days of deployment to confirm bounce reduction below 50%.

---

## 8. `AI_FACT_CONFLICT`
- **Skill:** `fact-consistency-audit`
- **Family:** `FACT.CONSISTENCY`
- **Purpose:** Identify when an AI assistant quotes prices that contradict on-site reality.
- **Input:** Observed AI assistant claims vs first-party fact snapshot.
- **Decision:** Finding triggered IF assistant states a price that is absent from all on-site listings.
- **Exclusion:** Do NOT report if assistant accurately quotes current on-site pricing.
- **Severity:** `high`.
- **Confidence:** `high`.
- **Remediation:** Publish explicit Product JSON-LD to ground assistant retrieval.
- **Verification:** Re-pose prompt to assistant and verify quoted price matches on-site schema.

---

## 9. `MISSING_IN_DEPTH_MECHANISMS`
- **Skill:** `geo-content-audit`
- **Family:** `CONTENT.SHALLOW_COVERAGE`
- **Purpose:** Detect when substantive content lacks the causal/explanatory depth required for AI citation.
- **Input:** Tokenized visible text across substantive product and content routes.
- **Decision:** Finding triggered IF depth score < 2 (fewer than 2 causal conjunctions: 'how', 'why', 'because', 'therefore', 'allows', 'enables').
- **Exclusion:** Do NOT report on purely transactional pages (login, cart).
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Refactor key text to explain underlying mechanisms, operational workflows, and causal benefits.
- **Verification:** Confirm presence of explanatory conjunctions and depth markers in visible text.

---

## Brand AI-Readiness Audit Report Schema

This document specifies the structure, validation constraints, and field semantics for the audit report emitted by `audit-orchestrator`.

---

## Top-Level Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `site` | String | Yes | Target domain or URL (e.g., `example.com` or `https://example.com`) |
| `audited_at` | String (ISO 8601) | Yes | UTC timestamp in ISO 8601 format (e.g., `2026-09-20T14:32:00Z`) |
| `audit_status` | String (Enum) | Yes | Audit completion status: `complete`, `partial`, `failed` |
| `summary` | Object | Yes | Aggregate counts of findings categorized by severity (`critical`, `high`, `medium`, `low`) |
| `findings` | Array | Yes | Ordered list of verified defects with supporting evidence and suggested actions |
| `proactive_actions` | Array | No | Deduplicated proactive opportunities (e.g. sitemap creation, llms.txt, JSON-LD) |
| `evidence_classes` | Object | No | Explicit segregation: `declared_identity_nodes` (Schema sameAs) vs `verified_candidate_backlinks` (verified via bounded probe) |
| `analytics_summary` | Object | No | Quantitative metrics from first-party analytics (total referrals, bounce rates, dwell) and heuristic fallback caveats |
| `page_improvement_plans` | Array | No | Deterministic page-level content improvement plans with gap analysis, structural and textual actions, and epistemic boundaries |

---

## Summary Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `total_findings` | Integer | Yes | Total count of items in `findings` |
| `critical` | Integer | Yes | Count of findings with severity `critical` |
| `high` | Integer | Yes | Count of findings with severity `high` |
| `medium` | Integer | Yes | Count of findings with severity `medium` |
| `low` | Integer | No | Count of findings with severity `low` |

---

## Finding Object

Each entry in the `findings` array represents a verified, evidence-backed defect.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | String | Yes | Unique finding identifier (e.g., `F-001`, `F-002`) |
| `title` | String | Yes | Concise, human-readable summary of the defect |
| `severity` | Enum | Yes | `critical` \| `high` \| `medium` \| `low` \| `evidence` | String | Yes | Concrete data, observed metrics, or reproduction steps verifying the finding |
| `suggested_action` | Object | Yes | Actionable, mechanism-sound remediation plan |
| `confidence` | Enum | No | `high` \| `medium` \| `low` |
| `category` | String | No | Functional category (e.g. `access`, `entity-integrity`, `fact-consistency`, `orientation`) |
| `cause_family` | String | No | Standardized taxonomy family (`DISCOVERY.ACCESS`, `ENTITY.IDENTITY`, etc.) |
| `cause_id` | String | No | Specific root cause identifier |
| `impact` | String | No | Explanation of downstream impact on AI citations and user retention |
| `verification` | String | No | Procedure to verify resolution |

### Suggested Action Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `summary` | String | Yes | Clear instruction on what to change and how to resolve the root cause |
| `priority` | Enum | Yes | `critical` \| `high` \| `medium` \| `low` |
| `verification` | String | No | Method to test that the fix worked |
| `implementation_guidance` | String | No | Optional code snippet, schema template, or configuration directive |

---

## Root Cause Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `cause_family` | String | Yes | Standard taxonomy family (e.g. `DISCOVERY.ACCESS`, `FACT.CONSISTENCY`) |
| `cause_id` | String | Yes | Specific root cause identifier |
| `root_cause` | String | Yes | Descriptive explanation of underlying failure |
| `finding_ids` | Array of Strings | Yes | Associated finding IDs grouped under this cause |
| `max_severity` | Enum | Yes | Highest severity among grouped findings |
| `suggested_priority` | Enum | Yes | Recommended resolution priority |

---

## Example Clean Production Report

```json
{
  "site": "https://frescopa.coffee",
  "audited_at": "2026-08-28T16:52:37Z",
  "audit_status": "complete",
  "summary": {
    "total_findings": 2,
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "findings": [{
      "id": "FACT.INTEGRITY.PRICE_CONFLICT.001",
      "title": "Product price is inconsistent across first-party surfaces",
      "severity": "high",
      "category": "fact-integrity",
      "root_cause": "The same product is represented with different current prices on the product and category pages.",
      "confidence": "high",
      "impact": "AI assistants quote conflicting prices across multi-page retrieval contexts.",
      "evidence": {
        "summary": "Product page states ₹5,499 while category page states ₹4,999 for the same product.",
        "scope": "product-catalog",
        "sources": [{
            "url": "https://frescopa.coffee/products/ethiopia-guji",
            "type": "html_dom",
            "observation": "Price rendered as ₹5,499"
          },
          {
            "url": "https://frescopa.coffee/products",
            "type": "html_dom",
            "observation": "Price rendered as ₹4,999"
          }
        ]
      },
      "suggested_action": {
        "summary": "Establish one authoritative offer value and synchronize visible content and structured data across affected pages.",
        "technical_fix": "Synchronize pricing database feeds to both product and catalog templates.",
        "creative_fix": "Audit promotional banners to ensure legacy discounts are not displayed.",
        "verification": "Crawl product and listing pages to verify matching ₹5,499 price tags.",
        "priority": "high"
      }
    },
    {
      "id": "DISCOVERY.REPRESENTATION_AVAILABILITY.RENDERED_CONTENT_GAP.002",
      "title": "Important product information is difficult to retrieve",
      "severity": "medium",
      "category": "discoverability",
      "root_cause": "Material product facts are absent from the initial machine-readable representation of sampled product pages.",
      "confidence": "medium",
      "impact": "AI crawlers unable to render client-side JavaScript miss core product specifications.",
      "evidence": {
        "summary": "Across sampled product pages, raw HTML word count < 25 words with unrendered app container.",
        "scope": "product-pages",
        "sources": [{
            "url": "https://frescopa.coffee/products/ethiopia-guji",
            "type": "raw_html",
            "observation": "Body contains <div id='root'></div> with only 12 words of static text."
          }
        ]
      },
      "suggested_action": {
        "summary": "Expose core product facts directly in crawlable HTML and keep structured representation consistent.",
        "technical_fix": "Implement Server-Side Rendering (SSR) for product detail pages.",
        "creative_fix": "Ensure primary value proposition is present in server-rendered markup.",
        "verification": "Fetch raw HTML via curl and confirm full specification text is present.",
        "priority": "medium"
      }
    }
  ],
  "proactive_actions": [{
      "id": "PROACTIVE.ENTITY.BRAND_IDENTITY.001",
      "title": "Strengthen canonical brand identity",
      "category": "entity",
      "summary": "Maintain a consistent organization identity, canonical name, logo and authoritative external references across major brand surfaces.",
      "technical_fix": "Embed Schema.org Organization JSON-LD with sameAs social links on homepage.",
      "creative_fix": "Ensure official legal company name is displayed in footer.",
      "verification": "Validate Organization schema with Google Rich Results Test.",
      "priority": "low"
    }
  ]
}
```

---

## Severity & Confidence Calibration Model

This document specifies the rules for assigning severity and confidence scores to audit findings.

---

## Severity Rubric

Severity reflects the direct impact of a defect on AI discovery, knowledge extraction, and visitor retention.

| Severity | Criteria | Examples |
| :--- | :--- | :--- |
| `critical` | **Total Exclusion / Hard Outage**: Prevents AI retrieval engines from crawling or indexing public content. | • `Disallow: /` for AI search retrieval crawlers (`OAI-SearchBot`, `PerplexityBot`).<br>• `<meta name="robots" content="noindex">` on landing page.<br>• HTTP 5xx/4xx on root URL. |
| `high` | **Material Retrieval / Factual Degradation**: Directly leads to corrupted facts, omitted products, or severe rendering extraction failure. | • Core text missing from initial HTML (< 25 words in SPA container).<br>• Conflicting prices published for the same product across first-party pages.<br>• AI assistant quotes wrong pricing due to ambiguous markup.<br>• WAF blocking crawler User-Agents. |
| `medium` | **Corroboration & Orientation Degradation**: Degrades entity clarity, navigation, or cross-web trust anchors. | • Broken `sameAs` authority profile URLs (HTTP 404).<br>• No machine-explicit Organization identity.<br>• Content page lacks `<h1>` or internal navigation menus.<br>• Copyright years vary significantly across site pages. |
| `low` | **Extractability Polish & Minor Signal Gaps**: Minor improvements that make fact extraction easier but do not block ingestion. | • Incomplete Product schema attributes (e.g. missing sku).<br>• Low-information H1 heading (e.g. "Welcome").<br>• Missing dateModified timestamps on static pages. |

---

## Confidence Model

Confidence reflects the strength and verifiability of the supporting evidence.

| Confidence | Evidence Quality | Action Rule |
| :--- | :--- | :--- |
| `high` | **Deterministic Direct Probe (L1 Evidence)**: Derived from exact HTTP status codes, verbatim robots.txt rules, DOM text extraction, or parsed JSON-LD structures. | Eligible for all severity levels (`critical`, `high`, `medium`, `low`). |
| `medium` | **Corroborated Heuristic (L2 Evidence)**: Derived from cross-page comparison, text word counts, or multi-probe behavioral analysis. | Eligible for `medium` or `low` severity; `high` severity requires explicit corroborating evidence. |
| `low` | **Weak / Inconclusive Signal (L3 Evidence)**: Speculative or single-sample heuristic lacking secondary corroboration. | **Demoted by the Eligibility Gate** to a proactive recommendation (`proactive_actions[]`); never asserted as a critical/high defect. |

---

## Composition, Evidence & Severity Guidelines

How `audit-orchestrator` acquires evidence, composes specialist outputs, gates
findings, enforces global deadlines, and reports root causes. This document describes the *implemented*
orchestrator — SKILL.md, this reference, and `scripts/orchestrator.py` are one
methodology, not three opinions.

---

## 1. Specialist Responsibilities

| Skill | Owns | Does NOT own |
| :--- | :--- | :--- |
| `discoverability-audit` | Access, crawler rules (distinguishing retrieval vs training bots), noindex, canonical, rendering risk, discovery aids | Structured data, page content |
| `entity-content-audit` | Entity identity, structured schema (JSON-LD), Answerability Engine, material attribute completeness | Crawler access rules |
| `fact-consistency-audit` | Fact ledger, scoped volatile facts (prices, contacts), cross-page contradictions, freshness timestamps | Entity identity correctness |
| `corroboration-authority-audit` | Independent source verification of first-party claims (sameAs, external profiles) | First-party content quality |
| `engagement-context-audit` | Intent orientation (5-second test), heading information scent, navigation continuity on landing pages | Technical crawlability |
| `geo-content-audit` | Generative Engine Optimization (GEO), statistical density, Q&A formatting, structured tabular/list content | Semantic engagement continuity |

---

## 2. Global Wall-Clock Deadline (< 5 Minutes)

The orchestrator enforces a strict total runtime budget (default 300 seconds):
- **Phase 1 (Acquisition Crawl):** Bounded to ≤ 60 seconds.
- **Phase 2 (Specialist Execution):** Dynamic allocation where each specialist receives `(remaining_time - buffer) / remaining_specialists`.
- **Budget Expiry:** If remaining time is ≤ 5s, remaining specialists are marked with `status: "not_run"` and `reason: "Execution skipped: global time budget exhausted"`. Tool failure is never converted into zero findings.

---

## 3. SSRF Protection & Bounded Streaming

Every network fetch in the orchestrator and all specialist tools enforces:
1. **Scheme Validation:** `http` and `https` only.
2. **DNS & IP Validation:** Rejection of private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`, `fe80::/10`), and cloud-metadata addresses.
3. **Bounded Redirects:** Max 5 redirects with target IP re-validation on every hop.
4. **Hard Size Caps:** HTML pages (max 2 MB), robots.txt (max 512 KB), sitemaps (max 2 MB), external authority probes (max 512 KB).
5. **Same-Origin Crawling:** Sitemaps and priority links must match the target domain origin.
6. **Zero Direct Agent URL Reading:** Autonomous AI agents are strictly prohibited from using built-in URL reading or browser tools (`read_url_content`, `open_browser_url`, `browser_subagent`) or manual `curl`/`wget`. All web scraping must flow through `safe_fetch.py` / `acquire_inventory.py`.

---

## 4. Crawler Matrix Semantics

- **Retrieval Bots:** `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `anthropic-ai`. Blocking on public content = `critical` / `high` finding.
- **Training Bots:** `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`. Blocking = `info` / `low` observation (training opt-out, not AI search retrieval failure).
- **User Fetch:** `ChatGPT-User`. User-initiated browsing token.

---

## 5. Eligibility Gate & Deduplication

Before a specialist finding enters `findings[]`:
1. It must cite concrete evidence (≥ 8 characters of gathered evidence). Evidence-less assertions become `proactive_actions[]`.
2. High/critical severity with low confidence is demoted to a recommendation.
3. Overlapping findings and recommendations are deduplicated using normalized fingerprints (`category:title` and `(action_category, action_title)`).

---

## 6. Taxonomy-Driven Root-Cause Clustering

Findings are clustered by standardized taxonomy families:
- `DISCOVERY.ACCESS`: HTTP availability, noindex, crawler disallow.
- `DISCOVERY.RENDERING`: Initial HTML text absence, client-side rendering dependency.
- `DISCOVERY.CANONICAL`: Canonical host consolidation discrepancies.
- `ENTITY.IDENTITY`: Missing Organization / Brand structured identity.
- `ENTITY.ANSWERABILITY`: Material attribute gaps across product, pricing, service pages.
- `FACT.CONSISTENCY`: Cross-page price, contact, or brand contradictions.
- `FACT.FRESHNESS`: Stale copyright years, missing modification timestamps.
- `AUTHORITY.CORROBORATION`: Broken sameAs authority profiles and unreachable backlink sources.
- `EXPERIENCE.CONTINUITY`: Heading information scent, missing navigation, viewport answer anchoring, CTA reachability, and AI referral bounce.
- `CONTENT.SHALLOW_COVERAGE`: Mechanistic explanations ('how'/'why') and standalone FAQ deficits (-5.7% citation penalty).
- `CONTENT.KEYWORD_STUFFING_DEGRADATION`: Excessive keyword density (>4.5%) degrading neural embedding perplexity.
- `CONTENT.CONTEXT_PLACEMENT_DEGRADATION`: Core answers delayed beyond top 30% / first 250 words (Stanford 'Lost in the Middle').
- `REPRESENTATION.ACCURACY`: Divergence between observed AI claims and first-party facts.

---

## 7. Objective Audit Metrics

Synthetic point deduction scores are avoided. The orchestrator emits objective metrics:
- `pages_sampled`: Count of URLs audited.
- `page_types_covered`: Breakdown of page types evaluated.
- `critical_blockers`: Total count of critical access/indexing blockers.
- `confidence_distribution`: High, medium, and low confidence evidence counts.
- `answerability_index`: Average material attribute coverage across sampled pages.
---

## Architectural Contracts

This document defines the frozen schemas and logic boundaries for the Brand AI Readiness Audit.

## 1. Specialist Status Contract
Every specialist strictly returns a JSON object containing a `status` field, which must be exactly one of:
- `ok`: Execution completed successfully and findings (if any) are valid.
- `inconclusive`: Execution succeeded but evidence was fundamentally blocked (e.g., HTML parse error, site blocked crawler).
- `failed`: An unhandled exception or critical process error occurred during specialist execution.
- `not_run`: Specialist was intentionally skipped (e.g., optional module disabled or timeout budget exhausted).

## 2. Public Report Contract
The public output (generated by the Orchestrator) must conform to the following schema:
- `site` (string): The audited canonical domain.
- `audited_at` (date-time): ISO 8601 UTC timestamp.
- `audit_status` (string): `complete` (all run), `partial` (some failed/not_run), `failed` (all failed).
- `summary` (object): Tally of findings by severity.
- `findings` (array of objects): Discovered material defects.
- `proactive_actions` (array of objects): Opportunities to improve AI representation beyond material defects.

### 2.1 Finding Contract
Required fields for every finding:
- `id` (string): e.g. "F-001"
- `title` (string)
- `severity` (string): `critical`, `high`, `medium`, `low`. (No `info`).
- `category` (string): Broad capability bucket (e.g., `fact-integrity`, `discoverability`).
- `root_cause` (string): The technical/content mechanism causing the observation.
- `confidence` (string): Evaluated certainty of the observation.
- `evidence` (object): `{ "summary": "", "scope": "", "sources": [{url, type, observation}] }`.
- `suggested_action` (object): Contains `summary`, `technical_fix`, `creative_fix`, `priority`, and `verification`.

## 3. Internal Shared State Contract
To allow stateful cross-specialist graph intelligence without coupling, specialists read/write to a temporary `state.json`.
The atomic state file must maintain:
```json
{
  "version": 1,
  "entities": {},
  "facts": {},
  "claims": {},
  "observations": {},
  "page_context": {}
}
```
Rules:
- Read completely before modification.
- Only mutate your namespace or append to existing graphs.
- Write atomically (`tempfile` + `os.replace`).

## 4. No Heuristic Defects Rule
Heuristics (like counting `<table>` tags or measuring keyword density) may be used to build a classifier profile, but **cannot alone trigger a finding**. Findings must require semantic corroboration or explicit logic breakdown (e.g., missing `<title>` tag).

## 5. Output Delivery Mandate (Output Standard)
The entrypoint skill is responsible for composing the specialist outputs into a single schema-valid audit report and emitting it directly as the final output:
1. **Direct JSON Code Block:** The complete, unabridged Draft-07 schema-valid JSON report MUST be rendered directly in the response within a single ````json```` code block. Never truncate or substitute the JSON report with a vague summary pointing to disk.
2. **Zero Conversational Preamble:** Do NOT output conversational preambles ("Here is the complete audit..."), execution traces, or scratch script dumps before the JSON report.
3. **Zero Duplicate Markdown Tables:** Do NOT render duplicate Markdown tables summarizing the findings before the JSON code block. Downstream consumers require clean, unpolluted output.
4. **Clean String Formatting:** In all JSON string properties (such as `technical_fix`, `creative_fix`, `evidence.summary`, `proactive_actions[].summary`), strings MUST be concise, single-line or semicolon-delimited (` ; `). NEVER embed escaped literal newlines (`\n\n`), raw Markdown tables (`| Col | Col |`), or raw HTML `<table>` markup inside JSON strings.

## 6. Query-Intent Scenario Modeling
When authoring `root_cause` and `impact` for findings, articulate the specific query mode failure in conversational AI search engines:
1. **Navigational / Brand Query ("What is [Brand]?"):**
   - Explain why the LLM fails to recognize the brand, hallucinates facts, or refuses attribution (e.g., lack of Wikidata entity, circular sameAs mirror networks, ambiguous Organization schema).
2. **Categorical / Discovery Query ("Where can I buy/stream/find [Topic]?"):**
   - Explain why the LLM selects competitors over this domain (e.g., competitors have verified licensing disclosures, structured Product/Offer/VideoObject schemas, and modular 120-180 word RAG passage chunks with high causal depth).

## 7. Domain-Specific Remediation Catalog
Tailor `suggested_action.technical_fix` and `creative_fix` to the detected website archetype:
- **Media & Streaming Services:**
  - *Technical Fix:* Implement structured `TVSeries`, `TVEpisode`, or `VideoObject` with licensed stream descriptors, canonical media IDs, and rich server-rendered HTML descriptions.
  - *Creative Fix:* Add original editorial overviews, episode guides, and thematic synopses using explanatory conjunctions (because, enables, features).
- **SaaS & Cloud Software:**
  - *Technical Fix:* Expose transparent pricing matrices with structured `OfferCatalog`, semantic comparison `<table>` elements, and developer API documentation.
  - *Creative Fix:* Detail technical specifications, integration workflows, and quantifiable benchmark statistics (percentage latency reductions, throughput metrics).
- **E-Commerce & Commercial Retail:**
  - *Technical Fix:* Complete all material attributes (`price`, `priceCurrency`, `availability`, `itemCondition`, `returnPolicy`) within JSON-LD `Product` and `Offer` graphs.
  - *Creative Fix:* Provide transparent pricing terms, exact billing cadences, and scannable feature lists.
- **Publishing & Content Portals:**
  - *Technical Fix:* Embed named author `Person` markup with credentials (`jobTitle`, `alumniOf`) and primary source citation links (DOI, academic institutions, standards bodies).
  - *Creative Fix:* Adopt the "Direct Answer Inversion" pattern: an H2 question heading followed immediately by a concise 40-60 word answer lead, followed by 100 words of mechanistic explanation.

## 8. Scoring Model v2 & Composite GEO Score

To produce a single, holistic benchmark of AI search readiness while retaining empirical rigor, the orchestrator computes the Composite GEO Score (0–100):

### Mathematical Formulation:
GEO Score = (Technical * 0.20) + (Citability * 0.35) + (Schema * 0.20) + (Brand * 0.25)

1. **Technical Accessibility (Weight: 20%):**
   - 11-Crawler matrix access (retrieval bots weighted 2x training bots).
   - llms.txt discovery and parseability.
   - Clean canonical and meta tag compliance.
2. **Content Citability (Weight: 35%):**
   - Head-First Information Cues and 40–60 word Direct Answer Inversion leads.
   - Quantifiable statistics and causal conjunction density (Princeton KDD 2024).
   - Low hedge language density (< 0.5% target).
   - Content recency (< 3 months bonus, > 6 months deficit).
3. **Structured Data Completeness (Weight: 20%):**
   - Machine-explicit JSON-LD schemas (`Organization`, `Product`, `Offer`, `BreadcrumbList`).
   - Server-side rendering compliance (no client-only schema injection).
   - Zero retired/deprecated schema types.
4. **Brand Corroboration & Authority (Weight: 25%):**
   - Bidirectional external sameAs linkbacks.
   - External third-party substantiation (Wikidata, Wikipedia, LinkedIn, GitHub).
   - First-party fact ledger consistency across all sampled routes.

### Letter Grade Scale:
- **A (85–100):** Elite AI Readiness. Fully optimized for instant multi-engine citation.
- **B (70–84):** Good AI Readiness. Minor structural or recency optimizations needed.
- **C (50–69):** Moderate Visibility. Notable entity or citability gaps depress selection.
- **D (30–49):** High Risk. Severe crawl blockers or material entity ambiguity.
- **F (0–29):** Critical Failure. Complete absence from generative search engines.

---

## 9. Machine-Readable `GEO-AUDIT-META` Specification

For programmatic integration, CI/CD gates, and automated trend monitoring, the orchestrator embeds a machine-readable HTML comment block in the report preamble:

```html
<!-- GEO-AUDIT-META
{
  "version": "2.1.0",
  "site": "https://example.com",
  "timestamp": "2026-09-02T17:40:00Z",
  "composite_geo_score": 78.5,
  "letter_grade": "B",
  "archetype": "saas_software",
  "breakdown": {
    "technical_accessibility": 92.0,
    "content_citability": 68.5,
    "structured_data": 80.0,
    "brand_authority": 76.0
  },
  "critical_blockers": 0,
  "total_findings": 3
}
-->
```

## 10. The Canonical 16-Defect Matrix (HF-01 to HF-08 and W-01 to W-08)

To eliminate subjective ambiguity, audit findings must map directly to the canonical defect taxonomy:

### A. Hard Failures (HF-01 to HF-08) — Deterministic Blockers

| Code | Title | Category | Severity | Root Cause Definition |
| :--- | :--- | :--- | :--- | :--- |
| **HF-01** | Target URL Unreachable / Non-200 | Crawlability | Critical | HTTP status >= 400 or network timeout. |
| **HF-02** | Canonical URL Contradictory | Discoverability | High | Target page declares contradictory or missing canonical tag. |
| **HF-03** | Search Crawler Blocked in robots.txt | Crawlability | Critical | `OAI-SearchBot`, `Claude-SearchBot`, or `PerplexityBot` disallowed. |
| **HF-04** | noindex Directive Active | Indexability | Critical | `<meta name="robots" content="noindex">` or HTTP `X-Robots-Tag`. |
| **HF-05** | nosnippet on Core Content | Snippet Control | High | `nosnippet`, restrictive `max-snippet`, or `data-nosnippet` on text. |
| **HF-06** | Product Data Contradiction | Commerce | Critical | HTML visible price differs from JSON-LD `Offer.price`. |
| **HF-07** | Critical Claims in Non-Text Media | Extractability | High | Core facts exist solely in images, PDFs, or dynamic JS rendering. |
| **HF-08** | Schema Directly Contradicts Visible HTML | Structured Data | High | Schema entities state values incompatible with on-page copy. |

### B. High-Value Warnings (W-01 to W-08) — Probabilistic & Quality Risks

| Code | Title | Category | Severity | Root Cause Definition |
| :--- | :--- | :--- | :--- | :--- |
| **W-01** | Initial HTML Extraction Deficit | Retrieval | Medium | SSR content availability gap exceeds 15% (CAG >= 0.15). |
| **W-02** | High-Value Facts Lack Source Attribution | Citability | Medium | Crucial commercial claims lack verifiable sources or citations. |
| **W-03** | Commercial Pricing / Inventory Drift | Consistency | Medium | Cross-page or feed discrepancy in price, currency, or stock status. |
| **W-04** | Brand Entity Discordance | Authority | Medium | Organization name or sameAs links conflict across routes. |
| **W-05** | Excessive Discovery Depth | Architecture | Low | Authoritative evidence requires > 3 clicks/hops from homepage. |
| **W-06** | llms.txt Link Decay | Manifest | Low | Links inside `/llms.txt` return 4xx redirects or non-canonical URLs. |
| **W-07** | Low Atomic Fact Density | Content | Medium | FTR < 0.040; prose lacks verifiable dates, figures, or metrics. |
| **W-08** | Cross-Engine Citation Divergence | Visibility | Medium | CECO < 0.50; brand cited on only 1 engine while absent on others. |

---

## 11. The 6 Orthogonal Scoring Dimensions & Statistical Formulation

To avoid conflating crawlability with empirical visibility, the audit synthesizes six distinct, orthogonal scores:

Score Formulation = Crawlability (20%) + Retrieval (20%) + Citation Readiness (20%) + Entity Authority (15%) + Cross-Engine Visibility (15%) + Agentic Commerce (10%)

### Mathematical Formulations:
1. **Cross-Engine Citation Coverage (CECO):**
   CECO = (number of engines citing brand or domain) / (total engines tested)
2. **Wilson 95% Score Confidence Interval:**
   CI_95% = (p_hat + z^2 / (2n) +/- z * sqrt(p_hat * (1 - p_hat) / n + z^2 / (4n^2))) / (1 + z^2 / n)
   Where p_hat is the observed sample citation rate, n is total query runs (minimum n >= 10), and z = 1.96.
3. **Product Consistency Index:**
   ProductConsistency = 1 - (number of conflicting fields / total checked fields)

---

## 12. Causal Dependency Graph (DAG) & The Keystone Defect Rule

To prevent the AI from confusing downstream symptoms with upstream root causes, the orchestrator evaluates findings along an explicit 6-layer Causal Directed Acyclic Graph (DAG):

```text
CAUSAL DEPENDENCY GRAPH (DAG)
=============================
Layer 0: INGESTION & ACCESS
  [AI_RETRIEVAL_BLOCKED, NOINDEX_EXCLUSION, ROBOTS_5XX_FAIL_CLOSED, ROBOTS_TXT_OVERSIZED]
       |
       v (Blocks engine access to raw response)
Layer 1: CONTENT EXTRACTION & DELIVERY
  [RENDERED_CONTENT_GAP, NOSNIPPET_ON_CORE_CONTENT, WAF_BOT_CHALLENGE, CANONICAL_FRAGMENTATION]
       |
       v (Prevents ingestion of DOM nodes and schema)
Layer 2: ENTITY & SEMANTIC RESOLUTION
  [MATERIAL_ENTITY_AMBIGUITY, BROKEN_AUTHORITY_ANCHOR, CIRCULAR_SAMEAS_SELF_REFERENCE, WEAK_IDENTITY_SIGNALS]
       |
       v (Deprives knowledge graph of grounded entity identity)
Layer 3: FACTUAL KNOWLEDGE LEDGER
  [FIRST_PARTY_FACT_CONFLICT, COMMERCIAL_PRODUCT_DATA_CONTRADICTION, INCOMPLETE_OFFER_ATTRIBUTES, STALE_AUTHORITATIVE_FACT]
       |
       v (Causes hallucinations and conflicting price quotes)
Layer 4: GENERATIVE CITABILITY & SCENT
  [MISSING_IN_DEPTH_MECHANISMS, STANDALONE_FAQ_DEFICIT, LOW_FACT_TO_TOKEN_RATIO, EXCESSIVE_KEYWORD_DENSITY, CONTEXT_PLACEMENT_DEGRADATION, LOW_INFORMATION_SCENT]
       |
       v (Degrades neural passage attention during RAG synthesis)
Layer 5: ENGINE SELECTION & CONVERSION
  [AI_CITATION_GAP, AI_FACT_CONFLICT, AI_REFERRAL_DISCONTINUITY, INTENT_TO_LANDING_MISMATCH]
```

### The Keystone Defect Rule (Anti-Inflation Gate):
1. **Upstream Preemption**: If a Layer 0 defect (e.g. `AI_RETRIEVAL_BLOCKED` or `ROBOTS_5XX_FAIL_CLOSED`) or a Layer 1 defect (e.g. `RENDERED_CONTENT_GAP` or `WAF_BOT_CHALLENGE`) is present, downstream omissions at Layers 2–4 are **consequential symptoms**, not independent defects.
2. **Consolidation Mandate**: The orchestrator MUST attribute the root failure to the single upstream "Keystone Defect". Downstream observations (such as missing JSON-LD or zero body text extracted) must be recorded as supporting evidence under that Keystone Defect, rather than inflating the report with 5 separate critical findings.
3. **Severity Decoupling**: Downstream findings cannot carry higher severity than their enabling upstream root cause.

---

## 13. Epistemic Falsification & Disambiguation Protocol (Anti-Hallucination Gates)

Before committing an observation as an authoritative finding, the AI must execute mandatory falsification tests to rule out common benign architectures and edge cases:

| Target Observation | Sensor Trigger | Mandatory Falsification Test | Disambiguation Outcome |
| :--- | :--- | :--- | :--- |
| **Price Mismatch Across Pages** | Price on `/product` != price on `/pricing` | Check currency code, billing interval (monthly vs annual upfront), variant IDs, and promotional tier labels. | • If prices correspond to different billing terms or editions -> REJECT `FIRST_PARTY_FACT_CONFLICT`. Emit `COMMERCIAL_TERMS_TRANSPARENCY` recommendation.<br>• If prices claim to represent the identical scope/term -> CONFIRM `FIRST_PARTY_FACT_CONFLICT`. |
| **Missing Root `Organization` Schema** | No standalone `Organization` block in homepage JSON-LD | Inspect nested `@graph` arrays, `WebSite.publisher` references, microdata `itemtype`, and OpenGraph `og:site_name`. | • If organization is declared within `@graph` or inherited from root -> REJECT `MATERIAL_ENTITY_AMBIGUITY`.<br>• If machine-explicit entity identity is entirely absent across all syntaxes -> CONFIRM `MATERIAL_ENTITY_AMBIGUITY`. |
| **Low Text Word Count (<50 words)** | Scraped HTML body has minimal text | Inspect HTTP headers (`Server`, `cf-ray`, `x-akamai`), HTML `<title>` ("Attention Required", "Just a moment..."), and status codes (403/429/503). | • If an edge firewall challenge is detected -> Trigger `WAF_BOT_CHALLENGE`.<br>• If HTTP 200 with an unhydrated `<div id="root"></div>` -> CONFIRM `RENDERED_CONTENT_GAP` (SPA dependency). |
| **Crawler Disallow in `robots.txt`** | `Disallow: /` for an AI-prefixed bot | Check exact User-Agent name against RFC 9309 crawler taxonomy. | • If bot is an offline model training harvester (`GPTBot`, `ClaudeBot`, `Google-Extended`, `CCBot`) -> REJECT `AI_RETRIEVAL_BLOCKED`. Log as informational training opt-out.<br>• If bot is an AI search retrieval bot (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) -> CONFIRM `AI_RETRIEVAL_BLOCKED`. |
| **Stale Copyright Year** | Hardcoded footer says "© 2023" or "© 2024" | Inspect HTTP `Last-Modified` header, JSON-LD `dateModified`, article publication dates, and recent changelog updates. | • If substantive articles/products are updated within 90 days -> REJECT `STALE_AUTHORITATIVE_FACT`. Footer string is an aesthetic defect.<br>• If substantive copy and prices have had zero updates for >365 days -> CONFIRM `CONTENT_RECENCY_DEFICIT`. |

---

## 14. The 5-Step Cognitive Synthesis Protocol (From Sensors to Diagnostic Judgment)

The AI orchestrator executes this five-step cognitive loop to transform raw sensor outputs into an executive-grade diagnostic report:

```text
[Step A: Triangulation] -> [Step B: Causal Root-Tracing] -> [Step C: Falsification] -> [Step D: Engine Simulation] -> [Step E: Dual-Track Prescription]
```

1. **Step A — Multi-Sensor Triangulation & Route Indexing:**
   - Group raw sensor findings by URL path and entity identifier. Cross-correlate discoverability, entity schema, fact consistency, and engagement metrics into a unified route ledger.
2. **Step B — Causal Root-Tracing (The 5-Whys Analysis):**
   - Traverse the Causal DAG backwards from each symptom to identify the deepest upstream enabling failure. Identify the single Keystone Defect responsible for clustered symptoms.
3. **Step C — Counterfactual Falsification Gate:**
   - Evaluate: *"If engineering fixes this proposed defect, does the AI search barrier immediately dissolve, or does an unaddressed upstream gate remain?"* If an upstream gate remains, re-center priority on the upstream blocker.
4. **Step D — Platform-Specific Retrieval Simulation:**
   - Model how the defect specifically penalizes Google AI Overviews, ChatGPT Search, and Perplexity Pro using the differential retrieval mechanics defined in Section 15.
5. **Step E — Dual-Track Remediation Prescription:**
   - Author domain-tailored technical specifications (for software engineers and DevOps) and creative copy/architecture guidance (for content strategists and brand marketers), complete with a deterministic verification procedure.

---

## 15. Multi-Engine Retrieval Simulation Matrix

Generative search engines do not share a monolithic retrieval architecture. The AI orchestrator models defects against the three dominant engine paradigms:

| Architectural Dimension | Google AI Overviews (Gemini) | ChatGPT Search (OpenAI / Bing) | Perplexity Pro |
| :--- | :--- | :--- | :--- |
| **Primary Indexing Pipeline** | Google Search Web Index (Top-10 organic ranking strongly correlated with citation). | Bing Web Index + Dedicated `OAI-SearchBot` real-time crawl. | Custom Perplexity Web Crawler + Live Search API Aggregation Pipeline. |
| **Entity Grounding Anchor** | Google Knowledge Graph + Verified Google Business Profile nodes. | Wikidata Q-Identifiers + Wikipedia entities (47.9% anchor share) + Schema `@id`. | Third-Party Consensus (Reddit, forums, authoritative news, multi-domain agreement). |
| **Optimal Content Geometry** | Semantic HTML `<table>` elements + concise 40–60 word Direct Answer leads. | Deep, comprehensive guides (2,000+ words) with rich technical mechanisms. | Fast server response + recency (<90 days, 3x citation boost) + explicit data attribution. |
| **Machine-Readable Manifests** | XML Sitemaps + Clean Server-Side Rendered HTML. | Root `/llms.txt` + `/pricing.md` API-ready manifests. | Clean markdown headers + structured citations. |
| **Dominant Failure Mode** | Ranking below Page 1 in traditional organic search; unrendered client JS. | Entity confusion with similarly named brands; hallucinated facts due to missing schema. | Total omission if recent third-party discussion or reviews are absent. |

---

## 16. Bayesian Evidence Triangulation & Sample Size Discounting

The AI calibrates finding confidence using an objective Bayesian evidence framework:

### Evidence Tiers:
- **L1 — Deterministic Direct Ground Truth (Confidence: `high`, 1.0):**
  Derived from exact HTTP status codes, RFC 9309 parsed robots rules, or syntax-validated schema parse exceptions. Eligible for all severity levels (`critical`, `high`, `medium`, `low`).
- **L2 — Corroborated Multi-Page Heuristic (Confidence: `high` if n >= 5, `medium` if n < 5):**
  Derived from verified contradictions across 2 or more distinct pages (e.g. cross-route price mismatch or multi-page text availability ratio).
- **L3 — Single-Sample Uncorroborated Heuristic (Confidence: `low`):**
  Derived from single-page text metrics, word count heuristics, or isolated stylistic observations. **Action Rule:** Automatically demoted by the Eligibility Gate to `proactive_actions[]`; never emitted as a critical or high defect.

### Sample Size Discounting Rule:
- When total crawled page count n < 5, sitewide extrapolations are strictly prohibited.
- Finding evidence scope must be annotated as `"sample-restricted"` rather than `"sitewide"`.
- High-severity heuristic findings must be downgraded to `medium` severity until confirmed across a larger catalog crawl.

---

## 17. Effort-vs-Impact Executive Prioritization Matrix

To provide clear strategic roadmaps rather than unprioritized laundry lists, the AI orchestrator classifies all proactive actions and suggested remediations into a 2x2 executive decision matrix:

| Impact \ Technical Effort | Low Effort (Hours / Days) | High Effort (Weeks / Sprints) |
| :--- | :--- | :--- |
| **High Citability Impact** | **P1: Quick Wins**<br>• Unblock `OAI-SearchBot` and `PerplexityBot` in `robots.txt`.<br>• Add Schema.org `Organization` with Wikidata `sameAs`.<br>• Fix broken authority profile anchors.<br>• Synchronize contradictory visible prices. | **P2: Architectural Priorities**<br>• Migrate client-rendered SPA shells to Server-Side Rendering (SSR).<br>• Implement machine-readable `/llms.txt` and `/llms-full.txt`.<br>• Build automated catalog-to-schema synchronization pipeline.<br>• Re-architect core landing pages for BLUF 30% answer leads. |
| **Moderate / Incremental Impact** | **P3: Optimization Polish**<br>• Invert generic H1 headings ("Home") to descriptive value propositions.<br>• Reduce epistemic hedge language density below 1.2%.<br>• Add explicit `dateModified` timestamps to substantive content.<br>• Enrich Product schema with optional SKU and review fields. | **P4: Deprioritized / Backlog**<br>• Re-writing non-commercial informational footer pages.<br>• Micro-optimizing text readability on low-traffic utility routes.<br>• Sitewide taxonomy restructuring without search engine impact. |

---

## 18. State-of-the-Art Generative Engine Optimization (GEO) Benchmarks

### 18.1 Academic & Empirical Research Foundations

#### 1. "GEO: Generative Engine Optimization" (Aggarwal et al., Princeton / ACM SIGKDD 2024 / arXiv:2311.09735)
Optimization for generative engines differs fundamentally from traditional search engines across the 10,000-query GEO-bench:
- **Statistics Addition:** **+30% to +41%** relative lift in AI visibility (replacing qualitative claims with specific, attributed numerical data).
- **Cite Sources:** **+30% to +40%** relative lift across top results, and up to **+115% visibility lift** for lower-ranked niche pages.
- **Quotation Addition:** **+30% to +40%** relative lift (extractable pull-quotes from named experts).
- **Fluency & Simplification:** **+15% to +30%** lift.
- **Authoritative Tone:** **+10.4%** on position-adjusted metrics, **+18.7%** on subjective impression.
- **Keyword Stuffing:** Caused a **-10% to negative effect**, actively harming attribution.

**Mathematical Formulation:**
```text
PAWC(S, R) = sum(WordCount(c) / log2(Rank(c) + 1))
```
Where C_S is the set of citations to source S in response R, WordCount(c) is the token volume attributed to the citation, and Rank(c) is the 1-indexed position of the citation within the synthesized response.

#### 2. "C-SEO Bench: Does Conversational SEO Work?" (Puerto et al., NeurIPS 2025 / arXiv:2506.11097)
In competitive multi-agent retrieval environments, pages featuring **LLM Guidance headers** (structured Markdown summaries directly beneath the main title, conceptually matching `/llms.txt`) substantially outperform standard narrative layouts by directing LLM context attention during RAG ingestion.

#### 3. "Evaluating Verifiability in Generative Search Engines" (Liu, Zhang, & Liang, Stanford / Findings of EMNLP 2023 / arXiv:2304.09848)
- **Citation Recall:** Only **51.5%** of generated sentences were fully supported by citations.
- **Citation Precision:** Only **74.5%** of citations actually supported the sentence they cited.
- LLMs penalize ambiguous or composite sentences. Retrieval systems favor source passages that present unambiguous, one-to-one semantic entailments. Content must be structured as atomic, self-contained claim-evidence propositions.

#### 4. "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al., Stanford / TACL 2024 / arXiv:2307.03172)
LLM retrieval accuracy follows a U-shaped curve: information at the absolute beginning (top 15–20%) or end of context receives high attention, whereas retrieval degradation in the middle exceeds **30–40%**.
- **Empirical AI Overviews Data:** **44.2% of citations in ChatGPT Search and Perplexity are pulled from the top 30% of the web page**.
- **Audit Rule (BLUF Top-30%):** The direct definition, resolution, or transactional answer must appear within the first 250 words (or top 30% of DOM content) before contextual background or narrative exposition.

### 18.2 Quantitative Scoring Formulas & Benchmarks

1. **Lakoff & Hyland Linguistic Hedging Metric:**
   ```text
   HedgeRate = (Sum(w_hedge) / N_total_words) * 100
   ```
   - Authoritative / Highly Cited: HedgeRate <= 1.2%
   - Neutral Informational: 1.2% < HedgeRate <= 2.2%
   - Speculative / Low-Trust (Penalized): HedgeRate > 2.5%

2. **Atomic Fact-to-Token Ratio (FTR):**
   ```text
   FTR = N_atomic_facts / N_tokens
   ```
   - Citable AI-Engineered Tier: FTR >= 0.080 (at least 1 atomic verifiable fact per 12.5 tokens).
   - Fluff / Thin Content Tier: FTR <= 0.035 (verbose marketing prose lacking verifiable claims).

3. **Shannon Text Entropy:**
   ```text
   H(X) = -Sum(p(x_i) * log2(p(x_i)))
   ```
   - Optimized Range for RAG Comprehension: 6.8 <= H(X) <= 7.6 bits (for English text chunks of 150–200 words).

4. **Passage Extractability & Self-Containment:**
   - Optimal RAG Chunk Size: **134 to 167 words** per section under each semantic header (`<h2>`/`<h3>`).
   - Exophoric Pronoun Ratio: Leading sentence ambiguous pronoun ratio must equal 0.0%.

### 18.3 Consolidated 17-Rule Audit Matrix (`CR01`–`TX06`)

| Code | Category | Algorithmic Test | Benchmark / Pass Threshold |
|---|---|---|---|
| **CR01** | Crawler Access | RFC 9309 Parser | `OAI-SearchBot` Allowed = True |
| **CR02** | Crawler Access | RFC 9309 Parser | `Claude-SearchBot` Allowed = True |
| **CR03** | Crawler Access | RFC 9309 Parser | `PerplexityBot` Allowed = True |
| **CR04** | Crawler Access | robots.txt File Size | <= 500 KiB (512,000 octets) |
| **CR05** | Crawler Access | robots.txt Status Code | HTTP 200 (Fail if 5xx) |
| **LL01** | Machine-Readable Standards | Root `/llms.txt` Fetch | HTTP 200, Content: MD/Plain |
| **LL02** | Machine-Readable Standards | `/llms.txt` Structure | Has H1 Title + Blockquote Summary |
| **RD01** | Rendering & Delivery | Content Availability Gap | CAG = 1 - (NoJS / JS) < 0.15 |
| **RD02** | Content Extraction | Signal-to-Noise Ratio (SNR) | Text Bytes / HTML Bytes > 0.12 |
| **SC01** | Structured Data | Extruct JSON-LD | `Organization` with >= 2 `sameAs` |
| **SC02** | Structured Data | Extruct JSON-LD | `Product` offers: valid ISO 4217 |
| **SC03** | Structured Data | Extruct JSON-LD | Schema `dateModified` <= 60 days |
| **TX01** | Information Architecture | BLUF Top-30% Check | Entity answer in top 250 words |
| **TX02** | Linguistic Hedging | Hyland Lexicon Density | HedgeRate <= 1.2% |
| **TX03** | Information Density | Atomic Fact Ratio (FTR) | FTR >= 0.080 |
| **TX04** | Passage Self-Containment | Exophoric Pronoun Check | Leading sentence ExoRatio = 0 |
| **TX05** | Context Complexity | Shannon Entropy | 6.8 <= H(X) <= 7.6 bits |
| **TX06** | Empirical Lift Factor | Princeton GEO Criteria | >= 1 stat + 1 quote / 150 words |

---

## 19. Multiplicative Layered Probability Model & Advanced Citability Framework

### 19.1 Executive Probability Formulation

The empirical literature establishes that AI search visibility is a multiplicative layered pipeline:
```text
AI Visibility ≈ Crawl Eligibility × Retrieval Eligibility × Content Citability × Entity/Source Authority × Citation Fidelity
```

- **Methodological Principle:** The "+40% visibility improvement" from the canonical GEO paper (Aggarwal et al., KDD 2024) is **Position-Adjusted Word Count (PAWC)** *among an already retrieved set of sources*, not a 40% increase in baseline retrieval probability.
- **Engine-Specific Conditional Probability:**
  ```text
  P(Citation | Engine) != P(Citation)
  ```

### 19.2 Citation Quality Evaluation Frameworks

1. **ALCE (Automatic LLM Citation Evaluation — Gao et al., EMNLP 2023):**
   - Three-Dimensional Model: [Fluency + Correctness + Citation Quality]
   - CitationCoverage = (claims with supporting citation) / (total claims)
   - CitationPrecision = (citations that actually entail the claim) / (total citations)

2. **FActScore (Atomic Fact Support — Min et al., EMNLP 2023):**
   ```text
   BrandFactScore = Sum(w_i * supported_i) / Sum(w_i)
   ```
   Where weights w_i are elevated for critical commercial claims (price, availability, certifications, product specifications, dates, performance metrics).

3. **Citation Correctness vs. Faithfulness (Wallat et al., 2024 / arXiv:2412.18004):**
   Up to **57% of citations lack faithfulness** due to post-hoc rationalization. Systems must evaluate both `entailment_score` and `faithfulness_score`.

4. **Cross-Engine Citation Coverage (CECO) & Wilson 95% Confidence Intervals:**
   ```text
   CECO = (number of engines citing brand/domain) / (total engines tested)
   CI_95% = (p_hat + z^2 / (2n) ± z * sqrt(p_hat * (1 - p_hat) / n + z^2 / (4n^2))) / (1 + z^2 / n)
   ```
   Where z = 1.96 and n >= 10 runs per engine (n = 5 minimum floor).

---

## 20. Citation Absorption & Structural Feature Engineering (GEO-SFE)

### 20.1 "From Citation Selection to Citation Absorption" (Zhang, He, Yao — 2026 / arXiv:2604.25707)

Citation influence quantifies how deeply an AI engine incorporates source content into the synthesized answer:
```text
Influence_i = 0.20 * min(ref_count_i / 3, 1) + 0.15 * (1 - first_position_ratio_i) + 0.20 * paragraph_coverage_ratio_i + 0.25 * tfidf_cosine_i + 0.20 * ((bigram_overlap_i + trigram_overlap_i) / 2)
```

#### Actionable Evidence-Genre Lift Table:

| Detected Evidence Genre | Relative Influence Lift | Audit Action |
| :--- | :---: | :--- |
| **Code Snippets / Syntax Blocks** | **+76.9%** | Highest influence; provide executable CLI/code blocks. |
| **Quantitative Numbers / Statistics** | **+61.6%** | Replace narrative claims with exact benchmarks. |
| **Explicit Definition Markers** | **+57.3%** | Include unambiguous IS-A definitions (`defined as`, `refers to`). |
| **Comparison Structures / Tables** | **+55.3%** | Provide head-to-head evaluation matrices (`vs`, `unlike`). |
| **How-To / Procedural Guidance** | **+41.2%** | Numbered implementation workflows. |
| **Standalone Q&A / FAQ Format Alone** | **-5.7% (Negative Penalty)** | **Do not rely on FAQ format alone!** Augment with data and comparisons. |

#### Semantic-Role Influence Hierarchy:
1. **Definition Content:** Mean influence 0.153
2. **Comparison Content:** Mean influence 0.142
3. **Statistical Data:** Mean influence 0.138
4. **Procedural Steps:** Mean influence 0.119
5. **Pure Background / Reference:** Mean influence 0.053 (lowest)

### 20.2 Structural Feature Engineering for GEO (GEO-SFE — Yu et al., 2026 / arXiv:2603.29979)
Structure-aware rewriting alone—holding textual content constant—delivers **+17.3% citation improvement and +18.5% perceptual quality gain**.
- **Macro Architecture:** Strict heading hierarchy (`<h1>` -> `<h2>` -> `<h3>`), table of contents, executive takeaways.
- **Meso Chunking:** Standalone section self-containment (134–167 words per section) extractable without antecedent loss.
- **Micro Visual Emphasis:** Semantic bullet lists (density >= 0.40), comparison tables, and bold key takeaway leads.

### 20.3 Citation Failure Modes Decision Tree (Tian et al., 2026 / arXiv:2603.09296)
**43% of topically relevant pages receive zero citation** under baseline conditions due to 5 distinct failure modes:
1. **Retrieval Failure:** `robots.txt` disallow / `noindex` / unindexed SSR shell -> Fix: SSR, crawler permissions, XML sitemap.
2. **Relevance Failure:** Query intent mismatch / title-H1 semantic drift -> Fix: Target conversational intent, align H1 and title.
3. **Redundancy Failure:** Generic content duplicate of higher-authority domain -> Fix: Proprietary benchmarks, first-party data.
4. **Trust Failure:** Low FTR (<0.040) / excessive hedging (>2.5%) / no `sameAs` -> Fix: Eliminate weasel words, cite named experts.
5. **Extraction Failure:** `nosnippet` / `data-nosnippet` / low SNR (<0.12) -> Fix: Clean DOM, remove nosnippet, elevate text ratio.

### 20.4 Off-Site Third-Party Dominance (57% Branded Citation Footprint)
- **57% of branded query citations** come from third-party reviews, comparison listicles, Reddit discussions, and independent press (Omniscient Digital 2026).
- **Only ~4.5% of citations** derive from the brand's own official About, FAQ, or Homepage.
- Top 15 third-party authority domains capture **~68%** of all generative engine citations (Reddit, Wikipedia, YouTube, LinkedIn, Forbes, Trustpilot, G2).
- An audit that examines only on-page SEO misses 57% of the citation surface. External identity anchors and third-party corroboration nodes are mandatory.

### 20.5 The 0–30 CITE Citability Score Rubric

| Code | Dimension | Points | Evaluation Metric |
| :--- | :--- | :---: | :--- |
| **DA** | Direct Answer | 0–5 | Section openers provide standalone, extractable 40–60 word answer leads. |
| **DD** | Data Density | 0–5 | Specific numbers, percentages, durations, benchmark statistics (FTR >= 0.080). |
| **AS** | Authority Signals | 0–5 | Named researchers, DOIs, authoritative outbound citations, verified `sameAs` nodes. |
| **SQ** | Structure Quality | 0–5 | Heading hierarchy, comparison tables, list density >= 0.40, code blocks. |
| **FR** | Freshness | 0–5 | Visible `dateModified` <= 60 days, recent temporal grounding. |
| **UQ** | Uniqueness | 0–5 | Proprietary case data, original frameworks, zero generic boilerplate. |

**Score Bands:** Grade A (27–30) / Grade B (22–26) / Grade C (17–21) / Grade D (12–16) / Grade F (<12).

---

## 21. Archetype Dynamic Adaptation & Query-Strategy Profiles

> **Generalization Invariant:** Archetype classification NEVER gates which sensors run. All 6 specialist sensors ALWAYS execute across all domains. Archetype classification is used strictly by the AI reasoning layer to re-weight defect severities, contextualize simulated assistant queries, and synthesize high-leverage proactive recommendations.

### 21.1 Archetype Classification Matrix

| Archetype | Primary Detection Signals (from Telemetry) | Highest-Priority Checks | Distinctive Technical Fixes | Distinctive Creative Fixes | Proactive Strategic Moves |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SaaS / Developer Platform** | • `/docs`, `/api`, `/pricing`, `/billing` routes<br>• `SoftwareApplication` JSON-LD<br>• Code blocks and API endpoints in DOM | • `/llms.txt` presence and validity<br>• API doc chunking (`geo.avg_chunk_token_length`)<br>• Pricing comparison transparency<br>• Auth-wall orientation | Serve machine-readable `/llms.txt` and `/pricing.md`; structure doc pages with `<h2>` chunk boundaries every 300–500 tokens | Author 40–60 word BLUF answers under question headers; eliminate asterisk conditions on plan tiers | Deploy `/pricing.md` and `/llms.txt` manifests specifically formatted for autonomous AI purchasing agents |
| **E-Commerce / Retail** | • `/product`, `/shop`, `/item`, `/cart` routes<br>• `Product` & `Offer` JSON-LD<br>• Currency symbols & pricing tables | • Schema.org `Product`/`Offer` completeness (`price`, `priceCurrency`, `availability`)<br>• Cross-page multi-currency consistency<br>• Merchant return policies | Embed nested `Offer` with ISO 4217 currency and `ItemAvailability` enum; add `MerchantReturnPolicy` schema | Reconcile visible "In Stock" copy with structured availability; provide clean tabular product specifications | Deploy comprehensive Schema.org `@graph` connecting `Product` to `MerchantReturnPolicy` and `AggregateRating` |
| **Enterprise B2B** | • `/about`, `/leadership`, `/solutions`, `/investors`<br>• `Organization` JSON-LD<br>• Multiple external `sameAs` links | • Authority corroboration on Wikidata, LinkedIn, Crunchbase<br>• Named executive leadership in text & schema (`Person`)<br>• Entity disambiguation | Embed Schema.org `Organization` with disambiguated `sameAs` URIs; nest `Person` schema for leadership team | Maintain identical legal entity name and headquarters address across all external directory anchors | Establish verified Wikidata entity node and reconcile third-party corporate entity graphs |
| **News / Media Publisher** | • Byline patterns, publication dates<br>• `NewsArticle` or `BlogPosting` JSON-LD<br>• Date-path URLs (e.g. `/2026/09/`) | • Pre-paywall machine-readability<br>• Author byline authority & E-E-A-T credentials<br>• RFC 9309 AI bot licensing directives | Add `isAccessibleForFree` and `hasPart` schema for paywalls; link author profiles to external credentials | Provide 50-word executive summary (dek) above paywall; attribute facts to verifiable primary studies | Replace blanket crawler disallow with granular RFC 9309 rules distinguishing search retrieval from model training |
| **Local / Regional Service** | • `/locations`, `/contact`, store locator<br>• `LocalBusiness` JSON-LD<br>• Phone, physical address, NAP patterns | • `LocalBusiness` geo-coordinates (`latitude`, `longitude`)<br>• `openingHoursSpecification` completeness<br>• NAP consistency between footer and text | Declare `LocalBusiness.geo` coordinates and ISO 8601 opening hours; link to Google Maps CID | Reconcile phone number and address discrepancies between header, footer, and contact page | Embed localized `Service` schema with `areaServed` geographic polygons |

### 21.2 Severity Reweighting Rubric by Archetype

```python
ARCHETYPE_SEVERITY_OVERRIDES = {
    "ecommerce": {
        "ATTRIBUTE_INCOMPLETENESS": "critical",       # Missing price/currency blocks checkout journey
        "INCOMPLETE_OFFER_ATTRIBUTES": "critical",     # Missing availability misleads buying agents
        "COMMERCIAL_PRODUCT_DATA_CONTRADICTION": "critical",
        "MATERIAL_ENTITY_AMBIGUITY": "high",          # Brand must be identified for product citations
        "FIRST_PARTY_FACT_CONFLICT": "critical",       # Pricing drift misleads AI comparisons
    },
    "saas": {
        "LOW_FACT_TO_TOKEN_RATIO": "high",            # Thin text prevents category recommendation
        "MISSING_IN_DEPTH_MECHANISMS": "high",        # Lack of causal depth prevents technical citations
        "FIRST_PARTY_FACT_CONFLICT": "critical",       # Plan cost drift breaks AI purchasing agents
        "CONTEXT_PLACEMENT_DEGRADATION": "high",       # Key value prop buried below auth wall
    },
    "publisher": {
        "MATERIAL_ENTITY_AMBIGUITY": "high",          # Missing publisher authority drops citations
        "STANDALONE_FAQ_DEFICIT": "high",             # Missing FAQ schema limits AI Overview rich snippets
        "STALE_AUTHORITATIVE_FACT": "high",           # Outdated facts erode synthetic trust
        "CONTENT_RECENCY_DEFICIT": "medium",
    },
    "local_business": {
        "MATERIAL_ENTITY_AMBIGUITY": "critical",       # Local assistants cannot route without entity
        "MISSING_MATERIAL_FACT": "critical",           # Missing address/phone makes brand invisible
        "BROKEN_AUTHORITY_ANCHOR": "high",            # Broken map/directory link prevents grounding
    },
    "corporate": {}  # Baseline sensor severities
}
```

### 21.3 Simulated Assistant Query Profiles by Archetype

#### 1. SaaS / Developer Platform
- **Navigational Query:** *"What does [Brand] do and what are its core features?"*
  - *Retriever test:* Does `/` or `/about` contain a 40–60 word standalone definition without fluff?
- **Commercial Investigation Query:** *"How much does [Brand] cost per user, and does it offer an API?"*
  - *Retriever test:* Is pricing explicitly stated in visible text or `/pricing.md` without forced registration?
- **Technical Comparison Query:** *"Compare [Brand] vs [Competitor] for enterprise scale."*
  - *Retriever test:* Are architectural benchmarks and causal mechanisms (`because`, `therefore`) present?

#### 2. E-Commerce / Retail
- **Direct Product Query:** *"Where can I buy [Product Name] and is it in stock?"*
  - *Retriever test:* Does the page expose Schema.org `Offer` with `price`, `priceCurrency`, and `InStock`?
- **Specification Query:** *"What are the dimensions, materials, and warranty for [Product Name]?"*
  - *Retriever test:* Are product attributes in a clean HTML `<table>` or structured bullet list?

#### 3. Enterprise B2B
- **Vendor Due Diligence Query:** *"Who owns [Brand], where is it headquartered, and who is the CEO?"*
  - *Retriever test:* Does Schema.org `Organization` link to verified Wikidata/LinkedIn and declare `founder`/`employee`?
- **Security & Compliance Query:** *"Is [Brand] SOC 2 certified or GDPR compliant?"*
  - *Retriever test:* Are compliance statements un-gated and corroborated by third-party links?

#### 4. Media / Publisher
- **Fact Verification Query:** *"According to [Publisher], what is the latest finding on [Topic]?"*
  - *Retriever test:* Is the headline supported by a 50-word BLUF paragraph with named researcher attribution?

#### 5. Local Service
- **Local Intent Query:** *"What time does [Brand] open in [City] and what is their phone number?"*
  - *Retriever test:* Does `LocalBusiness` declare valid `openingHoursSpecification` and E.164 phone?
