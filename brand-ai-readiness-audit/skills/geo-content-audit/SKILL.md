---
name: geo-content-audit
description: "Generative Engine Optimization (GEO): Evaluates text density, statistical claim volume, and answer-block formatting for LLM comprehension."
version: "1.0.0"
---

# Generative Engine Optimization (GEO) Audit

This specialist evaluates HTML content for AI answerability and extraction likelihood based on advanced Generative Engine Optimization research (e.g., Princeton KDD 2024).

It performs causal analysis on:
1. **Statistical Density**: Measures numeric facts per 100 words. High statistical density increases the likelihood an LLM selects a page for data-driven RAG.
2. **Answer Block Formatting**: Verifies if questions (`H2`/`H3`) are immediately followed by concise 20-70 word definition paragraphs.
3. **Structured Data Extraction**: Detects `<dl>` and `<table>` blocks, which LLMs heavily prioritize over unstructured prose for factual representation.

## Expected Causal Taxonomies
* `CONTENT.GEO_UNOPTIMIZED`: Content is formatted in dense prose without statistical anchoring, reducing LLM extraction likelihood.
* `CONTENT.POOR_DATA_DENSITY`: Missing tables/lists for product specifications.

