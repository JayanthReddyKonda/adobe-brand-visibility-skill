# Geo Content Audit Check Procedures

Generative Engine Optimization (GEO) content and citation probability checks.

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

