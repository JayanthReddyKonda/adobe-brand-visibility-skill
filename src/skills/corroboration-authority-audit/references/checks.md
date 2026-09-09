# Corroboration & Authority Audit Check Procedures

External identity-link authority, knowledge graph, and profile corroboration checks.

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

