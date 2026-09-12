# Check procedures

Research-derived rules, not unconditional failure predicates. Read only applicable IDs.

## A1 robots.txt exists, HTTP 200, valid

Feasibility: Possible. Reference band: S4. Solution level: C.

Detection: Fetch the correct scheme/host/port `/robots.txt`; retain redirects, headers, bytes, encoding, parseable directives, and line errors. Detect actual response/parse observations. A 404 is not an automatic crawl block; an empty valid file is acceptable. HTTP 200 returning an HTML error template is not a valid robots file.

Activation: Use S4 only for an established robots response/rule failure that prevents the intended consumer from crawling target content. Mere file absence, harmless syntax debris, or a 404 is not this condition; usually S0. Unknown consumer behavior is U.

Recommendation and validation: Propose a corrected robots response/file only for an observed problem. Missing robots alone needs no repair. Policy is required to generate intended rules; server details are required for a deployable fix. Validate parsing, response behavior, and the effective permission matrix.

## A2 No blanket wildcard disallow

Feasibility: Possible. Reference band: S4. Solution level: C.

Detection: Evaluate effective rules for each sampled URL and relevant bot, including matching groups, most-specific paths, Allow ties, wildcard/end matching, and URL encoding. Report an effective disallow with rule lines. `Disallow: /` alone is insufficient if exceptions or more-specific bot groups apply. Do not assert accidental blocking.

Activation: Effective rules prohibit an intended retrieval/search consumer from target pages. Confirm URL matching, exceptions, and intent. Legitimate restrictions are S0; training-policy choices alone are not a GEO defect.

Recommendation and validation: Draft the smallest rule change for the exact blocked path and named bot after crawl intent is established. Preserve other restrictions. Run before/after rule tests including exceptions, private paths, and other bot groups; do not replace the file with “allow all.”

## A3 Per-bot permission matrix

Feasibility: Partial. Reference band: S4. Solution level: C.

Detection: Compute policy by bot and URL locally; record role, source, registry version, effective rule, and declared permission. Real provider access and citation eligibility are not possible to prove with a spoofed UA. Keep training, search, user-triggered fetch, and product-use controls separate; legitimate governance choices are observations, not automatic defects.

Activation: An established desired search/retrieval use is effectively prohibited for the scoped URLs. Report the affected product/use, not universal invisibility. A permission matrix with no demonstrated undesired restriction is informational; unknown policy is U.

Recommendation and validation: Generate a policy-specific per-bot diff and resulting permission matrix. Need the owner's allowed uses and provider-specific semantics. Validate all affected groups; do not promise actual provider access or citation eligibility from robots rules alone.

## A4 Crawl-delay starvation

Feasibility: Partial. Reference band: U. Solution level: C.

Detection: Parse value and applicable group; apply only to providers documented to honor it. Report the delay. Starvation and indexing loss are not possible from a URL: page totals, concurrency, crawl schedules, and provider budgets are unknown. Optional verified server logs improve observation; never score a universal “excessive delay” threshold.

Activation: URL-only evidence cannot establish starvation or an appropriate limit. Keep the parsed delay informational. Provider/server evidence of material constrained discovery could support S2/S3; do not assign high severity from the number alone.

Recommendation and validation: Propose measurement or rate-limit tuning for the specific honored directive. Need server capacity and actual crawler activity before choosing a value. Validate load and crawl behavior; never invent an optimal delay from page count.

## A5 Sitemap directive in robots

Feasibility: Possible. Reference band: S1. Solution level: V.

Detection: Parse all `Sitemap` directives and validate their absolute URLs and fetch results. Missing declaration is an observation only: sitemaps can be submitted elsewhere or discovered at other paths. Preserve malformed URL evidence rather than claiming the site has no sitemap.

Activation: Adding a verified appropriate declaration is optional discovery assistance. Missing declaration alone is not a defect and may be S0. A broken declared sitemap is assessed under D1 once, not escalated here.

Recommendation and validation: Generate a `Sitemap:` line for an already verified appropriate sitemap, as optional enrichment. Preserve existing declarations. Parse the modified file and re-fetch the destination; no inferred sitemap URL or promise of indexing.

## B1 Meta noindex

Feasibility: Possible. Reference band: S4. Solution level: C.

Detection: Parse applicable `robots` and provider-specific meta directives in source and rendered head; recognize `none` as applicable. Capture tag, selector, bot scope, and stage. Report “noindex directive present.” Whether exclusion is wrong is not possible without established indexation intent; a login or account page may correctly use noindex.

Activation: An applicable effective directive excludes a page confirmed to be intended for the target index. Unknown indexation intent is U; intentional exclusion is S0. Do not generalize to all direct-fetch AI uses.

Recommendation and validation: Propose removal of the exact effective noindex directive only when indexing is intended. Preserve unrelated directives. Need template/CMS access for the real patch; retest source and rendered meta plus headers so another noindex does not remain.

## B2 X-Robots-Tag noindex

Feasibility: Possible. Reference band: S4. Solution level: C.

Detection: Inspect every header occurrence, preserving bot-specific scope and combinations. Associate headers with the exact response, including PDF responses; do not transfer an intermediate redirect's header to its destination. Report effective directive for supported provider semantics, with the same intent caveat as B1.

Activation: Same as B1 for the actual response/header scope. This can stop intended index eligibility; fix the responsible layer. Deduplicate simultaneous meta/header manifestations into one exclusion issue where appropriate.

Recommendation and validation: Propose changing the specific X-Robots-Tag source for the affected responses. Need intent and the responsible server/CDN/application layer. Verify final GET headers, provider scope, and unaffected restricted pages; HTML edits alone cannot fix a header.

## B3 Canonical correctness

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Extract HTML and HTTP-Link canonicals, resolve relative URLs, record multiple distinct targets, and fetch allowed targets. Reproducible dead targets, loops, or competing declarations are objective issues. Self-reference absence, cross-domain targets, and content differences alone cannot establish the owner's intended canonical. Compare entity/variant context; intent remains not possible.

Activation: Conflicting/broken canonical declarations or an established wrong target undermine intended URL identity. Non-self or cross-domain canonicals alone are S0/U. A separate inaccessible target is assessed under B4, not assumed from the canonical.

Recommendation and validation: Draft one canonical target after preferred URL and duplicate/variant semantics are established. Align contradictory declarations without flattening real distinctions. Verify target reachability and consistent canonical signals; the crawler's ultimate canonical choice cannot be guaranteed.

## B4 HTTP status and redirects

Feasibility: Possible. Reference band: S4. Solution level: C.

Detection: GET observed links and sitemap URLs, record redirect hops, loops, final status, and source-link location. Recheck transient failures. Report the actual broken reference or redirect; an intentional 301 is not broken and a 403/429 may reflect this checker. Do not infer crawl-budget loss from hop count alone.

Activation: A reproducible error/loop prevents access to a scoped intended target. For nonessential broken references with alternatives, use S2; harmless functioning redirects are S0. Checker-specific blocks require scope/intent qualification.

Recommendation and validation: For each broken reference, propose a verified equivalent destination if one exists. Otherwise offer restore, remove-reference, or retained-gone options conditional on content intent. Status alone does not choose the right remedy. Test links, redirect loops, and final content identity.

## B5 Login, CAPTCHA, bot walls

Feasibility: Partial. Reference band: S4. Solution level: C.

Detection: Capture unauthenticated response, redirect target, rendered challenge/form, and absence of expected target content. Require multiple signals: a challenge vendor script alone can be harmless. Report “content blocked in this session.” Whether it should be public or real bots encounter the same wall is not possible from the URL.

Activation: A wall demonstrably blocks intended public content in the tested consumer/session. Confirm intended access and preserve necessary protections. A vendor script, brief usable challenge, or intentional account wall is not automatically critical.

Recommendation and validation: Describe the exact observed access barrier and propose an appropriately scoped public-content exception after intent/security policy is known. Need origin/CDN/auth configuration. Verify access and protected-route regressions; do not recommend globally disabling authentication or bot protection.

## C1 Raw versus rendered word count

Feasibility: Possible. Reference band: S3. Solution level: C.

Detection: Compare main-content text in parsed source against rendered visible text with the same segmentation and language-aware tokenization. Count boilerplate separately. Report actual text and content differences. A `<25 words` threshold, `#root` presence, or low count is not a failure; short utility pages can be complete.

Activation: Essential content demonstrably unavailable to an established source-only consumer while available after rendering. Word-count differences alone are S0. Full target access failure may be S4 with consumer evidence; do not assume all AI systems omit JavaScript.

Recommendation and validation: Identify exact essential content missing from source and specify server-delivered availability if that consumer requires it. Need application architecture for implementation. Retest source facts and hydration; do not add filler merely to pass a word-count threshold.

## C2 Target facts require JavaScript

Feasibility: Possible. Reference band: S3. Solution level: C.

Detection: Identify a specific rendered fact with an exact locator and context, then search source body text, metadata, JSON-LD, and embedded state separately using normalized units/values. Report the exact channel gap, e.g. “visible price absent from source body, present in JSON-LD.” Entity extraction ambiguity or differing variants means abstain.

Activation: A decision-critical fact is unavailable through channels supported by the target consumer. A price present in supported JSON-LD is not absent. Minor text differences are S1/S0; unknown consumer capabilities are U.

Recommendation and validation: Specify the exact fact and channel to expose in initial HTML, using the existing authoritative data path. Need template/data lifecycle details to avoid stale hardcoded values. Verify variant/currency consistency in raw and rendered states.

## C3 Hash/client-side routes

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Inventory observed hash links. Open each in a clean context; compare fresh load and reload against the parent page and record whether the target entity loads. Distinguish ordinary section anchors. Prove observed JS dependence or broken deep linking; proving no server-rendered equivalent exists anywhere is not possible with bounded discovery.

Activation: Direct access to an observed content unit loses its identity or requires unrelated navigation. Escalate to S4 if intended access is impossible. Working hash anchors and query-based routes are S0.

Recommendation and validation: Propose stable deep-link behavior for observed route failures. Need routing and URL compatibility requirements before selecting paths or redirects. Test fresh load, reload, server response, and legacy links; do not rewrite valid fragment anchors.

## C4 SSR or prerendered fallback

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Compare captured source content with rendered target facts and optionally a JS-disabled load. Report server-delivered content sufficiency. Identifying the exact build technique or whether a fallback exists for all bots is not possible externally; framework fingerprints and script filenames are not proof of SSR.

Activation: Use the demonstrated essential-content gap from C1/C2, not framework/SSR absence itself. Often the same issue: merge recommendations. A complete usable page built without SSR has no defect.

Recommendation and validation: Offer SSR/static-generation/server-content options matched to known constraints; choose a concrete implementation only with confirmed framework and data needs. Verify initial content, freshness, and hydration in the actual application.

## C5 Delayed assembly beyond crawler timeout

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Timestamp navigation, relevant resource completion, and first stable target-content visibility using browser timing and DOM observations. Repeat measurements. Report observed content delay or timeout. Actual crawler abandonment, its deadline, and causal blame on a resource are not possible without provider evidence; waterfall correlation alone does not prove causation.

Activation: Reproducible measured delay violates an established content-availability budget. Pure timing with no budget is informational/U. An actual persistent rendering failure can be S3/S4; never infer an unknown crawler abandonment deadline.

Recommendation and validation: Give a resource-specific investigation using the measured timeline. Recommend deferral/caching/render changes only after establishing causality. Validate content appearance and interactions under comparable conditions; do not fabricate a provider timeout.

## D1 Reachable valid sitemap

Feasibility: Possible. Reference band: S2. Solution level: V.

Detection: Fetch declared locations plus a bounded conventional-path probe. Detect gzip, parse safely with namespace/root checks, inspect URLs, and record MIME. A missing `/sitemap.xml` does not establish missing sitemaps. A MIME mismatch is a compatibility observation if XML parses; a 200 HTML fallback is not XML.

Activation: A declared sitemap demonstrably fails parsing/access and should be maintained. Link discovery may still work, so not an access blocker. S3 only if evidence establishes material reliance on this failed inventory route. A missing conventional path alone is S0.

Recommendation and validation: Generate a structurally valid replacement for a supplied parseable URL inventory or an unambiguous escaping/namespace correction. If URLs are unrecoverable, request the inventory. Validate XML, entries, limits, and preserved data; serving/configuration remains conditional.

## D2 Sitemap versus link graph coverage

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Compare normalized observed sitemap URLs with observed internal links, preserving substantive parameters and alternate locales. Report “N observed eligible URLs absent from inspected sitemaps.” Exhaustive coverage and orphan discovery are not possible from URL-only crawling. Sitemap omission is not a defect by itself, especially for duplicates or deliberately excluded pages.

Activation: Optional additions for verified eligible observed URLs. Sitemap absence is not evidence they are undiscoverable. Established important discovery gaps can be S2, but require more than set differences; unknown full inventory is U.

Recommendation and validation: Draft proposed additions from inspected URLs, with reasons and exclusions. Need authoritative inventory and canonical/indexation intent to call it complete or correct. Validate candidate membership and URLs; omission alone is not a defect.

## D3 lastmod reflects actual edits

Feasibility: Not possible. Reference band: U. Solution level: C.

Detection: A first audit has no edit history. Validate date syntax and record suspicious future dates as observations. Optional local snapshots can establish content changed between two observations while lastmod stayed unchanged; dynamic content, meaningful-edit policy, and exact edit dates still need context. HTTP Last-Modified is not authoritative editorial history.

Activation: Actual edits cannot be inferred from a one-time fetch. With reliable edit records, demonstrated misleading lastmod can be S2. Cosmetic date refreshes have no justified priority.

Recommendation and validation: Propose deriving lastmod from meaningful source edits, or omitting unreliable optional dates. Need edit history or CMS events to populate real timestamps. Validate dates against those events; never set everything to the audit date.

## D4 Key commercial pages excluded

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Identify observed product/pricing/docs pages using visible evidence and compare with inspected sitemaps and access directives. Report their actual membership and restrictions. Which pages are “key,” accidental exclusion, and undiscovered omissions are not possible without an inventory or explicit intent. Do not require every commercial page in a sitemap.

Activation: A confirmed important eligible page is missing from a known maintained inventory and inclusion is a warranted discovery improvement. Crawl/noindex prohibitions inherit A/B once. Mere absence from a sitemap is S1/S0, not proof of invisibility.

Recommendation and validation: Propose specific important-page additions or access changes only after importance and eligibility are established. Test sitemap inclusion and access. Do not infer business priority from a URL path alone.

## D5 Large sitemap/index support

Feasibility: Possible. Reference band: S2. Solution level: V.

Detection: Count each file's entries and uncompressed bytes; validate index references and inspect child files within bounds. Flag demonstrated protocol-limit violations, not merely the absence of an index. Multiple valid sitemaps may be declared separately. Hitting the checker's own limit means incomplete inspection, not truncation by the search engine.

Activation: Demonstrated protocol-limit violations impair a supported sitemap. Broader importance requires scope evidence; use S3 only for established material inventory loss. No index file with otherwise valid discovery is S0.

Recommendation and validation: Partition an available, approved URL set into valid size/count-bounded files and generate an index. Verify no lost/duplicated entries and valid XML. Hosting paths must be supplied/validated; adding an index is unnecessary when existing files already comply.

## E1 JSON-LD presence

Feasibility: Possible. Reference band: S1. Solution level: V.

Detection: Inventory source and rendered `application/ld+json` scripts and parse each separately. Report presence or absence specifically of JSON-LD. Microdata/RDFa may supply structured data instead. Neither JSON-LD absence nor schema absence alone proves the content is unextractable.

Activation: Optional structured representation of supported facts. Missing JSON-LD alone is not a defect, especially with other formats. Never a blocker simply because absent.

Recommendation and validation: Offer optional JSON-LD generated from explicit supported page facts. Omit unavailable fields. Validate JSON, supported type/property rules, and fact bindings; do not claim schema absence made the page invisible.

## E2 Organization/Brand fields

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Resolve graph nodes and references for the actual site entity; inventory name, logo, URL, and sameAs by page. Use the applicable type's properties, not one universal mandatory list. Not every page needs a full Organization block; brands, publishers, and legal entities differ. Absence is an optional enrichment opportunity.

Activation: Optional entity enrichment when verified fields are available. Demonstrated identity contradiction is N12/S3, not a penalty for missing sameAs or logo. Do not require full markup on every page.

Recommendation and validation: Generate an entity node from established name/URL/logo/profile facts, preserving stable IDs and distinctions between brand and legal organization. Validate references and types. Unsupported ownership/profile claims must be omitted or held for confirmation.

## E3 Product/Offer fields

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: For positively identified offers, inspect price, currency, availability, nested offers, AggregateOffer, variants, and price specifications. Apply a versioned provider feature rule only when that feature is the declared target. Quote-only products and unavailable fields must not be forced into invented prices. Record missing fields, not lost AI citation eligibility.

Activation: A supported, explicitly targeted feature lacks its required applicable offer fields. Optional enrichment is S1; missing/incorrect essential public facts are assessed separately at S3 when established. No universal markup requirement.

Recommendation and validation: Generate Product/Offer markup only from a known source for price, currency, availability, and variant. URL snapshots can support a draft but not a durable commerce implementation. Validate data bindings and variants; never invent stock or required commercial values.

## E4 FAQ/HowTo/Article applicability

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Use visible page content plus schema graph to report types represented and content-to-markup correspondence. A classifier's expected type is advisory. Missing FAQ or HowTo schema is not a confirmed defect and does not establish AI Overview ineligibility. Provider feature support must be maintained separately from schema.org vocabulary.

Activation: Optional FAQ/HowTo/Article markup accurately representing existing content. Missing markup alone has no demonstrated material impact; S0 is valid when unnecessary.

Recommendation and validation: Draft an optional supported schema representation of already visible FAQ, article, or procedural content. Preserve exact meanings and answer scope. Validate correspondence and type rules; feature eligibility and benefits are separate.

## E5 JSON-LD validity

Feasibility: Partial. Reference band: S2. Solution level: V.

Detection: Deterministically report JSON syntax errors with block/offset. For a documented supported subset, validate node shapes and known vocabulary; use a real JSON-LD processor for advanced constructs. Full semantic validity and Google Rich Results equivalence are not possible with a generic JSON Schema. Unknown extensions/contexts trigger unsupported, not invalid.

Activation: Confirmed syntax or supported-rule failure makes a relevant block unusable. It does not erase otherwise extractable prose. S3 only with evidence that essential information lacks a supported alternative channel.

Recommendation and validation: Repair unambiguous syntax/serialization defects while preserving known values, then parse and validate the supported subset. Ambiguous truncated text or conflicting semantic repairs require context. A parser passing cannot certify truth or all provider rules.

## E6 Duplicate/contradictory blocks

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Resolve nodes by stable `@id` and explicit entity/offer identifiers. Compare scalar claims only for the same variant, currency, location, and time. Identical duplication is informational; repeated `@type` is normal. Conflicting prices become a finding only when contexts demonstrably match and ranges/list prices are excluded. Otherwise abstain.

Activation: Incompatible essential values for the same entity/offer/context can mislead extraction. Identical duplicates are S1/S0; separate variants/entities are S0. Unresolved identity/context is U.

Recommendation and validation: Deduplicate proven identical nodes mechanically; choose a value for contradictory nodes only with a source of truth. Preserve legitimate multiple entities/offers. Validate graph references and same-context claims; do not assume visible text always wins.

## E7 Markup overclaims visible content

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Compare explicit same-entity facts, such as a single offer's visible price and marked-up price, after checking tabs/accordions/variants. Report supported discrepancies with both locators. Missing literal text alone is insufficient; alternate wording and legitimate nonliteral properties exist. Deliberate spam, fabrication, and provider penalties are not possible to infer.

Activation: Demonstrated material contradiction in price, availability, identity, or another essential fact. Minor wording differences are S0. Do not claim fraud/penalty or choose the correct side without evidence.

Recommendation and validation: Present the exact visible/marked-up discrepancy and draft alignment after the correct value is established. Validate all representations in the same state. Do not guess whether markup or visible copy is stale.

## F1 Facts locked in images/canvas

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Inventory images, CSS images, canvas, SVG text, accessible names, adjacent captions, and DOM equivalents. Without vision/OCR, factual content inside pixels is not possible to determine. With it, record candidate image facts and search equivalents in the inspected page. “No equivalent found on this page” is scoped evidence, not a site-wide absence proof.

Activation: Verified essential image/canvas information lacks a usable equivalent for the target reader/extractor. Need content interpretation and scoped equivalent search. Decorative images are S0; unreadable pixels without OCR/vision evidence are U.

Recommendation and validation: Draft an HTML fact/table equivalent from an authoritative transcription or verified original data. OCR/vision output needs checking, especially digits/units. Validate full correspondence and page placement; without readable source content, do not manufacture the facts.

## F2 Alt-text quality

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Scripts can record alt presence, empty values, accessible names, roles, filenames, and surrounding text. Whether an image is informational and its alternative is adequate requires semantic judgment. Optional vision/LLM advice should cite the image and context. Do not fail decorative images, short accurate alts, or impose length/generic-word thresholds.

Activation: Semantic quality suggestions remain advisory under the original detector limits. A verified essential missing equivalent can be S3 under F1, once. Empty decorative alt is S0; no severity from length or generic-word regex.

Recommendation and validation: Draft context-specific alternative text when the image is visible, preserving empty alt for decorative cases and nearby equivalents. Review image purpose and accuracy. A deterministic length or keyword check cannot prove alt quality.

## F3 Audio/video transcript or captions

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Inspect track elements and `textTracks`, fetch declared caption files, verify nonempty timed cues, and inspect visible transcript links and accessible embedded-player state. Presence of a track tag alone is insufficient. Caption completeness, transcription accuracy, and absence in opaque players are not possible without media analysis/player access.

Activation: A known meaningful media unit lacks a verified required/appropriate textual alternative in the inspected state. S3 when essential content has no accessible equivalent. Opaque player state is U; transcript presence alone does not prove accuracy.

Recommendation and validation: Generate transcript/caption integration from an existing verified transcript; generating missing speech text requires audio and transcription capability. Check wording, speakers, timing, and player behavior. A language model must not guess unheard speech.

## F4 Real text in tables/PDFs

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: HTML: enumerate actual table/grid text and headers; do not assume missing `<table>` means pixels. PDF: optional parser extracts page text and character mappings. Report extractable text per page. Empty/garbled extraction can mean scans, encryption, or encoding issues; it does not prove a scanned document. OCR/rendering provides additional evidence.

Activation: Essential information is demonstrably unavailable to the target text reader and no equivalent exists in scope. Empty parser output alone is U, not a scan finding. Supplemental readable content with minor structure issues can be S2.

Recommendation and validation: Propose searchable text/semantic tables from verified document content; use OCR or original source data as needed. Validate characters, rows, units, and reading order. Empty extraction alone does not justify regenerating a supposedly scanned PDF.

## F5 PDF-only facts

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: With a PDF parser, extract identifiable facts and compare against associated HTML pages and observed crawl text, including unit normalization. Report “no HTML equivalent found in inspected pages.” Proving absence across the website, or that a PDF format causes lower AI visibility, is not possible from this audit.

Activation: A usable text PDF can be sufficient; HTML mirroring is optional. S2/S3 needs a demonstrated access/task problem with the current format. Never penalize all PDF-only content automatically.

Recommendation and validation: Draft a faithful HTML mirror from readable, verified PDF content, retaining citations and tables. Need a maintenance strategy and publication context. Verify equivalence; avoid producing an unmaintained duplicate with stale facts.

## G1 llms.txt present

Feasibility: Possible. Reference band: S1. Solution level: V.

Detection: Fetch `/llms.txt`, distinguish an actual text document from an HTML catch-all, and record content/status. Absence is not a defect. Presence is an inventory observation, not a demonstrated visibility bonus.

Activation: Optional experiment with unestablished benefit. No missing-file defect; it belongs after confirmed issues and can reasonably be S0/no action.

Recommendation and validation: Generate an optional curated text file using verified titles, descriptions, and public URLs. Validate links and factual text. Missing file needs no defect remedy and adding one has no guaranteed AI benefit.

## G2 llms.txt accurate and synchronized

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Parse explicitly supported Markdown links, resolve them, and compare linked page identities and availability. Reproducibly dead links can be reported. Sitemap membership is not required because the file may be curated. Description truth, exhaustive currency, and global completeness are not possible without additional evidence.

Activation: Correct reproducibly broken references or supported inaccurate descriptions in an existing file. Do not infer a need for sitemap parity or a large audience relying on this file.

Recommendation and validation: Repair exact links using verified equivalent destinations; change descriptions only from established facts. Need editorial intent before dropping inaccessible entries. Validate file links and descriptions; don't force it to mirror every sitemap entry.

## H1 Response latency

Feasibility: Possible. Reference band: S2. Solution level: C.

Detection: Measure request timing and browser Navigation Timing, documenting whether DNS/TLS/redirects/cache are included. Run a small repeated sample and report values and spread for the test environment. “Too slow for AI” and crawl-budget harm are not possible without an agreed budget or provider data. Do not call a timeout full-load time.

Activation: Controlled measurements exceed an established practical performance budget. With no agreed budget, report observations. Reproduced inability to obtain content may be S4 under the access failure; speed improvement alone does not prove engagement lift.

Recommendation and validation: Provide timing-specific diagnostic steps; select caching, infrastructure, or rendering remedies only when bottlenecks and constraints are known. Re-measure under controlled comparable conditions and check freshness. A slow request alone does not justify a particular infrastructure change.

## H2 Headings and landmarks

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Enumerate native and ARIA headings, levels, main/navigation landmarks, accessible names, and hidden state. Report structural facts. Skipped levels or missing HTML5 tags alone do not establish broken extraction or accessibility. Optional axe-core helps with specific supported accessibility rules; it is not an AI-discoverability score.

Activation: A supported concrete structure/accessibility issue hinders interpreting or navigating content. Missing tags or skipped headings alone do not establish it. Pure semantic polish is S1; subjective assessments are advisory.

Recommendation and validation: Draft semantic markup changes for the observed structure and intended hierarchy. Need source/layout context to preserve appearance and accessibility. Validate headings, landmarks, keyboard behavior, and responsive layout; don't reorder headings solely to satisfy a simplistic counter.

## H3 Mobile/desktop parity

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Render the same URL in controlled fresh desktop/mobile contexts; compare normalized main facts and accessible content after equivalent safe expansions. Exclude layout-only hiding and responsive menus. Report reproduced fact differences in tested states. Their intent and behavior on real crawler infrastructure remain not possible to establish.

Activation: Essential facts/functionality are demonstrably unavailable on an intended supported mobile state. Cosmetic differences are S0. Complete essential task/access failure can be S4; reflow and menus can legitimately differ.

Recommendation and validation: Specify parity for the exact missing essential mobile fact after confirming it should be available. Need responsive templates/styles to implement. Test multiple widths and accessible expansion; matching desktop pixels is not the goal.

