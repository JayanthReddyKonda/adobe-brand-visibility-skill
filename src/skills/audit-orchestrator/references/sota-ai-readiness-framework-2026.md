# State-of-the-Art Research Briefing: Brand AI-Readiness & GEO/AEO Framework

**Research Cutoff:** September 2026  
**Scope:** Generative Engine Optimization, Answer Engine Optimization, AI-Search Citation Behavior, Crawlability, Structured Data, Agentic Commerce, Citation/Factuality Evaluation, and Production Audit Tooling.

---

## Executive Architecture: The Layered Probability Model

A rigorous 2026 AI-readiness audit cannot be implemented as simple SEO plus an `llms.txt` and keyword checks. The empirical literature establishes a multiplicative layered model:

```text
AI Visibility ≈ Crawl Eligibility × Retrieval Eligibility × Content Citability × Entity/Source Authority × Citation Fidelity
```

with a separate **Agentic Commerce Readiness** layer for transactional products and services.

### Core Methodological Principle
The famous "+40% visibility improvement" from the canonical GEO paper (Aggarwal et al., KDD 2024) is **not** a 40% increase in citation or retrieval probability. It represents a change in **Position-Adjusted Word Count (PAWC)** *among an already retrieved set of sources*. Treating it as citation-probability uplift is a critical implementation error.

AI-search behavior is engine-specific, stochastic, and query-dependent:
P(Citation | Engine) != P(Citation)

The audit architecture strictly demarcates:
1. **Deterministic Technical Failures** (HTTP, robots, canonicals, noindex, nosnippet).
2. **Measurable Content Properties** (atomic fact density, quote density, statistical specificity).
3. **Probabilistic Visibility Signals** (empirical citation likelihood, model-expression fit).
4. **Engine-Specific Observations** (ChatGPT vs. Perplexity vs. Claude vs. Google AI Overviews).

---

## 1. Foundational Academic Literature

### 1.1 Canonical GEO & Position-Adjusted Word Count (PAWC)
- **Citation:** Aggarwal, P., Murahari, V., Rajpurohit, T., Kalyan, A., Narasimhan, K., & Deshpande, A. (ACM SIGKDD 2024 / arXiv:2311.09735).
- **Formal Generative Engine Model:**
  f_GE: (q_u, P_U) -> r
  Where `q_u` is the user query, `P_U` is the underlying retrieved corpus context, and `r` is the generated response consisting of sentences `l_i` with citations `C_i` (subset of `S`).
- **Empirical PAWC Benchmark (Baseline: 19.3):**
  - Quotation Addition: **27.2 (+40.9% relative PAWC lift)**
  - Statistics Addition: **25.2 (+30.6%)**
  - Fluency Optimization: **24.7 (+28.0%)**
  - Cite Sources: **24.6 (+27.5%)**
  - Technical Terminology: **22.7 (+17.6%)**
  - Easy-to-Understand: **22.0 (+14.0%)**
  - Authoritative Style: **21.3 (+10.4%)**
  - Unique Words: **20.5 (+6.2%)**
  - Keyword Stuffing: **17.7 (-8.3% penalty)**
- **Mathematical Formulation:**
  PAWC(r) = sum(wc(s_i) * exp(-pos(s_i))) / sum(wc(s_j))
  Where `wc(s_i)` is word count and `pos(s_i)` is the position of the cited source within the generated answer. Prominence, not merely presence, drives authority.

### 1.2 Multi-Stage Pipeline & Cross-Platform Nuance
- **Citation:** "Optimizing Visibility in Generative Engines: A Critical Survey of GEO (2023–2026)" (arXiv:2607.14035).
- **Finding:** Generic heuristics do not reliably transfer across engines. Every heuristic in the audit system carries explicit provenance metadata:
  ```json
  {
    "signal": "statistical_specificity",
    "evidence_level": "empirical",
    "engines": ["perplexity", "chatgpt"],
    "confidence": 0.85,
    "last_validated": "2026-09-03"
  }
  ```

---

## 2. Citation Quality: Evaluation Frameworks

### 2.1 ALCE (Automatic LLM Citation Evaluation)
- **Citation:** Gao et al. (EMNLP 2023).
- **Three-Dimensional Model:** [Fluency + Correctness + Citation Quality]
- **Mathematical Formulations:**
  CitationCoverage = (claims with supporting citation) / (total claims)
  CitationPrecision = (citations that actually entail the claim) / (total citations)

### 2.2 FActScore (Atomic Fact Support)
- **Citation:** Min et al. (EMNLP 2023).
- **Formulation:**
  BrandFactScore = sum(w_i * supported_i) / sum(w_i)
  Where weights `w_i` are elevated for critical commercial claims (price, availability, certifications, product specifications, dates, performance metrics).

### 2.3 Citation Correctness vs. Faithfulness
- **Citation:** Wallat et al. (2024) — "Correctness is not Faithfulness in RAG Attributions" (arXiv:2412.18004).
- **Finding:** Up to **57% of citations lack faithfulness** due to post-hoc rationalization. Systems must evaluate both `entailment_score` and `faithfulness_score`.

---

## 3. Empirical AI-Search Landscape (2026 Benchmarks)

### 3.1 Google AI Overviews & Query Fan-Out
- **Ahrefs Empirical Studies (2025 vs. 2026):**
  - July 2025 (1M Keywords): 76.1% of citations ranked in Google Top-10 organic.
  - 2026 Follow-up (863K SERPs, 4M cited URLs):
    - Top 10 Organic: **37.9%** (collapsed from 76.1%)
    - Rank 11–100: **31.2%**
    - Beyond Top 100 / Non-ranking: **31.0%**
- **Query Fan-Out:** Google AI Mode decomposes one user prompt into multiple sub-queries. Traditional top-10 rank is no longer an absolute gate for AI visibility; subtopic coverage and entity relevance dominate.

### 3.2 Cross-Engine Citation Coverage (CECO) & Wilson Intervals
- **CECO Metric:**
  CECO = (number of engines citing brand/domain) / (total engines tested)
  Across ChatGPT, Perplexity, Claude, Gemini, and Google AI Overviews.
- **Wilson 95% Confidence Interval for Empirical Sampling:**
  CI_95% = (p_hat + z^2 / (2n) +/- z * sqrt(p_hat * (1 - p_hat) / n + z^2 / (4n^2))) / (1 + z^2 / n)
  With z = 1.96 and n >= 10 runs per engine (5 runs minimum floor).

---

## 4. The Canonical 16-Defect Matrix

### Hard Failures (Deterministic Blockers)
- **`HF-01`**: Target page returns non-success HTTP status (4xx/5xx).
- **`HF-02`**: Canonical URL unavailable, self-contradictory, or conflicting.
- **`HF-03`**: Search retrieval crawler (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) blocked in `robots.txt`.
- **`HF-04`**: `noindex` directive active on citation-critical route.
- **`HF-05`**: `nosnippet` or restrictive `max-snippet` active on core informational content.
- **`HF-06`**: Primary commercial product data absent or contradictory (HTML <-> JSON-LD price mismatch).
- **`HF-07`**: Critical factual claims exist solely in images/PDF/JS without equivalent HTML text.
- **`HF-08`**: Structured data directly contradicts visible page content.

### High-Value Warnings (Probabilistic & Quality Risks)
- **`W-01`**: Core factual claims cannot be extracted from initial HTML (SSR gap).
- **`W-02`**: High-value facts lack supporting independent source or verifiable attribution.
- **`W-03`**: Price/availability differs between HTML, JSON-LD, and merchant feeds.
- **`W-04`**: Brand identity discordance across Organization schema, visible copy, and external nodes.
- **`W-05`**: Evidence pages require excessive navigation depth (`DiscoveryDepth > 3` hops).
- **`W-06`**: `llms.txt` manifest contains broken, redirected, or non-canonical links.
- **`W-07`**: Citation-ready content lacks quantitative evidence (`FTR < 0.040`, no numerical data).
- **`W-08`**: AI visibility differs materially across engines (`CECO < 0.50`).

---

## 5. The 6 Orthogonal Scoring Dimensions

Rather than a single arbitrary score, the audit evaluates six orthogonal dimensions:

1. **Crawlability Score (Weight: 20%):**
   Deterministic access: HTTP 200, RFC 9309 compliance, crawler permissions (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`), sitemaps.
2. **Retrieval Readiness (Weight: 20%):**
   Text extractability, Signal-to-Noise Ratio (SNR >= 0.12), Content Availability Gap (`CAG < 0.15`), heading semantics, content freshness.
3. **Citation Readiness (Weight: 20%):**
   Atomic fact density (FTR >= 0.080), Princeton GEO evidence density (>= 1 stat + quote / 150 words), low hedge rate (`HedgeRate <= 1.2%`), BLUF top-30% placement.
4. **Entity / Authority Score (Weight: 15%):**
   Machine-explicit schema graph, bidirectional `sameAs` linkage (>= 2 nodes), cross-page fact ledger consistency, external Knowledge Graph footprint.
5. **Cross-Engine Visibility Score (Weight: 15%):**
   Empirical mention rate, citation rate, and `CECO` across the Big 5 engines, bound by Wilson 95% confidence intervals.
6. **Agentic Commerce Score (Weight: 10%):**
   Product completeness, clean float pricing, ISO 4217, Universal Commerce Protocol (UCP), Agent Payments Protocol (AP2), and Agent2Agent (A2A) readiness.
