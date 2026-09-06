---
name: web-scraper
description: >
  Autonomous, zero-dependency, SSRF-hardened web crawler and AI content extractor. Use this skill
  whenever the user asks to "crawl a website", "scrape web pages", "extract clean markdown",
  "audit robots.txt", "parse sitemaps", "extract JSON-LD", "check AI crawler permissions",
  or needs a structured site inventory for AI search readiness and downstream audit agents.
  Crawls public websites within strict monotonic budgets, parses RFC 9309 robots.txt permissions
  across 16 AI retrieval & training bots, extracts Trafilatura-grade clean Markdown with SNR scoring,
  scores commercial routes, and emits structured site inventories.
license: MIT
compatibility: ">=Python-3.9"
metadata:
  role: specialist
  parent: audit-orchestrator
  version: "1.0.0"
  author: "Jayanth Reddy Konda"
allowed-tools:
  - bash
  - python3
---

# Web Scraper Skill (Autonomous AI Retrieval Acquisition)

## When to Use
Invoke this skill whenever an AI agent or workflow needs to:
- Crawl a target website to extract page representations, HTML, clean Markdown, and metadata.
- Audit AI retrieval permissions across 16 crawler bots (`OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot`, `Google-Extended`, etc.) under RFC 9309 rules.
- Traverse XML sitemaps and nested sitemap indexes with recursive fallbacks.
- Extract Trafilatura-grade clean readable text without navigation boilerplate, headers, or footers.
- Flatten Schema.org `@graph` JSON-LD structures and validate Answerability attributes.
- Acquire a unified, authoritative `inv.json` site inventory for downstream audit skills without repeating network calls.

---

## Inputs
- `--site <url>` (string, required): Target URL or domain (e.g., `https://example.com`).
- `--output <path>` (string, optional): Destination path for the generated inventory JSON (e.g., `inv.json`).
- `--max-pages <int>` (integer, optional, default: `15`): Maximum pages to acquire within the target origin.
- `--timeout <float>` (float, optional, default: `30.0`): Monotonic deadline budget in seconds.
- `--max-depth <int>` (integer, optional, default: `3`): Maximum link traversal hops from homepage.
- `--format <json|markdown|both>` (enum, optional, default: `json`): Output format.

---

## Procedure (Deterministic Steps)

1. **Host Normalization & SSRF Pre-Flight:**
   - Normalize target URL to canonical scheme and domain (`https://example.com/`).
   - Resolve DNS hostnames and validate against zero-trust SSRF constraints (blocking RFC 1918 private IPs, loopbacks `127.0.0.0/8`, link-local `169.254.0.0/16`, cloud metadata `169.254.169.254`, IPv6 equivalents).

2. **Robots.txt RFC 9309 Audit:**
   - Fetch `robots.txt` using streaming chunked reads (bounded to 512 KiB).
   - Evaluate longest-match precedence rules across all 16 AI crawler bots.
   - Enforce fail-closed semantics for HTTP 5xx errors and fail-open semantics for HTTP 404.

3. **XML Sitemap Traversal:**
   - Probe `robots.txt` declared sitemaps and standard locations (`/sitemap.xml`, `/sitemap_index.xml`).
   - Recursively parse child sitemaps (bounded to depth 3 and 1,000 URLs).

4. **Commercial Priority Frontier Routing:**
   - Initialize frontier with the root homepage.
   - Score and prioritize high-value commercial routes (`/`, `/pricing`, `/products`, `/about`, `/contact`, `/docs`, `/faq`).
   - Strip URL tracking fragments and parameters (`utm_*`, `fbclid`, `gclid`).
   - Filter out junk operational paths (`/cart`, `/checkout`, `/login`, `/admin`).

5. **Streaming Single-Pass Extraction:**
   - Fetch each page within monotonic deadline and byte ceilings.
   - Extract title, meta description, canonical URL, OpenGraph, and Twitter tags.
   - Extract and flatten all Schema.org JSON-LD scripts, resolving `@graph` hierarchies.
   - Compute Signal-to-Noise Ratio (SNR) and extract Trafilatura-grade clean Markdown.
   - Flag sparse SPA shells if initial HTML contains `< 25` words inside mounting `div` containers.

6. **Inventory Serialization:**
   - Compile comprehensive inventory containing `site`, `crawled_at`, `pages`, `robots`, `sitemaps`, `infrastructure`, and `stats`.
   - Write output to `--output` file or emit to standard output.

---

## Output Contract (Site Inventory Schema)

The skill emits a structured JSON document conforming to the following shape:

```json
{
  "site": "https://example.com",
  "crawled_at": "2026-09-06T12:00:00Z",
  "robots": {
    "status": 200,
    "raw": "User-agent: *\nAllow: /",
    "sitemaps": ["https://example.com/sitemap.xml"],
    "matrix": {
      "OAI-SearchBot": true,
      "PerplexityBot": true,
      "Claude-SearchBot": true,
      "GPTBot": true
    }
  },
  "sitemaps": ["https://example.com/sitemap.xml"],
  "pages": [
    {
      "url": "https://example.com/",
      "status": 200,
      "page_type": "homepage",
      "resource_type": "html",
      "canonical": "https://example.com/",
      "title": "Example Brand",
      "word_count": 850,
      "snr_ratio": 0.42,
      "is_sparse_spa": false,
      "jsonld": [
        {
          "@type": "Organization",
          "name": "Example Brand",
          "url": "https://example.com"
        }
      ],
      "text": "Extracted Trafilatura-grade clean text...",
      "headings": {
        "h1": ["Empowering Innovation"],
        "h2": ["Features", "Pricing"]
      },
      "ctas": [
        {"text": "Get Started", "href": "/signup"}
      ]
    }
  ],
  "infrastructure": {
    "llms_txt": {"present": false, "status": 404},
    "llms_full_txt": {"present": false, "status": 404}
  },
  "stats": {
    "pages_crawled": 1,
    "total_bytes": 45120,
    "elapsed_seconds": 1.25
  }
}
```

---

## CLI Execution Examples

```bash
# 1. Standard Crawl: Acquire up to 15 pages into inv.json
python3 skills/web-scraper/scripts/run_scraper.py \
  --site https://example.com \
  --output inv.json \
  --format json

# 2. Fast Snapshot: 5 pages with 10-second timeout
python3 skills/web-scraper/scripts/run_scraper.py \
  --site https://example.com \
  --max-pages 5 \
  --timeout 10.0 \
  --output inv.json

# 3. Terminal Markdown Summary:
python3 skills/web-scraper/scripts/run_scraper.py \
  --site https://example.com \
  --max-pages 3 \
  --format markdown
```
