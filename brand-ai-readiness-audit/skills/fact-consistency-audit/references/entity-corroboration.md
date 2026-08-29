# Entity Corroboration & Knowledge Graph Grounding

AI assistants cross-verify facts against independent web sources to validate claims and resolve brand ambiguities. This document outlines best practices for entity disambiguation and cross-web grounding.

---

## 1. The Entity Disambiguation Problem

When multiple entities share a brand name or acronym (e.g., "Apex", "Canvas", "Beacon"), AI assistants can conflate products, assign incorrect founders, or attribute competitor features unless the brand provides authoritative grounding links.

---

## 2. Multi-Source Corroboration Links (`sameAs`)

In the root `Organization` JSON-LD schema, provide `sameAs` links to authoritative third-party repositories:

- **Wikidata**: The gold-standard open knowledge base (`https://www.wikidata.org/wiki/Q...`).
- **Wikipedia**: Authoritative encyclopedia entry (if notable).
- **Crunchbase / PitchBook**: Authoritative corporate entity registries.
- **Verified Social Profiles**: Official GitHub, LinkedIn, X/Twitter, and YouTube profiles.

### Example Schema Implementation

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Beacon Intelligence",
  "url": "https://beaconintelligence.example",
  "sameAs": [
    "https://www.wikidata.org/wiki/Q98765432",
    "https://www.crunchbase.com/organization/beacon-intelligence",
    "https://www.linkedin.com/company/beacon-intel",
    "https://github.com/beacon-intel"
  ]
}
```

---

## 3. Authoritative About Page Structure

A machine-verifiable About Page must contain:
1. **Clear Entity Statement**: "Beacon Intelligence is an enterprise AI observability company founded in 2021 by Jane Doe and John Smith."
2. **Physical / Legal Registry Data**: Legal registered company name, corporate headquarters city/state/country.
3. **Canonical Domain Declarations**: Explicit statement of official operating domains.

