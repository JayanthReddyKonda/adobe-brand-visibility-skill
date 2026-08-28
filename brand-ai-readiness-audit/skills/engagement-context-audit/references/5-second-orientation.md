# 5-Second Orientation & Information Scent Framework

This reference outlines the empirical methodology for evaluating first-visit user orientation, heading information scent, and intent-handoff continuity for visitors referred from AI search engines (ChatGPT Search, Claude, Perplexity AI, Google AI Overviews).

---

## 1. The 4-Question First-Visit Orientation Test

When a user clicks a citation link from an AI assistant answer, they arrive with high contextual momentum and narrow search intent. Within **5 seconds** (above the fold, before scrolling), the landing page must answer four core orientation questions:

1. **What is this?** (Product / Service category definition).
2. **Who is this for?** (Target persona, developer tier, industry vertical).
3. **Why is it relevant?** (Primary value proposition or differentiating capability).
4. **What can I do next?** (Clear next step, CTA, or discoverable destination navigation).

---

## 2. Heading Information Scent Matrix

Headings are the primary structural anchors used by both human scanners and AI extractors to construct the semantic outline of a page.

| Signal | Evaluation Criteria | Severity | Mechanism-Correct Action |
|---|---|---|---|
| **Informative H1** | Contains concrete brand nouns, capability verbs, and category terminology (e.g. *"Enterprise Cloud Infrastructure Monitoring"*). | **Pass** (Score: 1.0) | Retain and align with `<title>`. |
| **Generic H1** | One-word or generic greeting terms (e.g. *"Welcome"*, *"Home"*, *"Main"*, *"Overview"*). | **Low** (`LOW_INFORMATION_SCENT`) | Revise H1 to include concrete product nouns and value verbs. |
| **Missing H1 with Descriptive Title** | Page lacks an `<h1>` element but provides informative `<title>` and `<h2>` subheadings. | **Recommendation** | Add explicit semantic `<h1>` matching the page title. |
| **Missing H1, Subheadings & Title** | 0 `<h1>`, 0 `<h2>`, and uninformative `<title>` on a content page (>80 words). | **Medium** (`LOW_INFORMATION_SCENT`) | Add a prominent `<h1>` headline above the fold stating value proposition. |

---

## 3. Destination Reachability & Navigation Friction

AI-referred visitors often land on deep sub-pages (e.g. a specific product or documentation guide) rather than the homepage. The page must provide discoverable pathways to core brand destinations:

- **Core Destinations:**
  1. `Pricing` (or Plans / Billing / Tiers)
  2. `Products` (or Features / Catalog / Solutions)
  3. `About` (or Company / Team / Story)
  4. `Contact` (or Support / Help Desk)

- **Friction Detection Rule:**
  If a content page exposes fewer than 3 navigation links and lacks pathways to any of the 4 core destinations, flag `DESTINATION_NAVIGATION_FRICTION` (Severity: `medium`).

---

## 4. Intent-to-Landing Match (Specialized Routes)

Specialized landing routes must immediately satisfy the intent implied by their URL and title:

- **Pricing Route (`/pricing`, `/plans`):** Must display transparent numerical prices, starting price figures, tier names, or plan breakdown tables above the fold. Omitting price figures triggers `INTENT_TO_LANDING_MISMATCH` (Severity: `medium`).
- **Product Route (`/product/*`, `/shop/*`):** Must present the product name, primary specification, availability state, and purchase/inquiry CTA.
