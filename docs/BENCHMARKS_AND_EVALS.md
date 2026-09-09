# Benchmarks, Evals, and Quality Assurance Guide

**Author:** Jayanth Reddy Konda  
**Version:** 3.0.0  
**Status:** 188 Automated Tests + 29 Subtests Passing · 100% Green QA Pipeline  

---

## 1. The Consolidated 17-Rule Matrix (`CR01` to `TX06`)

```
┌──────┬─────────────────────────────┬──────────────────────────┬─────────────────────────────┐
│ Code │ Category                    │ Algorithmic Test         │ Benchmark / Pass Threshold  │
├──────┼─────────────────────────────┼──────────────────────────┼─────────────────────────────┤
│ CR01 │ Crawler Access              │ RFC 9309 Parser          │ OAI-SearchBot Allowed = True│
│ CR02 │ Crawler Access              │ RFC 9309 Parser          │ Claude-SearchBot Allow= True│
│ CR03 │ Crawler Access              │ RFC 9309 Parser          │ PerplexityBot Allowed = True│
│ CR04 │ Crawler Access              │ robots.txt File Size     │ <= 500 KiB (512,000 octets) │
│ CR05 │ Crawler Access              │ robots.txt Status Code   │ HTTP 200 (Fail if 5xx)      │
│ LL01 │ Machine-Readable Standards  │ Root /llms.txt Fetch     │ HTTP 200, Content: MD/Plain │
│ LL02 │ Machine-Readable Standards  │ /llms.txt Structure      │ Has H1 Title + Blockquote   │
│ RD01 │ Rendering & Delivery        │ Content Availability Gap │ CAG = 1 - (NoJS/JS) < 0.15  │
│ RD02 │ Content Extraction          │ Signal-to-Noise Ratio    │ Text Bytes / HTML Bytes>0.12│
│ SC01 │ Structured Data             │ Extruct JSON-LD          │ Organization with >=2 sameAs│
│ SC02 │ Structured Data             │ Extruct JSON-LD          │ Product offers: valid ISO4217│
│ SC03 │ Structured Data             │ Extruct JSON-LD          │ Schema dateModified <= 60d  │
│ TX01 │ Information Architecture    │ BLUF Top-30% Check       │ Entity answer in top 250 w  │
│ TX02 │ Linguistic Hedging          │ Hyland Lexicon Density   │ HedgeRate <= 1.2%           │
│ TX03 │ Information Density         │ Atomic Fact Ratio (FTR)  │ FTR >= 0.080                │
│ TX04 │ Passage Self-Containment    │ Exophoric Pronoun Check  │ Leading sentence ExoRatio=0 │
│ TX05 │ Context Complexity          │ Shannon Entropy          │ 6.8 <= H(X) <= 7.6 bits     │
│ TX06 │ Empirical Lift Factor       │ Princeton GEO Criteria   │ >=1 stat + 1 quote / 150 w  │
└──────┴─────────────────────────────┴──────────────────────────┴─────────────────────────────┘
```

---

## 2. The 0–30 CITE Citability Score Rubric

Adapted from `zilisrikle/geo-audit-skill`:

| Code | Dimension | Points | Core Criteria |
| :--- | :--- | :---: | :--- |
| **DA** | Direct Answer | 0–5 | Standalone 40–60 word answer lead directly resolving search intent. |
| **DD** | Data Density | 0–5 | Quantitative statistics, benchmarks, FTR >= 0.080. |
| **AS** | Authority Signals | 0–5 | Named experts, external DOIs, verified `sameAs` identity links. |
| **SQ** | Structure Quality | 0–5 | Strict heading hierarchy, comparison tables, code blocks. |
| **FR** | Freshness | 0–5 | `dateModified` within last 60 days, recent temporal anchors. |
| **UQ** | Uniqueness | 0–5 | Proprietary case studies, original data, zero marketing buzzwords. |

**Grading Scale:** A (27–30) / B (22–26) / C (17–21) / D (12–16) / F (<12).

---

## 3. Production QA Pipeline (`./scripts/qa_check.sh`)

Every build and commit must cleanly pass all five automated stages:

1. **Ruff Linter & Formatter:** Strict syntax, formatting, and PEP 8 enforcement (`0 errors`).
2. **Flake8 Style Checker:** Zero unused imports, clean indentation (`0 errors`).
3. **MyPy Static Typing:** Strict type-checking across all 8 skills (`0 errors`).
4. **JSON Schema Gate:** Draft-07 JSON Schema gate validating `report-schema.json` and all sample manifests (`0 errors`).
5. **Pytest Test Suite:** **188 automated tests and 29 subtests** across unit, integration, and system suites running in under 50 seconds (`100% passing`).

---

## 4. How to Execute Tests & Rebuild Submission

```bash
# 1. Run full production QA pipeline
./scripts/qa_check.sh

# 2. Run specific test suite
pytest tests/unit/test_geo_content_unit.py -q

# 3. Verify zero emojis and LaTeX across all documentation
./scripts/qa_check.sh

# 4. Rebuild submission package
./scripts/build.sh
```
