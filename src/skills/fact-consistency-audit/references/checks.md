# Check procedures

Research-derived rules, not unconditional failure predicates. Read only applicable IDs.

## N1 Self-contained answers

Feasibility: Not possible. Reference band: S2. Solution level: E.

Detection: Full semantic independence is not a dependable Boolean test. Extract heading-plus-answer units; the existing LLM may identify a specific unresolved referent and quote the missing context. “As above” alone is not a failure when the answer includes its antecedent. Advice only; no confirmed defect or isolation score.

Activation: Advisory restructuring of a specific ambiguous answer with known missing context. Needs semantic review; “as above” alone is not a defect. No priority if the answer is already clear in its actual use.

Recommendation and validation: Rewrite a specific context-dependent answer using an established antecedent. Preserve caveats and scope. If the referent is ambiguous, request context instead; review meaning in isolation and within the page.

## N2 Answer first

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Given an explicitly matched question and supporting answer span, record the answer's sentence/word offset within its section. Whether it should appear in the first two sentences is a contextual editorial judgment and not possible as an objective failure. Avoid applying answer-first rules to narrative introductions or pages without a question.

Activation: Advisory move of an established sought answer to improve scanning. First-two-sentence rules are not requirements. Critical answer absence is a different supported issue; below-fold presence alone is not failure.

Recommendation and validation: Move the supported direct answer earlier and retain supporting context. Verify the moved span/qualifiers; editorial review decides whether the new order suits the section. No mandatory first-two-sentence rule.

## N3 Replace vague claims with numbers

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract vague comparative language and nearby quantities with units, denominators, and dates. Report exact examples for review. Whether reliable numbers exist, are needed, or would improve retrieval is not possible from the page. Never recommend fabricated metrics or score every qualitative statement as defective.

Activation: Use available verified metrics where genuinely helpful. No need to invent or disclose unavailable metrics; qualitative claims can be appropriate. Missing numbers alone do not warrant a finding.

Recommendation and validation: Replace a vague statement only with an existing verified metric and its scope/date. If absent, suggest the exact measurement needed or a restrained qualitative rewrite. Never generate a number to satisfy the checklist.

## N4 Attribute factual claims

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Bind a concrete claim to nearby named sources, footnotes, links, or explicit first-party attribution. Report “no attribution found for this claim in this section,” with exclusions for own-product facts and common definitions. Source credibility, entailment, and truth are not possible to certify generally; optional source retrieval supports narrower verification.

Activation: An important externally checkable assertion would benefit from available credible attribution. Missing citations are review candidates, not proof of falsehood. Established consequential factual contradictions may instead be S3.

Recommendation and validation: Attach an available supporting source to the exact claim, or identify the claim needing evidence. Verify source entailment, not just link existence. Missing evidence means qualify/remove only with editorial approval, not fabricate a citation.

## N5 Credible quotation per relevant page

Feasibility: Not possible. Reference band: S1. Solution level: C.

Detection: Quote text, named speaker, role, and source link can be inventoried. Relevance, credibility, and authenticity are not reliably determined from presence or an LLM judgment. Do not fail pages without quotations. Optional linked-source comparison can confirm textual correspondence, not that the speaker actually said it.

Activation: Optional genuine relevant quotation. No universal page quota or automatic defect for absence; invented quotes are never an acceptable remedy.

Recommendation and validation: Select a genuine available quotation with attribution and context. Without an authenticated source, request one or leave the page unchanged. Never invent an expert/customer statement or make one up in a real person's voice.

## N6 Fluency

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Sentence lengths or readability metrics are observations, not reliable fluency detectors across languages and genres. An existing LLM can suggest edits to exact awkward passages as editorial advice. No dependency supplies a false-positive-free fluency verdict.

Activation: Passage-specific editorial polish, with meaning preserved. If interpretation fails, document that separately with supporting review; sentence/readability scores alone are not severity evidence.

Recommendation and validation: Draft a fluent revision of the actual passage. Check factual/qualifier preservation and language-specific readability; human editorial judgment remains necessary for quality.

## N7 Confident expert register

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: LLM advice may identify unsupported certainty or excessive hedging in a specific passage. Hedging can be correct scientific, technical, or risk communication. Never count “may” or “could” as defects or turn assertiveness into an authority score.

Activation: Optional tone revision. Appropriate uncertainty must remain. No unsupported authority or automatic penalty for hedging.

Recommendation and validation: Make supported statements direct while retaining justified uncertainty. Review for increased certainty, causal claims, or unsupported authority. Do not delete hedging mechanically.

## N8 Simplify and define jargon

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Record explicit definitions and first occurrences of candidate terms within the reading unit. An LLM can propose unexplained-term examples. Whether a term needs explanation for this audience is not possible without audience context; acronym regex and dictionary absence are not sufficient failure evidence.

Activation: Advisory explanation of a specific important term for an established audience. Specialist terminology may need no definition. Unknown audience means conditional opportunity, not a confirmed comprehension failure.

Recommendation and validation: Add concise definitions from supported domain context and simplify redundant jargon. Need audience assumptions stated explicitly; unfamiliar or version-specific terms may require authoritative references.

## N9 Correct technical terminology

Feasibility: Not possible. Reference band: S2. Solution level: C.

Detection: Correctness can depend on discipline, version, jurisdiction, and surrounding assumptions. Extract terms for optional expert/LLM review, but do not reward density or flag generic wording automatically. Authoritative version-matched references or subject expertise can support individual corrections, not a universal detector.

Activation: Correction supported by authoritative version/context evidence. A demonstrated essential instruction/specification error may be S3; mere low terminology density or LLM disagreement is S0/U.

Recommendation and validation: Correct terminology using a relevant authoritative definition and version/context. Without that evidence, offer a review question, not a confident technical correction.

## N10 No keyword stuffing

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Count repeated phrases only as evidence for editorial review, excluding navigation, catalogs, code, and repeated product names. There is no defensible universal repetition threshold establishing stuffing or a search penalty. LLM advice must cite an actual unnatural passage and remain unscored.

Activation: Optional revision of an actual unnatural passage. Counts alone do not prove stuffing or ranking loss; catalog/API repetition can be correct.

Recommendation and validation: Rewrite the specific repetitive passage naturally while preserving identity and query intent. Compare retained facts; do not remove necessary product/API names to hit a density target.

## N11 Applicable schema

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Reuse E1–E7, including Microdata/RDFa scope and context-specific provider rules. Record existing types and supported syntax issues. Missing optional markup is an enrichment suggestion, not a second content defect. Do not manufacture a required schema list from an uncertain page classifier.

Activation: Optional enrichment; reuse the actual E-series severity for an established syntax/contradiction issue. Never count two benefits for the same repair.

Recommendation and validation: Reuse E1–E5 generation for supported optional schema. Validate the same artifact once and reference all related checks; no duplicate “fix” for the same markup.

## N12 Entity consistency

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Compare explicit same-entity facts across inspected first-party pages; follow resolvable declared profiles optionally. Normalize legal/trading names, aliases, branch locations, languages, and dates. Exact wording need not match. Report demonstrated factual contradictions, not description-string differences; external completeness and which source is correct remain not possible.

Activation: Verified incompatible essential identity/contact facts for the same entity and time. Description phrasing, aliases, branches, and legal/trading distinctions are not contradictions. Which side to change may remain unresolved.

Recommendation and validation: Draft consistent statements only after resolving conflicting entity facts. Preserve legitimate alias/location differences. Validate all affected text; do not propagate the most frequent value as assumed truth.

## N13 FAQs with 40–80-word answers and schema

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Identify actual Q&A units, record answer text/length and matching markup, including expanded accessible accordions. Do not require the word band or FAQPage on every page. Relevance to real users and improved AI visibility are not possible to establish from the URL.

Activation: Optional answer coverage for established relevant user questions using known facts. No required FAQ format, schema, or 40–80-word band. Missing irrelevant questions is S0.

Recommendation and validation: Draft questions and self-contained answers from existing supported policies/facts; include citations to each answer's basis. Omit unanswerable questions and avoid a word-count quota. Optional markup is validated separately.

## N14 Freshness signals

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Extract labeled publication/update dates and citation dates, plus explicit expired claims or contradictions. Copyright years are not edit dates. Missing update dates and old accurate evergreen text are not defects. Actual last revision and real-world currency are not possible without history or authoritative current sources.

Activation: Verified stale decision-critical information with a reliable current source. Missing date/old evergreen text alone is S0/U. Minor dated reference maintenance is S2, cosmetic recency S0.

Recommendation and validation: Propose exact stale-claim/source updates only with current authoritative evidence. Need actual revision history for update dates. Never refresh dates cosmetically or assume older content is wrong.

## N15 Author credentials

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Identify visible byline, author page, stated credentials, and consistent Article author references. Report what is disclosed. Missing personal bylines can be appropriate for corporate material. Authentic credentials, expertise, and whether a byline is required cannot be established automatically; optional registries help with individual credentials.

Activation: Advisory provenance improvement for claim-heavy content when genuine author information is available. Missing personal byline is not universally defective; invented credentials or expertise are prohibited.

Recommendation and validation: Format a byline/credential block from confirmed author information. If missing, request it. Do not invent a reviewer, degree, professional role, or attribution.

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

## BC1 Clear identity sentence near top

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Extract homepage/About identity statements and their viewport coordinates. Compare entity and offering meaning, not literal wording. Report the statements and positions. Clarity and the requirement to use identical words are not objectively detectable; LLM evaluation stays advisory.

Activation: Advisory clearer supported identity statement and placement. Identical wording on homepage/About is not required; genuine identity contradiction is N12/S3.

Recommendation and validation: Draft a concise identity statement from observed supported company/service facts and propose placement. Preserve legal/brand distinctions. Review clarity and rendered fit; identical homepage/About wording is unnecessary.

## BC2 Numerical scale and impact

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract client counts, operating years, disclosed revenue, and case-study metrics with scope/date. Report evidence, not a quota of numbers. Whether omitted confidential metrics exist or should be public is not possible; avoid flagging “trusted by” solely for lacking a count.

Activation: Optional presentation of verified disclosed metrics. Missing confidential or unmeasured metrics is S0, not a weakness to fill with invented numbers.

Recommendation and validation: Build an evidence-based scale/impact block from disclosed metrics and dates. Request missing verified metrics; never invent clients, revenue, or saved time.

## BC3 Third-party validation

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Inventory named press, awards, certificates, client logos, and case-study links; verify reachable declared destinations and exact identities. Presence is possible. Actual certification validity, endorsement, and independent validation need optional authoritative sources; a logo alone proves neither trust nor a client relationship.

Activation: Advisory presentation of available legitimate validation relevant to the audience. Mere absence is not defective and source existence does not prove endorsement.

Recommendation and validation: Organize verified press/certification/case-study references. Need actual endorsement/award evidence before presenting claims. Validate links, entities, dates, and any usage permissions relevant to publication.

## BC4 Leadership quotes

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract quotations and speaker/role on About and press pages. Record publicly stated attribution. Authenticity and whether a quote adds value are not possible; missing quotes are not a defect.

Activation: Optional authentic editorial addition. No quote requirement or inferred authority uplift.

Recommendation and validation: Select and format an existing leadership quotation. Need genuine source and attribution; no invented founder quote. Verify wording and context.

## BC5 Consistent external description

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Reuse off-site entity matching and field comparisons for resolvable profiles. Separate categories and descriptions from hard identity facts. Wording differences are not contradictions. Missing platform access or search results yields not possible for that platform, not inconsistent branding.

Activation: Demonstrated essential factual contradiction across verified same-entity sources. Different description wording/category taxonomies are S0/U. Deduplicate with N12/profile mismatch.

Recommendation and validation: Draft platform-specific descriptions from resolved company facts, allowing taxonomy and length differences. Need accessible profiles and the correct current facts. Review before any external update.

## BC6 Organization and verified sameAs

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Resolve Organization nodes and outbound sameAs links. Check the linked profile's website/name/identity evidence. A link's presence does not verify ownership; reciprocal domain references strengthen matching but are not infallible. Do not demand every possible social platform.

Activation: Optional verified entity linking/markup. Unverified ownership and missing social accounts are not scored failures.

Recommendation and validation: Generate supported Organization/sameAs markup from verified identity links, reusing E2. Validate URLs and graph identity; do not mark similar-name accounts as official.

## BC7 Explanatory service pages

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Extract exact spans explaining service, audience, and included scope and map them to hypothetical questions. Absence within the inspected section can be noted. Brochure-versus-explanation quality, correct jargon level, and overall clarity are not possible as deterministic failures.

Activation: Advisory answer coverage about actual audience, scope, and service. Missing decisive scope facts can be S3 when need is established. Stylistic brochure judgments alone are not defects.

Recommendation and validation: Restructure actual service content around what it is, audience, and included scope. Preserve exclusions. Missing service terms require context, not creative completion.

## BC8 Service FAQs

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Find evidence for pricing model, timelines, and scope across service and policy pages. Record directly answerable questions and unaddressed sampled questions. Bespoke services may legitimately omit timelines or public pricing; dedicated FAQs and schema are optional.

Activation: Useful known answers for established prospect questions. Bespoke pricing/timelines may legitimately require consultation; don't force public commitments.

Recommendation and validation: Draft service questions and answers using established pricing/timeline/scope information. Explicitly omit unknown contractual terms; verify against cited service policies.

## PP1 Concrete outcomes

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Extract project-linked outcomes, numbers, units, and attribution. Report measurable claims found. Qualitative work and confidential results can be valid; absence of metrics is not a failure, and the claimed outcome's truth is not possible to establish from the portfolio.

Activation: Advisory clearer evidence of actual work/outcomes. Numeric outcomes are optional; confidentiality or qualitative projects are not failures.

Recommendation and validation: Present verified project outcomes clearly. Ask for underlying result data when absent; do not invent conversion gains or attribute a team's result solely to the individual.

## PP2 Real attributed testimonials

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract testimonial, name, role, organization, and declared source/profile URL. Attribute exactly what the page says. Existence of a named person does not authenticate a testimonial; “real” is not possible without independent corroboration.

Activation: Optional authentic attribution and presentation. Do not penalize portfolios without testimonials or infer their truth from names alone.

Recommendation and validation: Format genuine testimonials with approved attribution. Need actual quotes/roles; never manufacture a client reference.

## PP3 Problem approach result case studies

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Match explicit spans for problem, approach, and result in each inspected case study, regardless of heading wording. Report supported coverage. Requiring every gallery project to have a case study or numeric result is a business/editorial judgment, not a detected failure.

Activation: Advisory explanation of supported problem/approach/result for relevant projects. A gallery is not automatically incomplete; no mandated numeric result.

Recommendation and validation: Restructure existing project evidence as problem, approach, and result. Unknown outcomes stay omitted. Review that authorship and causal claims are preserved.

## PP4 Precise craft terminology

Feasibility: Not possible. Reference band: S1. Solution level: C.

Detection: Use N9 with discipline context. Tools and vocabulary can be inventoried, but their appropriateness and evidence of genuine expertise cannot be reliably inferred from term presence.

Activation: Optional precision supported by actual methods. Vocabulary density is not a severity signal; verified consequential technical error uses N9.

Recommendation and validation: Suggest terminology grounded in actual project methods and discipline references. Need evidence that tools/methods were used; don't add fashionable skills to imply expertise.

## PP5 Person schema

Feasibility: Partial. Reference band: S1. Solution level: V.

Detection: Inspect Person nodes, name, jobTitle/role, URL, and sameAs; match identity to the page. Record supported syntax issues and missing optional fields. A field named `role` is not a universal substitute for the appropriate schema.org property; absence of Person markup is optional enrichment.

Activation: Optional verified identity markup. No schema presence requirement.

Recommendation and validation: Generate Person markup from supported name, role, and verified profile URLs. Validate fields and identity. Unknown credentials or roles are omitted.

## PP6 Short fluent biography

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Measure length and provide optional passage-specific LLM edits. There is no universal ideal bio length; detailed credentials or artistic writing may be intentional. No automatic filler-adjective defect.

Activation: Editorial polish with preserved credentials/voice. No universal ideal length or automatic filler penalty.

Recommendation and validation: Condense the actual biography while retaining meaningful credentials, dates, and voice. Review omitted context; no universal length target.

## PP7 Recognition links

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Extract awards/publications/talks and resolve declared supporting URLs. Report broken references or contradictory dates when context matches. No awards is not a failure; authenticity and completeness need external evidence.

Activation: Optional supported publication/award references or local link repair. Absence of awards is S0; false recognition needs separate verified evidence.

Recommendation and validation: Add verified award/publication/talk references or repair links to confirmed originals. Without recognition evidence, return no supported addition.

## BN1 Sources for factual claims

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Use N4 at claim/paragraph level, allowing first-hand reporting, footnotes, bibliographies, and explicit author observations. Report exact unattributed claims as review candidates. Do not require every sentence to have a link or claim unsourced means false.

Activation: Claim-specific provenance improvement; allow original reporting and common definitions. Established consequential false/stale facts may be S3; unsourced does not mean false.

Recommendation and validation: Add claim-specific source attribution using sources that actually substantiate the statement. Need reporting/source material where absent. A valid URL is not an entailment check.

## BN2 Expert or primary-source quote

Feasibility: Partial. Reference band: S1. Solution level: C.

Detection: Inventory quote, attribution, role, and source linkage. Topic suitability, speaker expertise, and authenticity are not possible to certify. Absence alone is not a defect in explanatory or original research material.

Activation: Optional genuine relevant quote. No universal article requirement.

Recommendation and validation: Use a genuine relevant source quotation with faithful context. If no source is available, request one; do not fabricate interviews or expert reactions.

## BN3 Data instead of vague trends

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Find specific trend claims and associated metric, baseline, time range, and source. Highlight missing context rather than requiring numbers in all prose. Whether data exists and whether the claim is correct remains not possible without source evidence.

Activation: Clarify a central trend with existing source/baseline/date. Optional extra metrics are S1; missing evidence requires investigation, not fabricated statistics.

Recommendation and validation: Replace trend language with supported metric, baseline, interval, and source. Otherwise draft less assertive wording without a fabricated statistic.

## BN4 Byline dates Article schema

Feasibility: Possible. Reference band: S2. Solution level: C.

Detection: Record byline, stated credentials, labeled dates, and corresponding Article/BlogPosting fields; compare explicit author/date values for the same work. A detectable mismatch needs contextual confirmation. Missing fields are observations unless a specific applicable requirement was established; credentials themselves are unverified.

Activation: Relevant provenance or supported metadata inconsistency. True date/author conflicts need authoritative resolution. Optional schema alone is S1; old publication date is not staleness proof.

Recommendation and validation: Align visible byline/dates and Article fields from authoritative publishing metadata. Can format a draft from site claims; need correct author/revision records to resolve conflicts.

## BN5 Fluency

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Use N6. Readability scores and paragraph length do not establish poor fluency or extractability. Offer quoted editorial examples only.

Activation: Editorial revision of specific text. No automatic readability-based severity.

Recommendation and validation: Revise specific sentences/transitions for readability while preserving reporting detail and attribution. Semantic/editorial review remains required.

## BN6 Confident editorial voice

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Use N7. Preserve legitimate uncertainty, developing-story caveats, and quotations. Do not score hedge-word counts as authority.

Activation: Optional tone improvement preserving justified uncertainty. Do not rank assertiveness as correctness.

Recommendation and validation: Make prose direct without overstating developing facts or uncertainty. Compare certainty and attribution before/after, not just word count.

## BN7 Explain jargon initially

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Use N8 to record candidate terms and explicit definitions in the article's reading order. Definitions in linked glossaries may be sufficient. Whether this readership needs explanation remains not possible without audience context.

Activation: Advisory explanation needed for the established readership and article. Specialist audience may make this S0.

Recommendation and validation: Insert brief audience-appropriate definitions from supported references and preserve technical meaning. Unclear terms require a source rather than guessed explanations.

## BN8 Natural nonrepetitive headings

Feasibility: Not possible. Reference band: S1. Solution level: E.

Detection: Record headings and phrase repetition, excluding series titles and necessary topic continuity. “Keyword-stuffed” versus descriptive is an editorial judgment, not a threshold-based defect.

Activation: Optional heading clarity; necessary topic/series repetition is valid.

Recommendation and validation: Rewrite repetitive headings to describe the actual sections. Preserve section intent and factual qualifiers; editorial quality is not mechanically guaranteed.

## BN9 Evergreen update schedule

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Check dated sources, broken citation links, and explicit temporal contradictions. The publishing schedule and actual updates are not possible from a single audit. Local history can show changes; an old publication date alone does not mean stale information.

Activation: Confirmed broken citations or warranted evidence refresh. Actual stale decision-critical advice can be S3 with a current source; age/schedule absence alone is U/S0.

Recommendation and validation: Produce an article-specific update plan from verified broken/stale references. Need current authoritative information and revision policy for actual updates; do not simply change the date.

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

## PROFILE_DATA_MISMATCH

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Report two explicit incompatible values only after matching entity, field meaning, locale, and effective period. Preserve both quotes/URLs and label a discrepancy, not which source is wrong. Text differences and uncertain entity matching must not become a defect.

Activation: Verified incompatible essential fields for the same entity and time, such as a contact destination. Minor descriptions are S1/S0. Which source is correct may require investigation before remediation.

Recommendation and validation: Present both values and draft platform-specific correction only after identity and the true field value are established. Need a source of truth, not just majority agreement. External editing remains a separate authorized action.

## UNDECLARED_PROFILE_FOUND

Feasibility: Possible with optional discovery. Reference band: S1. Solution level: V.

Detection: For a verified found profile, search collected sameAs and profile links for equivalent resolved URLs. Report “verified profile not linked in inspected pages.” This is optional corroboration advice, not a defect; an incomplete crawl cannot establish no link anywhere. Without discovery capability, this branch is not possible.

Activation: Optional link to an independently verified profile. Missing linkage in inspected pages is not a defect or proof of lack of authority.

Recommendation and validation: Propose an optional sameAs/profile link for a verified identity match found by available discovery. Validate URL and entity association. Missing linkage is not a defect, and a search snippet alone cannot validate the profile.

## STALE_THIRD_PARTY_PROFILE

Feasibility: Not possible generally. Reference band: U. Solution level: C.

Detection: A mismatch does not identify the stale side. A narrow case becomes viable when dated, authoritative evidence establishes a change and the same verified profile explicitly presents the old value as current. The first-party homepage alone is not automatically the truth source; otherwise report discrepancy only.

Activation: Mismatch alone cannot identify the stale source. Dated authoritative evidence can establish a consequential S3 or minor S2 update. Platform access/editing rights remain separate.

Recommendation and validation: Draft an update backed by dated authoritative change evidence. Need platform context and correct current facts. Do not assume the first-party page is newer or the business controls the profile.

## MISSING_EXPECTED_PROFILE

Feasibility: Not possible. Reference band: U. Solution level: X.

Detection: A finite unsuccessful search cannot prove absence or eligibility for a profile. With optional search, report “no verified profile found in these searches,” or “results inaccessible,” without severity. Do not recommend a platform solely because an uncertain business classifier expects it.

Activation: Unsuccessful search cannot prove missing existence or eligibility. No active defect priority; offer a scoped verification task only if useful.

Recommendation and validation: No missing-profile remedy can be asserted from an unsuccessful search. Return the search scope and an optional owner verification step. Registration advice requires established eligibility and owner intent, not the claimed absence.

