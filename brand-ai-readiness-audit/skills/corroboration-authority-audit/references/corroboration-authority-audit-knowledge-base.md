# CORROBORATION-AUTHORITY-AUDIT KNOWLEDGE BASE

This document contains all mandatory rules, schemas, and taxonomies required for this skill.



========================================================================
=== SOURCE FILE: identity-vs-claim.md ===
========================================================================

# Identity Link Verification vs Claim Corroboration Reference

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

## 2. External Claim Corroboration (Out-of-Scope Boundary)

External claim corroboration refers to searching the open web to independently verify factual claims made by the brand (e.g. "Founded in 2018", "#1 Coffee Roaster in California").

### Boundary Rules:
- **No Unbounded Web Crawling:** Performing open-ended web searches during an audit introduces non-deterministic latency, third-party API dependencies, and rate limits that violate the 5-minute wall-clock execution ceiling.
- **First-Party Grounding:** The audit evaluates first-party machine-explicitness, structured schema integrity, and declared anchor validity.
- **Inconclusive Handling:** If a third-party registry times out, rate-limits (HTTP 429), or requires Cloudflare bot verification, the probe is recorded as `inconclusive` and NEVER reported as a broken link defect.


========================================================================
=== SOURCE FILE: corroboration-contracts.md ===
========================================================================

# Corroboration & Authority — Check Contracts

Every check in this skill follows this contract. Findings are only emitted
when the DEFECT conditions are met with direct evidence; everything else is
either INCONCLUSIVE or a proactive recommendation.

## CHECK 1: Outbound corroboration links

- **Measures**: Whether the site links out to authoritative third-party
  sources (standards bodies, registries, publications) that support its claims.
- **Evidence required**: Anchor inventory of fetched page(s).
- **Defect**: Site makes strong factual claims ("award-winning", "#1",
  certifications) with zero outbound or citation support.
- **NOT a defect**: Few outbound links on a page that makes few factual claims.
  Marketing pages legitimately link sparingly.
- **Severity conditions**: high only when specific unsupported factual claims
  are extractable from the text; otherwise low / recommendation.
- **Remediation**: Add citations or evidence pages behind the claims.

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
