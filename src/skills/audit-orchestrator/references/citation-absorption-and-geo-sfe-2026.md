# Citation Absorption, GEO-SFE, and Empirical Retrieval Science (2026)

**Research Scope:** Citation Absorption Mechanics (arXiv:2604.25707), Structural Feature Engineering for GEO (arXiv:2603.29979), Citation Failure Modes (arXiv:2603.09296), and Off-Site Third-Party Authority Dynamics.

---

## 1. "From Citation Selection to Citation Absorption" (Zhang, He, Yao — 2026)
- **Citation:** Zhang, X., He, Y., & Yao, J. (2026). *From Citation Selection to Citation Absorption: An Empirical Study of Generative Search Engine Attribution*. arXiv:2604.25707. Dataset: `geo-citation-lab`.
- **Dataset Scope:** 602 query prompts, 21,143 citations, 72 extracted features across ChatGPT Search, Perplexity AI, and Google AI Overviews.

### A. The Mathematical `Influence_i` Model
The paper formalizes citation influence as a multi-component metric reflecting how deeply an AI engine incorporates source content into the synthesized answer:

```text
Influence_i = 0.20 * min(ref_count_i / 3, 1) + 0.15 * (1 - first_position_ratio_i) + 0.20 * paragraph_coverage_ratio_i + 0.25 * tfidf_cosine_i + 0.20 * ((bigram_overlap_i + trigram_overlap_i) / 2)
```

Where:
- `ref_count_i`: Number of times source i is cited across distinct sentences in the answer.
- `first_position_ratio_i`: Normalized token offset of the source's first citation (earlier placement yields higher influence).
- `paragraph_coverage_ratio_i`: Proportion of generated paragraphs attributing facts to source i.
- `tfidf_cosine_i`: Cosine similarity between source text and synthesized answer.
- `phrase_overlap_i` (bigram / trigram): Lexical phrase absorption into final output.

### B. Actionable Evidence-Genre Lift Table
Content genres exhibit vastly divergent influence on generative engine answer generation:

| Detected Evidence Genre | Relative Influence Lift | Audit Action |
| :--- | :--- | :--- |
| **Code Snippets / Syntax Blocks** | **+76.9%** | Highest influence; provide executable CLI/code blocks. |
| **Quantitative Numbers / Statistics** | **+61.6%** | Replace narrative claims with exact benchmarks. |
| **Explicit Definition Markers** | **+57.3%** | Include unambiguous IS-A definitions (`defined as`, `refers to`). |
| **Comparison Structures / Tables** | **+55.3%** | Provide head-to-head evaluation matrices (`vs`, `unlike`). |
| **How-To / Procedural Guidance** | **+41.2%** | Numbered implementation workflows. |
| **Standalone Q&A / FAQ Format Alone** | **-5.7% (Negative Penalty)** | **Do not rely on FAQ format alone!** Augment with data and comparisons. |

### C. Semantic-Role Influence Hierarchy
1. **Definition Content:** Mean influence 0.153
2. **Comparison Content:** Mean influence 0.142
3. **Statistical Data:** Mean influence 0.138
4. **Procedural Steps:** Mean influence 0.119
5. **Pure Background / Reference:** Mean influence 0.053 (lowest)

### D. Platform Divergence: Selection Breadth vs. Absorption Depth
- **ChatGPT Search:** Cites fewer sources (mean 6.9 sources/query) but with substantially higher per-citation influence (0.271). Deeply absorbs core sources. Encyclopedic bias (Wikipedia 7.8% - 47.9%).
- **Perplexity AI:** Cites broadest surface (mean 16.4 sources/query) with lower per-citation influence (0.065). Community discussion bias (Reddit 46.7%).
- **Google AI Overviews:** Intermediate breadth (12.1 sources/query, 0.058 influence). Multimodal bias (YouTube 23.3%). Overlaps with Google AI Mode only 13.7% of the time!

---

## 2. Structural Feature Engineering for GEO (GEO-SFE — 2026)
- **Citation:** Yu, Yang, Ding, & Sato (Tokyo/Tsukuba/Hiroshima, 2026). arXiv:2603.29979.
- **Key Finding:** Structure-aware rewriting alone—holding textual content constant—delivers **+17.3% citation improvement and +18.5% perceptual quality gain**.
- **Three Structural Tiers:**
  1. **Macro Architecture:** Strict heading hierarchy (`<h1>` -> `<h2>` -> `<h3>`), table of contents, and executive takeaways.
  2. **Meso Chunking:** Standalone section self-containment (134–167 words per section) that can be extracted independently without antecedent loss.
  3. **Micro Visual Emphasis:** Semantic bullet lists (density >=0.40$), comparison tables, and bold key takeaway leads.

---

## 3. Citation Failure Modes Decision Tree (Tian et al. — 2026)
- **Citation:** Tian, Chen, Tang, Liu, & Jia (Virginia Tech / Zhejiang, 2026). arXiv:2603.09296.
- **Key Finding:** **43% of topically relevant pages receive zero citation** under baseline conditions. Non-citation is a binary structural failure mode.
- **Diagnostic Decision Tree:**
  ```
  Page Analysis
  │
  ├── [1. Retrieval Failure] ────► robots.txt disallow / noindex / unindexed SSR shell
  │                                Fix: Server-side rendering, crawler permissions, XML sitemap
  │
  ├── [2. Relevance Failure] ────► Query intent mismatch / title-H1 semantic drift
  │                                Fix: Target conversational query intent, align H1 and title
  │
  ├── [3. Redundancy Failure] ───► Generic content duplicate of higher-authority domain
  │                                Fix: Inject proprietary benchmarks, first-party data, code
  │
  ├── [4. Trust Failure] ────────► Low FTR (<0.040) / excessive hedging (>2.5%) / no sameAs
  │                                Fix: Eliminate weasel words, cite named researchers, link Wikidata
  │
  └── [5. Extraction Failure] ───► nosnippet / data-nosnippet / low SNR (<0.12) / complex DOM
                                   Fix: Clean DOM, remove nosnippet, elevate text-to-HTML ratio
  ```

---

## 4. Off-Site Third-Party Dominance (57% Branded Citation Footprint)
- **Empirical Study:** Omniscient Digital (23,387 branded query citations analyzed, 2026).
- **Core Discovery:**
  - **57% of branded query citations** come from third-party reviews, comparison listicles, Reddit discussions, and independent press.
  - **Only ~4.5% of citations** derive from the brand's own official About, FAQ, or Homepage!
  - Top 15 third-party authority domains capture **~68%** of all generative engine citations (Reddit, Wikipedia, YouTube, LinkedIn, Forbes, Trustpilot, G2).
- **Audit Mandate:** A brand audit that examines only on-page SEO misses 57% of the real-world citation surface. The audit must evaluate external identity anchors, review footprint, and third-party corroboration nodes.

---

## 5. The 0–30 CITE Citability Score Rubric
The 0–30 CITE Citability Score Rubric defines the objective criteria for evaluating content readiness:

| Code | Dimension | Points | Evaluation Metric |
| :--- | :--- | :---: | :--- |
| **DA** | Direct Answer | 0–5 | Section openers provide standalone, extractable 40–60 word answer leads. |
| **DD** | Data Density | 0–5 | Specific numbers, percentages, durations, benchmark statistics (FTR >=0.080$). |
| **AS** | Authority Signals | 0–5 | Named researchers, DOIs, authoritative outbound citations, verified `sameAs` nodes. |
| **SQ** | Structure Quality | 0–5 | Heading hierarchy, comparison tables, list density >=0.40$, code blocks. |
| **FR** | Freshness | 0–5 | Visible dateModified $< 60$ days, recent temporal grounding. |
| **UQ** | Uniqueness | 0–5 | Proprietary case data, original frameworks, zero generic boilerplate. |

**Total Score Bands:** A (27–30) / B (22–26) / C (17–21) / D (12–16) / F (<12).
