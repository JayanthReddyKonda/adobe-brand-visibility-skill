# State-of-the-Art Generative Engine Optimization (GEO) Benchmarks & Standards

This document establishes the empirical, algorithmic, and architectural benchmarks for the Brand AI-Readiness Audit Skill, derived from peer-reviewed AI research (KDD 2024, NeurIPS 2025, EMNLP 2023, TACL 2024), search engine crawler disaggregation specifications, and 2025–2026 empirical AI retrieval studies.

---

## 1. Academic & Empirical Research Foundations

### A. Foundational GEO & Attribution Mechanics

#### 1. "GEO: Generative Engine Optimization"
- **Citation:** Aggarwal, P., Murahari, V., Rajpurohit, T., Kalyan, A., Narasimhan, K., & Deshpande, A. (ACM SIGKDD 2024 / arXiv:2311.09735).
- **Core Findings & Visibility Lift Statistics:**
  - Optimization for generative engines differs fundamentally from traditional search engines across the 10,000-query GEO-bench:
    - **Statistics Addition:** **+30% to +41%** relative lift in AI visibility (replacing qualitative claims with specific, attributed numerical data).
    - **Cite Sources:** **+30% to +40%** relative lift across top results, and up to **+115% visibility lift** for lower-ranked niche pages.
    - **Quotation Addition:** **+30% to +40%** relative lift (extractable pull-quotes from named experts).
    - **Fluency & Simplification:** **+15% to +30%** lift.
    - **Authoritative Tone:** **+10.4%** on position-adjusted metrics, **+18.7%** on subjective impression.
    - **Keyword Stuffing:** Caused a **-10% to negative effect**, actively harming attribution.
- **Mathematical Formulation:**
  $$\text{PAWC}(S, R) = \sum_{c \in C_S} \frac{\text{WordCount}(c)}{\log_2(\text{Rank}(c) + 1)}$$
  Where $C_S$ is the set of citations to source $S$ in response $R$, $\text{WordCount}(c)$ is the token volume attributed to the citation, and $\text{Rank}(c)$ is the 1-indexed position of the citation within the synthesized response.
- **Audit Rule (`TX06` / `Rule_GEO_EvidenceDensity`):**
  Every 150–200 words of substantive copy must contain at least one verifiable quantitative statistic (`\d+(\.\d+)?%?|\$[\d,]+`) and at least one cited entity reference or quotation.

#### 2. "C-SEO Bench: Does Conversational SEO Work?"
- **Citation:** Puerto, H., Gubri, M., Green, T., Oh, S. J., & Yun, S. (NeurIPS 2025 Datasets and Benchmarks Track / arXiv:2506.11097).
- **Core Findings:**
  - In competitive multi-agent retrieval environments, pages featuring **LLM Guidance headers** (structured Markdown summaries directly beneath the main title, conceptually matching `/llms.txt`) substantially outperform standard narrative layouts by directing LLM context attention during RAG ingestion.
- **Audit Rule (`LL02` / `Rule_LLM_ExecutiveSummary`):**
  Pages should feature an executive abstract or takeaway block (`<aside class="summary">` or Markdown blockquote `>`) within the first 100 words summarizing the core entities, answers, and conclusions.

#### 3. "Evaluating Verifiability in Generative Search Engines"
- **Citation:** Liu, N. F., Zhang, T., & Liang, P. (Stanford University, Findings of EMNLP 2023 / arXiv:2304.09848).
- **Core Findings:**
  - Evaluated Bing Chat, Perplexity, NeevaAI, and YouChat.
  - **Citation Recall:** Only **51.5%** of generated sentences were fully supported by citations.
  - **Citation Precision:** Only **74.5%** of citations actually supported the sentence they cited.
  - LLMs penalize ambiguous or composite sentences. Retrieval systems favor source passages that present unambiguous, one-to-one semantic entailments.
- **Audit Rule (`Rule_Atomic_Entailment`):**
  Content must be structured as atomic, self-contained claim-evidence propositions without split antecedents across complex sentences.

#### 4. "Lost in the Middle: How Language Models Use Long Contexts"
- **Citation:** Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (Stanford, TACL 2024 / arXiv:2307.03172).
- **Core Findings:**
  - LLM retrieval accuracy follows a U-shaped curve: information at the absolute beginning (top 15–20%) or end of context receives high attention, whereas retrieval degradation in the middle exceeds **30–40%**.
  - Supported by empirical AI Overviews data: **44.2% of citations in ChatGPT Search and Perplexity are pulled from the top 30% of the web page**.
- **Audit Rule (`TX01` / `Rule_BLUF_Top30Percent`):**
  Bottom Line Up Front (BLUF): The direct definition, resolution, or transactional answer must appear within the first 250 words (or top 30% of DOM content) before contextual background or narrative exposition.

---

### B. 2025/2026 Empirical Retrieval Landscape

```
                       EMPIRICAL AI RETRIEVAL LANDSCAPE
  
  [ Organic SERP vs. AI Overviews ]
  Overlap between Google Top-10 & AI Overviews:  Collapsed from ~75% (2024) to 17%–38% (2026)
  
  [ ChatGPT Search Selection Bias ]
  Non-Top 20 organic Google URLs cited:          ~80%–90% of the time (favors niche density)
  
  [ Perplexity Recency Bias ]
  Cited pages updated within previous 30 days:   76.4%
  
  [ E-Commerce Referral Conversion Rates ]
  ChatGPT Referrals: 14.2%–15.9%  |  Claude: 16.8%  |  Traditional Organic Search: 1.76%
```

- **Organic-AI Overlap Disconnection:** Google Top-10 SERP overlap with AI Overviews collapsed from ~75% to **17%–38%**. In ChatGPT Search, Chris Long / Semrush data demonstrates that over **28% of cited pages possess zero organic Google visibility**, with position 21+ pages accounting for ~90% of citations when semantic density is high.
- **Perplexity Freshness Half-Life:** **76.4% of Perplexity's top citations were updated within the last 30 days**. Pages with recent timestamps (`dateModified`) experience a **2.8x higher citation frequency**.
- **Commercial Conversion Multipliers:** AI answer engine referrals convert at **10.5% (Perplexity), 14.2%–15.9% (ChatGPT), and up to 16.8% (Claude)**, compared to **1.76%** for legacy organic search links.

---

## 2. Crawler Disaggregation & RFC 9309 Protocol Standards

### A. The Three AI Crawler Categories

| Engine / Lab | Training Crawler (Disallow Safe) | Search Indexer (MUST ALLOW for GEO) | User-Directed Fetcher (Real-time Proxy) |
| :--- | :--- | :--- | :--- |
| **OpenAI** | `GPTBot` | `OAI-SearchBot` | `ChatGPT-User` |
| **Anthropic** | `ClaudeBot` | `Claude-SearchBot` | `Claude-User` |
| **Perplexity** | *(Indexes for answers)* | `PerplexityBot` | `Perplexity-User` |
| **Google** | `Google-Extended` *(token)* | `Googlebot` | `Google-CloudVertexBot` / User agents |
| **Meta** | `Meta-ExternalAgent` | `Meta-ExternalFetcher` | `Meta-ExternalFetcher` |
| **Apple** | `Applebot-Extended` | `Applebot` | `Applebot` |

### B. RFC 9309 Compliance Rules
- **Longest-Match Precedence (§2.2.2):** Between an `Allow` and a `Disallow` directive that match the same URI, the directive with the longest octet path string wins.
- **5xx Server Error State (§2.3.1.2):** If `robots.txt` returns HTTP `500` through `599`, crawlers assume a full temporary disallow (fail-closed) and suspend crawling. If it returns HTTP `404`, crawlers assume full access (fail-open).
- **File Size Cap (§2.2):** Crawlers must parse at least 500 Kibibytes (512,000 octets). Directives beyond 500 KiB are discarded.
- **Deprecation of `Crawl-delay`:** Non-standard directive. Modern AI crawlers manage rate limits via HTTP `429 Too Many Requests` with `Retry-After` headers.

---

## 3. Quantitative Scoring Formulas & Benchmarks

### 1. Lakoff & Hyland Linguistic Hedging Metric
$$\text{HedgeRate} = \left( \frac{\sum w_{\text{hedge}}}{N_{\text{total\_words}}} \right) \times 100$$
- **Authoritative / Highly Cited Content:** $\text{HedgeRate} \le 1.2\%$
- **Neutral Informational Content:** $1.2\% < \text{HedgeRate} \le 2.2\%$
- **Speculative / Low-Trust Content (Penalized):** $\text{HedgeRate} > 2.5\%$

### 2. Atomic Fact-to-Token Ratio (FTR)
$$\text{FTR} = \frac{N_{\text{atomic\_facts}}}{N_{\text{tokens}}}$$
- **Citable AI-Engineered Tier:** $\text{FTR} \ge 0.080$ (at least 1 atomic verifiable fact per 12.5 tokens).
- **Fluff / Thin Content Tier:** $\text{FTR} \le 0.035$ (verbose marketing prose lacking verifiable claims).

### 3. Shannon Text Entropy
$$H(X) = -\sum_{i=1}^{n} p(x_i) \log_2 p(x_i)$$
- **Optimized Range for RAG Comprehension:** $6.8 \le H(X) \le 7.6\text{ bits}$ (for English text chunks of 150–200 words).

### 4. Passage Extractability & Self-Containment Rubric
- **Optimal RAG Chunk Size:** **134 to 167 words** per section under each semantic header (`<h2>`/`<h3>`).
- **Exophoric Pronoun Ratio:**
  $$\text{ExoRatio} = \frac{\text{Count of leading pronouns lacking intra-chunk antecedents}}{\text{Total section lead sentences}}$$
  - **Target:** $0.0\%$. Brand entity must explicitly replace ambiguous pronouns in the first sentence of every section.

---

## 4. Consolidated 17-Rule Audit Matrix (`CR01`–`TX06`)

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
