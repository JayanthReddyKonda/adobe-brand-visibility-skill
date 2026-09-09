# ENTITY-CONTENT-AUDIT KNOWLEDGE BASE

## Table of Contents

- [Preconditions](#preconditions)
- [C1. Identity explicitness](#c1-identity-explicitness)
- [C2. Product/offer extraction](#c2-productoffer-extraction)
- [C3. Claim completeness](#c3-claim-completeness)
- [C4. sameAs corroboration (recommendation only)](#c4-sameas-corroboration-recommendation-only)
- [Evidence standards](#evidence-standards)
- [1. Syntax & Placement Best Practices](#1-syntax-placement-best-practices)
- [2. Organization Schema](#2-organization-schema)
- [3. Product & Offer Schema](#3-product-offer-schema)
- [4. Defect vs Recommendation Rules](#4-defect-vs-recommendation-rules)
- [Signal](#signal)
- [Do NOT Report As Defect When:](#do-not-report-as-defect-when)
- [Report ONLY As:](#report-only-as)
- [Report As Defect ONLY When:](#report-as-defect-only-when)
- [1. Master Linked Graph Template (Organization + WebSite + SearchAction)](#1-master-linked-graph-template-organization-website-searchaction)
- [2. Product & Offer Schema with Full Answerability](#2-product-offer-schema-with-full-answerability)

---

This document contains all mandatory rules, schemas, and taxonomies required for this skill.

---

## Entity & Content Audit — Check Contracts

Every check in this skill states what it measures, what evidence is required,
and what does **not** constitute a defect. Findings are only emitted for
what is directly observable in the fetched initial HTML.

## Preconditions
Entity analysis needs real content. If the initial HTML carries too few
words to analyze (e.g. a CSR shell), the script returns
`status: "inconclusive"` with an explanatory error instead of guessing —
a rendering-gap finding belongs to `discoverability-audit`, and this skill
must not fabricate entity verdicts from an empty page.

## C1. Identity explicitness
- **Measures:** Whether a machine can determine **who** the site is from machine-explicit Schema.org `Organization` or `Brand` JSON-LD markup on the homepage.
- **Defect:** Absence of Schema.org `Organization` JSON-LD on homepage → `MATERIAL_ENTITY_AMBIGUITY` ("Organization identity not machine-explicit", severity `medium`, confidence `high`). Machine search engines and LLM knowledge graphs require explicit structured data to disambiguate the brand entity.
- **Mandatory Anti-Suppression Invariant:** Never suppress `MATERIAL_ENTITY_AMBIGUITY` merely because HTML `<title>` or OpenGraph (`og:site_name`) tags exist. Machine search engines require machine-explicit Schema.org JSON-LD to ground corporate identity without entity collision.

## C2. Product/offer extraction
- **Measures:** Presence and explicitness of product/offering entities
  (structured data first, then explicit markup).
- **Defect:** A detected product lacking explicit attributes (price,
  description) → `low`, confidence `high`.
- **Not a defect:** A site with no products (services, portfolios) —
  absence of a product entity on a non-commerce site is expected.

## C3. Claim completeness
- **Measures:** Whether the flagship entity carries attribute coverage
  (L2/L3 facts: what is offered, for whom, at what quality) in machine-
  readable form.
- **Defect:** Entity exists but claims are only implicit in prose.
- **Severity:** `low` to `medium` depending on how much a summarizing AI
  would have to guess.

## C4. sameAs corroboration & social authority linking
- **Measures:** Presence of `sameAs` links on the Organization entity and consistency with discovered DOM social anchors.
- **Defect (`MISSING_SAMEAS_VERIFICATION`):** When authoritative social profile links (LinkedIn, X/Twitter, GitHub, YouTube, etc.) are present in the website's HTML DOM (header/footer) but completely omitted from Schema.org `Organization.sameAs` → `MISSING_SAMEAS_VERIFICATION` (severity `medium`, confidence `high`). AI search engines and knowledge graph extractors rely on bidirectional `sameAs` links to corroborate corporate identity.
- **Recommendation:** When no external social anchors are detected on-site, absence of `sameAs` is emitted as an informational recommendation rather than a confirmed defect.

## Evidence standards
- Every finding quotes the observed state (which signals were present/absent).
- Confidence is stated per finding.
- The skill never infers facts from absent markup beyond what the check
  contract above explicitly licenses.

---

## Structured Data Reference & Validation Guide

Implementation rules for JSON-LD structured data to ensure unambiguous entity recognition, offer extraction, and rich result eligibility.

---

## 1. Syntax & Placement Best Practices

- **Format:** JSON-LD format inside `<script type="application/ld+json">` is strongly recommended.
- **Graph Combining (`@graph`):** Combine multiple entities into a single linked graph to preserve relationships between the publisher, webpage, and main offering.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [{
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "Acme Aerospace",
      "url": "https://example.com",
      "logo": "https://example.com/logo.png",
      "sameAs": ["https://www.wikidata.org/wiki/Q12345",
        "https://www.linkedin.com/company/acme"
      ]
    },
    {
      "@type": "Product",
      "@id": "https://example.com/products/x9#product",
      "name": "Velocity X9",
      "brand": { "@id": "https://example.com/#organization" },
      "description": "Commercial autonomous survey drone with 4K camera.",
      "offers": {
        "@type": "Offer",
        "price": "5499",
        "priceCurrency": "INR",
        "availability": "https://schema.org/InStock",
        "url": "https://example.com/products/x9"
      }
    }
  ]
}
</script>
```

---

## 2. Organization Schema

Explicit organization metadata enables knowledge graph recognition and entity disambiguation.

- **Primary Surfaces:** `/`, `/about`, `/contact`
- **Schema.org Type:** `Organization`

| Property | Type | Requirement | High Representation Risk | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | Text | Required | Yes | Official brand name |
| `url` | URL | Required | Yes | Canonical homepage URL |
| `logo` | ImageURL / ImageObject | Recommended | No | Direct link to high-res logo |
| `sameAs` | Array of URLs | Recommended | Yes | Authoritative profile URLs (Wikidata, Crunchbase, official social) |
| `contactPoint` | ContactPoint | Optional | Yes | Support phone and email details |

- **Verification Conditions:**
  - `identity_corroboration`: Declared `sameAs` URLs return HTTP 200 and contain the brand name claim without redirecting to unrelated domains.

---

## 3. Product & Offer Schema

Ensures commercial terms (pricing, availability, variants) are extracted deterministically by AI assistants.

- **Primary Surfaces:** `/products/*`, `/item/*`, `/p/*`, `/shop/*`
- **Schema.org Type:** `Product`

| Property | Type | Requirement | Volatile | High Representation Risk | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `name` | Text | Required | No | Yes | Official product title |
| `offers.price` | Number / Text | Required | Yes | Yes | Numerical price without currency symbols |
| `offers.priceCurrency` | ISO 4217 Text | Required | No | Yes | Currency code (e.g. `USD`, `INR`, `EUR`) |
| `offers.availability` | ItemAvailability URL | Required | Yes | Yes | `https://schema.org/InStock`, `OutOfStock`, `PreOrder` |
| `brand` | Brand / Organization | Recommended | No | Yes | Producing brand entity |
| `description` | Text | Recommended | No | No | Accurate product summary |
| `sku` | Text | Optional | No | No | Stock keeping unit |

- **Verification Conditions:**
  - `price_consistency`: Product page HTML price == JSON-LD `offers.price` == Catalog list price.
  - `availability_consistency`: JSON-LD `availability` state == Add to Cart button enabled state.

---

## 4. Defect vs Recommendation Rules

- **Absence of Markup:** An extractability opportunity (`recommendation`), NEVER an automatic defect if visible text is clear.
- **Markup-vs-DOM Contradiction:** A verified defect (`finding`) if JSON-LD price contradicts visible on-page price.
- **Incomplete Product Markup:** A low-severity defect if Product schema exists but omits price or availability.

---

## False Positive Decision Table: Absence of JSON-LD Schema

## Signal
Page contains readable HTML text but has no `<script type="application/ld+json">` blocks.

## Do NOT Report As Defect When:
- The page is a standard secondary informational or blog article where `<title>`, `<h1>`, and body copy clearly explain a topic without entity ambiguity.
- The visible text is explicit and unambiguous for human and AI readers.
- The site is crawlable and has no ranking or factual ambiguity issues.

## Report ONLY As:
- **Proactive Recommendation (`proactive_actions[]`)**: Suggesting structured data (`Article`, `FAQPage`) on informational articles to enhance machine extraction and rich snippet eligibility.

## Report As Defect (`finding`) When:
- **Homepage Lacks `Organization` Schema:** The brand publishes no Schema.org `Organization` JSON-LD markup on its homepage (`MATERIAL_ENTITY_AMBIGUITY`). HTML title tags or OpenGraph meta tags do NOT suppress this finding.
- **Commercial Offer Attribute Incompleteness:** The page is a core commercial product or service page where Product or Offer schema is missing required price, priceCurrency, or availability attributes (`ATTRIBUTE_INCOMPLETENESS`).

---

## Schema.org Copy-Paste Templates Catalog

## 1. Master Linked Graph Template (Organization + WebSite + SearchAction)

Embed this single linked JSON-LD block inside the `<head>` of the homepage:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [{
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "Acme Corporation",
      "url": "https://example.com",
      "logo": "https://example.com/assets/logo.png",
      "sameAs": ["https://www.wikidata.org/wiki/Q123456",
        "https://en.wikipedia.org/wiki/Acme_Corp",
        "https://www.linkedin.com/company/acme-corp",
        "https://twitter.com/acme"
      ],
      "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+1-800-555-0199",
        "contactType": "customer service",
        "areaServed": "US",
        "availableLanguage": ["en", "es"]
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://example.com/#website",
      "url": "https://example.com",
      "name": "Acme Official Platform",
      "publisher": {
        "@id": "https://example.com/#organization"
      },
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://example.com/search?q={search_term_string}",
        "query-input": "required name=search_term_string"
      }
    }
  ]
}
</script>
```

## 2. Product & Offer Schema with Full Answerability

Embed this on product detail pages to satisfy all commercial AI shopping agents:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Acme CloudSync Enterprise",
  "image": "https://example.com/images/cloudsync.jpg",
  "description": "Enterprise cloud synchronization platform with AES-256 encryption and automated failover.",
  "sku": "ACME-CS-ENT",
  "brand": {
    "@type": "Brand",
    "name": "Acme"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/pricing",
    "price": "49.00",
    "priceCurrency": "USD",
    "priceValidUntil": "2027-12-31",
    "availability": "https://schema.org/InStock",
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "applicableCountry": "US",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 30
    },
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingDestination": {
        "@type": "DefinedRegion",
        "addressCountry": "US"
      },
      "deliveryTime": {
        "@type": "ShippingDeliveryTime",
        "handlingTime": { "@type": "QuantitativeValue", "minValue": 0, "maxValue": 1, "unitCode": "DAY" },
        "transitTime": { "@type": "QuantitativeValue", "minValue": 1, "maxValue": 3, "unitCode": "DAY" }
      }
    },
    "seller": {
      "@id": "https://example.com/#organization"
    }
  }
}
</script>
```

---

## 3. LocalBusiness Schema Template (Physical Store / Regional Service)

Embed this on local business / branch landing pages to enable local AI search grounding:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": "https://example.com/#localbusiness",
  "name": "Acme Regional Store",
  "url": "https://example.com/locations/downtown",
  "telephone": "+1-800-555-0199",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Market Street",
    "addressLocality": "San Francisco",
    "addressRegion": "CA",
    "postalCode": "94105",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "09:00",
      "closes": "18:00"
    }
  ],
  "sameAs": [
    "https://maps.google.com/?cid=1234567890",
    "https://www.yelp.com/biz/acme-store"
  ]
}
</script>
```

---

## 4. Google 2025/2026 Merchant Listing & Schema Deprecation Rules

Derived from Google Search Merchant Listing documentation and `schema_ecommerce_validate.py`:

### Retired / Deprecated Schema Types (Emit Finding `SCHEMA_DEPRECATION`):
- `Vehicle` / `VehicleListing` (retired June 2025)
- `ClaimReview` (retired June 2025)
- `EstimatedSalary` (retired June 2025)
- `LearningVideo` / `CourseInfo` (retired June 2025)
- `SpecialAnnouncement` (deprecated July 2025)
- `Practice Problem` (Search Console / Rich Results support removed January 2026)
- `Book Actions` (deprecated from search rich results)

### FAQPage Rich Result Status (May 2026 Update):
- Google retired FAQ rich results for **all websites** on May 7, 2026 (superseding the August 2023 gov/health restriction).
- FAQPage markup is still ingested by non-Google LLMs (ChatGPT, Claude, Perplexity) as structured text, but has zero Google SERP rich result benefit.
- For genuine user Q&A communities, implement **`QAPage`** or **`DiscussionForumPosting`**.

### Server-Side Rendering (SSR) Mandate for Structured Data:
- Per Google's December 2025 JavaScript SEO guidelines, JSON-LD injected purely via client-side JavaScript (`useEffect`, client component hydration) faces severe queuing delays and may be missed during rapid AI retrieval crawls.
- Core commercial schemas (`Organization`, `Product`, `Offer`) MUST be delivered in the initial server-rendered HTML payload.

### Merchant Listing Minimum Property Groups:
- **Mandatory Minimum:** `name` + `image` + `offers`
- **Offer Type Constraint:** `offers.@type` must be `Offer` (never `AggregateOffer` on specific SKU pages)
- **Essential Attributes:** `price`, `priceCurrency`, `availability`
- **Trust Policies:** `hasMerchantReturnPolicy` (return windows and conditions) and `shippingDetails` (transit times and regional delivery rates) are essential for automated shopping inclusion by generative search engines.
