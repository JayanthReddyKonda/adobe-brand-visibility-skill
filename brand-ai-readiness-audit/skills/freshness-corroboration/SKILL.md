---
name: freshness-corroboration
description: Audit fact freshness, temporal signals (copyright year, dateModified), cross-page consistency, and external entity corroboration (sameAs, Wikidata, Knowledge Graph) for AI trust and accurate brand representation. Use when diagnosing why an AI assistant cites outdated facts, wrong pricing, or confuses a brand with another company.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
metadata:
  role: specialist
  domain: trust-accuracy
  version: "1.0.0"
---

# Freshness Corroboration

Specialist audit skill focused on temporal freshness and factual corroboration: verifying that website claims are up to date, internally consistent, and anchored to authoritative external knowledge graphs via `sameAs` entity identifiers to prevent AI hallucination or identity confusion.

## When to use

- Check if an AI model is repeating outdated brand facts (e.g. legacy pricing, deprecated features, old leadership).
- Diagnose entity collision where an AI assistant mixes up a brand with a similarly named business.
- Audit copyright notices, `dateModified` timestamps, and temporal freshness signals.
- Verify cross-web grounding links in structured data.

## Inputs

- **`site`** (string, required): Domain or URL to audit.
- **`file`** (string, optional): Local HTML file for offline evaluation.

## Procedure

1. **Inspect Temporal Metadata**:
   - Check footer copyright year against current calendar year.
   - Verify presence of `dateModified` or `article:modified_time` in meta headers and JSON-LD.
2. **Evaluate Cross-Page Consistency**:
   - Compare pricing, feature descriptions, and company details across pages for divergence.
3. **Assess Entity Grounding & Disambiguation**:
   - Inspect `sameAs` array in `Organization` schema against [Entity Corroboration Guide](references/ENTITY_CORROBORATION.md).
   - Check links to Wikidata, Crunchbase, or verified social profiles.
4. **Formulate Evidence-Backed Findings**:
   - Record findings with severity and concrete remediation guidance following the [Freshness Checklist](references/FRESHNESS_CHECKLIST.md).

## Output

Returns a JSON list of structured findings:

```json
[
  {
    "id": "FC-001",
    "title": "Outdated copyright year detected",
    "severity": "medium",
    "evidence": "Visible copyright notice displays '© 2021', signalling stale maintenance.",
    "suggested_action": {
      "summary": "Update footer copyright year to current year and expose ISO 8601 dateModified metadata.",
      "priority": "medium"
    }
  }
]
```

## Gotchas

- **Dynamic Scripts Hiding in JS**: Some sites use JavaScript to render `new Date().getFullYear()`. In raw HTML scrapes, this may appear as blank or a fallback year unless evaluated properly.
- **SameAs Target Quality**: Linking to personal or unverified social pages does not provide strong entity disambiguation; prefer Wikidata and canonical registry entries.

## Available scripts & references

- **`scripts/freshness_check.py`** — Runs automated freshness and entity checks:
  ```bash
  python3 skills/freshness-corroboration/scripts/freshness_check.py --site example.com
  ```
  *(On Windows, use `python` or `py`)*
- **`references/FRESHNESS_CHECKLIST.md`** — Detailed checklist for temporal decay and stale claim detection.
- **`references/ENTITY_CORROBORATION.md`** — Entity disambiguation and knowledge graph grounding reference.
