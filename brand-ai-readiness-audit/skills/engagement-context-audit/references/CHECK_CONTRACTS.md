# Engagement & Context Continuity Audit — Check Contracts

Formal check contracts, decision thresholds, and evidence criteria for engagement and visitor orientation.

---

## C1. 5-Second Orientation & Heading Information Scent
- **Measures:** Presence and clarity of primary heading (`<h1>`), page `<title>`, and structural subheadings (`<h2>`) against the 4-question orientation framework (What is this? Who is it for? Why is it relevant? What can I do next?).
- **Defect:** Content-rich page (>150 words) with missing or empty `<h1>`, uninformative `<title>`, and zero `<h2>` subheadings (`LOW_INFORMATION_SCENT`, Severity: `medium`). Generic single-word heading like "Welcome" with low information scent (`LOW_INFORMATION_SCENT`, Severity: `low`).
- **Not a defect:** Clean, self-explanatory pages where `<title>`, hero copy, and interactive options orient the user immediately. Dedicated contact pages with standard headers ("Contact us", "Contáctenos") in any language.

---

## C2. Destination Discoverability & Navigation Friction
- **Measures:** Header, footer, and contextual navigation reachability to core brand destinations (catalog, pricing, about, contact, support).
- **Defect:** Truly orphaned landing pages (>150 words, 0 `<nav>` elements, <2 internal links) that trap visitors without navigation paths (`DESTINATION_NAVIGATION_FRICTION`, Severity: `medium`).
- **Not a defect:** Focused task funnels (checkout, standalone onboarding) or pages with clear contextual internal links and CTAs.

---

## C3. Intent-to-Landing Alignment
- **Measures:** Semantic continuity between incoming referral intent (e.g. pricing comparison, product purchase) and above-the-fold content.
- **Defect:** A pricing-designated landing URL containing zero visible numerical price figures, plan tiers, or commercial terms (`INTENT_TO_LANDING_MISMATCH`, Severity: `medium`).
- **Not a defect:** Enterprise "Contact Sales" quotes where custom pricing is explicitly indicated.
