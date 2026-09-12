# Entity Content Audit Check Procedures

Entity identity, structured data, and commercial answerability checks across 5 core business archetypes.

### Table of Contents

#### E-Commerce Product Entities (EC1-EC9)
- [EC1 Numeric product facts](#ec1-numeric-product-facts)
- [EC2 Comparative-claim sources](#ec2-comparative-claim-sources)
- [EC3 Real customer quotes and Review schema](#ec3-real-customer-quotes-and-review-schema)
- [EC4 Authoritative nonhype tone](#ec4-authoritative-nonhype-tone)
- [EC5 Prepurchase FAQ](#ec5-prepurchase-faq)
- [EC6 Product schema completeness](#ec6-product-schema-completeness)
- [EC7 Fair structured comparisons](#ec7-fair-structured-comparisons)
- [EC8 No stuffed titles/descriptions](#ec8-no-stuffed-titlesdescriptions)
- [EC9 Current price/stock/promotions](#ec9-current-pricestockpromotions)

#### SaaS and Software Offerings (SA1-SA9)
- [SA1 Feature outcomes](#sa1-feature-outcomes)
- [SA2 Independent benchmarks/reviews](#sa2-independent-benchmarksreviews)
- [SA3 Result-specific customer quotes](#sa3-result-specific-customer-quotes)
- [SA4 Correct documentation terminology](#sa4-correct-documentation-terminology)
- [SA5 Fair comparisons/alternatives](#sa5-fair-comparisonsalternatives)
- [SA6 Applicable software/product schema](#sa6-applicable-softwareproduct-schema)
- [SA7 Different marketing/docs tone](#sa7-different-marketingdocs-tone)
- [SA8 Nonstuffed feature headings](#sa8-nonstuffed-feature-headings)
- [SA9 Dated changelog/release notes](#sa9-dated-changelogrelease-notes)

#### Social Communities and Marketplaces (SC1-SC7)
- [SC1 Plain policy facts and sourced statistics](#sc1-plain-policy-facts-and-sourced-statistics)
- [SC2 Real member/moderator quotes](#sc2-real-membermoderator-quotes)
- [SC3 Disclosed community counts](#sc3-disclosed-community-counts)
- [SC4 Self-contained FAQ help center](#sc4-self-contained-faq-help-center)
- [SC5 Entity parity with app stores/press](#sc5-entity-parity-with-app-storespress)
- [SC6 Nonstuffed landing pages](#sc6-nonstuffed-landing-pages)
- [SC7 Authoritative trust/safety tone](#sc7-authoritative-trustsafety-tone)

#### Education and Courseware Catalogs (ED1-ED9)
- [ED1 Concrete course outcomes](#ed1-concrete-course-outcomes)
- [ED2 Curriculum sources](#ed2-curriculum-sources)
- [ED3 Instructor/learner quotes](#ed3-instructorlearner-quotes)
- [ED4 Course FAQs and FAQPage](#ed4-course-faqs-and-faqpage)
- [ED5 Defined subject terminology](#ed5-defined-subject-terminology)
- [ED6 HowTo on tutorials](#ed6-howto-on-tutorials)
- [ED7 Fluency and simplicity](#ed7-fluency-and-simplicity)
- [ED8 No stuffed course catalogs](#ed8-no-stuffed-course-catalogs)
- [ED9 Curriculum freshness](#ed9-curriculum-freshness)

#### Media and Entertainment Catalogs (ME1-ME8)
- [ME1 Concrete entertainment metadata](#me1-concrete-entertainment-metadata)
- [ME2 Attributed critic scores](#me2-attributed-critic-scores)
- [ME3 Review/cast/critic quotes](#me3-reviewcastcritic-quotes)
- [ME4 Video/Movie/TVSeries schema](#me4-videomovietvseries-schema)
- [ME5 Fluent nonoverstated synopsis](#me5-fluent-nonoverstated-synopsis)
- [ME6 Practical FAQs](#me6-practical-faqs)
- [ME7 No title/metadata stuffing](#me7-no-titlemetadata-stuffing)
- [ME8 Current availability and status](#me8-current-availability-and-status)

---



## EC1 Numeric product facts

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Extract labeled dimensions, composition, specifications, ratings denominators, and delivery/restock windows for the specific variant. Record facts found and which hypothetical buyer questions remain unanswered. Not every product has measurable performance or published review breakdowns; absence is not automatically a defect and accuracy is not proven.

Activation: An established purchase-critical specification is missing/contradictory for the exact product/variant. Extra numerical embellishment without a demonstrated need is S1. Unknown confidential metrics are not defects.

Recommendation and validation: Build a product-spec block from verified variant data, units, and delivery policies. Unknown dimensions, review percentages, or shipping windows require owner data. Validate every field against its source.

## EC2 Comparative-claim sources

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract each measurable comparison and its named test/lab/source link; resolve public links and preserve the claim context. Report absent attribution locally. Whether tests substantiate the comparison or the source is independent requires optional source review; do not treat all marketing adjectives as factual comparisons.

Activation: Source a material comparison when evidence exists, or investigate unsupported claims. Missing a source is not proof the claim is false. Verified consequential misstatement may be S3.

Recommendation and validation: Add the actual test/source supporting a comparison, with method/scope where known. If absent, propose a noncomparative draft or evidence request. Do not manufacture lab validation.

## EC3 Real customer quotes and Review schema

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Inventory visible quotes, attribution, reviewed product, and matching Review nodes. “Real customer” authenticity is not possible from a URL. Missing quotations/reviews is not a failure for new products; do not recommend marking ordinary promotional copy as reviews.

Activation: Optional authentic evidence. New products and products without reviews should not be penalized; no review-count requirement.

Recommendation and validation: Format verified customer testimonials and appropriate optional Review markup. Need real quote and attribution. Validate text and product association; source presence alone does not prove authenticity.

## EC4 Authoritative nonhype tone

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: The existing LLM may quote promotional claims and show nearby supporting specifications or their absence. Appropriateness and degree of hype are subjective. Do not score adjectives, confidence, or inferred conversion effects.

Activation: Advisory factual rewrite of identified marketing language. No deterministic adjective-based failure or promised conversion gain.

Recommendation and validation: Rewrite the exact marketing passage around supported specifications without unsupported superiority. Review meaning and brand tone; no deterministic hype score.

## EC5 Prepurchase FAQ

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Map observed product characteristics to hypothetical sizing/compatibility/return questions, then find exact supporting answers and schema. Include linked policies when relevant. A dedicated FAQ block is not required if the answers are elsewhere; importance of each question remains an assumption.

Activation: Answer established relevant sizing/compatibility/return questions with known policy facts. S3 only for demonstrated decision-critical missing information; a dedicated FAQ section is unnecessary when already answered.

Recommendation and validation: Draft product-specific FAQ answers from verified sizing, compatibility, and returns information. Missing policy details remain unanswered. Review factual completeness and preserve regional exceptions.

## EC6 Product schema completeness

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Reuse E3/E5 for applicable product and offer fields; compare SKU, reviews, and images to actual visible content. Record 3D/video only if available. Do not require reviews, media, public prices, or one SKU model universally. State which named feature rule, if any, makes a field required.

Activation: Applicable supported feature requirements or broken relevant markup. Optional missing fields/media are S1/S0; same issue as E3/E5 is merged.

Recommendation and validation: Draft applicable Product markup from authoritative commerce fields. Omit unavailable reviews/media. Verify live data bindings and same-variant consistency instead of hardcoding an audit snapshot.

## EC7 Fair structured comparisons

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Detect comparison tables/lists, named products, matched attributes, units, and stated dates. Compare internal claims for identical variants. Fairness, comprehensiveness, and competitors' current specifications are not possible without external evidence. Prose comparisons and absent “versus” pages are not defects.

Activation: Advisory restructuring of an existing relevant comparison with verified attributes. Missing comparison pages is S0; factually wrong decisive claims may be S3 with evidence.

Recommendation and validation: Produce a comparison table only from compatible, sourced product attributes. Unknown competitor values remain unknown. Verify model/version/date and units; factual cells alone cannot prove fairness.

## EC8 No stuffed titles/descriptions

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Use N10 on actual product titles and descriptions. Preserve repeated phrase examples for advice, excluding necessary model/variant wording. No keyword-density rule can establish a confirmed defect.

Activation: Editorial reduction of unnecessary repetition. Preserve actual model/variant terms; no density threshold.

Recommendation and validation: Rewrite the actual title/description to reduce unnecessary repetition while retaining model, variant, and important specifications. Validate factual preservation and editorial suitability.

## EC9 Current price/stock/promotions

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Compare visible and marked-up values for the same locale/variant/session; inspect explicit offer end dates. Reproduced internal contradictions are viable. Real stock, current backend prices, and intentional promotion extensions are not possible without commerce data; don't enter checkout to infer them.

Activation: Verified stale or incompatible essential commerce values in matching contexts. Real-world state needs authoritative evidence; cannot infer stock from audit snapshots. An actual broken purchase path is a separate scoped task blocker.

Recommendation and validation: Propose synchronization between commerce source, visible price/stock, and markup. Need the correct backend state. Test variants, locale, promotions, and update behavior; do not pick a conflicting price by intuition.

## SA1 Feature outcomes

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Map each observed feature to explicit function and claimed outcome spans, including metric context when present. Report answer coverage. Many features need a precise capability description rather than a numeric business outcome; no missing-number defect.

Activation: Advisory clear supported capability and constraints. Missing numeric ROI is S0; demonstrated incorrect decisive capability/plan information is S3.

Recommendation and validation: Explain the feature's supported capability in clear terms; include outcomes only if evidenced. Verify plan/version limits and avoid inventing ROI.

## SA2 Independent benchmarks/reviews

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract benchmark/review source, score, review count, date, and link; verify accessible declared source identity. Independence and validity require source inspection; absence is not a defect and vendor-hosted benchmark claims are not automatically false.

Activation: Relevant provenance opportunity with authentic comparable evidence. Absence is not an automatic defect; no invented independent validation.

Recommendation and validation: Add verified benchmark/review attribution and dated score/count. Need source evidence and comparable benchmark conditions; do not invent independent validation.

## SA3 Result-specific customer quotes

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract quotation plus named customer and quantitative/qualitative outcome. Specificity can be described from text; truth and causal attribution are not possible to establish. Generic praise may remain valid testimony, so no required-result threshold.

Activation: Optional authentic quotation with known context. Generic praise need not be replaced or fabricated into quantified claims.

Recommendation and validation: Select an authentic result-specific customer quote when available. Do not turn generic praise into an invented quantified outcome. Verify exact quotation and context.

## SA4 Correct documentation terminology

Feasibility: Not possible. Reference band: S3. Solution level: C.

Detection: Use N9; version-matched official specifications and executable examples can support selected technical checks if separately scoped. Term density cannot prove correctness or ranking benefit.

Activation: Verified version-specific technical error materially misleads implementation/use. General term-density or style judgment is S1/U; an observed essential task blocker can be S4 only with separate task evidence.

Recommendation and validation: Correct documentation from version-matched specifications or repository behavior. Need technical source/access for reliable fixes; validate examples separately where executable.

## SA5 Fair comparisons/alternatives

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Reuse EC7; bind comparison claims to plan, version, date, and provider. Internal contradictions are viable; competitive fairness and completeness are not possible without authoritative evidence. Missing alternatives pages is not a defect.

Activation: Advisory useful sourced comparison or repair of a local issue. Missing comparison pages is S0. Demonstrated material misinformation may be S3.

Recommendation and validation: Generate a comparison from sourced, same-plan/version attributes. Unknown competitor behavior requires research. Verify context and avoid blanket superiority claims.

## SA6 Applicable software/product schema

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Inventory supported types and inspect syntax/content correspondence under E1–E7. SoftwareApplication, Product, FAQPage, HowTo, and Review are not universal requirements by page path. Do not force testimonial markup into an inapplicable review feature.

Activation: Optional applicable representation. Actual supported syntax/required-feature issue inherits E5/E3 severity once. No automatic requirement by page category.

Recommendation and validation: Generate supported optional schema from established software/page facts, with unavailable values omitted. Validate graph/content correspondence; dynamic pricing and unresolved facts move those fields to C.

## SA7 Different marketing/docs tone

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Classify page purpose tentatively and offer passage-specific LLM advice. Tone suitability is contextual and cannot be certified from a style score; literal technical prose may appropriately contain complex sentences.

Activation: Optional purpose-appropriate editorial work. Correct technical complexity is not a defect.

Recommendation and validation: Draft purpose-appropriate marketing/docs revisions using the actual content. Retain literal technical constraints in docs and supported facts in marketing. Review style semantically.

## SA8 Nonstuffed feature headings

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Use N10 on extracted headings. Repeated feature names can be necessary for navigation or API documentation. Preserve exact examples as advice, without penalty predictions.

Activation: Editorial clarity without repetition quotas. Preserve capabilities and product terminology.

Recommendation and validation: Rewrite specific feature headings around documented user capabilities without redundant terms. Verify that support/availability claims remain unchanged.

## SA9 Dated changelog/release notes

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Discover linked changelog/releases, extract version-date entries, and check relevant links. Presence and stated recency are observable. Active maintenance, undisclosed releases, and absence everywhere are not possible from a bounded public crawl; quiet release cadence is not a failure.

Activation: Advisory discoverable real release/version information useful to users. Missing public changelog does not prove inactive maintenance; incorrect decisive version information can be S3 if established.

Recommendation and validation: Format a dated changelog from real release records or propose a publication structure. Need actual versions/dates/changes; no invented maintenance history.

## SC1 Plain policy facts and sourced statistics

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract policy claims, usage/moderation numbers, scope/date, and attribution. Apply N4 to exact statistical assertions. Plainness and the truth/completeness of operational policies are not possible to prove from wording.

Activation: Advisory precision and evidence for material policy/statistical claims. Substantive inaccurate policy needs authoritative evidence and may be S3; writing style alone is not policy failure.

Recommendation and validation: Clarify policy copy using established policy decisions and verified statistical sources. Need owner/legal policy context for substantive changes; do not create new enforcement promises.

## SC2 Real member/moderator quotes

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Inventory editorial quotes and stated community roles. Authenticity and consent cannot be inferred from page presence; missing quotes is not a defect. Optional linked original posts can corroborate wording only.

Activation: Optional genuine editorial evidence. No quote quota or authenticity assumption.

Recommendation and validation: Format genuine member/moderator quotes with context and attribution. Need actual source material; no fabricated community voices.

## SC3 Disclosed community counts

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract labeled active-user/post/growth metrics with time windows and population definitions. Do not confuse registered accounts with active users. Undisclosed numbers or a qualitative community description are not failures.

Activation: Optional accurate disclosed metrics. No penalty for withholding counts or using an appropriate qualitative description.

Recommendation and validation: Present disclosed community metrics with active/registered definitions and time windows. Need authoritative counts; do not infer them from visible pages or follower estimates.

## SC4 Self-contained FAQ help center

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Identify actual Q&A and answer evidence, assess raw/rendered availability, and compare any markup. LLM clarity/self-containment advice remains subjective. Do not require FAQPage for all help articles or a particular answer length.

Activation: Advisory answer completeness for known support tasks. A verified wrong essential procedure may be S3; missing FAQ schema is S1/S0.

Recommendation and validation: Draft help-center answers from verified product behavior/policies. Unknown workflow steps require testing/context. Review exact procedural correctness; optional FAQ schema can be validated separately.

## SC5 Entity parity with app stores/press

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Follow declared app listings and press links; match app/developer/brand identity before comparing explicit fields. Platform name, publisher, and legal company can differ legitimately. Independent discovery and inaccessible listings require optional search/access; no missing-profile claim from failed fetches.

Activation: Explicit essential identity contradiction after matching developer, app, company, and date. Legitimate different entities and wording are S0/U.

Recommendation and validation: Draft consistent platform/app descriptions from resolved developer/brand facts. Need current listing evidence; preserve legitimate app-versus-company distinctions.

## SC6 Nonstuffed landing pages

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Use N10. Count repetitions for inspection, but do not interpret broad topic coverage as stuffing without editorial context.

Activation: Optional editorial cleanup; no penalty from keyword counts alone.

Recommendation and validation: Simplify actual landing-page repetition while preserving platform scope and capabilities. Editorial review decides clarity; no deterministic keyword target.

## SC7 Authoritative trust/safety tone

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: An LLM can suggest clearer wording for quoted passages. Tone cannot prove policy precision, enforceability, or effectiveness; no confident-language score.

Activation: Optional style precision preserving policy. Actual consequential policy error belongs to SC1 at its supported band, not a duplicate tone finding.

Recommendation and validation: Revise trust/safety wording for precision while preserving policy obligations and exceptions. Substantive policy changes require owner context; tone does not prove operational trustworthiness.

## ED1 Concrete course outcomes

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract stated skills, expected duration, completion/pass metrics, and cohort/time scope. Report answers available to a prospective learner. Not every course tracks or publishes success rates; missing rates are not defects and claimed outcomes are unverified.

Activation: Advisory clarity on actual skills/duration/audience. Verified misleading essential prerequisites or certification claims can be S3. Missing completion/pass metrics alone is S0.

Recommendation and validation: Create course-outcome/duration blocks from approved syllabus and cohort data. Need true metrics for rates/results. Validate learner level, prerequisites, and definitions.

## ED2 Curriculum sources

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract textbooks, references, research links, and stated instructor credentials; resolve available declared sources. Their adequacy, authority, and actual curriculum use are not possible to certify from a URL.

Activation: Advisory genuine sources/credentials relevant to substantive educational claims. Absence does not establish false content; invented accreditation is not an acceptable improvement.

Recommendation and validation: Add actual curriculum references and instructor qualifications. Need source/credential evidence; no invented textbooks, research, or accreditation.

## ED3 Instructor/learner quotes

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Inventory bios, attributed quotations, learner outcomes, and supporting links. Credentials and outcomes need independent verification. No requirement for every instructor or course to contain a quote; authenticity is not possible from presence alone.

Activation: Optional authentic evidence. No universal quote requirement or fabricated learner success.

Recommendation and validation: Format authentic instructor/learner quotations and outcomes. Verify source and context; do not create employment or salary success stories.

## ED4 Course FAQs and FAQPage

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Find answers to prerequisites, format, certification, and refunds across course and policy pages; compare actual FAQ markup if present. Do not require a dedicated FAQ or schema on every course. Applicability of refund questions depends on the offering.

Activation: Useful established answers on prerequisites, format, and applicable policies. Already answered elsewhere is S0; missing optional markup is not medium severity by itself.

Recommendation and validation: Draft course FAQs from verified prerequisites, format, certification, and refund policy. Unknown promises remain omitted; markup is optional.

## ED5 Defined subject terminology

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Use N8/N9; record explicit definitions and candidate unexplained terms. Difficulty must match stated learner level. Correctness and whether definitions are needed are not possible as broad automatic judgments.

Activation: Context-supported explanation/correction for the learner level. Verified materially wrong instructional content can be S3; subjective simplicity alone remains advisory.

Recommendation and validation: Define/correct subject terms using authoritative curriculum material and learner level. Need subject expertise when ambiguous. Verify conceptual accuracy rather than a terminology-density metric.

## ED6 HowTo on tutorials

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Identify actual sequential instructions and any HowTo graph; inspect supported syntax and correspondence. Missing optional HowTo markup is not a defect. Never infer an AI feature benefit solely from adding it.

Activation: Optional representation of an existing accurate procedure. No automatic eligibility failure when absent.

Recommendation and validation: Generate optional HowTo markup from an existing verified sequence of steps. Preserve conditions, order, and warnings; validate supported structure/content. Do not invent steps or promise a search feature.

## ED7 Fluency and simplicity

Feasibility: Not possible. Reference band: S2. Solution level: E.

Detection: Use N6/N8. Advanced or academic prose is not automatically unextractable; the LLM may suggest edits appropriate to the declared learner level without an automated failure label.

Activation: Advisory simplification of a specific learner-relevant passage with accuracy preserved. Academic wording and sentence length are not independently detectable failures.

Recommendation and validation: Simplify actual instructional prose while preserving technical rigor and necessary caveats. Review with intended learner level; short sentences alone do not ensure accuracy.

## ED8 No stuffed course catalogs

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Use N10, excluding repeated subject labels across distinct course cards. Report only passage-specific editorial candidates; repeated “Python” across a Python catalog does not prove stuffing.

Activation: Optional wording improvement, preserving true subject/level. Catalog repetitions across distinct courses are legitimate.

Recommendation and validation: Rewrite course titles/descriptions naturally, retaining subject, level, format, and true scope. Review that distinct courses remain distinguishable.

## ED9 Curriculum freshness

Feasibility: Not possible. Reference band: U. Solution level: C.

Detection: Actual curriculum changes require syllabus history, LMS/CMS access, or authoritative version evidence. A single course page can expose dates or conflicting prerequisites; those narrow observations may be reported separately. Old dates alone do not establish an outdated course.

Activation: Need approved current curriculum/version evidence. A verified materially stale syllabus/prerequisite can become S3; age of the page alone cannot establish it.

Recommendation and validation: Draft updates from an approved current syllabus/version history. Without it, specify the missing curriculum records; never infer updated prerequisites from generic subject knowledge.

## ME1 Concrete entertainment metadata

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract runtime, release dates, view/rating counts, awards, and named work/edition. Report presence and internal inconsistencies. A synopsis need not disclose popularity metrics; “fan favorite” alone is not a measurable defect.

Activation: Useful verified runtime/release/edition details relevant to a task. Missing popularity metrics is S0; wrong decisive dates may be S3 with current evidence.

Recommendation and validation: Build a metadata block from verified work/edition runtime, release, awards, and rating data. Need actual sources for missing metadata; do not invent popularity figures.

## ME2 Attributed critic scores

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Bind each critic score to source, scale, count/date when available, and work version; resolve declared source URLs. Attribution presence is observable. Source authenticity and current score need optional external evidence; don't compare incompatible scales.

Activation: Relevant source/scale/date clarification. Unverified current scores require research; source absence is not proof of fabricated ratings.

Recommendation and validation: Attribute critic scores to the correct source, scale, edition, and date. Need authoritative score evidence to resolve conflicts or refresh values.

## ME3 Review/cast/critic quotes

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract quote, speaker/source, and context. Original-source matching may corroborate text. Authenticity, fair quotation, and whether a quote is needed are not possible to guarantee; absence is not a defect.

Activation: Optional authentic editorial addition. No required quotation or assumed uplift.

Recommendation and validation: Add genuine critic/cast/interview quotes with context. Need original source; do not fabricate reactions or transform paraphrases into direct quotes.

## ME4 Video/Movie/TVSeries schema

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Validate properties appropriate to each actual type; distinguish a trailer video from the movie/series it describes. Inspect relevant dates, duration, cast, and rating context without imposing every field on every type. Record markup defects only within supported rules.

Activation: Optional supported metadata representation. Actual broken relevant markup uses E5; material contradictory metadata uses E6/E7.

Recommendation and validation: Generate applicable Movie/TVSeries/VideoObject markup from supported metadata with correct entity distinctions. Validate properties and references; absent or disputed metadata is not filled speculatively.

## ME5 Fluent nonoverstated synopsis

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: LLM advice may cite unsupported superlatives or awkward passages. Vividness, appropriate opinion, and rhetorical exaggeration cannot be detected reliably enough for confirmed failures.

Activation: Editorial improvement preserving plot and attribution. Vividness and subjective superlatives cannot independently prove severity.

Recommendation and validation: Rewrite the supplied synopsis for clarity without inventing plot, reception, or superlatives. Review accuracy, spoiler scope, and editorial voice.

## ME6 Practical FAQs

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Map observed works to hypothetical release/watch/episode/age-rating questions and retrieve supporting spans from pages or linked guides. Scope answers by region and edition. Not every question applies to every work, and a dedicated schema-marked FAQ is optional.

Activation: Advisory known answers about the actual work/territory. Do not invent streaming availability or expect every work to need an FAQ.

Recommendation and validation: Draft practical answers from supported work/territory facts. Availability and schedules require current sources; unknown answers are omitted rather than guessed.

## ME7 No title/metadata stuffing

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Inventory titles/descriptions and repeated phrases for N10 advice. Titles may legitimately include edition, access mode, or episode labels. No automatic failure from keyword frequency.

Activation: Optional accurate title/description cleanup. Preserve editions, episode numbers, and actual access conditions.

Recommendation and validation: Rewrite metadata naturally while preserving exact title, edition, episode, and access conditions. Verify no unsupported “free” or availability claim is introduced.

## ME8 Current availability and status

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Compare explicit dates/status fields across inspected pages and schema for the same territory/work/time. Report reproduced contradictions. Current licensing, renewal decisions, and episode schedules are not possible to certify without authoritative external feeds or owner data.

Activation: Authoritatively verified stale or conflicting decision-critical availability/status in a matching territory/time. An old page timestamp alone is U/S0.

Recommendation and validation: Propose synchronization with authoritative schedule/licensing/status data. Need region/time-specific sources. Test consistent presentation; website snapshots alone cannot establish current rights.

