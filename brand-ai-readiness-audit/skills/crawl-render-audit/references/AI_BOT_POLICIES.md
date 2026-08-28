# AI Bot Crawler Policies Reference

AI assistants and generative search engines deploy automated crawlers to discover, retrieve, and index content. This reference outlines primary AI user-agents and optimal configuration patterns.

---

## 1. Key AI Bot User-Agents

| Bot User-Agent | Provider / App | Purpose | Impact if Blocked |
| :--- | :--- | :--- | :--- |
| **`GPTBot`** | OpenAI / ChatGPT | Web crawl for GPT training & real-time search | ChatGPT Search cannot index or cite site |
| **`ChatGPT-User`** | OpenAI | On-demand live search browsing on user query | Real-time ChatGPT answers cannot retrieve page |
| **`ClaudeBot`** | Anthropic / Claude | Web crawler for training and assistant retrieval | Claude assistants cannot inspect site facts |
| **`PerplexityBot`** | Perplexity AI | Real-time conversational search crawler | Excluded from Perplexity answer synthesis |
| **`Google-Extended`** | Google / Gemini | Controls Google Gemini & Vertex AI web training | Controls AI training ingest |
| **`Bytespider`** | ByteDance | General AI crawler | AI apps powered by ByteDance models |
| **`CCBot`** | Common Crawl | Public open web archive | Omission from open foundational datasets |

---

## 2. Recommended `robots.txt` Configuration

To maximize brand discoverability in AI search engines while protecting private/admin areas:

```txt
# Allow verified AI search agents to index marketing & documentation
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

# General rules
User-agent: *
Disallow: /admin/
Disallow: /api/private/
Disallow: /checkout/

Sitemap: https://www.example.com/sitemap.xml
```

---

## 3. `llms.txt` Standard

Publishing a `/llms.txt` file at the domain root provides a structured, token-efficient table of contents formatted specifically for LLM context windows.

