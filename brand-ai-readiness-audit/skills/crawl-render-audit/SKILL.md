---
name: crawl-render-audit
description: Audit website crawlability, bot directives (robots.txt, AI user-agents), client-side rendering gaps (SSR vs CSR), machine-readable DOM content, and Schema.org JSON-LD structured data for AI discoverability. Use when diagnosing why AI search assistants cannot crawl, read, or parse a brand's website.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
allowed-tools: Bash Read
metadata:
  role: specialist
  domain: discoverability
  version: "1.0.0"
---

# Crawl Render Audit

Specialist audit skill focused on the technical foundational layer of AI discoverability: ensuring AI crawlers can access the site, read substantive text from raw HTML (without failing on client-side JS rendering), and parse semantic facts via Schema.org JSON-LD.

## When to use

- Inspect `robots.txt` and meta tags for blocks against AI user-agents (`GPTBot`, `ClaudeBot`, `PerplexityBot`).
- Check if critical website content is trapped in client-side Single Page Application (SPA) javascript shells.
- Detect machine-readability barriers such as facts trapped in un-annotated images or canvas elements.
- Validate Schema.org structured data (Organization, Product, FAQPage) for entity recognition.

## Inputs

- **`site`** (string, required): Domain or URL to audit.
- **`file`** (string, optional): Local HTML file for offline/sandboxed evaluation.
- **`robots`** (string, optional): Local `robots.txt` file for offline evaluation.

## Procedure

1. **Evaluate Crawl Access Signals**:
   - Inspect `robots.txt` against known AI bot user-agents using [AI Bot Policies](references/AI_BOT_POLICIES.md).
   - Check `<meta name="robots">` and HTTP headers for `noindex` or `nofollow`.
2. **Evaluate DOM Rendering & JS-Reliance**:
   - Parse initial raw HTML text volume.
   - Flag client-side rendering (CSR) gaps where substantive facts only load after script execution.
3. **Inspect Text vs Non-Text Content**:
   - Verify image `alt` attributes and check for facts locked inside non-text graphics.
4. **Audit Structured Data (JSON-LD)**:
   - Extract and validate JSON-LD blocks against [Structured Data Specs](references/STRUCTURED_DATA_SPECS.md).
5. **Formulate Evidence-Backed Findings**:
   - Record exact findings with severity ratings per the [Crawl & Render Checklist](references/CRAWL_RENDER_CHECKLIST.md).

## Output

Returns a JSON list of structured findings:

```json
[
  {
    "id": "CR-001",
    "title": "Robots.txt blocks AI crawler user-agents",
    "severity": "critical",
    "evidence": "robots.txt disallows GPTBot and ClaudeBot access.",
    "suggested_action": {
      "summary": "Update robots.txt to allow indexing for verified AI search crawlers.",
      "priority": "critical"
    }
  }
]
```

## Gotchas

- **Do Not Rely Exclusively on Headless Browsers**: Many AI retrieval bots fetch only initial raw HTML without full JavaScript execution. A site that renders beautifully in Chrome may appear completely empty to an AI scraper.
- **JSON-LD Syntax Errors**: A single syntax error in a JSON-LD script tag invalidates the entire structured data block for machines.

## Available scripts & references

- **`scripts/crawl_render_check.py`** — Runs automated crawl & render diagnostics:
  ```bash
  python3 skills/crawl-render-audit/scripts/crawl_render_check.py --site example.com
  ```
  *(On Windows, use `python` or `py`)*
- **`references/CRAWL_RENDER_CHECKLIST.md`** — Step-by-step checklist for crawl and render failure modes.
- **`references/STRUCTURED_DATA_SPECS.md`** — Schema.org JSON-LD templates and guidelines.
- **`references/AI_BOT_POLICIES.md`** — AI crawler user-agent list and policy guidelines.
