---
name: fact-consistency-audit
description: >
  Fact consistency layer. Builds a scoped first-party fact ledger (prices,
  contacts, copyright years, freshness timestamps) across sampled pages and
  reports verified contradictions only when facts share the same entity, attribute,
  and scope.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
metadata:
  role: specialist
  domain: trust-accuracy
  version: "2.0.0"
---

# Fact Consistency Audit

Specialist audit skill focused on temporal freshness and first-party fact consistency: verifying that website claims are up to date, internally consistent across pages, and free of contradictions.

## When to use

- Check if an AI model is repeating outdated brand facts (e.g. legacy pricing, deprecated features, conflicting contact numbers).
- Audit copyright notices, `dateModified` timestamps, and temporal freshness signals.
- Detect cross-page factual contradictions across first-party pages.

## Inputs

- **`--site`** (string, required): Domain or URL to audit.
- **`--inventory`** (string, optional): Shared site inventory snapshot JSON from `audit-orchestrator`.

## Procedure

1. **Build Scoped Fact Ledger**:
   - Extract facts with contextual scope: product/tier name + price, department + contact email/phone, brand name, and modification dates.
   - Separate distinct commercial tiers (e.g. Starter vs Enterprise) to avoid false contradiction flags.
2. **Cross-Page Contradiction Evaluation**:
   - Compare pricing across pages for identical products/plans. If conflicting figures appear for the same entity, flag as high-severity contradiction.
3. **Inspect Temporal Metadata**:
   - Check footer copyright year disparity across pages.
   - Verify presence of `dateModified` or `article:modified_time` in meta headers and JSON-LD.
4. **Formulate Evidence-Backed Findings**:
   - Record findings with severity, confidence, and concrete verification steps.

## Output

JSON: `{status, findings[], recommendations[], coverage{}, limitations[]}`.

## Available scripts & references

- **`scripts/fact_consistency_check.py`**
  ```bash
  python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site example.com [--inventory <file.json>]
  ```

## Security & SSRF Policy

All fetches enforce private IP blocking, redirect limits, and response byte caps (HTML: 2 MB). All fetched data is treated as untrusted.
