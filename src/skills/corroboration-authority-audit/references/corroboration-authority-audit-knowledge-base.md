# CORROBORATION-AUTHORITY-AUDIT KNOWLEDGE BASE

This document contains all mandatory rules, schemas, and taxonomies required for this skill.

---

## Identity Link Verification vs Claim Corroboration Reference

This reference defines the strict boundary between identity link verification (`sameAs` resolution) and external claim corroboration.

---

## 1. Identity Link Verification (Specialist Finding Scope)

Identity link verification tests whether external authority anchors declared by the brand in its Schema.org `Organization` markup actually exist and resolve cleanly without HTTP errors.

### The Verification Contract:
1. **Target URLs:** Declared `sameAs` links pointing to external registries (Wikidata, Wikipedia, Crunchbase, official GitHub, LinkedIn, X/Twitter).
2. **Deterministic Probing:** Probe up to 5 declared links using SSRF-safe HTTP HEAD/GET requests with a bounded 5-second timeout.
3. **Defect Condition:** If a declared `sameAs` link returns HTTP `4xx` (404 Not Found, 410 Gone) or `5xx` server error:
   - **Classification:** Finding (`BROKEN_AUTHORITY_ANCHOR`).
   - **Severity:** `Medium`.
   - **Confidence:** `High`.
   - **Rationale:** A broken authority link actively degrades the AI model's trust in the entity resolution graph.
4. **Absence of Links:** If no `sameAs` links are declared in JSON-LD:
   - **Classification:** **Recommendation** (never a defect finding).
   - **Severity:** `Low` / Proactive.

---

## 2. Declared Identity Nodes vs. Verified Candidate Backlinks (Two Explicit Evidence Classes)

A critical architectural principle of this skill is the strict separation between two evidence classes:

1. **Declared Identity Nodes (`declared_identity_nodes`):**
   - **Definition:** Outbound entity declarations provided by the brand within its first-party JSON-LD `sameAs` array (Wikidata, Wikipedia, LinkedIn, YouTube, X, GitHub, Crunchbase).
   - **Purpose:** Disambiguates *who the brand is* across global knowledge graphs and social footprints.
   - **Verification:** Probed via SSRF-safe HTTP HEAD/GET to ensure resolution with HTTP 200 and explicit brand name corroboration in title or OpenGraph metadata.
   - **Defect:** 4xx/5xx responses indicate broken identity anchors (`BROKEN_AUTHORITY_ANCHOR`).

2. **Verified Candidate Backlinks (`verified_candidate_backlinks`):**
   - **Definition:** Inbound hyperlinks from third-party websites pointing *to* the brand's canonical domain or deep links (`<a href="https://brand.com/...">`).
   - **Purpose:** Validates external editorial citations, press mentions, reviews, and community references that AI search engines retrieve during query fan-out.
   - **Verification Input Contract:** Ingests user-supplied candidate backlink URLs via `--candidate-backlinks` or `inventory.json`. Probes each candidate page (capped at 10, 5s timeout, 512 KiB limit, SSRF-safe) to verify the actual presence of the inbound hyperlink, anchor text, and `rel` attributes (`nofollow`, `ugc`, `sponsored`, `dofollow`).

### The Common Crawl CDX Limitation (Why Web-Wide Discovery Cannot Be Claimed):
- **The Myth:** Some tools claim to perform "instant web-wide backlink discovery" using the public Common Crawl CDX API.
- **The Technical Reality:** The Common Crawl CDX index is an index of **crawled URLs**, capturing page URLs, timestamps, MIME types, and WARC offsets. It is **NOT** an inverted index of web links/hyperlinks pointing to arbitrary target domains. To discover all pages linking to a brand from Common Crawl, one would need to download and parse petabytes of WARC/WAT files across billions of pages.
- **Engineering Boundary:** The skill operates honestly: it does NOT claim web-wide backlink discovery from URL-only indexes. Instead, it provides a bounded, SSRF-safe verification engine for user-supplied candidate backlink ledgers.

---

## 3. External Claim Corroboration (Out-of-Scope Boundary)

External claim corroboration refers to searching the open web to independently verify factual claims made by the brand (e.g. "Founded in 2018", "#1 Coffee Roaster in California").

### Boundary Rules:
- **No Unbounded Web Crawling:** Performing open-ended web searches during an audit introduces non-deterministic latency, third-party API dependencies, and rate limits that violate the 5-minute wall-clock execution ceiling.
- **First-Party Grounding:** The audit evaluates first-party machine-explicitness, structured schema integrity, and declared anchor validity.
- **Inconclusive Handling:** If a third-party registry times out, rate-limits (HTTP 429), or requires Cloudflare bot verification, the probe is recorded as `inconclusive` and NEVER reported as a broken link defect.

---

## Corroboration & Authority — Check Contracts

Every check in this skill follows this contract. Findings are only emitted
when the DEFECT conditions are met with direct evidence; everything else is
either INCONCLUSIVE or a proactive recommendation.

## CHECK 1: Identity Profile Verification (`sameAs` resolution)

- **Measures**: Whether declared `sameAs` authority links in Schema.org `Organization` resolve cleanly with HTTP 200.
- **Evidence required**: Bounded SSRF-safe probe of declared `sameAs` URLs.
- **Defect**: Declared authority profile returns HTTP 4xx or 5xx (`BROKEN_AUTHORITY_ANCHOR`).
- **NOT a defect**: Absence of declared `sameAs` links (emitted as a proactive recommendation, never a defect). Timeout or rate-limit recorded as `inconclusive`.
- **Severity conditions**: `medium` severity, `high` confidence when declared authority links provably fail.
- **Remediation**: Update dead `sameAs` URLs to live canonical profile links or remove broken references.

## CHECK 2: Identity consistency for corroboration

- **Measures**: Whether the site's name, domain, and profile references are
  coherent enough for third parties to corroborate the entity.
- **Evidence required**: Title/org extraction across home + internal pages.
- **Defect**: Verified contradiction (e.g., different organization names
  presented as canonical on different first-party pages).
- **NOT a defect**: Missing `sameAs`, missing social links, or a single
  organization name that merely varies in formatting (e.g. "Acme" vs "Acme Inc").
- **Severity conditions**: medium for verified contradictions; missing links
  are never findings.
- **Remediation**: Standardize the canonical entity name and add `sameAs`.

## Evidence hierarchy

Findings here rely on Levels 1–3 (direct HTTP/DOM, structured data, cross-page
first-party). Level 6 (heuristic inference) never produces high severity.

---

## External Authority Channels & AI Citation Weight Matrix

AI search engines (Perplexity, ChatGPT Search, Claude Search) do not rely solely on internal HTML markup; they cross-validate entity claims against authoritative external web nodes.

## Top Authority Node Archetypes:
1. Wikidata & Wikipedia (QID Linking): Primary source of truth for entity disambiguation in Google Knowledge Graph and open foundation models.
2. Official YouTube & Social Hubs: Highly weighted multi-modal citation anchors (~0.737 correlation with AI search answers).
3. LinkedIn Corporate Directory: Verifies operational legitimacy, employee size, and headquarters locale.
4. SEC / Crunchbase / Official Registries: Provides authoritative fiscal and corporate founding facts.

## Audit Rule:
Declaring sameAs links to 4xx/5xx dead profiles damages the brand entity trust score. Probing declared links in real time ensures only live, authoritative anchors enter the Stateful Knowledge Graph.

---

## CHECK 3: Internal Mirror Domain Cluster Detection (`CIRCULAR_SAMEAS_SELF_REFERENCE`)

- **Measures**: Whether declared `sameAs` links point to external verifying authorities versus an internal cluster of mirror domains (`.to`, `.bz`, `.ru`, `.com`).
- **Defect**: When 2+ `sameAs` entries share the target brand's second-level domain (SLD) across different TLDs, indicating an alternate domain mirror cluster rather than independent verification.
- **Classification**: `CIRCULAR_SAMEAS_SELF_REFERENCE` (Family: `AUTHORITY.IDENTITY_CORROBORATION`).
- **Severity**: `high`.
- **Confidence**: `high`.
- **Impact**: In AI knowledge graphs, self-referencing mirrors trigger duplicate content penalties, domain-spoofing flags, and entity fragmentation.
- **Remediation**: Remove internal mirror domains from `sameAs` array in JSON-LD. Reserve `sameAs` strictly for independent third-party authorities (Wikidata, Wikipedia, Crunchbase, verified social hubs).

---

## Three-Tier Authority Classification Matrix

| Tier | Category | Target Examples | Knowledge Graph Value |
|---|---|---|:---:|
| **Tier 1** | **Global Knowledge Graph Nodes** | `wikidata.org`, `wikipedia.org`, `crunchbase.com` | **Highest (+100% Trust)**: Anchors entity in pre-training corpora |
| **Tier 2** | **Verified Social / Code Footprints** | `x.com`, `linkedin.com/company`, `github.com` | **High (+70% Trust)**: Validates continuous operational activity |
| **Tier 3** | **Internal Mirror Domains (Defect)** | Same SLD across `.to`, `.bz`, `.ru`, `.com` | **Negative (Domain Spoofing / Entity Fragmentation)** |

---

## Empirical Platform Correlation with AI Citations (Ahrefs 75,000 Brand Study)

Brand mentions correlate 3x more strongly with AI visibility than traditional backlinks:

| Platform | Correlation Coefficient | AI Search Weight | Strategic Mechanism |
|---|:---:|:---:|---|
| **YouTube** | **0.737** | **Highest (25%)** | Video titles, chapters, and auto-transcripts are indexed by multimodal search (Perplexity, Google AI Overviews). |
| **Reddit** | **High** | **High (25%)** | Conversational forums provide experiential, unvarnished peer consensus queried during intent fan-out. |
| **Wikipedia** | **High** | **High (20%)** | Foundation model pre-training corpora establish base entity identity from Wikipedia. |
| **LinkedIn** | **Moderate** | **Moderate (15%)** | Validates corporate founding, employee count, and B2B operational scale. |
| **Backlinks (DR)** | **0.266** | **Low (15%)** | Traditional PageRank signals have weak correlation with generative citation selection. |

