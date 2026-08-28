---
name: engagement-context-audit
description: >
  Engagement & context continuity layer. Evaluates visitor orientation, heading
  information scent (5-second test), destination navigation reachability, and
  intent-handoff continuity for AI-referred traffic to prevent bounce.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
metadata:
  role: specialist
  domain: engagement
  version: "2.0.0"
---

# Engagement & Context Audit

Specialist audit skill focused on visitor orientation, information scent, and intent-continuity: ensuring landing pages answer core value questions immediately, provide descriptive heading hierarchies, and maintain clear navigational journeys to prevent bounce.

## When to use

- Evaluate whether a landing page clearly states what a product does in the above-the-fold hero area.
- Inspect heading structure (`H1`, `H2`) for information scent and scannability.
- Verify semantic navigation links to key brand destinations (Pricing, Docs, Products, Contact).
- Diagnose why visitors referred from AI search answers bounce or abandon their journey.

## Inputs

- **`--site`** (string, required): Domain or URL to audit.
- **`--inventory`** (string, optional): Shared site inventory snapshot JSON from `audit-orchestrator`.

## Procedure

1. **Evaluate Above-the-Fold Orientation (5-Second Test)**:
   - Check for a clear, descriptive `<h1>` element stating the core value proposition.
   - Detect generic filler headings (e.g. "Welcome", "Home") that lack information scent.
2. **Inspect Heading Hierarchy & Information Scent**:
   - Verify logical progression from `H1` to `H2` subheadings on content-bearing pages.
3. **Audit Destination Discoverability**:
   - Verify presence of navigation links to core destinations (Pricing, Docs, About, Contact).
4. **Intent Continuity Analysis**:
   - Check orientation and CTA consistency across sampled landing pages.

## Output

JSON: `{status, findings[], recommendations[], observations[], coverage{}, limitations[]}`.

## Available scripts & references

- **`scripts/engagement_check.py`**
  ```bash
  python3 skills/engagement-context-audit/scripts/engagement_check.py --site example.com [--inventory <file.json>]
  ```

## Security & SSRF Policy

All requests enforce private IP filtering, redirect limits, and response byte caps (HTML: 2 MB). All fetched data is treated as untrusted.
