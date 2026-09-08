# ENGAGEMENT-CONTEXT-AUDIT KNOWLEDGE BASE

## Table of Contents

- [1. First-Visit Orientation Heuristics (Above-the-Fold)](#1-first-visit-orientation-heuristics-above-the-fold)
- [2. Heading Hierarchy & Information Scent](#2-heading-hierarchy-information-scent)
- [3. Navigational Integrity & Journey Continuity](#3-navigational-integrity-journey-continuity)
- [1. Conclusion-First Writing Architecture](#1-conclusion-first-writing-architecture)
- [2. Heading Hierarchy & Information Scent](#2-heading-hierarchy-information-scent)
- [3. Snippet Visibility Controls](#3-snippet-visibility-controls)
- [C1. 5-Second Orientation & Heading Information Scent](#c1-5-second-orientation-heading-information-scent)
- [C2. Destination Discoverability & Navigation Friction](#c2-destination-discoverability-navigation-friction)
- [C3. Intent-to-Landing Alignment](#c3-intent-to-landing-alignment)
- [1. The 4-Question First-Visit Orientation Test](#1-the-4-question-first-visit-orientation-test)
- [2. Heading Information Scent Matrix](#2-heading-information-scent-matrix)
- [3. Destination Reachability & Navigation Friction](#3-destination-reachability-navigation-friction)
- [4. Intent-to-Landing Match (Specialized Routes)](#4-intent-to-landing-match-specialized-routes)

---

This document contains all mandatory rules, schemas, and taxonomies required for this skill.

---

## On-Site Orientation & Engagement Heuristics Rubric

This rubric evaluates how well a website retains visitors who arrive from AI search referrals, and how easily machines and humans comprehend the core offering within the first 5 seconds.

---

## 1. First-Visit Orientation Heuristics (Above-the-Fold)

- **The 5-Second Test**: Does the page immediately answer three core questions in semantic text without scrolling?
  1. *What is this product/service?*
  2. *Who is it for?*
  3. *What is the primary next step / Call to Action (CTA)?*
- **Hero Area Text Clarity**: Avoid vague buzzwords ("The next generation of synergy"). Demand concrete, specific value propositions ("Automated SOC 2 compliance for AWS and GCP environments").

---

## 2. Heading Hierarchy & Information Scent

- **Semantic Heading Flow (`H1` -> `H2` -> `H3`)**:
  - Exactly one substantive `<h1>` describing the page's core topic.
  - Logical `<h2>` subsections organizing features, workflows, and proofs.
  - Clear `<h3>` detail blocks.
- **Scannable Information Scent**: Headers must provide meaningful standalone value so both skimming human readers and AI summarizers can parse the key takeaways without reading full paragraphs.

---

## 3. Navigational Integrity & Journey Continuity

- **Clear Primary Navigation**: Visible links to Product, Features, Pricing, Docs, and About without hidden or broken multi-level hover menus.
- **Context Retention**: When users click from a specific AI citation link (e.g. deep link to a feature), does the destination page retain context or dump them into a generic homepage redirect?
- **Frictionless CTAs**: Clear, accessible buttons with unambiguous labels ("Start Free Trial", "Book Demo", "Read Documentation").

---

## AI Snippet & Information Scent Guidelines

How to structure on-page content so AI search assistants and human visitors can immediately extract answers and orient without bouncing.

---

## 1. Conclusion-First Writing Architecture

AI models and skimming visitors prioritize direct answers in above-the-fold passages:

- **Direct Answer in Lead Paragraph:** State the core definition, price, or product capability within the first 50–100 words.
- **Fact-Dense Sentences:** Use explicit combinations of `[Subject] + [Attribute] + [Numerical Value/Unit] + [Timeframe]`.
  - *Poor:* "Our revolutionary solution offers unprecedented affordability and power."
  - *Strong:* "The Velocity X9 drone costs ₹5,499, delivers 30 minutes of flight time, and captures 4K 60fps video."

---

## 2. Heading Hierarchy & Information Scent

Headings provide structural boundaries for passage indexing and AI chunking:

- **Single H1 per Page:** The primary `<h1>` must clearly name the brand, product, or core topic. Avoid generic filler titles ("Welcome", "Home", "Overview").
- **Question-Form H2/H3 Headings:** Phrase subheadings as clear questions or explicit topic statements (e.g. `<h2>What is the battery range of Velocity X9?</h2>`).
- **No Skipping Levels:** Maintain a strict logical hierarchy (`H1` -> `H2` -> `H3`). Never skip from `H1` directly to `H4`.

---

## 3. Snippet Visibility Controls

| Directive | Implementation | Effect on AI Answers |
| :--- | :--- | :--- |
| `nosnippet` | `<meta name="robots" content="nosnippet">` | Prevents the page from being quoted in snippets or AI Overviews entirely. |
| `max-snippet` | `<meta name="robots" content="max-snippet:160">` | Restricts snippet quotes to the specified character length. |
| `data-nosnippet` | `<div data-nosnippet>...</div>` | Excludes specific proprietary text or pricing footnotes from AI quotes while keeping the rest indexable. |

---

## Engagement & Context Continuity Audit — Check Contracts

Formal check contracts, decision thresholds, and evidence criteria for engagement and visitor orientation.

---

## C1. 5-Second Orientation & Heading Information Scent
- **Measures:** Presence and clarity of primary heading (`<h1>`), page `<title>`, and structural subheadings (`<h2>`) against the 4-question orientation framework (What is this? Who is it for? Why is it relevant? What can I do next?).
- **Decision:** If primary H1 is missing or generic (e.g. "Welcome", "Home"), emit a proactive **recommendation** (`LOW_INFORMATION_SCENT`, Priority: `low`). Heuristic heading absence alone never creates a high-severity defect finding per the "No Heuristic Defects" rule.
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

---

## 5-Second Orientation & Information Scent Framework

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

---

## 5. Agent UX & Accessibility Architecture (AI Browsing Readiness)

Derived from `agent-friendly-pages` and web.dev criteria:

### The Three AI Agent Interaction Channels:
1. **Accessibility Tree Quality:** Clean semantic roles (`button`, `link`, `heading`, `main`).
2. **Raw HTML Semantics:** Real `<button type="button">` and `<a href="...">` vs non-semantic `<div onclick>` / `<span onclick>` widgets.
3. **Interactive Element Discoverability:** Distinct visible text labels and accessible ARIA attributes.

### Defect Taxonomy:
- **`AGENT_INTERACTION_BARRIER` (Medium Severity):**
  Triggered when interactive conversion buttons or navigation triggers are implemented using `<div onclick>` or `<span onclick>` without semantic elements. Autonomous AI browsing agents (e.g. OpenAI Operator, Claude Computer Use) cannot discover or trigger non-semantic onclick divs.
  *Remediation:* Refactor to semantic HTML5 `<button type="button">` or `<a href="...">` elements.
- **`PROACTIVE.ENGAGEMENT.SEMANTIC_LANDMARKS.001` (Low Priority):**
  Triggered when content pages lack HTML5 semantic landmarks (`<main>`, `<nav>`, `<article>`).
  *Remediation:* Wrap primary article/product content in `<main>` and primary navigation in `<nav>`.

---

## 6. Search Experience Optimization (SXO) & Value-Driven CTAs

### SXO Core Principle:
A page can achieve a 95/100 technical SEO score and still fail completely in AI search and visitor retention if there is a **page-type intent mismatch**:
- If an AI query is commercial/comparison ("Best Cloud Database for SaaS"), an informational blog post lacking comparison tables and transparent pricing will immediately bounce AI-referred users.
- **The 5-Second Orientation Test:** A visitor arriving from an AI summary must comprehend what the product is, who it is for, and why it is uniquely relevant within 5 seconds.

### Value-Driven CTAs vs. Weak Action Verbs:
- **Weak Generic CTAs:** `Submit`, `Click Here`, `Learn More`, `Read More`, `Continue`, `Go`. (Depress conversion rates and lose intent context scent).
- **Strong Value-Driven CTAs:** `Start Free Trial`, `See Live Pricing`, `Explore Documentation`, `Download Architecture PDF`.
- **Formula:** `[Action Verb] + [Specific Desired Outcome/Asset]`.

---

## 7. Autonomous AI Buying Agent Readiness (`/pricing.md`)

Autonomous AI agents (OpenAI Operator, Google Project Mariner) increasingly evaluate software and service options programmatically before human buyers ever visit the site:
- **Opaque Pricing Failure:** If pricing is locked behind client-rendered dynamic JavaScript or a forced "Contact Sales" wall, automated agents skip the vendor and recommend competitors with machine-readable plans.
- **Standard Machine-Readable Manifests:**
  - `/pricing.md` or `/pricing.txt`: A structured markdown summary of tiers, monthly/annual rates, usage limits, and core features.
  - Trivially ingestible by LLMs with zero HTML parsing or browser rendering overhead.

---

## 8. First-Party Analytics Ingestion & Dual-Track Evaluation (Static Proxies vs. Observed Outcomes)

To prevent false alarms and provide ground-truth business impact, the engagement audit implements a dual-track evaluation architecture that distinguishes **static UX proxies** from **observed user behavioral outcomes**:

### 1. Dual-Track Architecture:
- **Track 1: Static UX Proxies (DOM-derived):** Evaluates structural HTML layout, heading hierarchy, first-3 interactive CTA placement, and information scent similarity.
- **Track 2: Observed Engagement Outcomes (Analytics-derived):** Ingests first-party analytics data (bounce rate, dwell time, scroll depth, conversion rate, and AI search referral cohort retention).

### 2. Analytics Ingestion Schema:
Supported page-level metrics via `--analytics <file.json|file.csv>` or `inventory["analytics"]`:
- `url` or `path`: Normalized route string (e.g., `/pricing` or `https://brand.com/pricing`).
- `bounce_rate`: Float (0.0–1.0) or percentage string (e.g. `0.65` or `"65%"`).
- `avg_time_on_page_seconds` / `dwell_time_seconds`: Mean visitor duration on page.
- `scroll_depth_pct`: Median vertical scroll depth percentage.
- `conversion_rate`: Primary macro/micro conversion percentage.
- `ai_referral_bounce_rate`: Bounce rate specifically for traffic arriving from AI assistant citation links (ChatGPT, Perplexity, Claude).
- `organic_bounce_rate`: Baseline bounce rate from traditional search engines.

### 3. Cross-Correlation & Severity Adjustment Rules:
1. **Empirical Corroboration:** When a static UX defect (e.g. `INTENT_TO_LANDING_MISMATCH` or `LOW_INFORMATION_SCENT`) coincides with high observed bounce rate (>= 60%) or low dwell time (<= 20s), the finding severity and confidence are elevated to `high`, citing empirical confirmation of visitor abandonment.
2. **Heuristic Mitigation:** When a static heuristic flags an issue (e.g. absent H1 tag or low word count), but first-party analytics prove healthy visitor retention (bounce rate <= 35%, dwell time >= 60s), the finding is downgraded to `low` or informational, noting that real-world users are not abandoning the page.
3. **AI Referral Discontinuity:** When AI referral cohort bounce rate exceeds the organic baseline by >= 25%, the skill emits an `AI_REFERRAL_DISCONTINUITY` finding, diagnosing that post-citation visitors suffer orientation disconnect because cited claims are not immediately anchored in the viewport.
4. **Heuristic-Only Operation (Clear Limitations):** When no analytics dataset is provided, the skill operates in heuristic-only mode with explicit disclaimers: static proxies highlight potential UX friction, but do not represent observed user drop-off in production.
