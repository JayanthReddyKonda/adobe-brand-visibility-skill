# Unified Causal Failure Taxonomy for AI Brand Visibility

This document establishes the canonical root-cause classification across all skills in the Brand AI-Readiness Audit Marketplace.
Findings represent authentic **causal failure modes**, not superficial HTML checklist violations.

---

## Causal Taxonomy Hierarchy

```text
AUDIT TAXONOMY
│
├── DISCOVERY
│   ├── ACCESS
│   │   ├── AI_RETRIEVAL_BLOCKED            (robots.txt blocks AI search retrieval bots: OAI-SearchBot, PerplexityBot)
│   │   ├── NOINDEX_EXCLUSION               (noindex directive prevents indexing of public content)
│   │   └── WAF_BOT_CHALLENGE               (Edge WAF / firewall rejects AI crawler User-Agents)
│   ├── DISCOVERY_PATH
│   │   ├── CANONICAL_FRAGMENTATION         (Canonical consolidation points away from indexable content)
│   │   ├── ORPHANED_CONTENT_PATH           (Critical pages unlinked from site navigation or sitemaps)
│   │   └── SITEMAP_INDEXING_GAP            (Absence of sitemap for large multi-page catalog)
│   └── REPRESENTATION_AVAILABILITY
│       └── RENDERED_CONTENT_GAP            (Core textual content omitted from initial raw HTML payload)
│
├── ENTITY
│   ├── IDENTITY
│   │   ├── MATERIAL_ENTITY_AMBIGUITY       (Brand or organization entity cannot be resolved unambiguously)
│   │   └── WEAK_IDENTITY_SIGNALS           (Absence of structured machine-explicit Organization markup)
│   └── ANSWERABILITY
│       ├── MISSING_MATERIAL_FACT           (Material commercial fact missing from specialized landing page)
│       ├── INCOMPLETE_OFFER_ATTRIBUTES     (Product schema omits price, availability, or specifications)
│       └── WEAK_ANSWER_SURFACE             (Page fails to provide direct answers to high-intent queries)
│
├── FACT
│   ├── CONSISTENCY
│   │   ├── FIRST_PARTY_FACT_CONFLICT       (Contradictory values published for identical scoped entity)
│   │   └── CONFLICTING_COMMERCIAL_TERMS    (Discrepancy between on-page price and structured schema price)
│   ├── FRESHNESS
│   │   ├── LEGACY_FACT_PROPAGATION         (Retired taglines or outdated brand claims persist across pages)
│   │   └── STALE_AUTHORITATIVE_FACT        (Absence of currency signals / multi-year stale copyright dates)
│   └── LIFECYCLE
│       └── DISCONTINUED_VS_CURRENT_CONFLICT (Discontinued model marketed as active or in-stock)
│
├── AUTHORITY
│   ├── IDENTITY_CORROBORATION
│   │   └── BROKEN_AUTHORITY_ANCHOR         (Declared sameAs profile URL returns 4xx/5xx HTTP error)
│   └── CLAIM_CORROBORATION
│       └── CLAIM_CORROBORATION_GAP         (Material factual assertions lack external verification)
│
├── EXPERIENCE
│   └── CONTINUITY
│       ├── INTENT_TO_LANDING_MISMATCH      (Landing page fails to retain referral query intent)
│       ├── LOW_INFORMATION_SCENT           (Headline / hero uses vague filler lacking descriptive nouns)
│       └── DESTINATION_NAVIGATION_FRICTION (Absence of semantic navigation to key brand destinations)
│
└── REPRESENTATION
    └── ACCURACY
        ├── AI_FACT_CONFLICT                (Observed AI assistant quotes facts contradicting site reality)
        ├── AI_UNSUPPORTED_CLAIM            (Observed AI assistant makes ungrounded assertions)
        └── AI_CITATION_GAP                 (Brand mentioned in AI answer without source citation link)
```

---

## Root Cause Reference Table

| Cause Family | Cause ID | Description | Default Severity |
| :--- | :--- | :--- | :--- |
| `DISCOVERY.ACCESS` | `AI_RETRIEVAL_BLOCKED` | robots.txt blocks AI search retrieval crawlers (`OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot`). | `critical` / `high` |
| `DISCOVERY.ACCESS` | `NOINDEX_EXCLUSION` | Meta robots or headers exclude public content from AI ingestion. | `critical` |
| `DISCOVERY.DISCOVERY_PATH` | `CANONICAL_FRAGMENTATION` | Canonical URL consolidates onto a different un-audited host. | `medium` |
| `DISCOVERY.REPRESENTATION_AVAILABILITY` | `RENDERED_CONTENT_GAP` | Primary copy missing from raw HTML (client-side rendering dependency). | `high` |
| `ENTITY.IDENTITY` | `MATERIAL_ENTITY_AMBIGUITY` | Brand entity is missing machine-explicit Organization identity. | `medium` |
| `ENTITY.ANSWERABILITY` | `INCOMPLETE_OFFER_ATTRIBUTES` | Product/Offer schema omits required commercial fields (price, availability). | `low` |
| `ENTITY.ANSWERABILITY` | `MISSING_MATERIAL_FACT` | Page type missing core factual attributes expected for user query answerability. | `low` |
| `FACT.CONSISTENCY` | `FIRST_PARTY_FACT_CONFLICT` | Conflicting prices or specifications published for the same product/plan across pages. | `high` |
| `FACT.FRESHNESS` | `LEGACY_FACT_PROPAGATION` | Outdated slogans, legacy pricing, or stale copyright years persist across pages. | `medium` |
| `FACT.LIFECYCLE` | `DISCONTINUED_VS_CURRENT_CONFLICT` | Discontinued product marketed as active or in-stock on secondary pages. | `high` |
| `AUTHORITY.IDENTITY_CORROBORATION` | `BROKEN_AUTHORITY_ANCHOR` | Declared sameAs profile URL returns 4xx/5xx HTTP error. | `medium` |
| `EXPERIENCE.CONTINUITY` | `INTENT_TO_LANDING_MISMATCH` | Landing page omits answers to referral query intent above the fold. | `medium` |
| `EXPERIENCE.CONTINUITY` | `LOW_INFORMATION_SCENT` | Primary H1 uses generic filler words ("Welcome", "Home") lacking information scent. | `low` |
| `EXPERIENCE.CONTINUITY` | `DESTINATION_NAVIGATION_FRICTION` | Landing page lacks navigation links to core brand destinations. | `medium` |
| `REPRESENTATION.ACCURACY` | `AI_FACT_CONFLICT` | Observed AI assistant quotes pricing or facts contradicting on-site reality. | `high` |
| `REPRESENTATION.ACCURACY` | `AI_UNSUPPORTED_CLAIM` | Observed AI assistant asserts ungrounded claims about brand capabilities. | `medium` |
