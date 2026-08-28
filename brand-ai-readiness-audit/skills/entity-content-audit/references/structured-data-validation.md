# Structured Data Reference & Validation Guide

Implementation rules for JSON-LD structured data to ensure unambiguous entity recognition, offer extraction, and rich result eligibility.

---

## 1. Syntax & Placement Best Practices

- **Format:** JSON-LD format inside `<script type="application/ld+json">` is strongly recommended.
- **Graph Combining (`@graph`):** Combine multiple entities into a single linked graph to preserve relationships between the publisher, webpage, and main offering.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "Acme Aerospace",
      "url": "https://example.com",
      "logo": "https://example.com/logo.png",
      "sameAs": [
        "https://www.wikidata.org/wiki/Q12345",
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

| Property | Type | Requirement | Description |
| :--- | :--- | :--- | :--- |
| `name` | Text | Required | Official brand name |
| `url` | URL | Required | Canonical homepage URL |
| `logo` | ImageURL / ImageObject | Recommended | Direct link to high-res logo |
| `sameAs` | Array of URLs | Recommended | Authoritative profile URLs (Wikidata, Crunchbase, official social) |
| `contactPoint` | ContactPoint | Optional | Support phone and email details |

---

## 3. Product & Offer Schema

Ensures commercial terms (pricing, availability, variants) are extracted deterministically by AI assistants.

| Property | Type | Requirement | Description |
| :--- | :--- | :--- | :--- |
| `name` | Text | Required | Official product title |
| `offers.price` | Number / Text | Required | Numerical price without currency symbols |
| `offers.priceCurrency` | ISO 4217 Text | Required | Currency code (e.g. `USD`, `INR`, `EUR`) |
| `offers.availability` | ItemAvailability URL | Required | `https://schema.org/InStock`, `OutOfStock`, `PreOrder` |
| `brand` | Brand / Organization | Recommended | Producing brand entity |
| `description` | Text | Recommended | Accurate product summary |
| `sku` | Text | Optional | Stock keeping unit |

---

## 4. Defect vs Recommendation Rules

- **Absence of Markup:** An extractability opportunity (`recommendation`), NEVER an automatic defect if visible text is clear.
- **Markup-vs-DOM Contradiction:** A verified defect (`finding`) if JSON-LD price contradicts visible on-page price.
- **Incomplete Product Markup:** A low-severity defect if Product schema exists but omits price or availability.
