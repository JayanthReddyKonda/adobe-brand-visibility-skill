# Web Scraper Skill — Knowledge Base & Architecture Reference

## 1. Architectural Principles

The `web-scraper` skill is an autonomous, production-grade web acquisition engine purpose-built for You. It operates under strict constraints:
- **Zero Third-Party Dependencies:** 100% pure Python 3.9+ standard library (`urllib.parse`, `urllib.request`, `socket`, `html.parser`, `xml.etree.ElementTree`, `heapq`, `gzip`, `zlib`).
- **No Browser Runtimes:** No headless Chrome, Playwright, Selenium, or heavy Node.js dependencies.
- **Resource Sandboxing:** Strict monotonic time deadlines, page count caps, and per-resource byte ceilings.
- **Zero-Trust SSRF Defense:** Real-time IP address pre-resolution and socket-level filtering preventing loopback, private RFC 1918, link-local, and cloud metadata access.

---

## 2. The 16 AI Crawler Matrix & RFC 9309 Semantics

AI retrieval engines separate search retrieval crawlers (needed to cite the brand in live answers) from foundation model training scrapers (used for pre-training).

| User-Agent | Organization | Primary Role | Critical Disallow Consequence |
|---|---|---|---|
| `OAI-SearchBot` | OpenAI | ChatGPT Search live retrieval | Critical: Content invisible to ChatGPT Search |
| `PerplexityBot` | Perplexity AI | Perplexity Pro search citations | Critical: Excluded from Perplexity citations |
| `Claude-SearchBot` | Anthropic | Claude search retrieval | Critical: Excluded from Claude citations |
| `Bingbot` | Microsoft | Copilot & Bing grounding | Critical: Excluded from Copilot & Bing |
| `Google-Extended` | Google | Training control token (Gemini training data; uses Googlebot HTTP UA) | Low/Med: Governance decision (opts out of Gemini training) |
| `Applebot-Extended` | Apple | Training control token (Apple Intelligence training; uses Applebot HTTP UA) | Low/Med: Governance decision (opts out of Apple training) |
| `YouBot` | You.com | Generative search citations | Medium: Excluded from You.com search |
| `GPTBot` | OpenAI | Foundation training ingestion | Low: Governance decision (protects IP) |
| `ClaudeBot` | Anthropic | Foundation training ingestion | Low: Governance decision (protects IP) |
| `Googlebot` | Google | General web indexing | High: Classic search indexation failure |
| `Meta-ExternalAgent` | Meta | Llama training & Meta AI | Low: Governance decision |
| `Amazonbot` | Amazon | Alexa & Rufus search | Medium: Excluded from Amazon assistant |
| `ByteSpider` | ByteDance | TikTok / Doubao training | Low: Governance decision |
| `CCBot` | Common Crawl | Public research corpus | Low: Research crawl inclusion |
| `Diffbot` | Diffbot | Knowledge graph extraction | Medium: KG extraction failure |
| `cohere-ai` | Cohere | Enterprise RAG pre-training | Low: Governance decision |

### RFC 9309 Evaluation Rules
1. **Longest Match Precedence:** In conflicting directives, the longest matching path string takes precedence over shorter paths, regardless of declaration order.
2. **Fail-Closed 5xx Semantics:** If `robots.txt` returns HTTP 500-599, crawlers treat the entire domain as disallowed.
3. **Fail-Open 404 Semantics:** If `robots.txt` returns HTTP 404 Not Found, crawlers treat the entire domain as fully allowed.
4. **500 KiB File Ceiling:** Directives declared beyond 512,000 octets are discarded per RFC 9309 §2.2.

---

## 3. Trafilatura & Crawl4AI Content Extraction Heuristics

AI models require clean, distraction-free text. Raw HTML contains navigation menus, cookie consent banners, footers, tracking scripts, and styling noise that degrades LLM context windows.

### Boilerplate Stripping
The parser discards tags that do not contain core semantic content:
- `script`, `style`, `noscript`, `svg`, `canvas`, `iframe`
- `nav`, `header`, `footer`, `aside`, `dialog`
- Elements with CSS classes or IDs matching: `cookie`, `banner`, `popup`, `modal`, `overlay`, `tracker`, `advertisement`, `sponsored`

### Signal-to-Noise Ratio (SNR)
SNR quantifies the informational density of an HTML document:

SNR = (Length of Extracted Clean Text characters) / (Length of Raw HTML Source characters)

- **SNR >= 0.15**: High semantic density (typical of articles, docs, and structured product pages).
- **0.05 <= SNR < 0.15**: Moderate density (typical of commercial landing pages with rich UI).
- **SNR < 0.05**: Low density / potential Single Page Application (SPA) shell risk.

### Sparse SPA Shell Detection
A page is classified as a **Sparse SPA Shell** when:
1. Total initial HTML word count is < 25 words.
2. The DOM consists primarily of empty mounting containers (`<div id="root"></div>`, `<div id="app"></div>`, `<div id="__next"></div>`).
3. Heavy script bundles are present without server-side rendered text.

---

## 4. Priority Frontier Route Scoring

Rather than naive breadth-first crawling, the frontier prioritizes routes that carry the highest commercial and factual value:

| Route Pattern | Priority Score | Justification |
|---|---|---|
| `/` (Homepage) | 100 | Core entity definition, H1, navigation hub |
| `/pricing`, `/plans`, `/rates` | 90 | High-intent commercial answerability |
| `/products`, `/solutions`, `/services` | 85 | Product taxonomy and catalog specifications |
| `/about`, `/company`, `/team` | 80 | Knowledge graph entity identity and `sameAs` |
| `/docs`, `/documentation`, `/api` | 75 | Technical specifications and integration details |
| `/contact`, `/support` | 70 | Verified contact facts and support channels |
| `/blog`, `/news` | 50 | Editorial and recency claims |
| Operational paths (`/cart`, `/login`, `/checkout`) | **Filtered (0)** | Junk utility paths excluded from crawl |

---

## 5. Zero-Trust SSRF Defense Matrix

All outgoing HTTP socket connections are pre-resolved and validated against prohibited network ranges:

| Address Range | CIDR / Address | Security Classification | Action |
|---|---|---|---|
| Loopback IPv4 | `127.0.0.0/8` | Localhost | Block |
| Loopback IPv6 | `::1/128` | Localhost | Block |
| Private Class A | `10.0.0.0/8` | Internal Network | Block |
| Private Class B | `172.16.0.0/12` | Internal Network | Block |
| Private Class C | `192.168.0.0/16` | Internal Network | Block |
| Link-Local | `169.254.0.0/16` | Auto-IP / Cloud Metadata | Block |
| Cloud Metadata | `169.254.169.254` | AWS/GCP/Azure Metadata | Block |
| IPv4-mapped IPv6 | `::ffff:0:0/96` | Mapped Private IPs | Block |
