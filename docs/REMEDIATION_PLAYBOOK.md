# Dual-Track Remediation Playbook for Brand AI Readiness

**Author:** Jayanth Reddy Konda  
**Version:** 1.0.0  
**Standard:** Production Brand AI-Readiness & GEO Remediation Guide

---

## 1. Remediation Philosophy

Every brand AI-readiness defect has two complementary remediation vectors:
1. **Technical Track (`technical_fix`):** Structured data markup, server-side headers, robots.txt crawler rules, and routing configurations executed by software engineers.
2. **Creative & Content Track (`creative_fix`):** Information architecture, heading hierarchy, answer-block synthesis, and positioning clarity executed by copywriters and marketing teams.

---

## 2. Remediation Catalog by Category

### A. Discoverability & Indexation

#### 1. AI Search Crawlers Blocked in `robots.txt`
- **Defect:** `User-agent: OAI-SearchBot Disallow: /` or `User-agent: PerplexityBot Disallow: /`
- **Technical Fix:**
  ```text
  User-agent: OAI-SearchBot
  Allow: /

  User-agent: PerplexityBot
  Allow: /

  User-agent: Claude-SearchBot
  Allow: /
  ```
- **Creative Fix:** Update legal/governance disclosures to clarify that retrieval access for brand citations is permitted while reserving foundation model training rights.
- **Verification:** Run `curl -A "OAI-SearchBot" -I https://example.com/` and confirm HTTP 200 without meta noindex.

---

### B. Machine Entity Identity & Schema

#### 2. Missing Organization Entity Schema
- **Defect:** Homepage lacks machine-explicit `@graph` Schema.org Organization markup.
- **Technical Fix:**
  ```html
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [{
        "@type": "Organization",
        "@id": "https://brand.com/#org",
        "name": "Canonical Brand Name",
        "url": "https://brand.com",
        "logo": "https://brand.com/assets/logo.png",
        "sameAs": ["https://www.wikidata.org/wiki/Q12345",
          "https://www.linkedin.com/company/brand",
          "https://twitter.com/brand"
        ]
      },
      {
        "@type": "WebSite",
        "@id": "https://brand.com/#website",
        "url": "https://brand.com",
        "name": "Canonical Brand Name",
        "publisher": {"@id": "https://brand.com/#org"}
      }
    ]
  }
  </script>
  ```
- **Creative Fix:** Standardize brand naming in hero headings across all web properties.
- **Verification:** Test with Google Rich Results Test or validate with `python3 skills/entity-content-audit/scripts/entity_content_check.py`.

---

### C. Generative Engine Optimization (GEO)

#### 3. Low Causal Depth & Vague Marketing Copy
- **Defect:** Paragraphs lack causal conjunctions (`because`, `due to`, `therefore`) and concrete metrics.
- **Technical Fix:** Add structured `FAQPage` or `TechArticle` schema with machine-parsable question-answer pairs.
- **Creative Fix:** Rewrite key value propositions into the **Inverted-Pyramid Citability Pattern**:
  - *Before:* "Our cutting-edge software revolutionizes team productivity through modern cloud technology."
  - *After:* "BrandCorp accelerates developer sprint velocity by 35% because our distributed cache eliminates disk I/O latency. As a result, pipeline execution times drop from 12 minutes to under 80 seconds."
- **Verification:** Run `python3 skills/geo-content-audit/scripts/geo_content_check.py` and confirm GEO Mechanistic Depth score > 0.80.

---

### D. Multi-Page Fact Consistency

#### 4. Cross-Page Pricing / Plan Contradictions
- **Defect:** Homepage mentions *"Starts at $19/mo"* while Pricing page says *"Starts at $49/mo"*.
- **Technical Fix:** Consolidate pricing variables into a single source-of-truth database or CMS token rendered synchronously across all templates.
- **Creative Fix:** Audit all landing page copy to synchronize promotional rates, legacy tiers, and annual discount calculations.
- **Verification:** Run `python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py` and confirm 0 fact contradictions.

---

### E. Candidate Backlink & Authority Verification

#### 5. Dead or Unreachable Referring Backlinks
- **Defect:** Referring URLs cited as external authority anchors return HTTP 404, 500, or connection timeouts.
- **Technical Fix:** Implement automated backlink monitoring; set up 301 redirects on inbound target endpoints if permalinks moved.
- **Creative Fix:** Outreach to publishing editors to update broken citation URLs with current canonical deep-links; replace dead directories with active industry publications or Wikidata items.
- **Verification:** Run `python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --target-domain brand.com --candidate-backlinks "https://partner.com/review"` and verify `link_verified: true`.

---

### F. Experience & Post-Citation Handoff Continuity

#### 6. AI Referral Discontinuity (High Bounce on Citations)
- **Defect:** AI search traffic (ChatGPT Search, Perplexity, Claude) shows bounce rate $\ge 60\%$ and dwell time $< 30$ seconds.
- **Technical Fix:** Implement dynamic hero personalization based on UTM referral campaign/source (`utm_source=chatgpt.com` or `referrer: perplexity.ai`) to display immediate contextual continuity above the fold.
- **Creative Fix:** Align the landing page H1 headline directly with the question answered by the AI engine. Ensure the primary call-to-action is within the first 3 interactive elements and core facts are immediately visible without scrolling.
- **Verification:** Ingest updated telemetry via `python3 skills/engagement-context-audit/scripts/engagement_check.py --analytics data.json` and confirm bounce rate drops below 40%.

---

### G. Deterministic GEO Content Optimization

#### 7. Implementing Page-Level Content Improvement Plans
- **Defect:** Content scored with low citation probability due to missing causal depth, absent statistics, or unchunked paragraphs.
- **Technical Fix:** Format structured comparison tables with `<table>`, `<th>`, and `<td>` tags; wrap question-and-answer pairs in valid Schema.org `FAQPage` JSON-LD; apply semantic `<section>` and `<article>` tags.
- **Creative Fix:** Apply the 120–180 word passage chunking blueprint generated by `geo_content_check.py`. Begin each chunk with a direct assertion (BLUF), substantiate with 2+ quantitative data points, and connect with causal mechanisms (`because`, `enables`, `thereby reducing`).
- **Verification:** Re-run `python3 skills/geo-content-audit/scripts/geo_content_check.py` and verify `overall_citability_score` $\ge 0.70$ and 0 structural warnings.

