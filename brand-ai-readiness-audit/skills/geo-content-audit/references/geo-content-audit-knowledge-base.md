# GEO-CONTENT-AUDIT KNOWLEDGE BASE

This document contains all mandatory rules, schemas, and taxonomies required for this skill.

========================================================================
=== SOURCE FILE: geo-contracts.md ===
========================================================================

## 9. `CONTENT.POOR_DATA_DENSITY`
- **Skill:** `geo-content-audit`
- **Family:** `CONTENT.RETRIEVAL_OPTIMIZATION`
- **Purpose:** Detect when substantive content lacks the statistical density and formatting required for AI retrieval.
- **Input:** Raw visible text, tabular elements (`<table>`), and list elements (`<ul>`, `<ol>`).
- **Decision:** Finding triggered IF pages lack tabular/list structures or contain low statistical density, reducing LLM extraction likelihood.
- **Exclusion:** Do NOT report on purely transactional pages (login, cart).
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Refactor key text into explicit Q&A headers (`<h2>`), bulleted lists, and structured tables.
- **Verification:** Confirm presence of dense structural elements (tables/lists) and statistical data.
