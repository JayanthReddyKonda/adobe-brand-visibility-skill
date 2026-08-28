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
