# Fact Consistency & Lifecycle Audit — Check Contracts

Formal check contracts, decision thresholds, and evidence criteria for first-party fact consistency and lifecycle synchronization.

---

## C1. Scoped Price Contradictions
- **Measures:** Numeric prices, plan tier figures, and currency symbols across sampled first-party pages for the identical named entity.
- **Defect:** Two or more pages publishing different active prices for the same product without qualifying scope (`FIRST_PARTY_FACT_CONFLICT`, Severity: `high`, Confidence: `high`).
- **Not a defect:** Distinct commercial plan tiers (e.g. Basic \$10 vs Pro \$50) or seasonal promotions clearly scoped with temporal qualifiers.

---

## C2. Product Lifecycle & Stock State Synchronization
- **Measures:** Commercial lifecycle status (active, in_stock, out_of_stock, discontinued, retired) declared across product pages and listings.
- **Defect:** A product marked as discontinued on one page but actively listed as in-stock on another (`DISCONTINUED_VS_CURRENT_CONFLICT`, Severity: `high`).
- **Not a defect:** Backorder items with stated delivery estimates.

---

## C3. Contact Channel & Support Consistency
- **Measures:** Primary support email addresses, phone numbers, and physical addresses across contact, footer, and support pages.
- **Defect:** Multiple conflicting primary contact points without geographic or department qualifiers (`INCONSISTENT_CONTACT_INFO`, Severity: `medium`).

---

## C4. Temporal Freshness & Copyright Timestamps
- **Measures:** Copyright year notices and dateModified timestamps.
- **Defect:** Multi-year outdated copyright notices across core routes suggesting stale site maintenance (`TEMPORAL_FRESHNESS_DRIFT`, Severity: `low`).
