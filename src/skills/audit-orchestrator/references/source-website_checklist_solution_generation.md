# Customized solution generation for the website checklist

An LLM using this skill can propose website-specific recommendations for many checklist items. It cannot guarantee the correct solution to every item from a URL alone. The strongest design makes the evidence, allowed edits, and acceptance tests explicit, then uses the LLM to explain or draft within those boundaries.

Detection feasibility and solution feasibility are separate. Detecting `noindex` can be straightforward; deciding to remove it requires indexation intent. Conversely, objectively grading fluency is not reliable, but drafting a clearer version of an existing paragraph is feasible as editorial advice. The earlier 15 possible, 90 partial, 28 not possible, and one excluded counts describe detection, not guaranteed remediation.

This document covers the same 134 checklist IDs. It specifies proposed solution behavior; it does not implement a skill, audit a live domain, generate actual site-specific patches, or prove a measured accuracy rate.

## What correctness can mean

| Claim | What can establish it |
| --- | --- |
| The observed issue exists | Reproducible evidence and a correctly scoped detector. |
| The proposed change is appropriate | Evidence plus the applicable requirement, business intent, and relevant context. A detector alone may not supply these. |
| The output is syntactically valid | Parser, schema, compiler, or other deterministic validation within its supported scope. |
| The change fixes the tested behavior | Apply in a representative test environment and rerun the detector plus relevant regression tests. |
| The whole solution is factually and operationally correct | May require source-of-truth data, repository/configuration access, expert judgment, and broader tests. A URL rarely supplies all of these. |
| The change increases AI citations or conversions | Not established by this audit. Requires separate outcome measurement, with attribution limitations. |

Repeatability is not correctness: a program can return the same wrong answer every time. A fixed prompt or repeated LLM agreement cannot prove an answer correct. Deterministic validators can reject known errors and enforce bounded requirements, but a test passing does not establish facts the test cannot observe.

If a subset truly needs deterministic generation, use tested functions/templates to produce those outputs from validated inputs. Let the LLM choose among eligible proposals or explain them; do not let it override unmet preconditions. Unrestricted prose generation is not a substitute for a proof or a source of truth.

## Levels used in the item mapping

| Level | Meaning for a customized solution |
| --- | --- |
| V — Verifiable candidate | A narrow artifact or transformation can be generated from collected evidence and checked mechanically. This does not certify deployment, whole-site correctness, business intent, or outcome improvement. |
| C — Context required | The skill can propose a site-specific change or diagnostic plan, but correctness requires missing intent, authoritative data, implementation details, history, or access. Return the dependency explicitly; do not guess a final fix. |
| E — Editorial draft | A tailored rewrite or design suggestion is feasible. Semantic quality and suitability cannot be proven deterministically. Keep as optional advice and preserve verified meaning. |
| X — No supported solution | The requested state/claim is unavailable or this is a duplicate. Return a reason and any evidence that would unlock work. Do not invent a fix. |

Each level describes the narrow output named in its row. Even V requires a legitimate issue or explicitly desired improvement, complete evidence for that scope, and successful validation. A missing optional feature does not require a solution. A check may correctly return `no_change_needed`, `not_applicable`, or `insufficient_evidence`.

The mapping contains 16 V items, 81 C items, 34 E items, and 3 X items, totaling 134. These are design classifications, not measured accuracy estimates. The three X items are MISSING_EXPECTED_PROFILE, J7, and the duplicate J10. Some C items can become verifiable when the missing context is supplied; the counts are not a permanent limit on future capability.

## Minimum information the solution generator needs

Supply the actual evidence, not just a finding name or a screenshot:

- Exact affected URL, page type, entity/variant/locale, timestamp, source content, and verified locators.
- The detector's predicate, observed values, extraction completeness, and uncertainty.
- The relevant objective, if established: for example, which pages should be indexable and which bot uses are permitted. Unknown objectives stay unknown.
- The supported source of each fact, with a distinction between “the website states this” and “independently verified.” Repetition across the website does not prove truth.
- Known source code, CMS, server, CDN, and framework details only when actually available. Visible output does not reveal the responsible source file or configuration layer reliably.
- An allowed remedy type, its preconditions, and its acceptance/regression tests.

For URL-only operation, the default deliverable is an exact proposed content/markup change where evidence supports it, or a behavioral specification where implementation details are unknown. A CSS selector identifies an observed element, not its repository source file. A framework fingerprint does not authorize inventing a patch path or server directive.

## Generation and validation procedure

1. Collect and validate the finding. If a wall, timeout, or incomplete extraction caused the apparent absence, stop that branch.
2. Decide whether a change is warranted. Keep optional enrichment separate from defects. Require policy/intent before changing indexation, access, canonicals, or externally asserted facts.
3. Select a vetted remedy whose preconditions are satisfied. If none qualifies, return a precise diagnostic step or missing-data request.
4. Generate the smallest supported change. Copy verified facts exactly where possible. Preserve entities, currencies, variants, qualifiers, dates, units, quotation attribution, and exceptions.
5. Validate syntax, evidence references, allowed scope, and consistency. For mechanical transformations, construct output from verified source spans or validated field values. Free-form paraphrases need semantic review; string matching alone cannot certify meaning.
6. Check the proposed change against other findings. For example, a bot-access edit must preserve intentional training restrictions; a new FAQ must not contradict shipping policy; a canonical proposal must preserve meaningful variants.
7. When a representative test environment is available, apply the candidate there and run behavior and regression checks. An offline mock can validate a snippet, but cannot prove real server, CDN, hydration, or deployment behavior.
8. Return the candidate, verified scope, remaining assumptions, and test results. If it has not been applied and tested, label it a proposal, not “fixed” or “verified on site.”

Use statuses such as `no_change_needed`, `validated_candidate`, `conditional_proposal`, `editorial_draft`, and `insufficient_evidence`. A candidate can be validated for JSON syntax while remaining conditional on the truth of its price. Represent both dimensions rather than compressing everything into one confidence score.

No automatic publication is implied. The skill's present scope is read-only analysis and recommendation.

## Technical solution mapping

### A Crawl access

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| A1 | C | Propose a corrected robots response/file only for an observed problem. Missing robots alone needs no repair. Policy is required to generate intended rules; server details are required for a deployable fix. Validate parsing, response behavior, and the effective permission matrix. |
| A2 | C | Draft the smallest rule change for the exact blocked path and named bot after crawl intent is established. Preserve other restrictions. Run before/after rule tests including exceptions, private paths, and other bot groups; do not replace the file with “allow all.” |
| A3 | C | Generate a policy-specific per-bot diff and resulting permission matrix. Need the owner's allowed uses and provider-specific semantics. Validate all affected groups; do not promise actual provider access or citation eligibility from robots rules alone. |
| A4 | C | Propose measurement or rate-limit tuning for the specific honored directive. Need server capacity and actual crawler activity before choosing a value. Validate load and crawl behavior; never invent an optimal delay from page count. |
| A5 | V | Generate a `Sitemap:` line for an already verified appropriate sitemap, as optional enrichment. Preserve existing declarations. Parse the modified file and re-fetch the destination; no inferred sitemap URL or promise of indexing. |

### B Indexation

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| B1 | C | Propose removal of the exact effective noindex directive only when indexing is intended. Preserve unrelated directives. Need template/CMS access for the real patch; retest source and rendered meta plus headers so another noindex does not remain. |
| B2 | C | Propose changing the specific X-Robots-Tag source for the affected responses. Need intent and the responsible server/CDN/application layer. Verify final GET headers, provider scope, and unaffected restricted pages; HTML edits alone cannot fix a header. |
| B3 | C | Draft one canonical target after preferred URL and duplicate/variant semantics are established. Align contradictory declarations without flattening real distinctions. Verify target reachability and consistent canonical signals; the crawler's ultimate canonical choice cannot be guaranteed. |
| B4 | C | For each broken reference, propose a verified equivalent destination if one exists. Otherwise offer restore, remove-reference, or retained-gone options conditional on content intent. Status alone does not choose the right remedy. Test links, redirect loops, and final content identity. |
| B5 | C | Describe the exact observed access barrier and propose an appropriately scoped public-content exception after intent/security policy is known. Need origin/CDN/auth configuration. Verify access and protected-route regressions; do not recommend globally disabling authentication or bot protection. |

### C Rendering

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| C1 | C | Identify exact essential content missing from source and specify server-delivered availability if that consumer requires it. Need application architecture for implementation. Retest source facts and hydration; do not add filler merely to pass a word-count threshold. |
| C2 | C | Specify the exact fact and channel to expose in initial HTML, using the existing authoritative data path. Need template/data lifecycle details to avoid stale hardcoded values. Verify variant/currency consistency in raw and rendered states. |
| C3 | C | Propose stable deep-link behavior for observed route failures. Need routing and URL compatibility requirements before selecting paths or redirects. Test fresh load, reload, server response, and legacy links; do not rewrite valid fragment anchors. |
| C4 | C | Offer SSR/static-generation/server-content options matched to known constraints; choose a concrete implementation only with confirmed framework and data needs. Verify initial content, freshness, and hydration in the actual application. |
| C5 | C | Give a resource-specific investigation using the measured timeline. Recommend deferral/caching/render changes only after establishing causality. Validate content appearance and interactions under comparable conditions; do not fabricate a provider timeout. |

### D Sitemaps

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| D1 | V | Generate a structurally valid replacement for a supplied parseable URL inventory or an unambiguous escaping/namespace correction. If URLs are unrecoverable, request the inventory. Validate XML, entries, limits, and preserved data; serving/configuration remains conditional. |
| D2 | C | Draft proposed additions from inspected URLs, with reasons and exclusions. Need authoritative inventory and canonical/indexation intent to call it complete or correct. Validate candidate membership and URLs; omission alone is not a defect. |
| D3 | C | Propose deriving lastmod from meaningful source edits, or omitting unreliable optional dates. Need edit history or CMS events to populate real timestamps. Validate dates against those events; never set everything to the audit date. |
| D4 | C | Propose specific important-page additions or access changes only after importance and eligibility are established. Test sitemap inclusion and access. Do not infer business priority from a URL path alone. |
| D5 | V | Partition an available, approved URL set into valid size/count-bounded files and generate an index. Verify no lost/duplicated entries and valid XML. Hosting paths must be supplied/validated; adding an index is unnecessary when existing files already comply. |

### E Structured data

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| E1 | V | Offer optional JSON-LD generated from explicit supported page facts. Omit unavailable fields. Validate JSON, supported type/property rules, and fact bindings; do not claim schema absence made the page invisible. |
| E2 | V | Generate an entity node from established name/URL/logo/profile facts, preserving stable IDs and distinctions between brand and legal organization. Validate references and types. Unsupported ownership/profile claims must be omitted or held for confirmation. |
| E3 | C | Generate Product/Offer markup only from a known source for price, currency, availability, and variant. URL snapshots can support a draft but not a durable commerce implementation. Validate data bindings and variants; never invent stock or required commercial values. |
| E4 | V | Draft an optional supported schema representation of already visible FAQ, article, or procedural content. Preserve exact meanings and answer scope. Validate correspondence and type rules; feature eligibility and benefits are separate. |
| E5 | V | Repair unambiguous syntax/serialization defects while preserving known values, then parse and validate the supported subset. Ambiguous truncated text or conflicting semantic repairs require context. A parser passing cannot certify truth or all provider rules. |
| E6 | C | Deduplicate proven identical nodes mechanically; choose a value for contradictory nodes only with a source of truth. Preserve legitimate multiple entities/offers. Validate graph references and same-context claims; do not assume visible text always wins. |
| E7 | C | Present the exact visible/marked-up discrepancy and draft alignment after the correct value is established. Validate all representations in the same state. Do not guess whether markup or visible copy is stale. |

### F Representation

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| F1 | C | Draft an HTML fact/table equivalent from an authoritative transcription or verified original data. OCR/vision output needs checking, especially digits/units. Validate full correspondence and page placement; without readable source content, do not manufacture the facts. |
| F2 | E | Draft context-specific alternative text when the image is visible, preserving empty alt for decorative cases and nearby equivalents. Review image purpose and accuracy. A deterministic length or keyword check cannot prove alt quality. |
| F3 | C | Generate transcript/caption integration from an existing verified transcript; generating missing speech text requires audio and transcription capability. Check wording, speakers, timing, and player behavior. A language model must not guess unheard speech. |
| F4 | C | Propose searchable text/semantic tables from verified document content; use OCR or original source data as needed. Validate characters, rows, units, and reading order. Empty extraction alone does not justify regenerating a supposedly scanned PDF. |
| F5 | C | Draft a faithful HTML mirror from readable, verified PDF content, retaining citations and tables. Need a maintenance strategy and publication context. Verify equivalence; avoid producing an unmaintained duplicate with stale facts. |

### G Optional llms.txt

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| G1 | V | Generate an optional curated text file using verified titles, descriptions, and public URLs. Validate links and factual text. Missing file needs no defect remedy and adding one has no guaranteed AI benefit. |
| G2 | C | Repair exact links using verified equivalent destinations; change descriptions only from established facts. Need editorial intent before dropping inaccessible entries. Validate file links and descriptions; don't force it to mirror every sitemap entry. |

### H Performance and structure

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| H1 | C | Provide timing-specific diagnostic steps; select caching, infrastructure, or rendering remedies only when bottlenecks and constraints are known. Re-measure under controlled comparable conditions and check freshness. A slow request alone does not justify a particular infrastructure change. |
| H2 | C | Draft semantic markup changes for the observed structure and intended hierarchy. Need source/layout context to preserve appearance and accessibility. Validate headings, landmarks, keyboard behavior, and responsive layout; don't reorder headings solely to satisfy a simplistic counter. |
| H3 | C | Specify parity for the exact missing essential mobile fact after confirming it should be available. Need responsive templates/styles to implement. Test multiple widths and accessible expansion; matching desktop pixels is not the goal. |

## Common content solution mapping

Content drafting can use the existing LLM; an extra model dependency is unnecessary. The strongest factual guarantee is to reuse verified spans/values with a fixed structure. Rewriting changes entailment risk: even preserving every number can turn “up to 30%” into “30%” or imply causation. Qualifier preservation and semantic review matter.

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| N1 | E | Rewrite a specific context-dependent answer using an established antecedent. Preserve caveats and scope. If the referent is ambiguous, request context instead; review meaning in isolation and within the page. |
| N2 | E | Move the supported direct answer earlier and retain supporting context. Verify the moved span/qualifiers; editorial review decides whether the new order suits the section. No mandatory first-two-sentence rule. |
| N3 | C | Replace a vague statement only with an existing verified metric and its scope/date. If absent, suggest the exact measurement needed or a restrained qualitative rewrite. Never generate a number to satisfy the checklist. |
| N4 | C | Attach an available supporting source to the exact claim, or identify the claim needing evidence. Verify source entailment, not just link existence. Missing evidence means qualify/remove only with editorial approval, not fabricate a citation. |
| N5 | C | Select a genuine available quotation with attribution and context. Without an authenticated source, request one or leave the page unchanged. Never invent an expert/customer statement or make one up in a real person's voice. |
| N6 | E | Draft a fluent revision of the actual passage. Check factual/qualifier preservation and language-specific readability; human editorial judgment remains necessary for quality. |
| N7 | E | Make supported statements direct while retaining justified uncertainty. Review for increased certainty, causal claims, or unsupported authority. Do not delete hedging mechanically. |
| N8 | E | Add concise definitions from supported domain context and simplify redundant jargon. Need audience assumptions stated explicitly; unfamiliar or version-specific terms may require authoritative references. |
| N9 | C | Correct terminology using a relevant authoritative definition and version/context. Without that evidence, offer a review question, not a confident technical correction. |
| N10 | E | Rewrite the specific repetitive passage naturally while preserving identity and query intent. Compare retained facts; do not remove necessary product/API names to hit a density target. |
| N11 | V | Reuse E1–E5 generation for supported optional schema. Validate the same artifact once and reference all related checks; no duplicate “fix” for the same markup. |
| N12 | C | Draft consistent statements only after resolving conflicting entity facts. Preserve legitimate alias/location differences. Validate all affected text; do not propagate the most frequent value as assumed truth. |
| N13 | E | Draft questions and self-contained answers from existing supported policies/facts; include citations to each answer's basis. Omit unanswerable questions and avoid a word-count quota. Optional markup is validated separately. |
| N14 | C | Propose exact stale-claim/source updates only with current authoritative evidence. Need actual revision history for update dates. Never refresh dates cosmetically or assume older content is wrong. |
| N15 | C | Format a byline/credential block from confirmed author information. If missing, request it. Do not invent a reviewer, degree, professional role, or attribution. |

## E commerce and retail solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| EC1 | C | Build a product-spec block from verified variant data, units, and delivery policies. Unknown dimensions, review percentages, or shipping windows require owner data. Validate every field against its source. |
| EC2 | C | Add the actual test/source supporting a comparison, with method/scope where known. If absent, propose a noncomparative draft or evidence request. Do not manufacture lab validation. |
| EC3 | C | Format verified customer testimonials and appropriate optional Review markup. Need real quote and attribution. Validate text and product association; source presence alone does not prove authenticity. |
| EC4 | E | Rewrite the exact marketing passage around supported specifications without unsupported superiority. Review meaning and brand tone; no deterministic hype score. |
| EC5 | E | Draft product-specific FAQ answers from verified sizing, compatibility, and returns information. Missing policy details remain unanswered. Review factual completeness and preserve regional exceptions. |
| EC6 | C | Draft applicable Product markup from authoritative commerce fields. Omit unavailable reviews/media. Verify live data bindings and same-variant consistency instead of hardcoding an audit snapshot. |
| EC7 | C | Produce a comparison table only from compatible, sourced product attributes. Unknown competitor values remain unknown. Verify model/version/date and units; factual cells alone cannot prove fairness. |
| EC8 | E | Rewrite the actual title/description to reduce unnecessary repetition while retaining model, variant, and important specifications. Validate factual preservation and editorial suitability. |
| EC9 | C | Propose synchronization between commerce source, visible price/stock, and markup. Need the correct backend state. Test variants, locale, promotions, and update behavior; do not pick a conflicting price by intuition. |

## Business and corporate solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| BC1 | E | Draft a concise identity statement from observed supported company/service facts and propose placement. Preserve legal/brand distinctions. Review clarity and rendered fit; identical homepage/About wording is unnecessary. |
| BC2 | C | Build an evidence-based scale/impact block from disclosed metrics and dates. Request missing verified metrics; never invent clients, revenue, or saved time. |
| BC3 | C | Organize verified press/certification/case-study references. Need actual endorsement/award evidence before presenting claims. Validate links, entities, dates, and any usage permissions relevant to publication. |
| BC4 | C | Select and format an existing leadership quotation. Need genuine source and attribution; no invented founder quote. Verify wording and context. |
| BC5 | C | Draft platform-specific descriptions from resolved company facts, allowing taxonomy and length differences. Need accessible profiles and the correct current facts. Review before any external update. |
| BC6 | V | Generate supported Organization/sameAs markup from verified identity links, reusing E2. Validate URLs and graph identity; do not mark similar-name accounts as official. |
| BC7 | E | Restructure actual service content around what it is, audience, and included scope. Preserve exclusions. Missing service terms require context, not creative completion. |
| BC8 | E | Draft service questions and answers using established pricing/timeline/scope information. Explicitly omit unknown contractual terms; verify against cited service policies. |

## Portfolio and personal solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| PP1 | C | Present verified project outcomes clearly. Ask for underlying result data when absent; do not invent conversion gains or attribute a team's result solely to the individual. |
| PP2 | C | Format genuine testimonials with approved attribution. Need actual quotes/roles; never manufacture a client reference. |
| PP3 | E | Restructure existing project evidence as problem, approach, and result. Unknown outcomes stay omitted. Review that authorship and causal claims are preserved. |
| PP4 | C | Suggest terminology grounded in actual project methods and discipline references. Need evidence that tools/methods were used; don't add fashionable skills to imply expertise. |
| PP5 | V | Generate Person markup from supported name, role, and verified profile URLs. Validate fields and identity. Unknown credentials or roles are omitted. |
| PP6 | E | Condense the actual biography while retaining meaningful credentials, dates, and voice. Review omitted context; no universal length target. |
| PP7 | C | Add verified award/publication/talk references or repair links to confirmed originals. Without recognition evidence, return no supported addition. |

## Blogs and news solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| BN1 | C | Add claim-specific source attribution using sources that actually substantiate the statement. Need reporting/source material where absent. A valid URL is not an entailment check. |
| BN2 | C | Use a genuine relevant source quotation with faithful context. If no source is available, request one; do not fabricate interviews or expert reactions. |
| BN3 | C | Replace trend language with supported metric, baseline, interval, and source. Otherwise draft less assertive wording without a fabricated statistic. |
| BN4 | C | Align visible byline/dates and Article fields from authoritative publishing metadata. Can format a draft from site claims; need correct author/revision records to resolve conflicts. |
| BN5 | E | Revise specific sentences/transitions for readability while preserving reporting detail and attribution. Semantic/editorial review remains required. |
| BN6 | E | Make prose direct without overstating developing facts or uncertainty. Compare certainty and attribution before/after, not just word count. |
| BN7 | E | Insert brief audience-appropriate definitions from supported references and preserve technical meaning. Unclear terms require a source rather than guessed explanations. |
| BN8 | E | Rewrite repetitive headings to describe the actual sections. Preserve section intent and factual qualifiers; editorial quality is not mechanically guaranteed. |
| BN9 | C | Produce an article-specific update plan from verified broken/stale references. Need current authoritative information and revision policy for actual updates; do not simply change the date. |

## SaaS and web application solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| SA1 | E | Explain the feature's supported capability in clear terms; include outcomes only if evidenced. Verify plan/version limits and avoid inventing ROI. |
| SA2 | C | Add verified benchmark/review attribution and dated score/count. Need source evidence and comparable benchmark conditions; do not invent independent validation. |
| SA3 | C | Select an authentic result-specific customer quote when available. Do not turn generic praise into an invented quantified outcome. Verify exact quotation and context. |
| SA4 | C | Correct documentation from version-matched specifications or repository behavior. Need technical source/access for reliable fixes; validate examples separately where executable. |
| SA5 | C | Generate a comparison from sourced, same-plan/version attributes. Unknown competitor behavior requires research. Verify context and avoid blanket superiority claims. |
| SA6 | V | Generate supported optional schema from established software/page facts, with unavailable values omitted. Validate graph/content correspondence; dynamic pricing and unresolved facts move those fields to C. |
| SA7 | E | Draft purpose-appropriate marketing/docs revisions using the actual content. Retain literal technical constraints in docs and supported facts in marketing. Review style semantically. |
| SA8 | E | Rewrite specific feature headings around documented user capabilities without redundant terms. Verify that support/availability claims remain unchanged. |
| SA9 | C | Format a dated changelog from real release records or propose a publication structure. Need actual versions/dates/changes; no invented maintenance history. |

## Social and community solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| SC1 | C | Clarify policy copy using established policy decisions and verified statistical sources. Need owner/legal policy context for substantive changes; do not create new enforcement promises. |
| SC2 | C | Format genuine member/moderator quotes with context and attribution. Need actual source material; no fabricated community voices. |
| SC3 | C | Present disclosed community metrics with active/registered definitions and time windows. Need authoritative counts; do not infer them from visible pages or follower estimates. |
| SC4 | E | Draft help-center answers from verified product behavior/policies. Unknown workflow steps require testing/context. Review exact procedural correctness; optional FAQ schema can be validated separately. |
| SC5 | C | Draft consistent platform/app descriptions from resolved developer/brand facts. Need current listing evidence; preserve legitimate app-versus-company distinctions. |
| SC6 | E | Simplify actual landing-page repetition while preserving platform scope and capabilities. Editorial review decides clarity; no deterministic keyword target. |
| SC7 | E | Revise trust/safety wording for precision while preserving policy obligations and exceptions. Substantive policy changes require owner context; tone does not prove operational trustworthiness. |

## Education and LMS solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| ED1 | C | Create course-outcome/duration blocks from approved syllabus and cohort data. Need true metrics for rates/results. Validate learner level, prerequisites, and definitions. |
| ED2 | C | Add actual curriculum references and instructor qualifications. Need source/credential evidence; no invented textbooks, research, or accreditation. |
| ED3 | C | Format authentic instructor/learner quotations and outcomes. Verify source and context; do not create employment or salary success stories. |
| ED4 | E | Draft course FAQs from verified prerequisites, format, certification, and refund policy. Unknown promises remain omitted; markup is optional. |
| ED5 | C | Define/correct subject terms using authoritative curriculum material and learner level. Need subject expertise when ambiguous. Verify conceptual accuracy rather than a terminology-density metric. |
| ED6 | V | Generate optional HowTo markup from an existing verified sequence of steps. Preserve conditions, order, and warnings; validate supported structure/content. Do not invent steps or promise a search feature. |
| ED7 | E | Simplify actual instructional prose while preserving technical rigor and necessary caveats. Review with intended learner level; short sentences alone do not ensure accuracy. |
| ED8 | E | Rewrite course titles/descriptions naturally, retaining subject, level, format, and true scope. Review that distinct courses remain distinguishable. |
| ED9 | C | Draft updates from an approved current syllabus/version history. Without it, specify the missing curriculum records; never infer updated prerequisites from generic subject knowledge. |

## Media and entertainment solution mapping

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| ME1 | C | Build a metadata block from verified work/edition runtime, release, awards, and rating data. Need actual sources for missing metadata; do not invent popularity figures. |
| ME2 | C | Attribute critic scores to the correct source, scale, edition, and date. Need authoritative score evidence to resolve conflicts or refresh values. |
| ME3 | C | Add genuine critic/cast/interview quotes with context. Need original source; do not fabricate reactions or transform paraphrases into direct quotes. |
| ME4 | V | Generate applicable Movie/TVSeries/VideoObject markup from supported metadata with correct entity distinctions. Validate properties and references; absent or disputed metadata is not filled speculatively. |
| ME5 | E | Rewrite the supplied synopsis for clarity without inventing plot, reception, or superlatives. Review accuracy, spoiler scope, and editorial voice. |
| ME6 | E | Draft practical answers from supported work/territory facts. Availability and schedules require current sources; unknown answers are omitted rather than guessed. |
| ME7 | E | Rewrite metadata naturally while preserving exact title, edition, episode, and access conditions. Verify no unsupported “free” or availability claim is introduced. |
| ME8 | C | Propose synchronization with authoritative schedule/licensing/status data. Need region/time-specific sources. Test consistent presentation; website snapshots alone cannot establish current rights. |

## Off site solutions

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| PROFILE_DATA_MISMATCH | C | Present both values and draft platform-specific correction only after identity and the true field value are established. Need a source of truth, not just majority agreement. External editing remains a separate authorized action. |
| UNDECLARED_PROFILE_FOUND | V | Propose an optional sameAs/profile link for a verified identity match found by available discovery. Validate URL and entity association. Missing linkage is not a defect, and a search snippet alone cannot validate the profile. |
| STALE_THIRD_PARTY_PROFILE | C | Draft an update backed by dated authoritative change evidence. Need platform context and correct current facts. Do not assume the first-party page is newer or the business controls the profile. |
| MISSING_EXPECTED_PROFILE | X | No missing-profile remedy can be asserted from an unsuccessful search. Return the search scope and an optional owner verification step. Registration advice requires established eligibility and owner intent, not the claimed absence. |

## Bridge and engagement solutions

| ID | Level | Customized output and correctness requirement |
| --- | --- | --- |
| I1 | C | Specify working fresh-load/deep-link behavior for the exact observed content unit. Need routing/canonical compatibility context to implement. Test reload and stable entity identity; keep meaningful query URLs. |
| I2 | C | Propose handling the exact reproducibly problematic inert parameter without dropping meaningful parameters. Need routing/security context. Test baseline/probe/baseline, canonical behavior, and existing query semantics. |
| J1 | E | Draft a clearer identity statement and placement proposal from supported facts and screenshots. Review responsive rendering and comprehension; can't prove “understood in seconds.” |
| J2 | C | Propose a verified parent/category/home route and navigation affordance using known information architecture. Need intent before inventing a hierarchy. Test destinations, keyboard access, and mobile behavior. |
| J3 | E | Suggest a placement/layout revision for an established important fact. Validate visibility/occlusion at tested widths; business importance and improved comprehension remain judgments. |
| J4 | C | Suggest removing an observed unnecessary step only after workflow requirements are known. Need actual flow evidence to promise reduced steps. Do not assume login or consent is dispensable; no end-to-end claims from a landing page. |
| J5 | C | Propose presentation of real existing reviews, case studies, or credentials appropriate to the site. Need authenticated assets/claims. Never generate fake trust signals, testimonials, or conversion predictions. |
| J6 | C | Propose reducing the specific observed obstruction after overlay purpose and consent/access requirements are known. Validate dismissal, accessibility, and unaffected functions. Do not recommend deleting necessary consent or authentication steps on appearance alone. |
| J7 | X | No site-specific post-completion solution is supported without the actual state/flow. Request supplied recordings or an authorized test environment. Generic best practices are not a verified remedy. |
| J8 | C | Propose alternatives using verified relevant inventory or known category/support routes. Need current availability for substitute claims. Test safe destinations; don't fabricate comparable products or infer user intent. |
| J9 | V | Draft a 404 body with verified home/category/support links, plus accessible layout markup. Validate links and markup in a test page. Preserving actual 404 status requires server integration and retesting; search behavior cannot be certified without testing it. |
| J10 | X | Reuse H1/H3 recommendations when warranted. Do not generate a duplicate speed remedy or claim engagement improvement from timing measurements alone. |

## Examples of strong and weak outputs

**Malformed JSON-LD with an unambiguous trailing comma:** a tested serializer can produce a valid candidate and a parser can confirm it. Preserve the original values and compare the resulting intended object. If the document is truncated and values are unknown, stop rather than completing it from model knowledge.

**Price missing from markup:** if the page explicitly states a price, an example can use that value with its currency and variant context. A durable production fix should bind markup and visible content to the same authoritative commerce source. The URL alone does not identify that source or guarantee tomorrow's price.

**Noindex present:** the correct response is conditional on whether indexing is intended. “Remove noindex” is not universally right. Different crawl and indexing controls serve different purposes and can interact. [Google robots guidance](https://developers.google.com/search/docs/crawling-indexing/robots/intro).

**Canonical points to another URL:** the generator must not automatically switch to self-canonical. Duplicate and similar pages may intentionally identify a preferred version. Establish the intended target first. [Google canonical guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).

**No expert quote or conversion statistic:** if none is supported, the correct output is an evidence request or no change. The model must not fill this gap creatively.

**Missing optional markup:** an enrichment draft is reasonable when it represents actual content. Structured data correctness and rich-result eligibility remain separate, and correct markup does not guarantee display. [Google structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies). Do not promise AI visibility from adding schema or llms.txt; Google's AI features do not require special AI markup/files. [Google AI features guidance](https://developers.google.com/search/docs/appearance/ai-features).

## Recommended output record

Each checklist item should return one disposition rather than being forced to return a fix. A useful solution record contains:

```json
{
  "check_id": "E5",
  "disposition": "validated_candidate",
  "affected_url": "actual inspected URL",
  "finding_evidence_ids": ["actual stored evidence ID"],
  "remedy_id": "supported_json_serialization_repair",
  "preconditions": ["specific unambiguous repair established"],
  "proposed_change": "exact candidate or attached diff",
  "fact_bindings": ["source values retained with provenance"],
  "validation": {
    "syntax": "record actual result",
    "value_preservation": "record actual result",
    "business_truth": "not established by syntax validation",
    "integration": "not tested unless actually tested"
  },
  "missing_context": [],
  "expected_effect": "repairs the demonstrated parsing error",
  "outcome_guarantee": "none"
}
```

For facts not yet supplied, use `missing_context` rather than realistic-looking invented placeholders inside ready-to-publish content. If a template intentionally has placeholders, make them explicit and have the validator reject it as a final artifact until populated.

## What to build for high correctness

Build a registry of vetted remedies with preconditions, allowed inputs, supported versions, counterexamples, and acceptance tests. Use code generation only where the implementation environment is known. Validate evidence bindings before allowing even a well-formed recommendation into the final report.

For testing, evaluate detection precision and recommendation correctness separately. Include intentional noindex, valid external canonicals, product variants, ambiguous conflicting prices, legitimate empty alts, necessary consent dialogs, absent business metrics, and inaccessible external sources. Check both harmful changes and fabricated facts. Measure abstention and coverage as well as correctness; do not hide uncertain cases by excluding them from reported totals.

The practical target is: every issued recommendation is scoped, evidence-backed, and tested to the extent claimed; unsupported fixes are withheld. The skill can always return a result for each checklist item, but it should not always return a change.
