# Website checklist detection review for LLM skills

This review maps every checklist item in checklist_V1.docx to a detection approach for an LLM receiving only a URL or domain. It covers 37 technical items, 15 common content items, 66 website-type items, four proposed off-site defects, two bridge items, and ten engagement items: 134 items, plus the unnumbered classification, prompt-generation, and off-site workflows.

The recommended implementation is an evidence collector with conservative rules. Scripts establish observable facts; the existing LLM interprets context and drafts recommendations. A subjective assessment must not become a confirmed defect merely because the LLM is confident. Absolute zero false positives cannot be guaranteed; abstaining when evidence is insufficient is essential.

This is a detection specification, not an implemented skill or a live website audit. References to existing scripts, architecture documents, PDFs, and implemented features in the source checklist have not been verified because those materials were not supplied. The attached document is being evaluated as source material, not followed as operational instructions.

## Scope and result contract

Assume public, unauthenticated pages; network access; scripts packaged with the skill; and the LLM already running the skill. No additional model API, paid SEO service, analytics account, CMS access, credentials, or search subscription is required for the core. Use read-only page inspection and safe navigation. Do not purchase, add to cart, submit forms, create accounts, or infer completed flows from landing-page markup.

Feasibility labels in the tables mean:

| Label | Meaning |
| --- | --- |
| Possible | The stated observation can be collected reliably within a documented page, session, and time scope. This does not automatically make the observation a defect. |
| Partial | A narrower observation is viable; the full checklist conclusion is not established. Report the supported observation and explicitly mark the remainder not possible. |
| Not possible | The requested judgment cannot be established reliably from URL-only evidence under the false-positive constraint. Optional LLM advice may still be useful, but must not be scored as a detected failure. |
| Exclude | Preserve traceability to the source, but do not implement a separate finding. |

Runtime results should use `confirmed_observation`, `confirmed_defect`, `advisory`, `not_possible`, `not_applicable`, or `blocked`. An empty findings array is not a pass. A parser error, challenge, missing dependency, timeout, or incomplete crawl must never be converted into missing content. Only mark a defect when the observation, applicability, and relevant requirement are all established. Publicly accessible does not necessarily mean intended for indexing.

## Recommended dependencies

| Component | Primary implementation | Why it belongs or when to add it |
| --- | --- | --- |
| Runtime and HTTP | Python standard library: `urllib`, `http.client`, `ssl`, `json`, `gzip`, `hashlib`, `sqlite3`, `html.parser`, `xml.etree.ElementTree` | Covers transport, persisted evidence, JSON, bounded XML, and basic source extraction. Node plus its built-ins is an equivalent option if that is the existing runtime. Do not require both runtimes for the core. |
| Browser | Bundle Playwright and a pinned compatible Chromium build once with the skill environment | This is a real dependency, including browser binaries and platform libraries. It earns its cost: DOM, JavaScript, computed layout, screenshots, frames, and mobile emulation. If a suitable browser tool already exists, reuse it. Without it, rendering and engagement checks become not possible. [Playwright library documentation](https://playwright.dev/docs/library). |
| Robots rules | Bundle a tested RFC 9309 matcher and bot-policy registry | A local implementation is viable, but requires conformance fixtures. A mature compliant parser is preferable to ad hoc regex. Do not assume the standard-library parser matches every provider's extensions and precedence. No remote robots service is needed. |
| HTML parsing | Browser `DOMParser` over captured response source; rendered DOM evaluated separately | Avoid regex-based HTML parsing. Keep the source and rendered representations separate. A standards-compliant HTML parser package is an optional improvement if the browser is unavailable. |
| Structured data | Built-in JSON parsing plus a packaged, versioned vocabulary and explicitly scoped rule tables | No remote context fetch during audits. A JSON-LD processor is worth adding for expansion, aliases, graph references, and nonstandard contexts. A standards-aware Microdata/RDFa extractor is needed before claiming absence of all structured data. |
| PDFs | Optional `pypdf`, or another maintained PDF parser | Worth adding for F4/F5. General PDF text extraction is not a realistic standard-library-only task. Extraction failure does not establish a scanned PDF. [pypdf extraction limitations](https://pypdf.readthedocs.io/en/stable/user/extract-text.html). |
| Images and scanned PDFs | Existing vision-capable LLM, if available; optional local OCR and PDF renderer | OCR/vision can propose text candidates. Neither guarantees transcription accuracy or the absence of an equivalent elsewhere. Without these, image semantics are not possible. |
| Audio and video | Inspect DOM and fetch exposed caption/transcript resources | ASR, media decoders, and player-specific APIs are optional and materially heavier. Generating a transcript does not prove the website already supplied one. |
| Off-site discovery | Declared profile URLs first; optionally reuse an existing search tool | Independent discovery across the entire platform list needs search or platform access. Do not build a supposedly dependable search engine by scraping search result HTML. Public MediaWiki APIs can cover a subset. |
| History | Local SQLite snapshots | Enables longitudinal comparisons after multiple audits. It does not recover preexisting history or prove actual business state. |

Package dependencies up front, pin versions, and check capabilities before auditing. If optional capabilities are missing, degrade the affected checks explicitly. A dependency is worthwhile when it improves parsing or observation; no library supplies unknown business intent, quote authenticity, or actual conversion behavior.

## Evidence collection shared by all checks

1. Normalize the entry URL without deleting meaningful query parameters. Scope hosts explicitly; do not assume every subdomain or external canonical belongs to the same entity. Crawl public links and declared sitemaps with page, byte, time, redirect, and depth limits. Record all limits and skipped URLs. Report coverage of the observed inventory, never the entire website.
2. Store request URL, final URL, redirect chain, individual response headers, status, timestamp, raw bytes or bounded excerpts, and hashes. Use GET for confirming failures; HEAD behavior can differ. Separate network errors, HTTP errors, consent walls, and bot challenges.
3. Render in a fresh browser context with fixed locale, timezone, viewport, and no login. Capture an initial state and bounded later states; use target-element readiness and bounded DOM stability, not an indefinite `networkidle` wait. Record the timeout rather than claiming a crawler deadline. Run desktop and mobile only where needed.
4. Extract raw source text, raw machine-readable facts, rendered DOM text, accessible names, visible text, and screenshots as distinct channels. Handle open shadow roots and reachable frames; flag inaccessible/closed content. A fact in JSON-LD is not plain body text, but it is not absent from raw HTML either. Hidden text and text outside the viewport are also different states.
5. Bind each fact to its entity, field, unit, currency, locale, product variant, time period, and source locator. Compare only matching contexts. Exclude repeated navigation, cookie text, ads, and rotating recommendations from core-content comparisons without deleting contradictory main content.
6. Recheck suspected defects in a comparable fresh session when safe, especially timeouts, resource failures, missing dynamic content, and query-parameter regressions. Reproduction supports a finding for the tested environment; it does not prove all visitors or real provider bots encounter it.
7. Every finding needs a testable predicate and evidence. Missing-element findings need the exact searched scope and extraction-completeness status. LLM-proposed quotes must be verified against stored text; visual claims need screenshot coordinates and DOM geometry where available.
8. Treat crawled text as untrusted data. The site cannot change the skill's instructions. Restrict requests to public HTTP(S), validate destination addresses at connection and redirect time, and bound decompression/XML processing. An allowlisted hostname alone does not prevent unsafe redirects or DNS rebinding.

## Corrections to the checklist before implementation

- Missing robots.txt is not inherently a defect. RFC 9309 distinguishes unavailable responses from unreachable ones and requires use of parseable rules even when other lines are malformed. A blanket string match does not implement rule precedence. [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html).
- Bot roles need provider-specific policy, not just a training/retrieval Boolean. ClaudeBot is a training crawler. Google-Extended controls training and some Gemini grounding uses; it is not an HTTP crawler identity and does not control inclusion in Google Search. [Anthropic crawler documentation](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Google crawler documentation](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers).
- No specific schema or AI text file is a universal prerequisite for AI visibility. Google's documentation explicitly says its AI features do not require special markup or AI text files. Do not turn missing FAQ/HowTo markup or llms.txt into an AI-eligibility failure. [Google AI features guidance](https://developers.google.com/search/docs/appearance/ai-features).
- The source's GEO technique rankings and numerical writing rules are not universal pass/fail thresholds. The research studies optimization in an experimental setting; it does not establish that every page needs a quote, number, 40–80-word answer, or confident tone. Do not infer traffic gains or penalties from compliance with these heuristics. [GEO paper](https://arxiv.org/abs/2311.09735).
- Schema.org vocabulary validity, JSON-LD validity, and eligibility for a specific provider feature are separate tests. Multiple same-type entities can be legitimate. Microdata and RDFa are alternatives to JSON-LD. [Schema.org data model](https://schema.org/docs/datamodel.html), [Google structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
- An empty `alt` is correct for decorative images. Alt length and filename patterns are insufficient to determine accessibility or factual extractability. [W3C decorative image guidance](https://www.w3.org/WAI/tutorials/images/decorative/).
- Canonicals are not required to be self-referencing, and ordinary query-string URLs can identify distinct pages. JavaScript-rendered content is not universally invisible to search engines. Report demonstrated behavior for a defined consumer. [Google JavaScript guidance](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics).

## Technical items A through H

### A Crawl access

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| A1 robots.txt exists, HTTP 200, valid | Possible | Fetch the correct scheme/host/port `/robots.txt`; retain redirects, headers, bytes, encoding, parseable directives, and line errors. Detect actual response/parse observations. A 404 is not an automatic crawl block; an empty valid file is acceptable. HTTP 200 returning an HTML error template is not a valid robots file. |
| A2 No blanket wildcard disallow | Possible | Evaluate effective rules for each sampled URL and relevant bot, including matching groups, most-specific paths, Allow ties, wildcard/end matching, and URL encoding. Report an effective disallow with rule lines. `Disallow: /` alone is insufficient if exceptions or more-specific bot groups apply. Do not assert accidental blocking. |
| A3 Per-bot permission matrix | Partial | Compute policy by bot and URL locally; record role, source, registry version, effective rule, and declared permission. Real provider access and citation eligibility are not possible to prove with a spoofed UA. Keep training, search, user-triggered fetch, and product-use controls separate; legitimate governance choices are observations, not automatic defects. |
| A4 Crawl-delay starvation | Partial | Parse value and applicable group; apply only to providers documented to honor it. Report the delay. Starvation and indexing loss are not possible from a URL: page totals, concurrency, crawl schedules, and provider budgets are unknown. Optional verified server logs improve observation; never score a universal “excessive delay” threshold. |
| A5 Sitemap directive in robots | Possible | Parse all `Sitemap` directives and validate their absolute URLs and fetch results. Missing declaration is an observation only: sitemaps can be submitted elsewhere or discovered at other paths. Preserve malformed URL evidence rather than claiming the site has no sitemap. |

The packaged bot registry should cover the source's GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, Google-Extended, Googlebot, Bingbot, and optionally CCBot. Each entry needs provider policy links and a review date. User-triggered fetchers must use their documented robots behavior; do not apply a blanket crawler rule to them. [OpenAI crawler documentation](https://developers.openai.com/api/docs/bots), [Perplexity crawler documentation](https://docs.perplexity.ai/docs/resources/perplexity-crawlers).

### B Indexation signals

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| B1 Meta noindex | Possible | Parse applicable `robots` and provider-specific meta directives in source and rendered head; recognize `none` as applicable. Capture tag, selector, bot scope, and stage. Report “noindex directive present.” Whether exclusion is wrong is not possible without established indexation intent; a login or account page may correctly use noindex. |
| B2 X-Robots-Tag noindex | Possible | Inspect every header occurrence, preserving bot-specific scope and combinations. Associate headers with the exact response, including PDF responses; do not transfer an intermediate redirect's header to its destination. Report effective directive for supported provider semantics, with the same intent caveat as B1. |
| B3 Canonical correctness | Partial | Extract HTML and HTTP-Link canonicals, resolve relative URLs, record multiple distinct targets, and fetch allowed targets. Reproducible dead targets, loops, or competing declarations are objective issues. Self-reference absence, cross-domain targets, and content differences alone cannot establish the owner's intended canonical. Compare entity/variant context; intent remains not possible. |
| B4 HTTP status and redirects | Possible | GET observed links and sitemap URLs, record redirect hops, loops, final status, and source-link location. Recheck transient failures. Report the actual broken reference or redirect; an intentional 301 is not broken and a 403/429 may reflect this checker. Do not infer crawl-budget loss from hop count alone. |
| B5 Login, CAPTCHA, bot walls | Partial | Capture unauthenticated response, redirect target, rendered challenge/form, and absence of expected target content. Require multiple signals: a challenge vendor script alone can be harmless. Report “content blocked in this session.” Whether it should be public or real bots encounter the same wall is not possible from the URL. |

### C Rendering and JavaScript

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| C1 Raw versus rendered word count | Possible | Compare main-content text in parsed source against rendered visible text with the same segmentation and language-aware tokenization. Count boilerplate separately. Report actual text and content differences. A `<25 words` threshold, `#root` presence, or low count is not a failure; short utility pages can be complete. |
| C2 Target facts require JavaScript | Possible | Identify a specific rendered fact with an exact locator and context, then search source body text, metadata, JSON-LD, and embedded state separately using normalized units/values. Report the exact channel gap, e.g. “visible price absent from source body, present in JSON-LD.” Entity extraction ambiguity or differing variants means abstain. |
| C3 Hash/client-side routes | Partial | Inventory observed hash links. Open each in a clean context; compare fresh load and reload against the parent page and record whether the target entity loads. Distinguish ordinary section anchors. Prove observed JS dependence or broken deep linking; proving no server-rendered equivalent exists anywhere is not possible with bounded discovery. |
| C4 SSR or prerendered fallback | Partial | Compare captured source content with rendered target facts and optionally a JS-disabled load. Report server-delivered content sufficiency. Identifying the exact build technique or whether a fallback exists for all bots is not possible externally; framework fingerprints and script filenames are not proof of SSR. |
| C5 Delayed assembly beyond crawler timeout | Partial | Timestamp navigation, relevant resource completion, and first stable target-content visibility using browser timing and DOM observations. Repeat measurements. Report observed content delay or timeout. Actual crawler abandonment, its deadline, and causal blame on a resource are not possible without provider evidence; waterfall correlation alone does not prove causation. |

### D Sitemaps

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| D1 Reachable valid sitemap | Possible | Fetch declared locations plus a bounded conventional-path probe. Detect gzip, parse safely with namespace/root checks, inspect URLs, and record MIME. A missing `/sitemap.xml` does not establish missing sitemaps. A MIME mismatch is a compatibility observation if XML parses; a 200 HTML fallback is not XML. |
| D2 Sitemap versus link graph coverage | Partial | Compare normalized observed sitemap URLs with observed internal links, preserving substantive parameters and alternate locales. Report “N observed eligible URLs absent from inspected sitemaps.” Exhaustive coverage and orphan discovery are not possible from URL-only crawling. Sitemap omission is not a defect by itself, especially for duplicates or deliberately excluded pages. |
| D3 lastmod reflects actual edits | Not possible | A first audit has no edit history. Validate date syntax and record suspicious future dates as observations. Optional local snapshots can establish content changed between two observations while lastmod stayed unchanged; dynamic content, meaningful-edit policy, and exact edit dates still need context. HTTP Last-Modified is not authoritative editorial history. |
| D4 Key commercial pages excluded | Partial | Identify observed product/pricing/docs pages using visible evidence and compare with inspected sitemaps and access directives. Report their actual membership and restrictions. Which pages are “key,” accidental exclusion, and undiscovered omissions are not possible without an inventory or explicit intent. Do not require every commercial page in a sitemap. |
| D5 Large sitemap/index support | Possible | Count each file's entries and uncompressed bytes; validate index references and inspect child files within bounds. Flag demonstrated protocol-limit violations, not merely the absence of an index. Multiple valid sitemaps may be declared separately. Hitting the checker's own limit means incomplete inspection, not truncation by the search engine. |

Apply the sitemap protocol's limit of 50,000 URLs and 50 MB uncompressed per sitemap; index files have their own corresponding limits. Do not infer server-side truncation merely because a file reaches a limit. [Sitemap protocol](https://www.sitemaps.org/protocol.html).

### E Structured data

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| E1 JSON-LD presence | Possible | Inventory source and rendered `application/ld+json` scripts and parse each separately. Report presence or absence specifically of JSON-LD. Microdata/RDFa may supply structured data instead. Neither JSON-LD absence nor schema absence alone proves the content is unextractable. |
| E2 Organization/Brand fields | Partial | Resolve graph nodes and references for the actual site entity; inventory name, logo, URL, and sameAs by page. Use the applicable type's properties, not one universal mandatory list. Not every page needs a full Organization block; brands, publishers, and legal entities differ. Absence is an optional enrichment opportunity. |
| E3 Product/Offer fields | Partial | For positively identified offers, inspect price, currency, availability, nested offers, AggregateOffer, variants, and price specifications. Apply a versioned provider feature rule only when that feature is the declared target. Quote-only products and unavailable fields must not be forced into invented prices. Record missing fields, not lost AI citation eligibility. |
| E4 FAQ/HowTo/Article applicability | Partial | Use visible page content plus schema graph to report types represented and content-to-markup correspondence. A classifier's expected type is advisory. Missing FAQ or HowTo schema is not a confirmed defect and does not establish AI Overview ineligibility. Provider feature support must be maintained separately from schema.org vocabulary. |
| E5 JSON-LD validity | Partial | Deterministically report JSON syntax errors with block/offset. For a documented supported subset, validate node shapes and known vocabulary; use a real JSON-LD processor for advanced constructs. Full semantic validity and Google Rich Results equivalence are not possible with a generic JSON Schema. Unknown extensions/contexts trigger unsupported, not invalid. |
| E6 Duplicate/contradictory blocks | Partial | Resolve nodes by stable `@id` and explicit entity/offer identifiers. Compare scalar claims only for the same variant, currency, location, and time. Identical duplication is informational; repeated `@type` is normal. Conflicting prices become a finding only when contexts demonstrably match and ranges/list prices are excluded. Otherwise abstain. |
| E7 Markup overclaims visible content | Partial | Compare explicit same-entity facts, such as a single offer's visible price and marked-up price, after checking tabs/accordions/variants. Report supported discrepancies with both locators. Missing literal text alone is insufficient; alternate wording and legitimate nonliteral properties exist. Deliberate spam, fabrication, and provider penalties are not possible to infer. |

### F Content representation

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| F1 Facts locked in images/canvas | Partial | Inventory images, CSS images, canvas, SVG text, accessible names, adjacent captions, and DOM equivalents. Without vision/OCR, factual content inside pixels is not possible to determine. With it, record candidate image facts and search equivalents in the inspected page. “No equivalent found on this page” is scoped evidence, not a site-wide absence proof. |
| F2 Alt-text quality | Not possible | Scripts can record alt presence, empty values, accessible names, roles, filenames, and surrounding text. Whether an image is informational and its alternative is adequate requires semantic judgment. Optional vision/LLM advice should cite the image and context. Do not fail decorative images, short accurate alts, or impose length/generic-word thresholds. |
| F3 Audio/video transcript or captions | Partial | Inspect track elements and `textTracks`, fetch declared caption files, verify nonempty timed cues, and inspect visible transcript links and accessible embedded-player state. Presence of a track tag alone is insufficient. Caption completeness, transcription accuracy, and absence in opaque players are not possible without media analysis/player access. |
| F4 Real text in tables/PDFs | Partial | HTML: enumerate actual table/grid text and headers; do not assume missing `<table>` means pixels. PDF: optional parser extracts page text and character mappings. Report extractable text per page. Empty/garbled extraction can mean scans, encryption, or encoding issues; it does not prove a scanned document. OCR/rendering provides additional evidence. |
| F5 PDF-only facts | Partial | With a PDF parser, extract identifiable facts and compare against associated HTML pages and observed crawl text, including unit normalization. Report “no HTML equivalent found in inspected pages.” Proving absence across the website, or that a PDF format causes lower AI visibility, is not possible from this audit. |

### G Optional llms.txt

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| G1 llms.txt present | Possible | Fetch `/llms.txt`, distinguish an actual text document from an HTML catch-all, and record content/status. Absence is not a defect. Presence is an inventory observation, not a demonstrated visibility bonus. |
| G2 llms.txt accurate and synchronized | Partial | Parse explicitly supported Markdown links, resolve them, and compare linked page identities and availability. Reproducibly dead links can be reported. Sitemap membership is not required because the file may be curated. Description truth, exhaustive currency, and global completeness are not possible without additional evidence. |

### H Performance and accessibility observations

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| H1 Response latency | Possible | Measure request timing and browser Navigation Timing, documenting whether DNS/TLS/redirects/cache are included. Run a small repeated sample and report values and spread for the test environment. “Too slow for AI” and crawl-budget harm are not possible without an agreed budget or provider data. Do not call a timeout full-load time. |
| H2 Headings and landmarks | Partial | Enumerate native and ARIA headings, levels, main/navigation landmarks, accessible names, and hidden state. Report structural facts. Skipped levels or missing HTML5 tags alone do not establish broken extraction or accessibility. Optional axe-core helps with specific supported accessibility rules; it is not an AI-discoverability score. |
| H3 Mobile/desktop parity | Partial | Render the same URL in controlled fresh desktop/mobile contexts; compare normalized main facts and accessible content after equivalent safe expansions. Exclude layout-only hiding and responsive menus. Report reproduced fact differences in tested states. Their intent and behavior on real crawler infrastructure remain not possible to establish. |

## Nontechnical workflow and shared content checks

The source's unnumbered instructions to classify the website and generate likely search prompts are feasible as an LLM workflow, with limits. They are not deterministic defect detectors. Use extracted evidence to assign multiple website types when appropriate; a SaaS company can also have a blog, store, and community. Attach a type and evidence to each page rather than applying every vertical checklist to the whole domain.

Generate a bounded set of hypothetical user intents from observed offerings, audiences, and tasks: identity, suitability, features, price, comparison, usage, and support. Preserve the proposed prompt, why it applies, source pages, expected answer fields, and any assumptions. Do not invent offerings, competitors, user demand, or prompts with unanswerable business facts. The actual probability that a prompt triggers search, produces a citation, or sends traffic is not possible to determine without live platform testing; no such testing is part of this review.

For each hypothetical prompt, ask the existing LLM to retrieve an answer exclusively from collected page evidence, with exact quotes and URLs. Scripts verify that quoted spans exist. Record answerable, partly answerable, or not found in inspected pages. A failed retrieval attempt is not proof that an answer is absent: broaden deterministic searches over relevant pages and abstain if extraction is incomplete. A content opportunity can be reported without asserting that the site is poorly optimized for all prompts. Do not invent a numerical GEO score.

The shared content primitives are: claim plus source attribution, quotation plus named speaker, number plus unit/time scope, question plus answer, entity plus explicit identity fields, date plus label, and author plus visible credentials. Each primitive retains exact text and a locator. Scripts verify the literal evidence; appropriateness, authenticity, and real-world truth remain separate.

IDs N1–N15 below correspond to the source's 15 common improvements in their original order. Website-type IDs below follow each original list's order as well.

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| N1 Self-contained answers | Not possible | Full semantic independence is not a dependable Boolean test. Extract heading-plus-answer units; the existing LLM may identify a specific unresolved referent and quote the missing context. “As above” alone is not a failure when the answer includes its antecedent. Advice only; no confirmed defect or isolation score. |
| N2 Answer first | Partial | Given an explicitly matched question and supporting answer span, record the answer's sentence/word offset within its section. Whether it should appear in the first two sentences is a contextual editorial judgment and not possible as an objective failure. Avoid applying answer-first rules to narrative introductions or pages without a question. |
| N3 Replace vague claims with numbers | Partial | Extract vague comparative language and nearby quantities with units, denominators, and dates. Report exact examples for review. Whether reliable numbers exist, are needed, or would improve retrieval is not possible from the page. Never recommend fabricated metrics or score every qualitative statement as defective. |
| N4 Attribute factual claims | Partial | Bind a concrete claim to nearby named sources, footnotes, links, or explicit first-party attribution. Report “no attribution found for this claim in this section,” with exclusions for own-product facts and common definitions. Source credibility, entailment, and truth are not possible to certify generally; optional source retrieval supports narrower verification. |
| N5 Credible quotation per relevant page | Not possible | Quote text, named speaker, role, and source link can be inventoried. Relevance, credibility, and authenticity are not reliably determined from presence or an LLM judgment. Do not fail pages without quotations. Optional linked-source comparison can confirm textual correspondence, not that the speaker actually said it. |
| N6 Fluency | Not possible | Sentence lengths or readability metrics are observations, not reliable fluency detectors across languages and genres. An existing LLM can suggest edits to exact awkward passages as editorial advice. No dependency supplies a false-positive-free fluency verdict. |
| N7 Confident expert register | Not possible | LLM advice may identify unsupported certainty or excessive hedging in a specific passage. Hedging can be correct scientific, technical, or risk communication. Never count “may” or “could” as defects or turn assertiveness into an authority score. |
| N8 Simplify and define jargon | Partial | Record explicit definitions and first occurrences of candidate terms within the reading unit. An LLM can propose unexplained-term examples. Whether a term needs explanation for this audience is not possible without audience context; acronym regex and dictionary absence are not sufficient failure evidence. |
| N9 Correct technical terminology | Not possible | Correctness can depend on discipline, version, jurisdiction, and surrounding assumptions. Extract terms for optional expert/LLM review, but do not reward density or flag generic wording automatically. Authoritative version-matched references or subject expertise can support individual corrections, not a universal detector. |
| N10 No keyword stuffing | Not possible | Count repeated phrases only as evidence for editorial review, excluding navigation, catalogs, code, and repeated product names. There is no defensible universal repetition threshold establishing stuffing or a search penalty. LLM advice must cite an actual unnatural passage and remain unscored. |
| N11 Applicable schema | Partial | Reuse E1–E7, including Microdata/RDFa scope and context-specific provider rules. Record existing types and supported syntax issues. Missing optional markup is an enrichment suggestion, not a second content defect. Do not manufacture a required schema list from an uncertain page classifier. |
| N12 Entity consistency | Partial | Compare explicit same-entity facts across inspected first-party pages; follow resolvable declared profiles optionally. Normalize legal/trading names, aliases, branch locations, languages, and dates. Exact wording need not match. Report demonstrated factual contradictions, not description-string differences; external completeness and which source is correct remain not possible. |
| N13 FAQs with 40–80-word answers and schema | Partial | Identify actual Q&A units, record answer text/length and matching markup, including expanded accessible accordions. Do not require the word band or FAQPage on every page. Relevance to real users and improved AI visibility are not possible to establish from the URL. |
| N14 Freshness signals | Partial | Extract labeled publication/update dates and citation dates, plus explicit expired claims or contradictions. Copyright years are not edit dates. Missing update dates and old accurate evergreen text are not defects. Actual last revision and real-world currency are not possible without history or authoritative current sources. |
| N15 Author credentials | Partial | Identify visible byline, author page, stated credentials, and consistent Article author references. Report what is disclosed. Missing personal bylines can be appropriate for corporate material. Authentic credentials, expertise, and whether a byline is required cannot be established automatically; optional registries help with individual credentials. |

## Website type 1 E commerce and retail

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| EC1 Numeric product facts | Partial | Extract labeled dimensions, composition, specifications, ratings denominators, and delivery/restock windows for the specific variant. Record facts found and which hypothetical buyer questions remain unanswered. Not every product has measurable performance or published review breakdowns; absence is not automatically a defect and accuracy is not proven. |
| EC2 Comparative-claim sources | Partial | Extract each measurable comparison and its named test/lab/source link; resolve public links and preserve the claim context. Report absent attribution locally. Whether tests substantiate the comparison or the source is independent requires optional source review; do not treat all marketing adjectives as factual comparisons. |
| EC3 Real customer quotes and Review schema | Partial | Inventory visible quotes, attribution, reviewed product, and matching Review nodes. “Real customer” authenticity is not possible from a URL. Missing quotations/reviews is not a failure for new products; do not recommend marking ordinary promotional copy as reviews. |
| EC4 Authoritative nonhype tone | Not possible | The existing LLM may quote promotional claims and show nearby supporting specifications or their absence. Appropriateness and degree of hype are subjective. Do not score adjectives, confidence, or inferred conversion effects. |
| EC5 Prepurchase FAQ | Partial | Map observed product characteristics to hypothetical sizing/compatibility/return questions, then find exact supporting answers and schema. Include linked policies when relevant. A dedicated FAQ block is not required if the answers are elsewhere; importance of each question remains an assumption. |
| EC6 Product schema completeness | Partial | Reuse E3/E5 for applicable product and offer fields; compare SKU, reviews, and images to actual visible content. Record 3D/video only if available. Do not require reviews, media, public prices, or one SKU model universally. State which named feature rule, if any, makes a field required. |
| EC7 Fair structured comparisons | Partial | Detect comparison tables/lists, named products, matched attributes, units, and stated dates. Compare internal claims for identical variants. Fairness, comprehensiveness, and competitors' current specifications are not possible without external evidence. Prose comparisons and absent “versus” pages are not defects. |
| EC8 No stuffed titles/descriptions | Not possible | Use N10 on actual product titles and descriptions. Preserve repeated phrase examples for advice, excluding necessary model/variant wording. No keyword-density rule can establish a confirmed defect. |
| EC9 Current price/stock/promotions | Partial | Compare visible and marked-up values for the same locale/variant/session; inspect explicit offer end dates. Reproduced internal contradictions are viable. Real stock, current backend prices, and intentional promotion extensions are not possible without commerce data; don't enter checkout to infer them. |

## Website type 2 Business and corporate

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| BC1 Clear identity sentence near top | Partial | Extract homepage/About identity statements and their viewport coordinates. Compare entity and offering meaning, not literal wording. Report the statements and positions. Clarity and the requirement to use identical words are not objectively detectable; LLM evaluation stays advisory. |
| BC2 Numerical scale and impact | Partial | Extract client counts, operating years, disclosed revenue, and case-study metrics with scope/date. Report evidence, not a quota of numbers. Whether omitted confidential metrics exist or should be public is not possible; avoid flagging “trusted by” solely for lacking a count. |
| BC3 Third-party validation | Partial | Inventory named press, awards, certificates, client logos, and case-study links; verify reachable declared destinations and exact identities. Presence is possible. Actual certification validity, endorsement, and independent validation need optional authoritative sources; a logo alone proves neither trust nor a client relationship. |
| BC4 Leadership quotes | Partial | Extract quotations and speaker/role on About and press pages. Record publicly stated attribution. Authenticity and whether a quote adds value are not possible; missing quotes are not a defect. |
| BC5 Consistent external description | Partial | Reuse off-site entity matching and field comparisons for resolvable profiles. Separate categories and descriptions from hard identity facts. Wording differences are not contradictions. Missing platform access or search results yields not possible for that platform, not inconsistent branding. |
| BC6 Organization and verified sameAs | Partial | Resolve Organization nodes and outbound sameAs links. Check the linked profile's website/name/identity evidence. A link's presence does not verify ownership; reciprocal domain references strengthen matching but are not infallible. Do not demand every possible social platform. |
| BC7 Explanatory service pages | Partial | Extract exact spans explaining service, audience, and included scope and map them to hypothetical questions. Absence within the inspected section can be noted. Brochure-versus-explanation quality, correct jargon level, and overall clarity are not possible as deterministic failures. |
| BC8 Service FAQs | Partial | Find evidence for pricing model, timelines, and scope across service and policy pages. Record directly answerable questions and unaddressed sampled questions. Bespoke services may legitimately omit timelines or public pricing; dedicated FAQs and schema are optional. |

## Website type 3 Portfolio and personal

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| PP1 Concrete outcomes | Partial | Extract project-linked outcomes, numbers, units, and attribution. Report measurable claims found. Qualitative work and confidential results can be valid; absence of metrics is not a failure, and the claimed outcome's truth is not possible to establish from the portfolio. |
| PP2 Real attributed testimonials | Partial | Extract testimonial, name, role, organization, and declared source/profile URL. Attribute exactly what the page says. Existence of a named person does not authenticate a testimonial; “real” is not possible without independent corroboration. |
| PP3 Problem approach result case studies | Partial | Match explicit spans for problem, approach, and result in each inspected case study, regardless of heading wording. Report supported coverage. Requiring every gallery project to have a case study or numeric result is a business/editorial judgment, not a detected failure. |
| PP4 Precise craft terminology | Not possible | Use N9 with discipline context. Tools and vocabulary can be inventoried, but their appropriateness and evidence of genuine expertise cannot be reliably inferred from term presence. |
| PP5 Person schema | Partial | Inspect Person nodes, name, jobTitle/role, URL, and sameAs; match identity to the page. Record supported syntax issues and missing optional fields. A field named `role` is not a universal substitute for the appropriate schema.org property; absence of Person markup is optional enrichment. |
| PP6 Short fluent biography | Not possible | Measure length and provide optional passage-specific LLM edits. There is no universal ideal bio length; detailed credentials or artistic writing may be intentional. No automatic filler-adjective defect. |
| PP7 Recognition links | Partial | Extract awards/publications/talks and resolve declared supporting URLs. Report broken references or contradictory dates when context matches. No awards is not a failure; authenticity and completeness need external evidence. |

## Website type 4 Blogs and news

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| BN1 Sources for factual claims | Partial | Use N4 at claim/paragraph level, allowing first-hand reporting, footnotes, bibliographies, and explicit author observations. Report exact unattributed claims as review candidates. Do not require every sentence to have a link or claim unsourced means false. |
| BN2 Expert or primary-source quote | Partial | Inventory quote, attribution, role, and source linkage. Topic suitability, speaker expertise, and authenticity are not possible to certify. Absence alone is not a defect in explanatory or original research material. |
| BN3 Data instead of vague trends | Partial | Find specific trend claims and associated metric, baseline, time range, and source. Highlight missing context rather than requiring numbers in all prose. Whether data exists and whether the claim is correct remains not possible without source evidence. |
| BN4 Byline dates Article schema | Possible | Record byline, stated credentials, labeled dates, and corresponding Article/BlogPosting fields; compare explicit author/date values for the same work. A detectable mismatch needs contextual confirmation. Missing fields are observations unless a specific applicable requirement was established; credentials themselves are unverified. |
| BN5 Fluency | Not possible | Use N6. Readability scores and paragraph length do not establish poor fluency or extractability. Offer quoted editorial examples only. |
| BN6 Confident editorial voice | Not possible | Use N7. Preserve legitimate uncertainty, developing-story caveats, and quotations. Do not score hedge-word counts as authority. |
| BN7 Explain jargon initially | Partial | Use N8 to record candidate terms and explicit definitions in the article's reading order. Definitions in linked glossaries may be sufficient. Whether this readership needs explanation remains not possible without audience context. |
| BN8 Natural nonrepetitive headings | Not possible | Record headings and phrase repetition, excluding series titles and necessary topic continuity. “Keyword-stuffed” versus descriptive is an editorial judgment, not a threshold-based defect. |
| BN9 Evergreen update schedule | Partial | Check dated sources, broken citation links, and explicit temporal contradictions. The publishing schedule and actual updates are not possible from a single audit. Local history can show changes; an old publication date alone does not mean stale information. |

## Website type 5 Web applications and SaaS

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| SA1 Feature outcomes | Partial | Map each observed feature to explicit function and claimed outcome spans, including metric context when present. Report answer coverage. Many features need a precise capability description rather than a numeric business outcome; no missing-number defect. |
| SA2 Independent benchmarks/reviews | Partial | Extract benchmark/review source, score, review count, date, and link; verify accessible declared source identity. Independence and validity require source inspection; absence is not a defect and vendor-hosted benchmark claims are not automatically false. |
| SA3 Result-specific customer quotes | Partial | Extract quotation plus named customer and quantitative/qualitative outcome. Specificity can be described from text; truth and causal attribution are not possible to establish. Generic praise may remain valid testimony, so no required-result threshold. |
| SA4 Correct documentation terminology | Not possible | Use N9; version-matched official specifications and executable examples can support selected technical checks if separately scoped. Term density cannot prove correctness or ranking benefit. |
| SA5 Fair comparisons/alternatives | Partial | Reuse EC7; bind comparison claims to plan, version, date, and provider. Internal contradictions are viable; competitive fairness and completeness are not possible without authoritative evidence. Missing alternatives pages is not a defect. |
| SA6 Applicable software/product schema | Partial | Inventory supported types and inspect syntax/content correspondence under E1–E7. SoftwareApplication, Product, FAQPage, HowTo, and Review are not universal requirements by page path. Do not force testimonial markup into an inapplicable review feature. |
| SA7 Different marketing/docs tone | Not possible | Classify page purpose tentatively and offer passage-specific LLM advice. Tone suitability is contextual and cannot be certified from a style score; literal technical prose may appropriately contain complex sentences. |
| SA8 Nonstuffed feature headings | Not possible | Use N10 on extracted headings. Repeated feature names can be necessary for navigation or API documentation. Preserve exact examples as advice, without penalty predictions. |
| SA9 Dated changelog/release notes | Partial | Discover linked changelog/releases, extract version-date entries, and check relevant links. Presence and stated recency are observable. Active maintenance, undisclosed releases, and absence everywhere are not possible from a bounded public crawl; quiet release cadence is not a failure. |

## Website type 6 Social and community platforms

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| SC1 Plain policy facts and sourced statistics | Partial | Extract policy claims, usage/moderation numbers, scope/date, and attribution. Apply N4 to exact statistical assertions. Plainness and the truth/completeness of operational policies are not possible to prove from wording. |
| SC2 Real member/moderator quotes | Partial | Inventory editorial quotes and stated community roles. Authenticity and consent cannot be inferred from page presence; missing quotes is not a defect. Optional linked original posts can corroborate wording only. |
| SC3 Disclosed community counts | Partial | Extract labeled active-user/post/growth metrics with time windows and population definitions. Do not confuse registered accounts with active users. Undisclosed numbers or a qualitative community description are not failures. |
| SC4 Self-contained FAQ help center | Partial | Identify actual Q&A and answer evidence, assess raw/rendered availability, and compare any markup. LLM clarity/self-containment advice remains subjective. Do not require FAQPage for all help articles or a particular answer length. |
| SC5 Entity parity with app stores/press | Partial | Follow declared app listings and press links; match app/developer/brand identity before comparing explicit fields. Platform name, publisher, and legal company can differ legitimately. Independent discovery and inaccessible listings require optional search/access; no missing-profile claim from failed fetches. |
| SC6 Nonstuffed landing pages | Not possible | Use N10. Count repetitions for inspection, but do not interpret broad topic coverage as stuffing without editorial context. |
| SC7 Authoritative trust/safety tone | Not possible | An LLM can suggest clearer wording for quoted passages. Tone cannot prove policy precision, enforceability, or effectiveness; no confident-language score. |

## Website type 7 Education and LMS

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| ED1 Concrete course outcomes | Partial | Extract stated skills, expected duration, completion/pass metrics, and cohort/time scope. Report answers available to a prospective learner. Not every course tracks or publishes success rates; missing rates are not defects and claimed outcomes are unverified. |
| ED2 Curriculum sources | Partial | Extract textbooks, references, research links, and stated instructor credentials; resolve available declared sources. Their adequacy, authority, and actual curriculum use are not possible to certify from a URL. |
| ED3 Instructor/learner quotes | Partial | Inventory bios, attributed quotations, learner outcomes, and supporting links. Credentials and outcomes need independent verification. No requirement for every instructor or course to contain a quote; authenticity is not possible from presence alone. |
| ED4 Course FAQs and FAQPage | Partial | Find answers to prerequisites, format, certification, and refunds across course and policy pages; compare actual FAQ markup if present. Do not require a dedicated FAQ or schema on every course. Applicability of refund questions depends on the offering. |
| ED5 Defined subject terminology | Partial | Use N8/N9; record explicit definitions and candidate unexplained terms. Difficulty must match stated learner level. Correctness and whether definitions are needed are not possible as broad automatic judgments. |
| ED6 HowTo on tutorials | Partial | Identify actual sequential instructions and any HowTo graph; inspect supported syntax and correspondence. Missing optional HowTo markup is not a defect. Never infer an AI feature benefit solely from adding it. |
| ED7 Fluency and simplicity | Not possible | Use N6/N8. Advanced or academic prose is not automatically unextractable; the LLM may suggest edits appropriate to the declared learner level without an automated failure label. |
| ED8 No stuffed course catalogs | Not possible | Use N10, excluding repeated subject labels across distinct course cards. Report only passage-specific editorial candidates; repeated “Python” across a Python catalog does not prove stuffing. |
| ED9 Curriculum freshness | Not possible | Actual curriculum changes require syllabus history, LMS/CMS access, or authoritative version evidence. A single course page can expose dates or conflicting prerequisites; those narrow observations may be reported separately. Old dates alone do not establish an outdated course. |

## Website type 8 Media and entertainment

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| ME1 Concrete entertainment metadata | Partial | Extract runtime, release dates, view/rating counts, awards, and named work/edition. Report presence and internal inconsistencies. A synopsis need not disclose popularity metrics; “fan favorite” alone is not a measurable defect. |
| ME2 Attributed critic scores | Partial | Bind each critic score to source, scale, count/date when available, and work version; resolve declared source URLs. Attribution presence is observable. Source authenticity and current score need optional external evidence; don't compare incompatible scales. |
| ME3 Review/cast/critic quotes | Partial | Extract quote, speaker/source, and context. Original-source matching may corroborate text. Authenticity, fair quotation, and whether a quote is needed are not possible to guarantee; absence is not a defect. |
| ME4 Video/Movie/TVSeries schema | Partial | Validate properties appropriate to each actual type; distinguish a trailer video from the movie/series it describes. Inspect relevant dates, duration, cast, and rating context without imposing every field on every type. Record markup defects only within supported rules. |
| ME5 Fluent nonoverstated synopsis | Not possible | LLM advice may cite unsupported superlatives or awkward passages. Vividness, appropriate opinion, and rhetorical exaggeration cannot be detected reliably enough for confirmed failures. |
| ME6 Practical FAQs | Partial | Map observed works to hypothetical release/watch/episode/age-rating questions and retrieve supporting spans from pages or linked guides. Scope answers by region and edition. Not every question applies to every work, and a dedicated schema-marked FAQ is optional. |
| ME7 No title/metadata stuffing | Not possible | Inventory titles/descriptions and repeated phrases for N10 advice. Titles may legitimately include edition, access mode, or episode labels. No automatic failure from keyword frequency. |
| ME8 Current availability and status | Partial | Compare explicit dates/status fields across inspected pages and schema for the same territory/work/time. Report reproduced contradictions. Current licensing, renewal decisions, and episode schedules are not possible to certify without authoritative external feeds or owner data. |

## Off site profile discovery and consistency

The declared-link workflow is **partial**: inventory sameAs, footer, contact, and other explicit profile links; fetch public allowed destinations; record response and profile facts. Login walls, ambiguous identities, and unavailable pages mean blocked or not possible. A social share URL is not an entity profile. A destination's `nofollow` or `rel` attributes are observations, not evidence that a backlink is ineffective.

The independent-discovery workflow is **not possible reliably across the full specified platform list with the core alone**. Optionally use an already available search tool or official platform APIs to search exact brand, domain, and location combinations. A public API supports Wikipedia/Wikidata candidates without a paid search subscription, but this does not solve LinkedIn, Crunchbase, Google Business Profile, or all directories. Log query, source, time, results inspected, and access failures. A search result snippet is a candidate, not a verified profile. [MediaWiki search API](https://www.mediawiki.org/wiki/API:Search).

The source calls the allowlist owner-editable; this must not be assumed. In particular, Wikipedia and Wikidata are not business-owned profile pages. Account possession or a declared sameAs link does not prove unilateral editing rights on any platform. Suggested actions should say “verify and request/correct through the platform's process” unless management rights are established.

Match entities using explicit identifiers and reciprocal domain/location evidence, not name similarity alone. A declared link is useful evidence but can itself be stale or wrong. Independently discovered profiles can also yield strong evidence if identity is verified; discovery method does not determine truth. Two matching profile names alone are insufficient for either path.

| Consistency field from source | Comparison rule |
| --- | --- |
| Brand/legal name | Preserve legal name, trading name, former names, localized names, and subsidiaries separately. Normalize punctuation/case for matching, not for proving identity. |
| Category/industry | Compare descriptions of actual activity; platform taxonomy labels need not match literally. Ambiguous category mappings are advisory. |
| Description/tagline | Paraphrases and audience-specific summaries are valid. Only explicit incompatible factual assertions can form a contradiction. |
| Address/service area | Match the same branch, address type, and effective period. A registered office, storefront, mailing address, and service area are different facts. |
| Phone | Normalize country code and formatting with explicit country context. Sales/support/local numbers can all be correct. A phone parsing library helps formatting, not semantic identity. |
| Founding date | Distinguish brand launch, incorporation, predecessor, and acquisition dates. Different event definitions are not a mismatch. |
| Logo | Different resolutions, dark-mode assets, and campaigns are valid. Pixel inequality does not establish an outdated brand; vision advice remains subjective. |
| Social handles | Compare resolved profile IDs/URLs, aliases, redirects, and platform context. Rebrands require temporal evidence. Never infer ownership solely from a similar handle. |

| Source candidate defect | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| PROFILE_DATA_MISMATCH | Partial | Report two explicit incompatible values only after matching entity, field meaning, locale, and effective period. Preserve both quotes/URLs and label a discrepancy, not which source is wrong. Text differences and uncertain entity matching must not become a defect. |
| UNDECLARED_PROFILE_FOUND | Possible with optional discovery | For a verified found profile, search collected sameAs and profile links for equivalent resolved URLs. Report “verified profile not linked in inspected pages.” This is optional corroboration advice, not a defect; an incomplete crawl cannot establish no link anywhere. Without discovery capability, this branch is not possible. |
| STALE_THIRD_PARTY_PROFILE | Not possible generally | A mismatch does not identify the stale side. A narrow case becomes viable when dated, authoritative evidence establishes a change and the same verified profile explicitly presents the old value as current. The first-party homepage alone is not automatically the truth source; otherwise report discrepancy only. |
| MISSING_EXPECTED_PROFILE | Not possible | A finite unsuccessful search cannot prove absence or eligibility for a profile. With optional search, report “no verified profile found in these searches,” or “results inaccessible,” without severity. Do not recommend a platform solely because an uncertain business classifier expects it. |

## Bridge items

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| I1 Stable distinct citable URLs | Partial | For each discovered content unit, reopen its actual URL in a clean context and repeat load; verify the same core identity/content is reachable and inspect effective access/index directives. Normal query URLs such as `/product?id=123` are valid candidates. Report a reproduced deep-link failure or JS-only dependency. Unknown units and search-only alternatives cannot be exhaustively discovered. |
| I2 Robustness to unexpected parameters | Partial | On safe content GET URLs, preserve existing queries and compare baseline/test/baseline responses using an inert unique audit parameter and, if appropriate, a conventional UTM parameter. Compare core entity/facts and canonical destinations, allowing benign redirects and dynamic content. Repeat regressions before reporting. Do not use `session`, cart, or signed URL parameters as allegedly inert probes. Robustness to all unknown parameters is not possible to prove. |

For I2, a missing canonical is not itself a parameter-handling failure, and a successful redirect stripping the extra parameter is acceptable. The document's assumption that personalization does not exist is not established: cookies, locale, experiments, referrals, and geography can alter real sites. If variation cannot be controlled or a probe could change meaningful state, return not possible for that case.

## Engagement items

Use fixed, recorded viewports and screenshots. DOM order is not visual order. Bounding rectangles can establish position, and hit-testing can provide evidence of occlusion; neither proves a visitor's attention or comprehension. A visible element may be offscreen, covered, clipped, or have an inaccessible name. Interpret these separately.

| ID and item | Feasibility | Best detection and false-positive boundary |
| --- | --- | --- |
| J1 Immediate identity clarity | Partial | Extract the page's identity statement and record rendered coordinates, font/layout context, clipping, and first-viewport screenshot. An existing vision-capable LLM can provide grounded advice. Whether a visitor understands it “in seconds” and where their eyes land are not possible without user research; missing H1 or “Welcome” alone is insufficient. |
| J2 Structural navigability | Partial | Inventory visible breadcrumbs, native/ARIA navigation, parent/category links, and home/brand links; resolve safe destinations and record return paths. Confirmed broken navigational links are viable. Missing breadcrumbs alone is not a failure; single-page sites and alternative navigation patterns may be complete. Universal visitor understanding remains not possible. |
| J3 Key information prominence | Partial | For an explicitly identified fact, record viewport intersection, scroll offset, occlusion, and accessible presentation in defined states. Report “price below initial viewport at this viewport,” not “price hidden” or “poor engagement.” Which fact matters and whether prominence is adequate are not possible as objective failures from URL-only context. |
| J4 Steps and conversion friction | Partial | Observe visible CTA, linked destinations, selectors, login messaging, and blocking interstitials. Follow only safe nontransacting information links; keep an observed path separate from any LLM hypothesis. True minimum steps, guest-checkout availability, and end-to-end completion are not possible without exercising the flow. Never infer step count from preceding DOM controls. |
| J5 Credibility/trust signals | Partial | Inventory actual reviews, ratings, customer logos, case studies, certifications, and source links appropriate to a tentatively identified page type. Authenticity, perceived trust, and conversion impact are not possible to establish. No mandatory review count or trust-seal rule; absence is an optional content observation. |
| J6 Intrusive popups/interstitials | Partial | Observe initial load and bounded later states with screenshots and mutation sampling. Identify top-layer dialogs and overlays, measure overlap/hit-testing against core content, and record dismissibility through safe controls if available. Confirm physical obstruction in the observed state; fixed positioning or high z-index alone is insufficient. “Distracting” and all-session absence are not possible to prove. |
| J7 Post-completion value | Not possible | Requires a successful action and its actual completion state, outside the read-only scope. A public confirmation-page mockup is not evidence of the real flow. Only a separately supplied test environment, recorded completed flow, or authorized test transaction would make that narrower review possible. |
| J8 Alternatives when unavailable/mismatched | Partial | On naturally encountered explicit out-of-stock/unavailable pages, inventory visible similar-item/category/support alternatives and confirm their safe destinations. Report available recovery links in that state. The visitor's expectation mismatch, personalization, and absence across unobserved failure states are not possible. Do not force stock changes or claim every recommendation is relevant. |
| J9 Useful 404 recovery | Partial | Prefer naturally found broken links; optionally request a small number of unique nonexistent public paths. Capture final status, error content, and usable navigation/category/support links or a visible search form, without submitting it. Report observed recovery affordances. A 200 soft-error page is distinct from an HTTP 404; expired/authenticated states remain untested. |
| J10 Responsiveness/speed as separate engagement check | Exclude | Preserve as a source item, but reuse H1 measurements and H3 viewport evidence rather than adding a duplicate defect. Human perceived speed and conversion consequences are not possible from those measurements alone. |

## Gating and deduplication

Do not implement the source's blanket A → B → C suppression literally. A robots disallow for one bot does not make facts unreadable to every consumer; noindex does not make HTML impossible to inspect; a raw/rendered gap may matter only to consumers without JavaScript. A canonical pointing elsewhere is not automatically an access failure.

Use observation-specific dependencies instead:

- If the collector received a challenge instead of the target page, downstream target-content checks are blocked. Do not report “missing schema,” “empty content,” or “missing navigation” from the challenge template.
- If raw HTML is available but the browser fails, continue source checks; mark rendering/visual conclusions blocked.
- If markup is malformed, keep the syntax finding and do not manufacture missing-field findings from the unparsed block.
- If a PDF parser or external profile is unavailable, block only those branches.
- If a genuine noindex or bot-disallow is observed, retain independently observed content information, but do not claim each issue caused a separate loss of citations.

Deduplicate by page/entity, underlying evidence, and supported cause. C1/C2/C4 can share one demonstrated JavaScript fact gap; E3 and EC6 can share one schema issue; N12 and off-site checks can share one discrepancy. J3 and N2 may describe the same placement for different audiences, so link the observations instead of inflating the defect count. Preserve all checklist IDs in `related_check_ids`.

## Suggested script boundaries

These are proposed modules, not files implemented by this review:

| Module | Responsibility |
| --- | --- |
| `collect_site` | URL normalization, constrained HTTP collection, robots/sitemaps, crawl inventory, evidence persistence, and collection coverage. |
| `collect_browser` | Controlled raw/rendered capture, layouts, frames, accessible text, viewports, and timing. |
| `check_access` | A, B, D, I1/I2 transport and rule observations. |
| `check_representation` | C, E, F, G, H with explicit optional capability checks. |
| `extract_content_evidence` | Claim/source, quote/speaker, fact/context, dates, authors, Q&A, and page-type evidence for N and all vertical items. |
| `check_profiles` | Declared-link resolution, optional bounded discovery, entity matching, and scoped discrepancies. |
| `check_engagement` | J visual/navigation observations without conversion actions. |
| `assemble_report` | Applicability, evidence validation, abstention, cross-check deduplication, and LLM editorial advice kept separate from confirmed defects. |

Keep LLM interpretation in the already-running agent rather than adding a second model service to each script. The script returns structured evidence; the agent proposes context and explanations; a final validator rejects unsupported citations and overbroad conclusions. Agreement between multiple LLM calls is not proof.

Each result should include at least:

```json
{
  "check_id": "C2",
  "related_check_ids": ["C1", "C4"],
  "result": "confirmed_observation",
  "scope": "one URL, one locale, one product variant, raw and rendered capture",
  "observation": "The visible price is absent from source body text but present in source JSON-LD.",
  "evidence": [
    {"kind": "dom", "artifact": "capture-id", "locator": "verified-selector"},
    {"kind": "jsonld", "artifact": "response-id", "locator": "verified-json-path"}
  ],
  "applicability": "plain-body-text extraction only",
  "collection_complete_for_scope": true,
  "limitation": "Does not establish inability of all AI systems to extract price.",
  "required_capabilities": ["http", "browser"],
  "observed_at": "record actual capture time",
  "rule_version": "record packaged rule version"
}
```

Do not attach invented confidence percentages. Report reproducibility, evidence completeness, applicability, and unsupported dimensions explicitly. Do not give an overall pass or total score when key checks are not possible.

## Implementation priorities and validation

Implement deterministic collection and access/representation checks first. Add rendering comparisons, explicit same-context fact contradictions, broken references, and navigation obstruction next. Keep editorial assessments optional and unscored. Defer independent off-site discovery, PDF/OCR, and media analysis to capability modules.

Before using a detector in production, verify it against fixtures containing both failures and legitimate counterexamples. Essential cases include robots Allow exceptions; repeated user-agent groups; missing robots; intentional noindex; valid cross-domain canonical; query-based product URLs; short complete pages; raw JSON-LD facts; locale/variant prices; multiple legitimate schema entities; decorative empty alts; opaque media players; authenticated challenge pages; accessible accordions; mobile menus; and sitemaps at alternate paths. Test that missing capabilities, crawl limits, and uncertainty cause abstention. Measure precision on labeled findings and keep those results separate from coverage; low finding volume is acceptable under this requirement.

The items marked not possible are not necessarily impossible for every future system. They are not reliably establishable from this input and operating scope. Owner-provided intent, authoritative feeds, historical snapshots, credentials, or completed-flow evidence can expand the scope explicitly; extra parsing libraries alone cannot.
