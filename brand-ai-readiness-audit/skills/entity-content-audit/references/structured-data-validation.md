# Structured Data Validation (entity-content reference)

Internal reference for how the entity-content skill treats structured data
(JSON-LD). It deliberately positions structured data as a *consistency and
extractability aid*, not as a checklist that rewards markup for its own sake.

## The real signal: markup vs visible content

The single most valuable check is **does the structured data agree with what is
visibly on the page?**

```
VISIBLE: ₹5,499      JSON-LD: ₹4,999   →  REAL DEFECT (offer mismatch)
VISIBLE: ₹5,499      JSON-LD: ₹5,499   →  consistent, good
JSON-LD absent                           →  NOT automatically a finding
```

Markup that contradicts visible content (price, availability, currency, name) is
a genuine problem; markup that is merely absent is not. Incorrect or misleading
markup is the harmful case.

## When markup absence matters

Absence only becomes relevant in combination with a *reliability intent*: for a
local business, reviews, or product the pages your site truly wants cited.
Then it is framed as an extractability **opportunity** (a recommendation with a
coverage ratio), never as an automatic defect.

## Type-appropriate required properties (page-type aware)

Match expected attributes to the page type before judging completeness:

| Page type | Material attributes |
|-----------|---------------------|
| Product | price, currency, availability, brand, sku, variants, specs |
| LocalBusiness | address, hours, phone, geo, services |
| Article / Blog | headline, datePublished, author, publisher |
| Organization / WebSite | name, url, logo |
| Event | name, startDate, location, offers |

Gaps here become recommendations with a measured coverage ratio (e.g.
"offers/attrs present on X of Y product pages"), never a blanket defect.

## Validation order

1. Identify page type.
2. Identify important entities and material attributes.
3. Detect present JSON-LD.
4. Validate syntax (parses, valid `@context`, valid `@type`).
5. Validate semantics (`@id` consistency, required properties, datatypes).
6. Compare to visible content (the decisive step).

## `sameAs` and entity disambiguation

- `sameAs` pointing to authoritative profiles (Wikidata, official social,
  registries) strengthens entity identity.
- Present `sameAs` are verified reachable (HTTP 200) by corroboration-audit.
- Absent `sameAs` is a strengthening **recommendation**, raised only when
  competing entities share the brand name (disambiguation risk); otherwise
  informational.

## What is NOT treated as a defect

- Any valid structured data type present but not producing a rich result.
- FAQ / HowTo / Sitelinks SearchBox markup (features retired; markup remains
  valid schema.org and is not penalized).
- Absence of a rich-result feature: eligibility ≠ guarantee of appearance.
