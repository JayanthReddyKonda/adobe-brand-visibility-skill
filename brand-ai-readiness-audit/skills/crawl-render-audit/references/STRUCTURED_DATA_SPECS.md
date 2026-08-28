# Schema.org Structured Data Specifications for AI Discoverability

Structured data (specifically JSON-LD) provides unambiguous semantic facts to search engines and AI assistants. This document specifies essential schemas for brand readiness.

---

## 1. Organization & Brand Schema (Homepage)

Place in `<script type="application/ld+json">` on the root domain:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Corp",
  "url": "https://www.acme.example",
  "logo": "https://www.acme.example/logo.png",
  "description": "Enterprise cloud analytics platform delivering real-time telemetry.",
  "foundingDate": "2020",
  "sameAs": [
    "https://www.wikidata.org/wiki/Q123456",
    "https://www.linkedin.com/company/acmecorp",
    "https://twitter.com/acmecorp",
    "https://github.com/acmecorp"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "email": "support@acme.example"
  }
}
```

---

## 2. Product & Offer Schema (Product / Pricing Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Acme Telemetry Pro",
  "description": "Real-time AI telemetry and log monitoring tool for cloud infrastructure.",
  "brand": {
    "@type": "Brand",
    "name": "Acme"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://www.acme.example/pricing",
    "priceCurrency": "USD",
    "price": "49.00",
    "availability": "https://schema.org/InStock",
    "priceValidUntil": "2027-12-31"
  }
}
```

---

## 3. FAQPage Schema (Help / FAQ Pages)

Allows AI assistants to directly cite verified Q&A pairs:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What data formats does Acme support?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Acme natively ingests JSON, Syslog, OpenTelemetry traces, and Prometheus metrics."
      }
    }
  ]
}
```

