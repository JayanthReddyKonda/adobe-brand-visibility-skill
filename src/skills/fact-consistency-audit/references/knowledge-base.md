# Fact Consistency & Lifecycle Audit — Knowledge Base & Reference

Master reference defining the scoped first-party fact ledger, temporal freshness hierarchy, product lifecycle synchronization, and mathematical normalization algorithms.

---

## 1. Contextual Scope Invariant & False-Positive Prevention

A finding of `FIRST_PARTY_FACT_CONFLICT` is **valid ONLY when two or more first-party statements share the EXACT SAME entity, attribute, and scope**:

```text
Conflict(Fa, Fb) <==> (Entity_a == Entity_b) and (Attribute_a == Attribute_b) and (Scope_a == Scope_b) and (Value_a != Value_b)
```

### False Positive Prevention (What NOT to Compare):
- **Distinct Pricing Tiers:** A $10/mo "Starter Tier" and $50/mo "Pro Tier" share the attribute `price` but possess different entity scopes. Comparing them as a contradiction is a defect evaluation failure.
- **Volume & Billing Cycles:** Annual billing ($8/mo billed annually) vs monthly billing ($10/mo billed monthly) represent distinct billing scopes.
- **Regional Currencies:** $100 USD vs €95 EUR represent distinct currency scopes.
- **Catalog Listings:** Different products listed on an overview or category page.

### Report As Defect ONLY When:
- **Verified Cross-Page Contradiction:** The exact same product/tier (e.g. "Velocity X9 Drone") is stated at one price on the main product landing page (e.g. "$5,499") and a different contradictory price on a secondary/legacy page (e.g. "$4,999") without qualifying scope.
- **Markup Discrepancy:** The visible on-page text states "$49", but JSON-LD `offers.price` states `"99"`.

---

## 2. The Timestamp & Temporal Freshness Hierarchy

AI retrieval systems weight first-party brand statements based on temporal signals. When different pages on the same domain state conflicting facts, AI models evaluate freshness using the following signal hierarchy (ordered from strongest to weakest):

1. **Explicit Schema.org Timestamps:** `dateModified` and `datePublished` in JSON-LD.
2. **HTTP Last-Modified Header:** Server-validated document mutation timestamp.
3. **OpenGraph Timestamps:** `article:modified_time` and `og:updated_time`.
4. **On-Page Copyright Statement:** `© [Year] [Organization]`.

### Temporal Drift & Legacy Template Rules

| Signal | Criteria | Finding / Classification | Action |
|---|---|---|---|
| **Multi-Year Copyright Drift** | Copyright year on an active page is >= 2 years older than the homepage (e.g. 2022 on `/terms` vs 2026 on `/`). | **Low** (`LEGACY_FACT_PROPAGATION`) | Update legacy page templates to dynamically inherit current copyright year. |
| **Outdated Tagline Drift** | An old slogan is stated in footer markup while an active repositioning campaign exists on the homepage. | **Low** (`LEGACY_FACT_PROPAGATION`) | Harmonize brand tagline strings across all active layouts. |
| **Current Copyright Year** | Copyright year matches current calendar year or current year +/- 1. | **Pass** | No action required. |

---

## 3. Product Lifecycle Consistency Matrix

A major failure mode in AI-generated answers is recommending discontinued or out-of-stock products as active offerings, caused by contradictory lifecycle states across the brand's own pages.

### Contradiction Criteria:
- **Discontinued vs Active Conflict:** A product is declared `discontinued` or `out of production` on a product notice/archive page, but is marked `InStock` or listed as an active commercial offering on a pricing or category page.
- **Severity:** `High` (`DISCONTINUED_VS_CURRENT_CONFLICT`).
- **Impact:** AI shopping and search assistants provide inaccurate availability guidance to potential buyers.

### Verification Guardrail:
- Never classify an entire page as discontinued based on a single word in global headers or footers. The discontinued indicator must be strictly bound to the specific product entity or heading.

---

## 4. Formal Diagnostic Check Contracts

### C1. Scoped Price Contradictions
- **Measures:** Numeric prices, plan tier figures, and currency symbols across sampled first-party pages for the identical named entity.
- **Defect:** Two or more pages publishing different active prices for the same product without qualifying scope (`FIRST_PARTY_FACT_CONFLICT`, Severity: `high`, Confidence: `high`).
- **Not a defect:** Distinct commercial plan tiers (e.g. Basic $10 vs Pro $50) or seasonal promotions clearly scoped with temporal qualifiers.

### C2. Product Lifecycle & Stock State Synchronization
- **Measures:** Commercial lifecycle status (active, in_stock, out_of_stock, discontinued, retired) declared across product pages and listings.
- **Defect:** A product marked as discontinued on one page but actively listed as in-stock on another (`DISCONTINUED_VS_CURRENT_CONFLICT`, Severity: `high`).
- **Not a defect:** Backorder items with stated delivery estimates.

### C3. Contact Channel & Support Consistency
- **Measures:** Primary support email addresses, phone numbers, and physical addresses across contact, footer, and support pages.
- **Defect:** Multiple conflicting primary contact points without geographic or department qualifiers (`INCONSISTENT_CONTACT_INFO`, Severity: `medium`).

### C4. Temporal Freshness & Copyright Timestamps
- **Measures:** Copyright year notices and dateModified timestamps.
- **Defect:** Multi-year outdated copyright notices across core routes suggesting stale site maintenance (`TEMPORAL_FRESHNESS_DRIFT`, Severity: `low`).

---

## 5. Mathematical Normalization Algorithms

To eliminate false-positive contradictions caused by locale or formatting discrepancies, raw fact strings undergo normalization prior to ledger comparison:

### 5.1 Currency & Price Normalization

| Raw String | Locale / Format | Normalized Value | Notes |
|---|---|---|---|
| `₹5,499.00` | INR with decimal | `5499` | Strip currency symbol, comma, and trailing `.00`. |
| `$49.99` | USD standard | `49` | Normalized to base integer unit. |
| `€1.250,50` | European (dot thousands, comma decimal) | `1250` | Strip dot group separator, discard decimal comma. |
| `£99 / month` | GBP subscription | `99` | Strip cadence suffix and whitespace. |

### 5.2 Contact & Phone Normalization
- **Phone Numbers:** Strip non-digits (`+1 (800) 555-0199` -> `18005550199`). Compare only within the same contact department scope (e.g. Sales Phone vs Support Phone).
- **Email Addresses:** Lowercase and strip whitespace. Scoped by department mailbox (`support@brand.com` vs `sales@brand.com`).
