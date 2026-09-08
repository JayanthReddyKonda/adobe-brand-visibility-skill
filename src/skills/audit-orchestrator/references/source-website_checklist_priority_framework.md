# Severity and implementation priority for GEO and engagement

This framework labels all 134 items from the supplied checklist and defines how a later skill should order justified recommendations. It combines potential impact with implementation difficulty while preserving the earlier evidence and correctness requirements.

The labels are product prioritization judgments, not experimentally measured uplift estimates. We can place demonstrated access and task blockers above optional polish. We cannot know from a checklist alone which change will produce the largest traffic or conversion gain on every website. An audit should promise evidence-backed opportunities and fixes, not all changes that will certainly boost both outcomes.

## Severity scale

Severity describes the consequence of an established problem within its affected scope. It does not describe how easy the change is. Optional opportunities use the same planning bands but are explicitly marked advisory rather than called defects.

| Band | Label | Qualification |
| --- | --- | --- |
| S4 | Critical blocker | A demonstrated failure prevents the intended crawler from accessing/indexing a target page, or prevents a user from accessing required content/completing an essential observed task. Name the consumer and scope; one page is not automatically the whole site. |
| S3 | High | A demonstrated material problem prevents reliable extraction or an informed user decision, gives materially conflicting essential facts, or substantially obstructs a supported primary task. No speculative conversion/traffic claim is needed. |
| S2 | Medium | A concrete local issue reduces usable structure, discovery, answer coverage, or recovery while the main content/task remains available. |
| S1 | Low or optional | Enrichment, editorial polish, redundancy cleanup, or a weakly evidenced opportunity. No demonstrated material access/task failure. Optional absence is not a defect. |
| S0 | No change warranted | The observed condition is acceptable, intentional, inapplicable, already handled, or duplicated. It receives no implementation priority. |
| U | Unassessable | Required evidence, intent, or state is missing. This is not S0, not a pass, and not a low-severity defect. It goes to investigation or remains not possible. |

The tables assign a **reference band for the narrowly described condition**, not an unconditional severity to every page where the check runs. A4, D3, ED9, J7, and some profile checks are U under the URL-only baseline; their rows explain what could make them assessable later. Other checks can produce a supported narrower finding even if their full original wording was not reliably detectable.

The catalogue contains 7 S4, 23 S3, 51 S2, 46 S1, 1 S0, and 6 U entries, totaling 134. These are reference classifications, not counts of problems on any website. The accompanying `website_checklist_severity_catalogue.json` contains the same IDs, bands, benefit areas, and activation conditions for later skill integration; actual severity, difficulty, and priority are deliberately null until a real finding is evaluated.

For example: B1 can be S4 when an intended indexed landing page has an effective noindex. The same directive on an intentionally private/account page is S0. If intent is unknown, report the directive and use U for remediation severity. Do not automatically remove it or assign S4 because a meta tag exists.

## Evidence required before assigning an active priority

Keep these fields separate:

- `reference_band`: the catalogue label below.
- `actual_band`: the band justified for this particular finding, or U/S0.
- `finding_kind`: confirmed problem, editorial opportunity, informational observation, or investigation.
- `benefit_area`: GEO, engagement, or both; this describes a plausible mechanism, not guaranteed gains.
- `affected_scope`: exact URLs, entities, consumers, devices, and observed states.
- `remedy_readiness`: ready to propose, needs facts/intent/source access, or not possible.

A high-impact but unconfirmed hypothesis belongs in an investigation queue. An observed serious issue with no known safe remedy stays visible as a serious issue, but is not presented as a ready implementation task. Difficulty cannot compensate for missing evidence. No confidence percentage supplied by the LLM can satisfy an unmet precondition.

Confirmed problems and advisory opportunities should be displayed separately. An advisory item can use an S2 planning band for a useful content experiment without being misrepresented as a detected medium-severity defect. Never put an optional llms.txt addition or speculative quote recommendation ahead of confirmed blockers because it is easy.

## Grounding for the ordering

Google's technical eligibility requirements include crawl access, a successful response, and indexable content. Its AI features also require an indexed page eligible for a snippet; satisfying these conditions does not guarantee serving. This supports prioritizing applicable access failures over markup polish for those consumers. It does not prove identical behavior for every AI product. [Google technical requirements](https://developers.google.com/search/docs/essentials/technical), [Google AI features guidance](https://developers.google.com/search/docs/appearance/ai-features).

Google says special AI files or schema are not prerequisites for its AI features. Missing optional schema/llms.txt therefore does not justify a critical label. [Google AI features guidance](https://developers.google.com/search/docs/appearance/ai-features).

Intrusive interstitials can obscure content; Google distinguishes intrusive experiences from required dialogs. W3C identifies keyboard traps as barriers to navigating content. These support evaluating actual obstruction and recoverability rather than failing every popup or assuming its removal increases conversions. [Google interstitial guidance](https://developers.google.com/search/docs/appearance/avoid-intrusive-interstitials), [W3C keyboard trap guidance](https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap.html).

The exact S1–S4 assignments and ranking arithmetic below are our proposed policy, not numbers prescribed by these sources.

## Technical checklist severity

Benefit-area codes: G = GEO, E = engagement, B = both. B does not receive twice the score. For G, state the actual consumer or extraction mode; robots policies, indexing directives, and raw HTML affect different systems differently.

### A Crawl access

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| A1 robots response and parsing | S4 | G | Use S4 only for an established robots response/rule failure that prevents the intended consumer from crawling target content. Mere file absence, harmless syntax debris, or a 404 is not this condition; usually S0. Unknown consumer behavior is U. |
| A2 Blanket disallow | S4 | G | Effective rules prohibit an intended retrieval/search consumer from target pages. Confirm URL matching, exceptions, and intent. Legitimate restrictions are S0; training-policy choices alone are not a GEO defect. |
| A3 Per-bot permissions | S4 | G | An established desired search/retrieval use is effectively prohibited for the scoped URLs. Report the affected product/use, not universal invisibility. A permission matrix with no demonstrated undesired restriction is informational; unknown policy is U. |
| A4 Crawl-delay starvation | U | G | URL-only evidence cannot establish starvation or an appropriate limit. Keep the parsed delay informational. Provider/server evidence of material constrained discovery could support S2/S3; do not assign high severity from the number alone. |
| A5 Sitemap declaration | S1 | G | Adding a verified appropriate declaration is optional discovery assistance. Missing declaration alone is not a defect and may be S0. A broken declared sitemap is assessed under D1 once, not escalated here. |

### B Indexation and access

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| B1 Meta noindex | S4 | G | An applicable effective directive excludes a page confirmed to be intended for the target index. Unknown indexation intent is U; intentional exclusion is S0. Do not generalize to all direct-fetch AI uses. |
| B2 Header noindex | S4 | G | Same as B1 for the actual response/header scope. This can stop intended index eligibility; fix the responsible layer. Deduplicate simultaneous meta/header manifestations into one exclusion issue where appropriate. |
| B3 Canonical correctness | S3 | G | Conflicting/broken canonical declarations or an established wrong target undermine intended URL identity. Non-self or cross-domain canonicals alone are S0/U. A separate inaccessible target is assessed under B4, not assumed from the canonical. |
| B4 Status and redirect failures | S4 | B | A reproducible error/loop prevents access to a scoped intended target. For nonessential broken references with alternatives, use S2; harmless functioning redirects are S0. Checker-specific blocks require scope/intent qualification. |
| B5 Login and challenge walls | S4 | B | A wall demonstrably blocks intended public content in the tested consumer/session. Confirm intended access and preserve necessary protections. A vendor script, brief usable challenge, or intentional account wall is not automatically critical. |

### C Rendering

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| C1 Source/rendered content gap | S3 | G | Essential content demonstrably unavailable to an established source-only consumer while available after rendering. Word-count differences alone are S0. Full target access failure may be S4 with consumer evidence; do not assume all AI systems omit JavaScript. |
| C2 Essential fact requires JavaScript | S3 | G | A decision-critical fact is unavailable through channels supported by the target consumer. A price present in supported JSON-LD is not absent. Minor text differences are S1/S0; unknown consumer capabilities are U. |
| C3 Broken deep links/hash routing | S3 | B | Direct access to an observed content unit loses its identity or requires unrelated navigation. Escalate to S4 if intended access is impossible. Working hash anchors and query-based routes are S0. |
| C4 Server-rendered content/fallback | S3 | G | Use the demonstrated essential-content gap from C1/C2, not framework/SSR absence itself. Often the same issue: merge recommendations. A complete usable page built without SSR has no defect. |
| C5 Content assembly delay | S2 | B | Reproducible measured delay violates an established content-availability budget. Pure timing with no budget is informational/U. An actual persistent rendering failure can be S3/S4; never infer an unknown crawler abandonment deadline. |

### D Sitemaps

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| D1 Invalid/unreachable sitemap | S2 | G | A declared sitemap demonstrably fails parsing/access and should be maintained. Link discovery may still work, so not an access blocker. S3 only if evidence establishes material reliance on this failed inventory route. A missing conventional path alone is S0. |
| D2 Sitemap coverage | S1 | G | Optional additions for verified eligible observed URLs. Sitemap absence is not evidence they are undiscoverable. Established important discovery gaps can be S2, but require more than set differences; unknown full inventory is U. |
| D3 Accurate lastmod | U | G | Actual edits cannot be inferred from a one-time fetch. With reliable edit records, demonstrated misleading lastmod can be S2. Cosmetic date refreshes have no justified priority. |
| D4 Commercial-page inclusion | S2 | G | A confirmed important eligible page is missing from a known maintained inventory and inclusion is a warranted discovery improvement. Crawl/noindex prohibitions inherit A/B once. Mere absence from a sitemap is S1/S0, not proof of invisibility. |
| D5 Sitemap size/index limits | S2 | G | Demonstrated protocol-limit violations impair a supported sitemap. Broader importance requires scope evidence; use S3 only for established material inventory loss. No index file with otherwise valid discovery is S0. |

### E Structured data

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| E1 JSON-LD presence | S1 | G | Optional structured representation of supported facts. Missing JSON-LD alone is not a defect, especially with other formats. Never a blocker simply because absent. |
| E2 Organization/Brand fields | S1 | G | Optional entity enrichment when verified fields are available. Demonstrated identity contradiction is N12/S3, not a penalty for missing sameAs or logo. Do not require full markup on every page. |
| E3 Product/Offer completeness | S2 | G | A supported, explicitly targeted feature lacks its required applicable offer fields. Optional enrichment is S1; missing/incorrect essential public facts are assessed separately at S3 when established. No universal markup requirement. |
| E4 Content-specific schema | S1 | G | Optional FAQ/HowTo/Article markup accurately representing existing content. Missing markup alone has no demonstrated material impact; S0 is valid when unnecessary. |
| E5 Invalid JSON-LD | S2 | G | Confirmed syntax or supported-rule failure makes a relevant block unusable. It does not erase otherwise extractable prose. S3 only with evidence that essential information lacks a supported alternative channel. |
| E6 Contradictory schema | S3 | G | Incompatible essential values for the same entity/offer/context can mislead extraction. Identical duplicates are S1/S0; separate variants/entities are S0. Unresolved identity/context is U. |
| E7 Schema versus visible mismatch | S3 | B | Demonstrated material contradiction in price, availability, identity, or another essential fact. Minor wording differences are S0. Do not claim fraud/penalty or choose the correct side without evidence. |

### F Representation

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| F1 Essential facts only in pixels | S3 | B | Verified essential image/canvas information lacks a usable equivalent for the target reader/extractor. Need content interpretation and scoped equivalent search. Decorative images are S0; unreadable pixels without OCR/vision evidence are U. |
| F2 Alt-text quality | S1 | B | Semantic quality suggestions remain advisory under the original detector limits. A verified essential missing equivalent can be S3 under F1, once. Empty decorative alt is S0; no severity from length or generic-word regex. |
| F3 Transcript/captions | S2 | B | A known meaningful media unit lacks a verified required/appropriate textual alternative in the inspected state. S3 when essential content has no accessible equivalent. Opaque player state is U; transcript presence alone does not prove accuracy. |
| F4 Text in PDF/tables | S3 | B | Essential information is demonstrably unavailable to the target text reader and no equivalent exists in scope. Empty parser output alone is U, not a scan finding. Supplemental readable content with minor structure issues can be S2. |
| F5 HTML equivalent to PDFs | S1 | B | A usable text PDF can be sufficient; HTML mirroring is optional. S2/S3 needs a demonstrated access/task problem with the current format. Never penalize all PDF-only content automatically. |

### G Optional AI files

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| G1 llms.txt presence | S1 | G | Optional experiment with unestablished benefit. No missing-file defect; it belongs after confirmed issues and can reasonably be S0/no action. |
| G2 llms.txt accuracy | S1 | G | Correct reproducibly broken references or supported inaccurate descriptions in an existing file. Do not infer a need for sitemap parity or a large audience relying on this file. |

### H Performance and structure

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| H1 Response latency | S2 | B | Controlled measurements exceed an established practical performance budget. With no agreed budget, report observations. Reproduced inability to obtain content may be S4 under the access failure; speed improvement alone does not prove engagement lift. |
| H2 Headings and landmarks | S2 | B | A supported concrete structure/accessibility issue hinders interpreting or navigating content. Missing tags or skipped headings alone do not establish it. Pure semantic polish is S1; subjective assessments are advisory. |
| H3 Mobile/desktop parity | S3 | B | Essential facts/functionality are demonstrably unavailable on an intended supported mobile state. Cosmetic differences are S0. Complete essential task/access failure can be S4; reflow and menus can legitimately differ. |

## Common content checklist severity

These entries often identify editorial opportunities, not confirmed failures. The original requirement to avoid false positives still applies: assigning a planning band does not make an LLM style judgment deterministic. Missing evidence for a real-world factual claim means investigation, not a confident accusation.

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| N1 Self-contained answers | S2 | B | Advisory restructuring of a specific ambiguous answer with known missing context. Needs semantic review; “as above” alone is not a defect. No priority if the answer is already clear in its actual use. |
| N2 Answer placement | S2 | B | Advisory move of an established sought answer to improve scanning. First-two-sentence rules are not requirements. Critical answer absence is a different supported issue; below-fold presence alone is not failure. |
| N3 Quantified claims | S1 | B | Use available verified metrics where genuinely helpful. No need to invent or disclose unavailable metrics; qualitative claims can be appropriate. Missing numbers alone do not warrant a finding. |
| N4 Claim attribution | S2 | B | An important externally checkable assertion would benefit from available credible attribution. Missing citations are review candidates, not proof of falsehood. Established consequential factual contradictions may instead be S3. |
| N5 Credible quotations | S1 | B | Optional genuine relevant quotation. No universal page quota or automatic defect for absence; invented quotes are never an acceptable remedy. |
| N6 Fluency | S1 | B | Passage-specific editorial polish, with meaning preserved. If interpretation fails, document that separately with supporting review; sentence/readability scores alone are not severity evidence. |
| N7 Confident register | S1 | B | Optional tone revision. Appropriate uncertainty must remain. No unsupported authority or automatic penalty for hedging. |
| N8 Jargon definitions | S2 | B | Advisory explanation of a specific important term for an established audience. Specialist terminology may need no definition. Unknown audience means conditional opportunity, not a confirmed comprehension failure. |
| N9 Correct terminology | S2 | B | Correction supported by authoritative version/context evidence. A demonstrated essential instruction/specification error may be S3; mere low terminology density or LLM disagreement is S0/U. |
| N10 Keyword repetition | S1 | B | Optional revision of an actual unnatural passage. Counts alone do not prove stuffing or ranking loss; catalog/API repetition can be correct. |
| N11 Applicable schema | S1 | G | Optional enrichment; reuse the actual E-series severity for an established syntax/contradiction issue. Never count two benefits for the same repair. |
| N12 Entity consistency | S3 | B | Verified incompatible essential identity/contact facts for the same entity and time. Description phrasing, aliases, branches, and legal/trading distinctions are not contradictions. Which side to change may remain unresolved. |
| N13 Useful FAQs | S2 | B | Optional answer coverage for established relevant user questions using known facts. No required FAQ format, schema, or 40–80-word band. Missing irrelevant questions is S0. |
| N14 Freshness | S3 | B | Verified stale decision-critical information with a reliable current source. Missing date/old evergreen text alone is S0/U. Minor dated reference maintenance is S2, cosmetic recency S0. |
| N15 Authors and credentials | S2 | B | Advisory provenance improvement for claim-heavy content when genuine author information is available. Missing personal byline is not universally defective; invented credentials or expertise are prohibited. |

## E commerce and retail severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| EC1 Product facts | S3 | B | An established purchase-critical specification is missing/contradictory for the exact product/variant. Extra numerical embellishment without a demonstrated need is S1. Unknown confidential metrics are not defects. |
| EC2 Comparative sources | S2 | B | Source a material comparison when evidence exists, or investigate unsupported claims. Missing a source is not proof the claim is false. Verified consequential misstatement may be S3. |
| EC3 Customer quotations/reviews | S1 | B | Optional authentic evidence. New products and products without reviews should not be penalized; no review-count requirement. |
| EC4 Nonhype tone | S1 | B | Advisory factual rewrite of identified marketing language. No deterministic adjective-based failure or promised conversion gain. |
| EC5 Prepurchase answers | S2 | B | Answer established relevant sizing/compatibility/return questions with known policy facts. S3 only for demonstrated decision-critical missing information; a dedicated FAQ section is unnecessary when already answered. |
| EC6 Product schema | S2 | G | Applicable supported feature requirements or broken relevant markup. Optional missing fields/media are S1/S0; same issue as E3/E5 is merged. |
| EC7 Fair comparisons | S2 | B | Advisory restructuring of an existing relevant comparison with verified attributes. Missing comparison pages is S0; factually wrong decisive claims may be S3 with evidence. |
| EC8 Natural product wording | S1 | B | Editorial reduction of unnecessary repetition. Preserve actual model/variant terms; no density threshold. |
| EC9 Price/stock/promotion currency | S3 | B | Verified stale or incompatible essential commerce values in matching contexts. Real-world state needs authoritative evidence; cannot infer stock from audit snapshots. An actual broken purchase path is a separate scoped task blocker. |

## Business and corporate severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| BC1 Company identity clarity | S2 | B | Advisory clearer supported identity statement and placement. Identical wording on homepage/About is not required; genuine identity contradiction is N12/S3. |
| BC2 Scale/impact metrics | S1 | B | Optional presentation of verified disclosed metrics. Missing confidential or unmeasured metrics is S0, not a weakness to fill with invented numbers. |
| BC3 Third-party validation | S2 | B | Advisory presentation of available legitimate validation relevant to the audience. Mere absence is not defective and source existence does not prove endorsement. |
| BC4 Leadership quotes | S1 | B | Optional authentic editorial addition. No quote requirement or inferred authority uplift. |
| BC5 Cross-platform entity consistency | S3 | B | Demonstrated essential factual contradiction across verified same-entity sources. Different description wording/category taxonomies are S0/U. Deduplicate with N12/profile mismatch. |
| BC6 Organization/sameAs | S1 | G | Optional verified entity linking/markup. Unverified ownership and missing social accounts are not scored failures. |
| BC7 Service explanation | S2 | B | Advisory answer coverage about actual audience, scope, and service. Missing decisive scope facts can be S3 when need is established. Stylistic brochure judgments alone are not defects. |
| BC8 Service FAQs | S2 | B | Useful known answers for established prospect questions. Bespoke pricing/timelines may legitimately require consultation; don't force public commitments. |

## Portfolio and personal severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| PP1 Concrete project outcomes | S2 | B | Advisory clearer evidence of actual work/outcomes. Numeric outcomes are optional; confidentiality or qualitative projects are not failures. |
| PP2 Attributed testimonials | S1 | B | Optional authentic attribution and presentation. Do not penalize portfolios without testimonials or infer their truth from names alone. |
| PP3 Project case studies | S2 | B | Advisory explanation of supported problem/approach/result for relevant projects. A gallery is not automatically incomplete; no mandated numeric result. |
| PP4 Craft terminology | S1 | B | Optional precision supported by actual methods. Vocabulary density is not a severity signal; verified consequential technical error uses N9. |
| PP5 Person schema | S1 | G | Optional verified identity markup. No schema presence requirement. |
| PP6 Biography fluency/length | S1 | B | Editorial polish with preserved credentials/voice. No universal ideal length or automatic filler penalty. |
| PP7 Recognition sources | S1 | B | Optional supported publication/award references or local link repair. Absence of awards is S0; false recognition needs separate verified evidence. |

## Blogs and news severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| BN1 Factual attribution | S2 | B | Claim-specific provenance improvement; allow original reporting and common definitions. Established consequential false/stale facts may be S3; unsourced does not mean false. |
| BN2 Expert/primary quotes | S1 | B | Optional genuine relevant quote. No universal article requirement. |
| BN3 Evidence for trends | S2 | B | Clarify a central trend with existing source/baseline/date. Optional extra metrics are S1; missing evidence requires investigation, not fabricated statistics. |
| BN4 Byline/dates/schema | S2 | B | Relevant provenance or supported metadata inconsistency. True date/author conflicts need authoritative resolution. Optional schema alone is S1; old publication date is not staleness proof. |
| BN5 Fluency | S1 | B | Editorial revision of specific text. No automatic readability-based severity. |
| BN6 Editorial confidence | S1 | B | Optional tone improvement preserving justified uncertainty. Do not rank assertiveness as correctness. |
| BN7 Jargon explanations | S2 | B | Advisory explanation needed for the established readership and article. Specialist audience may make this S0. |
| BN8 Natural headings | S1 | B | Optional heading clarity; necessary topic/series repetition is valid. |
| BN9 Evergreen maintenance | S2 | B | Confirmed broken citations or warranted evidence refresh. Actual stale decision-critical advice can be S3 with a current source; age/schedule absence alone is U/S0. |

## SaaS and web applications severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| SA1 Feature explanation/outcomes | S2 | B | Advisory clear supported capability and constraints. Missing numeric ROI is S0; demonstrated incorrect decisive capability/plan information is S3. |
| SA2 Independent benchmarks | S2 | B | Relevant provenance opportunity with authentic comparable evidence. Absence is not an automatic defect; no invented independent validation. |
| SA3 Result-specific customer quotes | S1 | B | Optional authentic quotation with known context. Generic praise need not be replaced or fabricated into quantified claims. |
| SA4 Documentation correctness | S3 | B | Verified version-specific technical error materially misleads implementation/use. General term-density or style judgment is S1/U; an observed essential task blocker can be S4 only with separate task evidence. |
| SA5 Comparisons/alternatives | S2 | B | Advisory useful sourced comparison or repair of a local issue. Missing comparison pages is S0. Demonstrated material misinformation may be S3. |
| SA6 Software/product schema | S1 | G | Optional applicable representation. Actual supported syntax/required-feature issue inherits E5/E3 severity once. No automatic requirement by page category. |
| SA7 Marketing/docs tone | S1 | B | Optional purpose-appropriate editorial work. Correct technical complexity is not a defect. |
| SA8 Natural feature headings | S1 | B | Editorial clarity without repetition quotas. Preserve capabilities and product terminology. |
| SA9 Release notes | S2 | B | Advisory discoverable real release/version information useful to users. Missing public changelog does not prove inactive maintenance; incorrect decisive version information can be S3 if established. |

## Social and community severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| SC1 Policy clarity/sources | S2 | B | Advisory precision and evidence for material policy/statistical claims. Substantive inaccurate policy needs authoritative evidence and may be S3; writing style alone is not policy failure. |
| SC2 Member/moderator quotes | S1 | B | Optional genuine editorial evidence. No quote quota or authenticity assumption. |
| SC3 Community metrics | S1 | B | Optional accurate disclosed metrics. No penalty for withholding counts or using an appropriate qualitative description. |
| SC4 Help-center answers | S2 | B | Advisory answer completeness for known support tasks. A verified wrong essential procedure may be S3; missing FAQ schema is S1/S0. |
| SC5 Platform/app identity consistency | S3 | B | Explicit essential identity contradiction after matching developer, app, company, and date. Legitimate different entities and wording are S0/U. |
| SC6 Landing-page repetition | S1 | B | Optional editorial cleanup; no penalty from keyword counts alone. |
| SC7 Trust/safety tone | S1 | B | Optional style precision preserving policy. Actual consequential policy error belongs to SC1 at its supported band, not a duplicate tone finding. |

## Education and LMS severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| ED1 Course outcomes and requirements | S2 | B | Advisory clarity on actual skills/duration/audience. Verified misleading essential prerequisites or certification claims can be S3. Missing completion/pass metrics alone is S0. |
| ED2 Curriculum references | S2 | B | Advisory genuine sources/credentials relevant to substantive educational claims. Absence does not establish false content; invented accreditation is not an acceptable improvement. |
| ED3 Instructor/learner quotes | S1 | B | Optional authentic evidence. No universal quote requirement or fabricated learner success. |
| ED4 Course FAQs | S2 | B | Useful established answers on prerequisites, format, and applicable policies. Already answered elsewhere is S0; missing optional markup is not medium severity by itself. |
| ED5 Correct/defined terms | S2 | B | Context-supported explanation/correction for the learner level. Verified materially wrong instructional content can be S3; subjective simplicity alone remains advisory. |
| ED6 Tutorial HowTo schema | S1 | G | Optional representation of an existing accurate procedure. No automatic eligibility failure when absent. |
| ED7 Instructional simplicity | S2 | B | Advisory simplification of a specific learner-relevant passage with accuracy preserved. Academic wording and sentence length are not independently detectable failures. |
| ED8 Natural course titles | S1 | B | Optional wording improvement, preserving true subject/level. Catalog repetitions across distinct courses are legitimate. |
| ED9 Curriculum freshness | U | B | Need approved current curriculum/version evidence. A verified materially stale syllabus/prerequisite can become S3; age of the page alone cannot establish it. |

## Media and entertainment severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| ME1 Work metadata | S2 | B | Useful verified runtime/release/edition details relevant to a task. Missing popularity metrics is S0; wrong decisive dates may be S3 with current evidence. |
| ME2 Critic-score attribution | S2 | B | Relevant source/scale/date clarification. Unverified current scores require research; source absence is not proof of fabricated ratings. |
| ME3 Review/cast quotes | S1 | B | Optional authentic editorial addition. No required quotation or assumed uplift. |
| ME4 Media schema | S1 | G | Optional supported metadata representation. Actual broken relevant markup uses E5; material contradictory metadata uses E6/E7. |
| ME5 Synopsis quality | S1 | B | Editorial improvement preserving plot and attribution. Vividness and subjective superlatives cannot independently prove severity. |
| ME6 Practical answers | S2 | B | Advisory known answers about the actual work/territory. Do not invent streaming availability or expect every work to need an FAQ. |
| ME7 Natural metadata wording | S1 | B | Optional accurate title/description cleanup. Preserve editions, episode numbers, and actual access conditions. |
| ME8 Schedule/availability freshness | S3 | B | Authoritatively verified stale or conflicting decision-critical availability/status in a matching territory/time. An old page timestamp alone is U/S0. |

## Off site profile severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| PROFILE_DATA_MISMATCH | S3 | B | Verified incompatible essential fields for the same entity and time, such as a contact destination. Minor descriptions are S1/S0. Which source is correct may require investigation before remediation. |
| UNDECLARED_PROFILE_FOUND | S1 | G | Optional link to an independently verified profile. Missing linkage in inspected pages is not a defect or proof of lack of authority. |
| STALE_THIRD_PARTY_PROFILE | U | B | Mismatch alone cannot identify the stale source. Dated authoritative evidence can establish a consequential S3 or minor S2 update. Platform access/editing rights remain separate. |
| MISSING_EXPECTED_PROFILE | U | B | Unsuccessful search cannot prove missing existence or eligibility. No active defect priority; offer a scoped verification task only if useful. |

## Bridge and engagement severity

| ID and check | Reference band | Area | Activation condition and priority rationale |
| --- | --- | --- | --- |
| I1 Stable direct URLs | S3 | B | Reproducible inability to directly reach the intended observed content unit. Total access failure can be S4. Valid query URLs or working fragment references are not inherently defective; merge with C3 where the cause matches. |
| I2 Query-parameter robustness | S3 | B | A demonstrably inert parameter causes a reproducible material content/error regression on a supported target. Nonessential differences are S0/S1. Uncontrolled personalization/meaningful parameters are U; complete tested access failure can be S4. |
| J1 Identity orientation | S2 | E | Advisory clearer identity and placement based on actual content/layout. Human comprehension is not proven by screenshots. Generic H1 alone is insufficient evidence of a failure. |
| J2 Navigability | S2 | E | Supported local navigation/recovery issue or warranted advisory improvement. Broken essential path with no alternative may be S3/S4; missing breadcrumbs alone is S0. |
| J3 Fact prominence | S2 | E | Advisory placement of an established important fact. Mere below-fold location is not a defect. A verified covered/inaccessible essential fact is S3 or an actual access blocker, deduplicated with J6. |
| J4 Workflow friction | S3 | E | A verified unnecessary requirement materially obstructs a known primary task. Unknown end-to-end flows are U; DOM control count is not evidence. Essential observed task impossibility can be S4; necessary login/consent is not automatically defective. |
| J5 Trust evidence | S2 | E | Optional presentation of genuine audience-relevant evidence. Absence does not prove distrust or lost conversions. Use authentic assets and no review-count thresholds. |
| J6 Blocking overlays | S3 | E | Reproduced material obstruction of essential content/action in a defined state. Inescapable obstruction of the supported essential task can be S4; dismissible minor distraction is S1/advisory. Preserve necessary consent/auth functions. |
| J7 Post-completion value | U | E | State unavailable in the current read-only scope. No active priority. Supplied completion-flow evidence could support an S2 opportunity; no inference from a landing page. |
| J8 Unavailability recovery | S2 | E | Useful verified recovery routes on a naturally encountered unavailable item/state. No need to fabricate substitutes or infer expectation mismatch. Important confirmed dead-end flows may justify S3. |
| J9 Error-page recovery | S2 | E | An observed error page lacks usable appropriate recovery in a relevant journey. A deliberately nonexistent URL alone says little about audience reach. The broken target itself is B4; avoid double-counting. |
| J10 Separate speed score | S0 | B | Excluded duplicate. Link to H1/H3 findings rather than creating another severity or implementation task. |

## How to combine severity and difficulty

Use severity first and difficulty second for the default implementation order. This gives high-value easy fixes first without letting easy cosmetic edits outrank serious unresolved failures. This is an explicit product policy, not a claim that ordinal severity is measurable financial value.

### Difficulty rubric for the later LLM

Estimate the **complete proposed remedy**, including validation and rollout, not the length of its snippet. A one-line header or canonical edit can have difficult policy, configuration, and regression requirements.

| Difficulty | Meaning | Typical evidence needed |
| --- | --- | --- |
| D1 | Small isolated edit with an established correct value/location and straightforward verification | Exact content/config source, no unresolved policy or integration question. |
| D2 | Several related edits or one familiar component/template change with bounded tests | Known implementation path and affected states. |
| D3 | One subsystem change, meaningful content/data integration, or nontrivial validation | Repository/CMS data flow and affected dependencies understood. |
| D4 | Multiple components/systems, substantial migration, or extensive compatibility testing | Cross-system ownership, deployment, and rollback constraints understood. |
| D5 | Architectural change or large migration requiring broad coordination and validation | Sufficient implementation context to justify the scope; not simply uncertainty. |
| Unknown | Insufficient implementation information | Return missing context or an explicit plausible range. Do not assume unknown means easy or hard. |

For a URL-only audit, many difficulty estimates must remain provisional. The LLM should return a range when appropriate, such as D2–D4, with its assumptions. Do not use a low estimate to make a proposed fix look attractive.

### Deterministic ranking index

For ready, deduplicated tasks with a supported actual band S1–S4 and a justified difficulty D1–D5:

```text
priority_index = 5 × severity + (6 − difficulty)
```

Here severity is the integer 1–4 and difficulty is the integer 1–5. Higher is earlier. This is a compact encoding of severity descending, difficulty ascending; it is not predicted uplift, ROI, or a 100-point quality score.

| Severity | D1 | D2 | D3 | D4 | D5 |
| --- | --- | --- | --- | --- | --- |
| S4 Critical | 25 | 24 | 23 | 22 | 21 |
| S3 High | 20 | 19 | 18 | 17 | 16 |
| S2 Medium | 15 | 14 | 13 | 12 | 11 |
| S1 Low/optional | 10 | 9 | 8 | 7 | 6 |

S0 has no implementation task; U has no numeric index. If difficulty is D2–D4, retain the interval of possible indices instead of pretending to know an exact rank. For S3 that interval is 17–19. Keep unestimated serious tasks prominent in their severity band under “estimate required,” rather than burying them below minor known tasks.

This default deliberately does **not** divide severity by difficulty. These are ordinal judgments, not measured benefit and cost; a naive ratio can rank a tiny optional enhancement above a critical blocker. A separate ROI mode would require calibrated outcome/cost estimates and an explicit scheduling preference.

### Ordering rules that override a simple number

1. Separate confirmed problems, advisory opportunities, and investigations. Sort within each queue. The main recommendation list shows ready confirmed fixes first, while serious blocked/investigation items remain visible in their own section.
2. Resolve prerequisite tasks before dependent fixes. A necessary low-band data/configuration prerequisite can come before the high-band remedy it enables. Display that dependency, rather than artificially inflating its standalone severity.
3. Merge overlapping checklist manifestations into actual change tasks. One template repair affecting E3, EC6, and N11 is one task; use the highest justified actual band, never sum their scores. Preserve related IDs for coverage.
4. Within equal severity and difficulty, use **verified** affected breadth and established page/task importance as tie-breakers. Record observed URL counts and crawl completeness. Never invent traffic, revenue, or importance from URL names alone. Unknown breadth is unknown.
5. Do not add GEO and engagement severity together. If a task demonstrably benefits both, use the higher justified consequence band and describe both mechanisms. Dual benefit can be a qualitative tie-breaker only when supported.
6. Reassess after implementation or new evidence. A root-cause repair may resolve several observations. A still-blocked collector cannot establish that downstream content defects exist. Do not mechanically suppress all analysis merely because one bot has noindex/disallow.

### Illustrative ranking only

These are hypothetical tasks, not findings about a supplied website. Difficulty is assumed solely to demonstrate ordering.

| Task | Actual severity | Difficulty | Index | Interpretation |
| --- | --- | --- | --- | --- |
| Remove unintended effective noindex from an intended indexed landing page | S4 | D1 | 25 | Intent, actual edit source, and verification scope have already been established. |
| Repair an origin error preventing access to a public target | S4 | D3 | 23 | Harder than the metadata change, still ahead of polish. |
| Resolve a verified same-variant price mismatch using the authoritative commerce value | S3 | D2 | 19 | Correct data and implementation path are known. |
| Repair a malformed declared sitemap | S2 | D1 | 15 | Concrete local defect; content can still be discovered through links. |
| Add useful answers from verified policy facts | S2 advisory | D2 | 14 | Separate opportunity queue, not a confirmed defect. |
| Add optional llms.txt | S1 advisory | D1 | 10 | Optional experiment, not an eligibility fix. |

## Suggested record for the skill

```json
{
  "task_id": "stable task identifier",
  "check_ids": ["E7", "EC9"],
  "reference_band": "S3",
  "actual_band": "S3",
  "finding_kind": "confirmed_problem",
  "benefit_area": ["geo", "engagement"],
  "severity_reason": "Reproduced conflicting essential offer values in the same context",
  "evidence_ids": ["actual source evidence identifiers"],
  "affected_scope": "actual URLs, variant, currency, locale, and observed time",
  "remedy_readiness": "needs_authoritative_value",
  "difficulty": null,
  "difficulty_range": null,
  "difficulty_assumptions": [],
  "depends_on": [],
  "priority_index": null,
  "queue": "investigation",
  "expected_effect": "Align the conflicting representations after the correct value is established",
  "uplift_prediction": null
}
```

The score is null in this example because the issue can be serious while the safe remedy is not yet ready. Do not estimate implementation priority as though deciding the correct price were already solved.

## Validation requirements for implementation

Maintain all 134 IDs and attach the trigger/counterexample logic, not just the label. Test that intentional noindex, valid non-self canonicals, decorative empty alt, legitimate variants, short accurate answers, and absent optional markup do not activate inappropriate severity. Test that unknown truth/intent stays unresolved.

For ranking, test that severity dominates difficulty in the selected default policy; decreasing effort never lowers priority within a band; S0/U do not enter the numeric implementation queue; dependencies precede dependents; duplicates are merged; and uncertain difficulty is not silently converted to D1. These checks validate the ranking policy, not the claim that a recommendation will increase traffic or conversions.

The initial catalogue can be calibrated later using real audit outcomes and expert-reviewed task priorities. Keep a version and change rationale for revised severity rules. Do not change severity merely because an LLM generated a persuasive explanation or guessed an easy implementation.
