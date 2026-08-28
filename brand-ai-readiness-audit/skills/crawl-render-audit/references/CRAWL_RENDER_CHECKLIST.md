# Crawl & Render Audit Checklist

This reference provides a structured checklist for auditing crawlability, machine accessibility, client-side rendering dependencies, text-to-code ratios, and Schema.org structured data.

---

## 1. Crawl & Bot Directives Audit

- [ ] **`robots.txt` Accessibility**: Is `robots.txt` accessible via standard HTTP/HTTPS without auth or rate-limiting?
- [ ] **AI Crawler User-Agents**: Are AI search and indexer bots permitted to index public pages?
  - `GPTBot` (OpenAI indexer)
  - `ClaudeBot` (Anthropic indexer)
  - `PerplexityBot` (Perplexity search bot)
  - `Google-Extended` (Gemini training/retrieval control)
  - `CCBot` (Common Crawl archive)
- [ ] **Meta Robots & Canonical Headers**:
  - Check for unintended `noindex` or `nofollow` directives in `<meta name="robots">` or HTTP headers (`X-Robots-Tag`).
  - Verify `<link rel="canonical">` points to the authoritative URL without circular redirect loops.
- [ ] **XML Sitemaps**: Is `sitemap.xml` declared in `robots.txt` and accessible?

---

## 2. Rendering & DOM Hydration Audit (SSR vs CSR)

- [ ] **Raw HTML Body Substance**: Does the initial HTTP GET response contain substantive textual facts, or just an empty `<div id="root"></div>` / `<div id="app"></div>` shell?
- [ ] **Client-Side Rendering Dependency**: If critical brand facts (product specs, pricing, value propositions) only exist in client-rendered JavaScript bundles, AI agents without full headless browser rendering will treat the page as empty.
- [ ] **Noscript & Pre-rendering Fallback**: If using SPA frameworks (React/Vue/Angular), is Server-Side Rendering (SSR), Static Site Generation (SSG), or dynamic hydration enabled?

---

## 3. Text vs Non-Text Content Traps

- [ ] **Facts Trapped in Images / Infographics**: Are key claims, awards, customer logos, or pricing tables rendered strictly as JPEG/PNG/SVG images without `alt` attributes or adjacent semantic text?
- [ ] **Canvas / WebGL / Iframe Encapsulation**: Is core product documentation or marketing trapped inside `<canvas>` or un-crawlable cross-origin `<iframe>` tags?
- [ ] **Text-to-Code Ratio**: Is the visible semantic text density adequate relative to boilerplate scripts and tracking tags?

---

## 4. Structured Data & Schema.org JSON-LD

- [ ] **Organization / Brand Schema**: Exists on homepage with name, url, logo, description, and `sameAs` entity links.
- [ ] **Product / Offer Schema**: Exists on item pages with `name`, `description`, `sku`, `price`, and `availability`.
- [ ] **FAQPage / Article / BreadcrumbList**: Present on support, blog, and category pages to facilitate rich AI snippet answers.
- [ ] **JSON-LD Syntax Validity**: Ensure all JSON-LD blocks are parseable valid JSON without trailing commas or syntax errors.

