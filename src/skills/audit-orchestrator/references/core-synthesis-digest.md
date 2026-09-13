# Core Synthesis Digest: Brand AI-Readiness & GEO Audit

Unified master reference consolidating cross-skill diagnostic benchmarks, the 6-Layer Causal DAG, Princeton KDD 2024 / AutoGEO empirical citability vectors, and archetype playbooks. Designed for single-call agent comprehension (< 2,500 tokens).

---

## 1. The 6-Layer Causal DAG & Keystone Deduplication

Diagnostic findings must be processed through the strictly ordered 6-layer dependency DAG. Upstream blockers suppress downstream symptoms to prevent redundant findings:

```
[Layer 0: Crawlability & RFC 9309 Bots]
           ↓ (If blocked, suppress Layer 1-5 downstream findings)
[Layer 1: Raw HTML Extraction & CSR / SPA Parity]
           ↓ (If blank shell, suppress Layer 2-5 text/schema omissions)
[Layer 2: Entity Disambiguation & Schema.org @graph]
           ↓ (Grounds brand identity for LLM knowledge graphs)
[Layer 3: Cross-Page Factual Consistency & Pricing Ledger]
           ↓ (Eliminates multi-source hallucination triggers)
[Layer 4: Identity Corroboration & Authority Graph]
           ↓ (57% off-site citation grounding: Wikidata, LinkedIn, YouTube)
[Layer 5: Post-Citation Orientation & Transactional Handoff]
```

### Keystone Suppression Rules

1. **Route-Level Granular Suppression**: Suppression operates at route-level precision. An upstream blocker on `/en/products/default` suppresses downstream symptoms only on matching routes, allowing valid findings on rendered routes (e.g. `/pricing`) to surface normally. Site-wide blockers (e.g. universal `Disallow: /`) suppress domain-wide.
2. **Layer 0 Block (`AI_RETRIEVAL_BLOCKED`, `NOINDEX_EXCLUSION`)**: If `/robots.txt`, edge headers (`X-Robots-Tag: noindex`), or HTTP 403 blocks live AI retrieval crawlers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`), suppress downstream text citability, entity ambiguity, and authority findings on blocked routes (`MATERIAL_ENTITY_AMBIGUITY`, `MISSING_SAMEAS_VERIFICATION`, `UNLINKED_KNOWLEDGE_GRAPH_ANCHOR`, `MISSING_IN_DEPTH_MECHANISMS`, `LACK_OF_SPECIFIC_EVIDENCE`, `COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT`).
3. **Layer 1 Shell (`RENDERED_CONTENT_GAP`)**: If initial HTML is a blank SPA shell (SSR vs CSR text parity ratio < 0.40, < 30 body words, or SNR < 0.08), suppress downstream Layer 2 answerability (`ATTRIBUTE_INCOMPLETENESS`, `INCOMPLETE_OFFER_ATTRIBUTES`), Layer 3 fact consistency (`FIRST_PARTY_FACT_CONFLICT`, `CONFLICTING_COMMERCIAL_TERMS`, `MISSING_MATERIAL_FACT`), Layer 4 GEO citability (`LOW_CITABILITY_SCORE`, `SUB_THRESHOLD_CITABILITY`), and Layer 6 engagement (`CTA_REACHABILITY_FRICTION`, `ABOVE_FOLD_ACTION_DELAY`) findings on unrendered containers.
4. **Symptom Nesting (`downstream_symptoms`)**: Suppressed downstream findings are NOT discarded silently. They are nested under the keystone finding's `downstream_symptoms` list (`CAUSE_KEY: description`), preserving diagnostic observability without inflating report finding counts or triggering false alarms.
5. **Conditional Proactive Actions**: When unrendered product routes contain suppressed schema omissions, synthesize conditional pre-hydration structured data specifications under `proactive_actions` (e.g. `P-003: Pre-Hydration Product Schema Architecture`) to prepare engineering for post-SSR deployment.

---

## 2. Orthogonal Citability Weights & Composite Scoring

Audits compute 6 orthogonal dimensions normalized to [0, 100]:

| Dimension | Weight | Primary Diagnostic Focus | Healthy Threshold |
| --- | :---: | --- | :---: |
| **Crawlability** | 20% | RFC 9309 permissions across 16 AI bots, sitemap integrity, HTTP 200 | >= 85.0 |
| **Retrieval Readiness** | 15% | Text-to-HTML SNR (>0.08), semantic landmark coverage, raw HTML readability | >= 80.0 |
| **Citation Readiness** | 25% | Princeton KDD 2024 vectors: causal conjunctions, statistics, tables, BLUF | >= 70.0 |
| **Entity Authority** | 20% | Schema.org @graph Organization, declared sameAs nodes, Knowledge Graph anchors | >= 75.0 |
| **Cross-Engine Visibility** | 10% | Parity across ChatGPT Search, Claude, Perplexity, and Google AI Overviews | >= 75.0 |
| **Agentic Commerce** | 10% | Product/Offer schema, /pricing.md, /llms.txt, transactional CTA reachability | >= 75.0 |

```text
Composite Score = 0.20 * C_crawl + 0.15 * R_retr + 0.25 * C_cite + 0.20 * E_auth + 0.10 * V_cross + 0.10 * A_comm
```

- **Grade A**: >= 85.0 | **Grade B**: 70.0 - 84.9 | **Grade C**: 50.0 - 69.9 | **Grade D**: 30.0 - 49.9 | **Grade F**: < 30.0
- **Dimension Status**: Each dimension evaluates to `"pass"` (>= threshold), `"warning"` (healthy - 20 <= score < healthy), or `"fail"` (< healthy - 20).


---

## 3. The 9 Princeton KDD 2024 / AutoGEO Citability Vectors

Empirical benchmarks governing generative engine source selection:

1. **Attributed Quotations (+40.9% Citation Lift)**: Direct quotes from named, credentialed experts (Q-Graders, licensed engineers, PhD researchers) substantiate technical claims.
2. **Statistical Benchmark Density (+40.0% Lift)**: Verifiable quantitative metrics, percentages, ratios, and empirical cupping/benchmark numbers outperform qualitative adjectives.
3. **Causal Conjunctions (+28.2% Lift)**: Mechanistic depth explaining *how* and *why* via connectors (`because`, `therefore`, `enables`, `results in`).
4. **BLUF Primacy (Bottom Line Up Front)**: 40–60 word direct factual answer placed in the first 30% of a passage under a conversational question heading.
5. **Modular Passage Chunking**: Standalone, self-contained semantic passages sized between 134 and 167 words.
6. **Semantic Data Structuring**: Responsive HTML `<table>` comparison specs and `<dl>` definition lists provide dense tabular facts that answer engines ingest directly.
7. **Fluff Elimination**: Zero speculative marketing superlatives ("revolutionary", "ultimate", "state-of-the-art"). Replaced with objective empirical specifications.
8. **Self-Containment & Zero Pronoun Ambiguity**: Resolving exophoric pronouns ("it", "they", "we") to canonical brand/product entity names to eliminate dangling neural references.
9. **Unique Information Gain**: Proprietary primary data, lab cupping scores, extraction yield percentages, and original empirical research.

---

## 4. The 17 Keystone Root-Cause Taxonomy Keys

Every finding MUST bind to one of the 17 standardized cause keys. Runtime sensors emit empirical telemetry mapped to these canonical synthesis keys:

| Cause ID (Synthesis Key) | Runtime Sensor Mapping | Functional Domain | Detection Condition |
| --- | --- | --- | --- |
| **`AI_RETRIEVAL_BLOCKED`** | `AI_RETRIEVAL_BLOCKED` | Discoverability | Disallow on live retrieval bots (`OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot`). |
| **`META_DIRECTIVE_CONFLICT`** | `NOINDEX_EXCLUSION` | Discoverability | `noindex` or `none` in HTML meta tags or `X-Robots-Tag` HTTP header. |
| **`CANONICAL_TARGET_MISMATCH`** | `CANONICAL_FRAGMENTATION` | Discoverability | Canonical link points to external domain, 404 URL, or redirect chain. |
| **`RENDERED_CONTENT_GAP`** | `RENDERED_CONTENT_GAP` | Discoverability | Client-side CSR rendering gap; initial unrendered HTML is a blank shell. |
| **`MATERIAL_ENTITY_AMBIGUITY`** | `MATERIAL_ENTITY_AMBIGUITY` | Entity Identity | Zero Schema.org `Organization` JSON-LD markup or missing brand identity anchor. |
| **`ATTRIBUTE_INCOMPLETENESS`** | `ATTRIBUTE_INCOMPLETENESS` | Entity Identity | Product or Offer schema missing required priceCurrency, price, or availability. |
| **`FIRST_PARTY_FACT_CONFLICT`** | `FIRST_PARTY_FACT_CONFLICT` | Fact Consistency | Numerical contradiction across first-party routes (e.g. price divergence). |
| **`TEMPORAL_DRIFT_DETECTED`** | `CONTENT_RECENCY_DEFICIT` | Fact Consistency | Copyright year or corporate contact terms stale (>2 years out of date). |
| **`UNVERIFIED_AUTHORITY_GAP`** | `WEAK_IDENTITY_SIGNALS` | Corroboration | Zero declared `sameAs` links to third-party knowledge bases (Wikidata, LinkedIn). |
| **`BROKEN_AUTHORITY_ANCHOR`** | `BROKEN_AUTHORITY_ANCHOR` | Corroboration | Declared `sameAs` link returns HTTP 404 or points to an unrelated entity. |
| **`SUB_THRESHOLD_CITABILITY`** | `LOW_CITABILITY_SCORE` | GEO Content | Explanatory depth score < 3/10; body text lacks causal connectors and stats. |
| **`PRONOUN_AMBIGUITY_DENSITY`** | `PRONOUN_AMBIGUITY_DENSITY` | GEO Content | High ratio of unresolved pronouns ("it", "they") in lead descriptive sections. |
| **`MISSING_BLUF_PRIMACY`** | `CONTEXT_PLACEMENT_DEGRADATION` | GEO Content | Core factual answer buried beneath decorative hero text (>150 words to first fact). |
| **`HEADING_HIERARCHY_VACUUM`** | `GENERIC_H1` | Engagement | Page completely omits semantic `<h1>` tag or skips levels (`<h1>` -> `<h3>`). |
| **`INTENT_SCENT_DILUTION`** | `LOW_INFORMATION_SCENT` | Engagement | Landing `<h1>` fails to confirm referred entity and intent within 5-second test. |
| **`COMMERCIAL_HANDOFF_DISCONTINUITY`** | `INTENT_TO_LANDING_MISMATCH` | Engagement | Commercial pricing displayed without an actionable transactional purchase link. |
| **`ABOVE_FOLD_ACTION_DELAY`** | `CTA_REACHABILITY_FRICTION` | Engagement | Primary CTA buried beyond top 600px viewport or omitted from hero DOM. |

### Taxonomy & Alias Synchronization

The causal DAG and orchestrator recognize bidirectional aliases between synthesis keys and sensor output keys:

- `META_DIRECTIVE_CONFLICT` <-> `NOINDEX_EXCLUSION`
- `CANONICAL_TARGET_MISMATCH` <-> `CANONICAL_FRAGMENTATION`
- `UNVERIFIED_AUTHORITY_GAP` <-> `WEAK_IDENTITY_SIGNALS`
- `SUB_THRESHOLD_CITABILITY` <-> `LOW_CITABILITY_SCORE`
- `MISSING_BLUF_PRIMACY` <-> `CONTEXT_PLACEMENT_DEGRADATION`
- `INTENT_SCENT_DILUTION` <-> `LOW_INFORMATION_SCENT`
- `COMMERCIAL_HANDOFF_DISCONTINUITY` <-> `INTENT_TO_LANDING_MISMATCH`
- `ABOVE_FOLD_ACTION_DELAY` <-> `CTA_REACHABILITY_FRICTION`
- `TEMPORAL_DRIFT_DETECTED` <-> `CONTENT_RECENCY_DEFICIT`

---

## 5. Business Archetype Diagnostic Playbooks

| Archetype | Essential Schema Markup | Critical Proactive Requirements | Primary Conversion Vector |
| --- | --- | --- | --- |
| **`ecommerce`** | `Product`, `Offer`, `AggregateRating` | `/pricing.md`, spec tables, ISO 4217 | Primary purchase action in top 3 DOM elements |
| **`saas`** | `SoftwareApplication`, `Offer` | `/pricing.md`, un-gated tier matrix | Self-serve onboarding / free trial CTA in hero |
| **`publisher`** | `NewsArticle`, `Person` (E-E-A-T) | Author credentials, `/llms.txt`, BLUF leads | Related reading depth, newsletter subscription |
| **`local_business`** | `LocalBusiness`, `GeoCoordinates` | OpeningHoursSpecification, telephone, map link | Click-to-call, reservation / directions link |

---

## 6. Proactive Machine Manifests

Autonomous agents evaluate websites via clean plain-text endpoints:

1. **`/llms.txt`**: Standardized markdown index summarizing brand offerings with BLUF overviews and hierarchical links.
2. **`/pricing.md`**: Un-gated structured markdown comparison table detailing plan tiers, seat limits, shipping thresholds, and volume discounts for autonomous purchasing agents (OpenAI Operator, Google Mariner).

---

## 7. Engine-Specific Citability Profiles

Each major AI retrieval engine and generative search system utilizes distinct retrieval criteria, ranking weights, and citation synthesis heuristics:

| Engine | Primary Retrieval Vector | Critical Architectural Requirements | Key Citability Trigger |
| --- | --- | --- | --- |
| **ChatGPT Search** | Semantic HTML & Graph Linked Data | Clean HTML structure, Schema.org `@id` graph linked data, zero wrapper bloat | Top-30% BLUF placement directly beneath question headings |
| **Perplexity Pro** | Empirical Metrics & Academic Anchors | Numerical benchmark statistics density, verified real-time facts | Academic and institutional authority anchors (Wikidata, DOI, arXiv) |
| **Claude Search** | Mechanistic Explanatory Depth | Causal conjunction density (`how`, `why`, `because`, `therefore`), depth of explanation | Credentialed author attribution and substantive procedural detail |
| **Google AI Overviews** | Consensus & Information Gain | Multi-source consensus, complete `LocalBusiness` / `Product` schema attributes | First-party proprietary data providing net-new Information Gain |

---

## 8. Execution Invariants & Clean Output Delivery Standard

1. **Single-Pass Acquisition Mandate:** Web crawling is strictly performed once via `acquire_inventory.py` / `web-scraper` emitting `inv.json`. All downstream diagnostic sensors analyze `inv.json` offline.
2. **Strictly Banned Agent Tools:** Never use agent built-in URL reading tools (`read_url_content`, `open_browser_url`, `browser_subagent`) or direct `curl`/`wget`. Direct agent reading bypasses socket-level zero-trust SSRF validation and corrupts multi-skill analysis.
3. **Reproducible Report Synthesis (`--review`):** Candidate findings refined by the agent are synthesized using the canonical synthesis engine (`orchestrator.py --review <file>`), guaranteeing causal gating, scoring math consistency, and execution provenance via `run_manifest` (SHA-256 reference hashes).
4. **Clean Output Delivery:** Emit strictly the final validated Draft-07 JSON report in a single ````json```` block. Never prepend conversational preambles, intermediate tool traces, or duplicate Markdown tables before the JSON block.
5. **Clean String Formatting:** In JSON report string fields (`technical_fix`, `creative_fix`, `summary`, `evidence`), never embed escaped literal newlines (`\n\n`), raw Markdown tables (`| Col | Col |`), or raw HTML. Strings must be clean, single-line or semicolon-delimited (` ; `).

---

## 9. Post-Citation Engagement & The 5-Second Bounce Mechanisms

Securing an AI citation (via ChatGPT, Perplexity, or Claude) is only half the battle. When referred visitors arrive, an estimated 60-70% bounce within 5 seconds if the destination fails first-visit orientation. The suite diagnoses this through 7 distinct failure mechanisms:

1. **`VIEWPORT_ANSWER_ABSENCE`**: The exact proposition, price, or claim cited in the generative AI answer is absent from the top 600px above-the-fold viewport. The visitor cannot immediately verify what the AI promised, triggering an immediate bounce.
2. **`LOW_INFORMATION_SCENT` (`GENERIC_H1`)**: The primary `<h1>` or lead headline uses generic marketing slogans ("Welcome to the Future", "Elevate Your Journey") instead of confirming the specific brand, product, or topic entity cited by the AI model.
3. **`CTA_REACHABILITY_FRICTION`**: The next conversion action is buried beneath multi-tier navigation menus, modal overlays, or deep scrolling (>3 interaction events to reach the primary transaction path).
4. **`COMMERCIAL_HANDOFF_DISCONTINUITY`**: The AI summary cites commercial terms or products, but the landing page provides only informational content or forces a generic "Contact Sales" form without transparent transactional checkout.
5. **`AGENT_INTERACTION_BARRIER`**: Critical conversion triggers and navigation links are implemented as non-semantic `<div onclick>` or `<span onclick>` elements rather than standard `<a href>` or `<button type="button">`, blocking both autonomous buying agents (OpenAI Operator, Project Mariner) and assistive keyboard technologies.
6. **`LOCALE_MISCONFIGURATION`**: Cross-language or cross-regional links land users on mismatched languages, non-local currency, or missing `hreflang` routes, causing immediate regional bounce.
7. **`COGNITIVE_READABILITY_FRICTION`**: High Automated Readability Index (ARI > 14) and dense marketing jargon obscure direct answers, causing cognitive fatigue for users seeking immediate factual clarity.


