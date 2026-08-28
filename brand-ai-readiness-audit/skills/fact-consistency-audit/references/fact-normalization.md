# Fact Normalization & Contradiction Detection Reference

This reference defines the mathematical normalization algorithms and strict contextual scoping rules required to eliminate false positive contradiction findings across first-party pages.

---

## 1. Contextual Scope Invariant

A finding of `FIRST_PARTY_FACT_CONFLICT` is **valid ONLY when two or more first-party statements share the EXACT SAME entity, attribute, and scope**:

$$\text{Conflict}(\text{Fact}_A, \text{Fact}_B) \iff (\text{Entity}_A = \text{Entity}_B) \land (\text{Attribute}_A = \text{Attribute}_B) \land (\text{Scope}_A = \text{Scope}_B) \land (\text{Val}_A \neq \text{Val}_B)$$

### False Positive Prevention (What NOT to Compare):
- **Distinct Pricing Tiers:** A \$10/mo "Starter Tier" and \$50/mo "Enterprise Tier" share the attribute `price` but have different `entity` scopes. Comparing them as a contradiction is an automatic evaluation failure.
- **Volume & Billing Cycles:** Annual pricing (\$8/mo billed annually) vs Monthly pricing (\$10/mo billed monthly) represent distinct billing scopes.
- **Regional Currencies:** \$100 USD vs €95 EUR represent distinct currency scopes.

---

## 2. Currency & Price Normalization Algorithm

To compare prices across disparate formats (US, UK, Indian, European), values must undergo strict digit normalization:

| Raw String | Locale / Format | Normalized Value | Notes |
|---|---|---|---|
| `₹5,499.00` | INR with decimal | `5499` | Strip currency symbol, comma, and trailing `.00`. |
| `$49.99` | USD standard | `49` | Normalized to base integer unit. |
| `€1.250,50` | European (dot thousands, comma decimal) | `1250` | Strip dot group separator, discard decimal comma. |
| `£99 / month` | GBP subscription | `99` | Strip cadence suffix and whitespace. |

---

## 3. Contact & Phone Normalization

- **Phone Numbers:** Strip non-digits (`+1 (800) 555-0199` $\to$ `18005550199`). Compare only within the same contact department scope (e.g. Sales Phone vs Support Phone).
- **Email Addresses:** Lowercase and strip whitespace. Scoped by department mailbox (`support@brand.com` vs `sales@brand.com`).
