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
- **Verification:** Test with Google Rich Results Test or validate with `python3 src/skills/entity-content-audit/scripts/entity_content_check.py`.

---

### C. Generative Engine Optimization (GEO)

#### 3. Low Causal Depth & Vague Marketing Copy
- **Defect:** Paragraphs lack causal conjunctions (`because`, `due to`, `therefore`) and concrete metrics.
- **Technical Fix:** Add structured `FAQPage` or `TechArticle` schema with machine-parsable question-answer pairs.
- **Creative Fix:** Rewrite key value propositions into the **Inverted-Pyramid Citability Pattern**:
  - *Before:* "Our cutting-edge software revolutionizes team productivity through modern cloud technology."
  - *After:* "BrandCorp accelerates developer sprint velocity by 35% because our distributed cache eliminates disk I/O latency. As a result, pipeline execution times drop from 12 minutes to under 80 seconds."
- **Verification:** Run `python3 src/skills/geo-content-audit/scripts/geo_content_check.py` and confirm GEO Mechanistic Depth score > 0.80.

---

### D. Multi-Page Fact Consistency

#### 4. Cross-Page Pricing / Plan Contradictions
- **Defect:** Homepage mentions *"Starts at USD 19/mo"* while Pricing page says *"Starts at USD 49/mo"*.
- **Technical Fix:** Consolidate pricing variables into a single source-of-truth database or CMS token rendered synchronously across all templates.
- **Creative Fix:** Audit all landing page copy to synchronize promotional rates, legacy tiers, and annual discount calculations.
- **Verification:** Run `python3 src/skills/fact-consistency-audit/scripts/fact_consistency_check.py` and confirm 0 fact contradictions.

---

### E. Candidate Backlink & Authority Verification

#### 5. Dead or Unreachable Referring Backlinks
- **Defect:** Referring URLs cited as external authority anchors return HTTP 404, 500, or connection timeouts.
- **Technical Fix:** Implement automated backlink monitoring; set up 301 redirects on inbound target endpoints if permalinks moved.
- **Creative Fix:** Outreach to publishing editors to update broken citation URLs with current canonical deep-links; replace dead directories with active industry publications or Wikidata items.
- **Verification:** Run `python3 src/skills/corroboration-authority-audit/scripts/corroboration_check.py --target-domain brand.com --candidate-backlinks "https://partner.com/review"` and verify `link_verified: true`.

---

### F. Experience & Post-Citation Handoff Continuity

#### 6. AI Referral Discontinuity (High Bounce on Citations)
- **Defect:** AI search traffic (ChatGPT Search, Perplexity, Claude) shows bounce rate >= 60% and dwell time < 30 seconds.
- **Technical Fix:** Implement dynamic hero personalization based on UTM referral campaign/source (`utm_source=chatgpt.com` or `referrer: perplexity.ai`) to display immediate contextual continuity above the fold.
- **Creative Fix:** Align the landing page H1 headline directly with the question answered by the AI engine. Ensure the primary call-to-action is within the first 3 interactive elements and core facts are immediately visible without scrolling.
- **Verification:** Ingest updated telemetry via `python3 src/skills/engagement-context-audit/scripts/engagement_check.py --analytics data.json` and confirm bounce rate drops below 40%.

---

### G. Deterministic GEO Content Optimization

#### 7. Implementing Page-Level Content Improvement Plans
- **Defect:** Content scored with low citation probability due to missing causal depth, absent statistics, or unchunked paragraphs.
- **Technical Fix:** Format structured comparison tables with `<table>`, `<th>`, and `<td>` tags; wrap question-and-answer pairs in valid Schema.org `FAQPage` JSON-LD; apply semantic `<section>` and `<article>` tags.
- **Creative Fix:** Apply the 120–180 word passage chunking blueprint generated by `geo_content_check.py`. Begin each chunk with a direct assertion (BLUF), substantiate with 2+ quantitative data points, and connect with causal mechanisms (`because`, `enables`, `thereby reducing`).
- **Verification:** Re-run `python3 src/skills/geo-content-audit/scripts/geo_content_check.py` and verify `citability_score` >= 70 and 0 structural warnings.

#### 8. Remedying Standalone FAQ Deficits (`STANDALONE_FAQ_DEFICIT`)
- **Defect:** Page relies on standalone question-and-answer blocks without supporting empirical evidence (code snippets, statistics, or comparison tables), incurring an empirical -5.7% citation penalty (Zhang et al. 2026).
- **Technical Fix:** Embed structured comparison tables (`<table>`), technical code blocks (`<pre><code>`), or quantitative specification matrices into the FAQ answer markup.
- **Creative Fix:** Upgrade conversational soundbite answers into definitive mini-guides: cite benchmark metrics, percentages, and comparative trade-offs.
- **Verification:** Confirm at least 2 of the 5 high-influence evidence genres are present within the body content.

#### 9. Remedying Unnatural Keyword Stuffing (`EXCESSIVE_KEYWORD_DENSITY`)
- **Defect:** Non-stopword token density exceeds 4.5%, degrading neural embedding perplexity and incurring an empirical -8.3% to -10% citation degradation in LLMs.
- **Technical Fix:** Audit body copy and CMS templates; remove repetitive keyword tags and unnatural repeated product names.
- **Creative Fix:** Diversify lexical vocabulary using domain synonyms, technical attributes, and natural contextual pronouns.
- **Verification:** Verify that maximum individual non-stopword density drops below 3.5%.

#### 10. Remedying Delayed Answer Placement (`CONTEXT_PLACEMENT_DEGRADATION`)
- **Defect:** Definitive answer or commercial proposition is delayed beyond the first 250 words / top 30% of content, suffering 30-40% retrieval recall loss (Stanford "Lost in the Middle").
- **Technical Fix:** Restructure the DOM hierarchy to place the primary answer summary block directly beneath the `<h1>` before auxiliary elements.
- **Creative Fix:** Use the Inverted Pyramid format: deliver a 40–60 word definitive direct answer proposition in paragraph 1 before providing secondary context.
- **Verification:** Confirm the first 200 words contain direct definition copulas or quantitative propositions.

---

### H. Post-Citation Intent & Viewport Continuity

#### 11. Remedying Viewport Answer Absence (`VIEWPORT_ANSWER_ABSENCE`)
- **Defect:** Arriving AI referral visitors experience orientation shock because the specific proposition cited by the AI assistant is pushed below the fold (top 600px) by decorative banners or carousel sliders.
- **Technical Fix:** Remove or compress oversized hero carousels; insert a clean above-the-fold answer summary callout box directly below the main header.
- **Creative Fix:** Align the hero H1 headline and lead sentence directly with the core query answered by the generative search engine.
- **Verification:** Confirm that lead 100 words explicitly anchor the brand's primary commercial value or pricing starting point.

#### 12. Remedying CTA Reachability Friction (`CTA_REACHABILITY_FRICTION`)
- **Defect:** The first commercial continuation action ('Buy', 'Start Free Trial', 'Contact Sales') is preceded by more than 3 auxiliary interactive elements (header navigation links, social icons, breadcrumbs), stalling conversion.
- **Technical Fix:** Place a prominent primary action `<button>` or `<a href>` directly in the hero block above the fold before the navigation bar in DOM tab order, or provide a skip-to-action anchor.
- **Creative Fix:** Pair the primary value headline with an instant value-driven CTA button ('Start Free Trial', 'Explore Live Demo') to eliminate user hesitation.
- **Verification:** Confirm that the commercial continuation CTA appears within the first 3 interactive DOM elements on the page.

---

### I. Knowledge Graph & Social Corroboration

#### 13. Remedying Missing SameAs Social Verification (`MISSING_SAMEAS_VERIFICATION` / `UNLINKED_KNOWLEDGE_GRAPH_ANCHOR`)
- **Defect:** Verified brand social profiles (LinkedIn, X/Twitter, GitHub, YouTube) are linked in the website's HTML header/footer navigation but omitted from Schema.org `Organization.sameAs`.
- **Technical Fix:** Update the homepage `Organization` JSON-LD schema to include all discovered official social and authority URLs in the `sameAs` array:
  ```json
  "sameAs": [
    "https://www.linkedin.com/company/brand",
    "https://twitter.com/brand",
    "https://github.com/brand",
    "https://www.wikidata.org/wiki/Q12345"
  ]
  ```
- **Creative Fix:** Audit all external corporate profiles to ensure canonical brand naming, logo consistency, and back-links to the primary website domain.
- **Verification:** Run `python3 src/skills/entity-content-audit/scripts/entity_content_check.py` and confirm 0 unlinked social anchor warnings.

---

### J. Commercial Terms & Trial Consistency

#### 14. Remedying Conflicting Commercial Terms & Trial Durations (`CONFLICTING_COMMERCIAL_TERMS`)
- **Defect:** Inconsistent free trial lengths (e.g. 14-day on homepage vs 30-day on pricing) or money-back guarantee terms advertised across different site routes.
- **Technical Fix:** Define commercial trial variables centrally in the application configuration or headless CMS; bind all landing page templates and structured pricing tables to the single source of truth.
- **Creative Fix:** Audit marketing funnels, PPC landing pages, and promotional banners to retire legacy campaign copy and synchronize trial durations across all customer touchpoints.
- **Verification:** Run `python3 src/skills/fact-consistency-audit/scripts/fact_consistency_check.py` and confirm `conflicts: 0` in commercial terms ledger.

---

### K. Authorship & Content Intent Boundaries

#### 15. Remedying Commercial CTA Intrusion in Informational Content (`COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT`)
- **Defect:** Informational guides, documentation, or research articles contain dense commercial sales pitches (>= 4 high-friction CTAs), causing query routers to classify the page as promotional advertising rather than objective reference material.
- **Technical Fix:** Replace intrusive modal popups, sticky conversion banners, and repeated "Buy Now" buttons on informational routes with subtle, contextual text hyperlinks.
- **Creative Fix:** Maintain editorial integrity on informational pages: lead with unbiased technical or industry analysis and confine commercial calls-to-action to a single resource recommendation at the conclusion.
- **Verification:** Confirm that informational pages contain fewer than 4 commercial conversion CTAs.

#### 16. Deploying Credentialed Author Attribution (`PROACTIVE.GEO.CREDENTIALED_AUTHOR_ATTRIBUTION.001`)
- **Defect:** High-value technical, medical, or scientific content published anonymously or with generic company bylines, missing E-E-A-T citation preference.
- **Technical Fix:** Embed Schema.org `Person` markup within `Article.author` declaring `name`, `jobTitle`, and `sameAs` links to verified academic or professional profiles (LinkedIn, Google Scholar, ORCID):
  ```json
  "author": {
    "@type": "Person",
    "name": "Dr. Jane Doe",
    "jobTitle": "Chief AI Scientist",
    "sameAs": "https://www.linkedin.com/in/janedoe"
  }
  ```
- **Creative Fix:** Add a concise 2-line author biographical box beneath the article title highlighting relevant academic degrees, industry certifications, and domain expertise.
- **Verification:** Inspect article markup and verify `author` resolves to a typed `Person` node with credentialed properties.

---

### L. Edge Directives & Machine Manifests

#### 17. Deploying Machine Discoverability Manifests (`/llms.txt`, `/pricing.md`)
- **Defect:** Site does not expose machine-readable manifests, requiring generative AI crawlers to parse complex HTML chrome.
- **Technical Fix:** Deploy a static `/llms.txt` file at the domain root adhering to the Jeremy Howard / Answer.AI specification, and a `/pricing.md` table mapping all public plans, tiers, and limits.
- **Creative Fix:** Author clear, 60-word BLUF summaries for each core product and documentation guide referenced in `/llms.txt`.
- **Verification:** Request `curl -I https://example.com/llms.txt` and `curl -I https://example.com/pricing.md` and verify HTTP 200 with `text/plain` or `text/markdown` MIME types.

