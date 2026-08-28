# Freshness & Temporal Signals Checklist

This reference covers the checks required to detect stale, unmaintained, or conflicting facts that cause AI assistants to downgrade trust or hallucinate outdated brand data.

---

## 1. Temporal Metadata & Freshness Signals

- [ ] **Footer Copyright Year**: Does the footer copyright match the current year (or dynamic date script), or does it reflect an outdated prior year?
- [ ] **HTTP Headers & Meta Tags**:
  - Are `Last-Modified` HTTP headers returned on static assets and pages?
  - Are `<meta property="article:modified_time">` or `<meta property="og:updated_time">` exposed?
- [ ] **JSON-LD Temporal Properties**:
  - `datePublished` and `dateModified` in `Article`, `BlogPosting`, or `WebPage` schemas.
  - `priceValidUntil` in `Offer` schemas.

---

## 2. Cross-Page Fact Consistency

- [ ] **Pricing & Feature Divergence**: Do product pricing, tier limits, or feature matrices differ between the homepage, dedicated pricing page, and docs?
- [ ] **Company Identity Consistency**: Are company name, headquarters address, phone numbers (NAP), and executive leadership consistent across the About, Contact, and Legal pages?

---

## 3. Discontinued / Outdated Product Claims

- [ ] **Legacy Product References**: Does the site prominently advertise deprecated products, sunset APIs, or legacy pricing tiers without clear obsolescence notices?
- [ ] **Changelog & Release Notes Cadence**: Are recent product updates or version release notes accessible within the last 90 days?

