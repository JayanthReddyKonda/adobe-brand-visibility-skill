# Canonical AI Crawler Matrix & Platform Semantics Reference

Understanding the distinct purposes and operational impacts of AI web crawlers is essential for avoiding false-positive audit findings.

---

## Crawler Taxonomy & Impact Matrix

| User-Agent Token | Operator | Operational Role | Business Impact of Blocking | Severity if Disallowed |
| :--- | :--- | :--- | :--- | :--- |
| **`OAI-SearchBot`** | OpenAI | **Retrieval** (SearchGPT / ChatGPT Search) | The brand will NOT be indexed or cited in ChatGPT real-time web search answers. | `critical` / `high` |
| **`Claude-SearchBot`** | Anthropic | **Retrieval** (Claude Search) | The site cannot be retrieved for real-time web grounding inside Claude conversations. | `high` |
| **`PerplexityBot`** | Perplexity AI | **Retrieval** (Perplexity Search Index) | The site is excluded from Perplexity's core search index and citation cards. | `critical` / `high` |
| **`anthropic-ai`** | Anthropic | **Retrieval** (Live Search) | General live Anthropic retrieval system excluded from scraping public routes. | `high` |
| **`ChatGPT-User`** | OpenAI | **User-Initiated Fetch** | An end-user explicitly asking ChatGPT to inspect a URL will receive a fetch error. | `medium` |
| **`GPTBot`** | OpenAI | **Training** (Foundation Pre-training) | The brand's data is omitted from offline model pre-training corpora. (Intentional privacy opt-out). | `info` / `low` |
| **`ClaudeBot`** | Anthropic | **Training** (Foundation Pre-training) | The brand's data is omitted from Claude offline model training. (Intentional privacy opt-out). | `info` / `low` |
| **`Google-Extended`** | Google | **Training** (Gemini / Vertex AI) | Excludes content from Gemini foundation training. (Does NOT block Google Search or Google AI Overviews). | `info` / `low` |
| **`Applebot-Extended`** | Apple | **Training** (Apple Intelligence) | Excludes content from Apple Intelligence foundation model training. | `info` / `low` |
| **`CCBot`** | Common Crawl | **Training** (Open Corpora) | Excludes site from Common Crawl dumps used by open-source research. | `info` / `low` |

---

## Key Audit Rules

1. **Never Conflate Training with Retrieval:**
   - Blocking `GPTBot` or `Google-Extended` is a legitimate copyright/governance choice. It MUST NOT be reported as a critical AI search discovery defect.
   - Only blocking retrieval crawlers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) creates an active visibility outage.
2. **Google AI Overviews (AIO):**
   - Uses standard `Googlebot` crawling and indexing pipelines. `Google-Extended` disallows do NOT prevent Google Search or AI Overviews from citing a page.

