# Archetype Dynamic Adaptation Matrix
## Business Model Contextualization for Brand AI-Readiness & Visibility

This reference guides the AI Agent when interpreting telemetry from `orchestrator.py --telemetry` and re-weighting diagnostic findings and proactive recommendations based on verified site archetype.

> **Generalization Invariant:** Archetype classification NEVER gates which sensors run. All 6 specialist sensors ALWAYS execute across all domains. Archetype classification is used strictly by the AI reasoning layer to re-weight defect severities, contextualize simulated assistant queries, and synthesize high-leverage proactive recommendations.

---

## 1. Archetype Classification Matrix

| Archetype | Primary Detection Signals (from Telemetry) | Highest-Priority Checks | Distinctive Technical Fixes | Distinctive Creative Fixes | Proactive Strategic Moves |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SaaS / Developer Platform** | • `/docs`, `/api`, `/pricing`, `/billing` routes<br>• `SoftwareApplication` JSON-LD<br>• Code blocks and API endpoints in DOM | • `/llms.txt` presence and validity<br>• API doc chunking (`geo.avg_chunk_token_length`)<br>• Pricing comparison transparency<br>• Auth-wall orientation | Serve machine-readable `/llms.txt` and `/pricing.md`; structure doc pages with `<h2>` chunk boundaries every 300–500 tokens | Author 40–60 word BLUF answers under question headers; eliminate asterisk conditions on plan tiers | Deploy `/pricing.md` and `/llms.txt` manifests specifically formatted for autonomous AI purchasing agents |
| **E-Commerce / Retail** | • `/product`, `/shop`, `/item`, `/cart` routes<br>• `Product` & `Offer` JSON-LD<br>• Currency symbols & pricing tables | • Schema.org `Product`/`Offer` completeness (`price`, `priceCurrency`, `availability`)<br>• Cross-page multi-currency consistency<br>• Merchant return policies | Embed nested `Offer` with ISO 4217 currency and `ItemAvailability` enum; add `MerchantReturnPolicy` schema | Reconcile visible "In Stock" copy with structured availability; provide clean tabular product specifications | Deploy comprehensive Schema.org `@graph` connecting `Product` to `MerchantReturnPolicy` and `AggregateRating` |
| **Enterprise B2B** | • `/about`, `/leadership`, `/solutions`, `/investors`<br>• `Organization` JSON-LD<br>• Multiple external `sameAs` links | • Authority corroboration on Wikidata, LinkedIn, Crunchbase<br>• Named executive leadership in text & schema (`Person`)<br>• Entity disambiguation | Embed Schema.org `Organization` with disambiguated `sameAs` URIs; nest `Person` schema for leadership team | Maintain identical legal entity name and headquarters address across all external directory anchors | Establish verified Wikidata entity node and reconcile third-party corporate entity graphs |
| **News / Media Publisher** | • Byline patterns, publication dates<br>• `NewsArticle` or `BlogPosting` JSON-LD<br>• Date-path URLs (e.g. `/2026/09/`) | • Pre-paywall machine-readability<br>• Author byline authority & E-E-A-T credentials<br>• RFC 9309 AI bot licensing directives | Add `isAccessibleForFree` and `hasPart` schema for paywalls; link author profiles to external credentials | Provide 50-word executive summary (dek) above paywall; attribute facts to verifiable primary studies | Replace blanket crawler disallow with granular RFC 9309 rules distinguishing search retrieval from model training |
| **Local / Regional Service** | • `/locations`, `/contact`, store locator<br>• `LocalBusiness` JSON-LD<br>• Phone, physical address, NAP patterns | • `LocalBusiness` geo-coordinates (`latitude`, `longitude`)<br>• `openingHoursSpecification` completeness<br>• NAP consistency between footer and text | Declare `LocalBusiness.geo` coordinates and ISO 8601 opening hours; link to Google Maps CID | Reconcile phone number and address discrepancies between header, footer, and contact page | Embed localized `Service` schema with `areaServed` geographic polygons |

---

## 2. Severity Reweighting Rubric by Archetype

When synthesizing the final report, adjust the severity of findings based on how catastrophically the defect harms the specific business model:

```python
ARCHETYPE_SEVERITY_OVERRIDES = {
    "ecommerce": {
        "ATTRIBUTE_INCOMPLETENESS": "critical",       # Missing price/currency blocks checkout journey
        "INCOMPLETE_OFFER_ATTRIBUTES": "critical",     # Missing availability misleads buying agents
        "COMMERCIAL_PRODUCT_DATA_CONTRADICTION": "critical",
        "MATERIAL_ENTITY_AMBIGUITY": "high",          # Brand must be identified for product citations
        "FIRST_PARTY_FACT_CONFLICT": "critical",       # Pricing drift misleads AI comparisons
    },
    "saas": {
        "LOW_FACT_TO_TOKEN_RATIO": "high",            # Thin text prevents category recommendation
        "MISSING_IN_DEPTH_MECHANISMS": "high",        # Lack of causal depth prevents technical citations
        "FIRST_PARTY_FACT_CONFLICT": "critical",       # Plan cost drift breaks AI purchasing agents
        "CONTEXT_PLACEMENT_DEGRADATION": "high",       # Key value prop buried below auth wall
    },
    "publisher": {
        "MATERIAL_ENTITY_AMBIGUITY": "high",          # Missing publisher authority drops citations
        "STANDALONE_FAQ_DEFICIT": "high",             # Missing FAQ schema limits AI Overview rich snippets
        "STALE_AUTHORITATIVE_FACT": "high",           # Outdated facts erode synthetic trust
        "CONTENT_RECENCY_DEFICIT": "medium",
    },
    "local_business": {
        "MATERIAL_ENTITY_AMBIGUITY": "critical",       # Local assistants cannot route without entity
        "MISSING_MATERIAL_FACT": "critical",           # Missing address/phone makes brand invisible
        "BROKEN_AUTHORITY_ANCHOR": "high",            # Broken map/directory link prevents grounding
    },
    "corporate": {}  # Baseline sensor severities
}
```

---

## 3. Simulated Assistant Query Profiles by Archetype

Simulate the 3 major retrieval engines (ChatGPT Search, Claude, Perplexity Pro) using these archetype-specific natural user query scenarios:

### 3.1 SaaS / Developer Platform
- **Navigational Query:** *"What does [Brand] do and what are its core features?"*
  - *Retriever test:* Does `/` or `/about` contain a 40–60 word standalone definition without fluff?
- **Commercial Investigation Query:** *"How much does [Brand] cost per user, and does it offer an API?"*
  - *Retriever test:* Is pricing explicitly stated in visible text or `/pricing.md` without forced registration?
- **Technical Comparison Query:** *"Compare [Brand] vs [Competitor] for enterprise scale."*
  - *Retriever test:* Are architectural benchmarks and causal mechanisms (`because`, `therefore`) present?

### 3.2 E-Commerce / Retail
- **Direct Product Query:** *"Where can I buy [Product Name] and is it in stock?"*
  - *Retriever test:* Does the page expose Schema.org `Offer` with `price`, `priceCurrency`, and `InStock`?
- **Specification Query:** *"What are the dimensions, materials, and warranty for [Product Name]?"*
  - *Retriever test:* Are product attributes in a clean HTML `<table>` or structured bullet list?

### 3.3 Enterprise B2B
- **Vendor Due Diligence Query:** *"Who owns [Brand], where is it headquartered, and who is the CEO?"*
  - *Retriever test:* Does Schema.org `Organization` link to verified Wikidata/LinkedIn and declare `founder`/`employee`?
- **Security & Compliance Query:** *"Is [Brand] SOC 2 certified or GDPR compliant?"*
  - *Retriever test:* Are compliance statements un-gated and corroborated by third-party links?

### 3.4 Media / Publisher
- **Fact Verification Query:** *"According to [Publisher], what is the latest finding on [Topic]?"*
  - *Retriever test:* Is the headline supported by a 50-word BLUF paragraph with named researcher attribution?

### 3.5 Local Service
- **Local Intent Query:** *"What time does [Brand] open in [City] and what is their phone number?"*
  - *Retriever test:* Does `LocalBusiness` declare valid `openingHoursSpecification` and E.164 phone?
