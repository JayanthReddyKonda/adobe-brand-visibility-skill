# Audit Check Contracts Catalog

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
- **Purpose:** Detect when initial unrendered HTML payload carries insufficient text.
- **Input:** Raw HTTP response body word count.
- **Decision:** Finding triggered IF visible word count < 30 words AND empty SPA root marker (`<div id="root">`, `<div id="app">`) is present.
- **Exclusion:** Do NOT report if visible words ≥ 30 words or if the page is an API endpoint.
- **Severity:** `high`.
- **Confidence:** `medium` (risk indicator; modern search engines may execute JS).
- **Remediation:** Implement server-side rendering (SSR), static generation (SSG), or dynamic pre-rendering for core text.
- **Verification:** Fetch raw HTML response and confirm main heading and copy are present without JS execution.

---

## 3. `MATERIAL_ENTITY_AMBIGUITY`
- **Skill:** `entity-content-audit`
- **Family:** `ENTITY.IDENTITY`
- **Purpose:** Ensure brand entity identity is machine-explicit.
- **Input:** Landing page JSON-LD, OpenGraph, `<title>`.
- **Decision:** Finding triggered IF no Organization/Brand schema, no `og:site_name`, and no title identity exists.
- **Exclusion:** Do NOT report if identity is clearly stated in OpenGraph or title.
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Publish Organization JSON-LD markup declaring name, logo, url, and sameAs links.
- **Verification:** Re-fetch landing page and verify Organization JSON-LD parses cleanly.

---

## 4. `FIRST_PARTY_FACT_CONFLICT`
- **Skill:** `fact-consistency-audit`
- **Family:** `FACT.CONSISTENCY`
- **Purpose:** Detect conflicting first-party representations of a product/tier price or specification.
- **Input:** Scoped fact ledger across first-party pages.
- **Decision:** Finding triggered IF the same product/plan name has distinct price values across 2+ pages.
- **Exclusion:** Do NOT report when distinct prices belong to different named tiers (Starter vs Pro) or billing intervals.
- **Severity:** `high`.
- **Confidence:** `high`.
- **Remediation:** Establish a single canonical price for the entity and synchronize across all product listings.
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

## 8. `AI_FACT_CONFLICT`
- **Skill:** `assistant-representation-audit`
- **Family:** `REPRESENTATION.ACCURACY`
- **Purpose:** Identify when an AI assistant quotes prices that contradict on-site reality.
- **Input:** Observed AI assistant claims vs first-party fact snapshot.
- **Decision:** Finding triggered IF assistant states a price that is absent from all on-site listings.
- **Exclusion:** Do NOT report if assistant accurately quotes current on-site pricing.
- **Severity:** `high`.
- **Confidence:** `high`.
- **Remediation:** Publish explicit Product JSON-LD to ground assistant retrieval.
- **Verification:** Re-pose prompt to assistant and verify quoted price matches on-site schema.
