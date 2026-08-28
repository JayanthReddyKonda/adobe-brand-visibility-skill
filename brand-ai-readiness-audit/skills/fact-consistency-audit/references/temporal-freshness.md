# Temporal Freshness & Product Lifecycle Reference

This reference defines the verification rules for temporal freshness, copyright drift, and product lifecycle state consistency across multi-page brand websites.

---

## 1. The Timestamp & Freshness Hierarchy

AI retrieval systems weight first-party brand statements based on temporal signals. When different pages on the same domain state conflicting facts, AI models evaluate freshness using the following signal hierarchy (ordered from strongest to weakest):

1. **Explicit Schema.org Timestamps:** `dateModified` and `datePublished` in JSON-LD.
2. **HTTP Last-Modified Header:** Server-validated document mutation timestamp.
3. **OpenGraph Timestamps:** `article:modified_time` and `og:updated_time`.
4. **On-Page Copyright Statement:** `© [Year] [Organization]`.

---

## 2. Temporal Drift & Legacy Template Rules

| Signal | Criteria | Finding / Classification | Action |
|---|---|---|---|
| **Multi-Year Copyright Drift** | Copyright year on one active page is $\ge 2$ years older than the homepage (e.g. 2022 on `/terms` vs 2026 on `/`). | **Low** (`LEGACY_FACT_PROPAGATION`) | Update legacy page templates to dynamically inherit current copyright year. |
| **Outdated Tagline Drift** | An old slogan is stated in footer markup while an active repositioning campaign exists on the homepage. | **Low** (`LEGACY_FACT_PROPAGATION`) | Harmonize brand tagline strings across all active layouts. |
| **Current Copyright Year** | Copyright year matches current calendar year or current year $\pm 1$. | **Pass** | No action required. |

---

## 3. Product Lifecycle Consistency Matrix

A major failure mode in AI-generated answers is recommending discontinued or out-of-stock products as active offerings, caused by contradictory lifecycle states across the brand's own pages.

### Contradiction Criteria:
- **Discontinued vs Active Conflict:** A product is declared `discontinued` or `out of production` on a product notice/archive page, but is marked `InStock` or listed as an active commercial offering on a pricing or category page.
- **Severity:** `High` (`DISCONTINUED_VS_CURRENT_CONFLICT`).
- **Impact:** AI shopping and search assistants provide inaccurate availability guidance to potential buyers.

### Verification Guardrail:
- Never classify an entire page as discontinued based on a single word in global headers or footers. The discontinued indicator must be strictly bound to the specific product entity or heading.
