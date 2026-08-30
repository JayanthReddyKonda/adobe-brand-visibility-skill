---
name: geo-content-audit
description: >
  Generative Engine Optimization (GEO): Evaluates text density, statistical claim volume, and answer-block formatting for LLM comprehension.
license: MIT
compatibility: Cross-platform (Linux, macOS, Windows). Requires Python 3.8+ (standard library only).
metadata:
  role: specialist
  parent: audit-orchestrator
  version: "1.0.0"
---

> [!TIP]
> **Execution Context:** Assume your working directory is the repository root. All commands and file paths below are absolute relative to the root directory.

# Generative Engine Optimization (GEO) Audit

This specialist evaluates HTML content for AI answerability and extraction likelihood based on advanced Generative Engine Optimization research (e.g., Princeton KDD 2024).

It performs causal analysis on:
1. **Statistical Density**: Measures numeric facts per 100 words. High statistical density increases the likelihood an LLM selects a page for data-driven RAG.
2. **Answer Block Formatting**: Verifies if questions (`H2`/`H3`) are immediately followed by concise 20-70 word definition paragraphs.
3. **Structured Data Extraction**: Detects `<dl>` and `<table>` blocks, which LLMs heavily prioritize over unstructured prose for factual representation.

---

## When to Use

- Diagnose why an LLM fails to extract tabular data or specifications from a product page.
- Assess whether the content density is sufficient for an AI to formulate a comprehensive answer.

---

## References to Consult

> [!IMPORTANT]
> **MANDATORY READING:** You MUST read the unified knowledge base before proceeding.
> Execute: `cat skills/geo-content-audit/references/geo-content-audit-knowledge-base.md` (or use your file reader tool on `skills/geo-content-audit/references/geo-content-audit-knowledge-base.md`).
> Do NOT attempt to guess the rules. All schemas, causal taxonomies, and decision matrices are strictly defined in that single file.

---

## Mandatory Execution Command

Execute the deterministic extraction script using the shared inventory and `--format json`:

```bash
python3 skills/geo-content-audit/scripts/geo_content_check.py --site <target_url> --inventory <inventory.json> --format json
```

Direct standalone execution:
```bash
python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --format json
```
