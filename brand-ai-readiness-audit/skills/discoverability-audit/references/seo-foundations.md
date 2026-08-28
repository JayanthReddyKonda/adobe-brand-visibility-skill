# Technical SEO Foundations for AI Retrieval

This reference synthesizes essential technical SEO mechanisms and their causal impact on AI discovery, indexing, and retrieval.

---

## 1. robots.txt & Access Directives (RFC 9309)

robots.txt governs **crawling access**, not indexing.

### User-Agent Matching Precedence
- Per RFC 9309, specific user-agent tokens (e.g. `User-agent: OAI-SearchBot`) **override** the generic wildcard group (`User-agent: *`).
- Longest path match wins within a group; `Allow` wins equal-length ties.

### Path Syntax Rules
```txt
# Blocks /admin, /admin/, /admin123
Disallow: /admin

# Blocks ONLY paths under /admin/
Disallow: /admin/

# Wildcards
Disallow: /*.pdf$    # Blocks all PDF files
Disallow: /*/temp/   # Blocks temp directory at any depth
```

### Critical AI Distinctions
- **Retrieval Bots:** `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`. Blocking these prevents live citations in generative answers.
- **Training Bots:** `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`. Blocking these prevents model training but does not affect search visibility.

---

## 2. Canonicalization & Consolidation

The canonical link element (`<link rel="canonical" href="...">`) signals the authoritative primary URL for duplicate or parameterized content.

### Canonical Rules
- **Self-Referential Canonical:** Every unique indexable page should declare a self-referential canonical URL.
- **Protocol & Host Uniformity:** Consistently specify HTTPS and the chosen apex/www domain format.
- **Header Alternative:** Use `Link: <https://example.com/file.pdf>; rel="canonical"` for non-HTML assets.

### AI Search Impact
AI assistants consolidate citations onto the declared canonical target. Mismatches between sitemaps and markup create citation ambiguity.

---

## 3. XML Sitemaps & Discovery Aids

XML sitemaps provide an explicit inventory of indexable URLs.

### Sitemaps Standards
- Maximum 50,000 URLs and 50 MB per sitemap file.
- Use `<sitemapindex>` for larger multi-category sites.
- Specify accurate `<lastmod>` ISO 8601 timestamps (only update when material content changes).

### `llms.txt` Role
- `llms.txt` is an optional Markdown feed for community LLM tools.
- **Google does NOT use `llms.txt`** for AI Overviews or AI Mode (standard web indexing is used).
- Its absence is NEVER an SEO or AI discoverability defect.

---

## 4. Rendering & Content Extractability

### Server-Side Rendering (SSR) vs Client-Side Rendering (CSR)
- **SSR / SSG:** Initial HTML contains full semantic markup and text. Safest for all AI crawlers.
- **CSR (Client-Side SPA):** Initial HTML contains minimal text (`<div id="root"></div>`) requiring JavaScript execution.
- **AI Crawler Capability:** While Googlebot renders JavaScript, several AI search fetchers evaluate the raw HTTP stream only. Primary text should always be present in the initial HTML payload.

---

## 5. Snippet Controls for Generative AI

Fine-grained controls to govern how search engines and AI assistants quote content:

```html
<!-- Prevent snippet creation and AI quote extraction -->
<meta name="robots" content="nosnippet">

<!-- Limit snippet length -->
<meta name="robots" content="max-snippet:160">

<!-- Exclude specific sections from snippets/AI answers -->
<div data-nosnippet>Proprietary pricing notes not for snippet extraction.</div>
```
*(Note: `data-nosnippet` is only supported on `span`, `div`, and `section` tags).*
