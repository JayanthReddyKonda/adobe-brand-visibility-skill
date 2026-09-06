# Generative Engine Optimization (GEO) & Retrieval Science Synthesis

**Author:** Jayanth Reddy Konda  
**Version:** 3.0.0  
**Scope:** Peer-Reviewed Academic Literature, Empirical Benchmarks & Citation Science  

---

## 1. Foundational Academic Literature

### A. "GEO: Generative Engine Optimization" (Aggarwal et al., ACM SIGKDD 2024)
- **arXiv:** [2311.09735](https://arxiv.org/abs/2311.09735)
- **Core Contribution:** First formal mathematical model of generative search engines across 10,000 queries in the GEO-bench.
- **The Empirical Lift Table:**
  - Quotation Addition: **+40.9% PAWC lift** (highest position-adjusted impact).
  - Statistics Addition: **+30.6% PAWC lift** (replaces qualitative claims with numerical facts).
  - Fluency Optimization: **+28.0% lift**.
  - Cite Sources: **+27.5% lift**.
  - Technical Terminology: **+17.6% lift**.
  - Easy-to-Understand: **+14.0% lift**.
  - Authoritative Tone: **+10.4% lift** (+18.7% on subjective impression).
  - Keyword Stuffing: **-8.3% to -10.0% (actively harmful)**.
- **The Inverse Rank Correlation Discovery:**
  GEO gains are inversely correlated with baseline organic Google rank. A page ranked #5 gains up to **+115%** from adding citations, whereas a #1 page can experience diminished returns. **Target long-tail and niche pages for highest GEO ROI.**

---

### B. "From Citation Selection to Citation Absorption" (Zhang, He, Yao — 2026)
- **arXiv:** [2604.25707](https://arxiv.org/abs/2604.25707) · Dataset: `geo-citation-lab`
- **Scope:** 602 prompts, 21,143 citations, 72 extracted features across ChatGPT Search, Perplexity AI, and Google AI Overviews.
- **The Mathematical `Influence_i` Model:**
  ```text
Influence_i = 0.20 * min(ref_count_i / 3, 1) + 0.15 * (1 - first_position_ratio_i) + 0.20 * paragraph_coverage_ratio_i + 0.25 * tfidf_cosine_i + 0.20 * ((bigram_overlap_i + trigram_overlap_i) / 2)
```
- **Evidence-Genre Relative Lift:**
  - Code Snippets / Blocks: **+76.9% lift** (highest influence).
  - Numbers / Statistics: **+61.6% lift**.
  - Definition Markers: **+57.3% lift**.
  - Comparison Structures / Tables: **+55.3% lift**.
  - How-To Steps: **+41.2% lift**.
  - **Standalone Q&A / FAQ Format Alone: -5.7% (Negative Penalty!)**
  - **Critical Rule:** Never reward FAQ format alone. FAQ blocks without data, code, or comparisons suffer an empirical citation penalty.

---

### C. "Citation Failure Modes in GEO" (Tian et al. — 2026)
- **arXiv:** [2603.09296](https://arxiv.org/abs/2603.09296)
- **Key Finding:** **43% of topically relevant pages receive zero citation** under baseline conditions.
- **The 5-Stage Failure Taxonomy:**
  1. **Retrieval Failure:** Crawler block (`robots.txt`), 4xx/5xx errors, `noindex`, unrendered SPA shell.
  2. **Relevance Failure:** Title/H1 query-intent mismatch or semantic drift.
  3. **Redundancy Failure:** Generic prose losing context allocation to authoritative domain summaries.
  4. **Trust Failure:** Low fact density (FTR < 0.040), excessive hedging (> 2.5%), missing `sameAs`.
  5. **Extraction Failure:** `nosnippet`, low text Signal-to-Noise Ratio (< 0.12), DOM fragmentation.

---

### D. "Lost in the Middle" & Context Retention (Liu et al., Stanford, TACL 2024)
- **arXiv:** [2307.03172](https://arxiv.org/abs/2307.03172)
- **Finding:** LLM attention follows a U-shaped curve; information placed in the middle of long contexts degrades in retrieval accuracy by **30%–40%**.
- **Empirical Corroboration (Zyppy 2025/2026):** **44.2% of citations in ChatGPT Search and Perplexity are extracted from the top 30% of a page.**
- **Rule:** BLUF (Bottom Line Up Front). Core answers and definitions must appear within the first 250 words.

---

### E. Citation Faithfulness vs. Correctness (Wallat et al. — 2024)
- **arXiv:** [2412.18004](https://arxiv.org/abs/2412.18004)
- **Key Finding:** Up to **57% of citations lack faithfulness** due to model post-rationalization. A citation may be factually correct while not being the actual source the model relied upon. Systems must evaluate both entailment and factual faithfulness.

---

## 2. Real-World AI Search Empirical Benchmarks

### 1. The Google AI Overviews 2026 Shift (Query Fan-Out)
- **Ahrefs Empirical Dataset (863K SERPs, 4M Citations):**
  - Google Top-10 Organic Overlap collapsed from **76.1% (2024)** to **37.9% (2026)**.
  - Rank 11–100 accounts for **31.2%** of citations.
  - Outside Top 100 / Non-ranking URLs account for **31.0%** of citations.
- **Mechanism:** Google AI Mode uses **Query Fan-Out**, decomposing one user question into multiple sub-queries. Traditional search rank is no longer a prerequisite for AI inclusion.

### 2. The 57% Off-Site Branded Footprint Discovery (Omniscient Digital 2026)
- **Dataset:** 23,387 branded query citations analyzed across ChatGPT, Perplexity, and Claude.
- **Distribution:**
  - **57% of branded citations** come from third-party reviews, comparison listicles, Reddit, Wikipedia, and press.
  - **Only ~4.5% of citations** derive from the brand's own official About, FAQ, or Homepage!
  - Top 15 third-party authority domains capture **~68%** of all AI citations.
- **Takeaway:** On-page optimization governs only a fraction of branded AI visibility; external third-party corroboration nodes are essential.

### 3. Multi-Platform Divergence
- Only **11% of domains** are cited by both ChatGPT and Perplexity for identical queries.
- **ChatGPT Search:** Encyclopedic bias (Wikipedia 7.8% - 47.9%), high per-citation influence (0.271).
- **Perplexity AI:** Community discussion bias (Reddit 46.7%), recency bias (76.4% citations < 30 days old).
- **Google AI Overviews:** Multimodal bias (YouTube 23.3%).

---

## 3. Mathematical Formulations for Evaluation

### 1. Lakoff & Hyland Linguistic Hedging Rate
```text
HedgeRate = (sum(w_hedge) / N_total_words) * 100
```
- Authoritative / Highly Cited: <= 1.2%
- Neutral Informational: 1.2% - 2.2%
- Speculative / Low Trust: > 2.5%

### 2. Atomic Fact-to-Token Ratio (FTR / FActScore)
```text
FTR = N_atomic_facts / N_tokens
```
- Citable AI-Engineered: >= 0.080
- Thin / Marketing Fluff: < 0.040

### 3. Wilson 95% Score Confidence Interval
```text
CI_95% = (p_hat + z^2 / (2n) +/- z * sqrt(p_hat * (1 - p_hat) / n + z^2 / (4n^2))) / (1 + z^2 / n)
```
Where z = 1.96, p_hat is observed citation rate, and n >= 10 runs per engine.
