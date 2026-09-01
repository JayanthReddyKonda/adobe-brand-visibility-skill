# GEO-CONTENT-AUDIT KNOWLEDGE BASE

This document contains all mandatory rules, schemas, taxonomies, and research citations for the `geo-content-audit` skill.

========================================================================
=== SOURCE FILE: geo-contracts.md ===
========================================================================

# Generative Engine Optimization (GEO) Check Contracts

This reference formalizes the decision boundaries, heuristics, and research foundations for optimizing content citability in AI search engines (ChatGPT Search, Claude, Perplexity, Gemini).

---

## 1. Research Foundations (Princeton KDD 2024 & AutoGEO)

Empirical research on 10,000 queries (Aggarwal et al., Princeton University / KDD 2024) demonstrates that traditional search engine optimization (SEO) tactics (e.g. keyword density) do not improve generative AI citations. Generative engines evaluate content along specific, quantifiable dimensions:

| Optimization Vector | Measured Citation Impact | Implementation in Skill |
| :--- | :--- | :--- |
| **Cite Sources / Attributions** | **+115% visibility increase** | Recommends linking claims to authoritative primary repositories. |
| **Quantifiable Statistics** | **+40% citation rate** | Scans text for numerical data, metrics, currency values, and dates. |
| **Authoritative Quotes** | **+41% citation likelihood** | Evaluates expert quotation structures (`"..." - Author, Org`). |
| **Explanatory Mechanisms** | **+28% selection preference** | Analyzes causal conjunctions (`how`, `why`, `because`, `therefore`). |
| **Keyword Stuffing** | **Negative to neutral impact** | Explicitly discouraged; penalized in AI ranking models. |

---

## 2. Check Contracts

### Check 1: `MISSING_IN_DEPTH_MECHANISMS`
- **Skill:** `geo-content-audit`
- **Family:** `CONTENT.SHALLOW_COVERAGE`
- **Purpose:** Ensure substantive commercial and informative pages provide the causal and mechanistic depth required for AI synthesis.
- **Input:** Tokenized visible text across `product_detail`, `article`, and `pricing` pages.
- **Decision:** Finding triggered IF `depth_score < 2` (fewer than 2 occurrences of causal words: `how`, `why`, `because`, `therefore`, `allows`, `enables`, `results in`, `mechanism`).
- **Exclusion:** Do NOT report on purely transactional routes (login, cart, checkout, account settings) or short contact forms.
- **Severity:** `medium`.
- **Confidence:** `high`.
- **Remediation:** Expand body text to explain the underlying mechanisms, operational workflows, and causal benefits rather than surface-level claims.
- **Verification:** Re-evaluate page text to confirm presence of causal conjunctions and explanatory depth markers.

---

### Check 2: `LACK_OF_SPECIFIC_EVIDENCE`
- **Skill:** `geo-content-audit`
- **Family:** `CONTENT.RETRIEVAL_OPTIMIZATION`
- **Purpose:** Encourage empirical substantiation of marketing statements with concrete figures.
- **Input:** Regular expression extraction of numerical metrics (`\b\d+(\.\d+)?(%|\$|€|£|x|ms|s|min|hr|gb|tb|k|m|b)\b`).
- **Decision:** Proactive recommendation emitted IF a substantive page contains zero numerical or statistical evidence.
- **Severity:** `low` (proactive action, never an error defect).
- **Remediation:** Add concrete benchmark numbers, performance metrics, SLA percentages, or pricing figures.

---

### Check 3: Semantic Structure & Answer Blocks (Advisory)
- **Product Pages:** Check for presence of `<table>`, `<dl>`, or structured `<ul>`/`<ol>` elements. LLM retrieval parsers prioritize structured tabular elements over unstructured prose for attribute extraction.
- **Article Pages:** Check for question-form headings (`<h2>What is...</h2>`, `<h2>How do I...</h2>`). Direct answer paragraphs (20–70 words) immediately following question headings maximize rich snippet extraction in conversational search.

---

## 3. False Positive Decision Table

| Observed State | Action | Rationale |
| :--- | :--- | :--- |
| Zero `<table>` tags on a product page | Emit proactive recommendation | Tag absence is a formatting opportunity, not a critical defect. |
| Depth score < 2 on `/login` or `/cart` | Ignore (no finding) | Transactional workflows do not require narrative explanations. |
| Numbers present in header/footer only | Evaluate body text only | Header/footer navigation digits do not constitute substantive evidence. |
| Page contains fewer than 50 total words | Defer to `discoverability-audit` | Handled by rendering gap checks (`RENDERED_CONTENT_GAP`). |
