---
name: engagement-audit
description: Audit on-site visitor orientation, above-the-fold clarity, heading hierarchies (H1 to H3), information scent, navigation health, and summary readability for AI extractors and bounce prevention. Use when diagnosing why visitors referred from AI search bounce or fail to engage, or why AI assistants produce vague or diluted brand summaries.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
allowed-tools: Bash Read
metadata:
  role: specialist
  domain: engagement
  version: "1.0.0"
---

# Engagement Audit

Specialist audit skill focused on visitor orientation, information scent, and AI summary extractability: ensuring landing pages answer core value questions immediately, provide structured heading hierarchies, and maintain clear navigational journeys to prevent bounce.

## When to use

- Evaluate whether a landing page clearly states what a product does in the above-the-fold hero area.
- Inspect heading structure (`H1`, `H2`, `H3`) for information scent and scannability.
- Verify semantic navigation links to prevent visitor abandonment.
- Assess signal-to-noise ratio for AI assistant summaries and email briefers.

## Inputs

- **`site`** (string, required): Domain or URL to audit.
- **`file`** (string, optional): Local HTML file for offline evaluation.

## Procedure

1. **Evaluate Above-the-Fold Orientation**:
   - Assess whether the page passes the 5-second test using the [Engagement Rubric](references/ENGAGEMENT_RUBRIC.md).
   - Check for a clear, descriptive `<h1>` element stating the core value proposition.
2. **Inspect Heading Hierarchy & Information Scent**:
   - Verify logical progression from `H1` to `H2` and `H3` subheadings.
   - Detect "walls of text" lacking scannable subheadings.
3. **Audit Navigation & Context Retention**:
   - Verify existence of semantic `<nav>` menus and key destination links (Pricing, Docs, About).
4. **Evaluate AI Summary Signal-to-Noise**:
   - Apply [AI Snippet Guidelines](references/AI_SNIPPET_GUIDELINES.md) to ensure high fact density in lead paragraphs.
5. **Formulate Evidence-Backed Findings**:
   - Output structured findings with prioritized recommendations.

## Output

Returns a JSON list of structured findings:

```json
[
  {
    "id": "ENG-001",
    "title": "Missing semantic H1 heading tag on landing page",
    "severity": "high",
    "evidence": "Found 0 <h1> tags on example.com; page uses un-annotated graphic banners for title.",
    "suggested_action": {
      "summary": "Add a prominent <h1> element clearly stating the core value proposition above the fold.",
      "priority": "high"
    }
  }
]
```

## Gotchas

- **Graphic Banners Replacing Text**: Designing hero text inside image banners makes it completely invisible to AI search bots and assistive readers.
- **Vague Buzzwords**: Slogans like "Unlock Potential" carry low information scent; ensure concrete nouns and verbs are present.

## Available scripts & references

- **`scripts/engagement_check.py`** — Runs automated engagement and hierarchy analysis:
  ```bash
  python3 skills/engagement-audit/scripts/engagement_check.py --site example.com
  ```
  *(On Windows, use `python` or `py`)*
- **`references/ENGAGEMENT_RUBRIC.md`** — Comprehensive orientation and bounce prevention heuristics.
- **`references/AI_SNIPPET_GUIDELINES.md`** — Summary extractability and signal-to-noise guidelines.
