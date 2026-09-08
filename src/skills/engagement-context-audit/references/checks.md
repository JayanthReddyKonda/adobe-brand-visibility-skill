# Check procedures

Research-derived rules, not unconditional failure predicates. Read only applicable IDs.

## I1 Stable distinct citable URLs

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: For each discovered content unit, reopen its actual URL in a clean context and repeat load; verify the same core identity/content is reachable and inspect effective access/index directives. Normal query URLs such as `/product?id=123` are valid candidates. Report a reproduced deep-link failure or JS-only dependency. Unknown units and search-only alternatives cannot be exhaustively discovered.

Activation: Reproducible inability to directly reach the intended observed content unit. Total access failure can be S4. Valid query URLs or working fragment references are not inherently defective; merge with C3 where the cause matches.

Recommendation and validation: Specify working fresh-load/deep-link behavior for the exact observed content unit. Need routing/canonical compatibility context to implement. Test reload and stable entity identity; keep meaningful query URLs.

## I2 Robustness to unexpected parameters

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: On safe content GET URLs, preserve existing queries and compare baseline/test/baseline responses using an inert unique audit parameter and, if appropriate, a conventional UTM parameter. Compare core entity/facts and canonical destinations, allowing benign redirects and dynamic content. Repeat regressions before reporting. Do not use `session`, cart, or signed URL parameters as allegedly inert probes. Robustness to all unknown parameters is not possible to prove.

Activation: A demonstrably inert parameter causes a reproducible material content/error regression on a supported target. Nonessential differences are S0/S1. Uncontrolled personalization/meaningful parameters are U; complete tested access failure can be S4.

Recommendation and validation: Propose handling the exact reproducibly problematic inert parameter without dropping meaningful parameters. Need routing/security context. Test baseline/probe/baseline, canonical behavior, and existing query semantics.

## J1 Immediate identity clarity

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: Extract the page's identity statement and record rendered coordinates, font/layout context, clipping, and first-viewport screenshot. An existing vision-capable LLM can provide grounded advice. Whether a visitor understands it “in seconds” and where their eyes land are not possible without user research; missing H1 or “Welcome” alone is insufficient.

Activation: Advisory clearer identity and placement based on actual content/layout. Human comprehension is not proven by screenshots. Generic H1 alone is insufficient evidence of a failure.

Recommendation and validation: Draft a clearer identity statement and placement proposal from supported facts and screenshots. Review responsive rendering and comprehension; can't prove “understood in seconds.”

## J2 Structural navigability

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Inventory visible breadcrumbs, native/ARIA navigation, parent/category links, and home/brand links; resolve safe destinations and record return paths. Confirmed broken navigational links are viable. Missing breadcrumbs alone is not a failure; single-page sites and alternative navigation patterns may be complete. Universal visitor understanding remains not possible.

Activation: Supported local navigation/recovery issue or warranted advisory improvement. Broken essential path with no alternative may be S3/S4; missing breadcrumbs alone is S0.

Recommendation and validation: Propose a verified parent/category/home route and navigation affordance using known information architecture. Need intent before inventing a hierarchy. Test destinations, keyboard access, and mobile behavior.

## J3 Key information prominence

Feasibility: Partial. Reference band: S2. Solution level: E.

Detection: For an explicitly identified fact, record viewport intersection, scroll offset, occlusion, and accessible presentation in defined states. Report “price below initial viewport at this viewport,” not “price hidden” or “poor engagement.” Which fact matters and whether prominence is adequate are not possible as objective failures from URL-only context.

Activation: Advisory placement of an established important fact. Mere below-fold location is not a defect. A verified covered/inaccessible essential fact is S3 or an actual access blocker, deduplicated with J6.

Recommendation and validation: Suggest a placement/layout revision for an established important fact. Validate visibility/occlusion at tested widths; business importance and improved comprehension remain judgments.

## J4 Steps and conversion friction

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Observe visible CTA, linked destinations, selectors, login messaging, and blocking interstitials. Follow only safe nontransacting information links; keep an observed path separate from any LLM hypothesis. True minimum steps, guest-checkout availability, and end-to-end completion are not possible without exercising the flow. Never infer step count from preceding DOM controls.

Activation: A verified unnecessary requirement materially obstructs a known primary task. Unknown end-to-end flows are U; DOM control count is not evidence. Essential observed task impossibility can be S4; necessary login/consent is not automatically defective.

Recommendation and validation: Suggest removing an observed unnecessary step only after workflow requirements are known. Need actual flow evidence to promise reduced steps. Do not assume login or consent is dispensable; no end-to-end claims from a landing page.

## J5 Credibility/trust signals

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: Inventory actual reviews, ratings, customer logos, case studies, certifications, and source links appropriate to a tentatively identified page type. Authenticity, perceived trust, and conversion impact are not possible to establish. No mandatory review count or trust-seal rule; absence is an optional content observation.

Activation: Optional presentation of genuine audience-relevant evidence. Absence does not prove distrust or lost conversions. Use authentic assets and no review-count thresholds.

Recommendation and validation: Propose presentation of real existing reviews, case studies, or credentials appropriate to the site. Need authenticated assets/claims. Never generate fake trust signals, testimonials, or conversion predictions.

## J6 Intrusive popups/interstitials

Feasibility: Partial. Reference band: S3. Solution level: C.

Detection: Observe initial load and bounded later states with screenshots and mutation sampling. Identify top-layer dialogs and overlays, measure overlap/hit-testing against core content, and record dismissibility through safe controls if available. Confirm physical obstruction in the observed state; fixed positioning or high z-index alone is insufficient. “Distracting” and all-session absence are not possible to prove.

Activation: Reproduced material obstruction of essential content/action in a defined state. Inescapable obstruction of the supported essential task can be S4; dismissible minor distraction is S1/advisory. Preserve necessary consent/auth functions.

Recommendation and validation: Propose reducing the specific observed obstruction after overlay purpose and consent/access requirements are known. Validate dismissal, accessibility, and unaffected functions. Do not recommend deleting necessary consent or authentication steps on appearance alone.

## J7 Post-completion value

Feasibility: Not possible. Reference band: U. Solution level: X.

Detection: Requires a successful action and its actual completion state, outside the read-only scope. A public confirmation-page mockup is not evidence of the real flow. Only a separately supplied test environment, recorded completed flow, or authorized test transaction would make that narrower review possible.

Activation: State unavailable in the current read-only scope. No active priority. Supplied completion-flow evidence could support an S2 opportunity; no inference from a landing page.

Recommendation and validation: No site-specific post-completion solution is supported without the actual state/flow. Request supplied recordings or an authorized test environment. Generic best practices are not a verified remedy.

## J8 Alternatives when unavailable/mismatched

Feasibility: Partial. Reference band: S2. Solution level: C.

Detection: On naturally encountered explicit out-of-stock/unavailable pages, inventory visible similar-item/category/support alternatives and confirm their safe destinations. Report available recovery links in that state. The visitor's expectation mismatch, personalization, and absence across unobserved failure states are not possible. Do not force stock changes or claim every recommendation is relevant.

Activation: Useful verified recovery routes on a naturally encountered unavailable item/state. No need to fabricate substitutes or infer expectation mismatch. Important confirmed dead-end flows may justify S3.

Recommendation and validation: Propose alternatives using verified relevant inventory or known category/support routes. Need current availability for substitute claims. Test safe destinations; don't fabricate comparable products or infer user intent.

## J9 Useful 404 recovery

Feasibility: Partial. Reference band: S2. Solution level: V.

Detection: Prefer naturally found broken links; optionally request a small number of unique nonexistent public paths. Capture final status, error content, and usable navigation/category/support links or a visible search form, without submitting it. Report observed recovery affordances. A 200 soft-error page is distinct from an HTTP 404; expired/authenticated states remain untested.

Activation: An observed error page lacks usable appropriate recovery in a relevant journey. A deliberately nonexistent URL alone says little about audience reach. The broken target itself is B4; avoid double-counting.

Recommendation and validation: Draft a 404 body with verified home/category/support links, plus accessible layout markup. Validate links and markup in a test page. Preserving actual 404 status requires server integration and retesting; search behavior cannot be certified without testing it.

## J10 Responsiveness/speed as separate engagement check

Feasibility: Exclude. Reference band: S0. Solution level: X.

Detection: Preserve as a source item, but reuse H1 measurements and H3 viewport evidence rather than adding a duplicate defect. Human perceived speed and conversion consequences are not possible from those measurements alone.

Activation: Excluded duplicate. Link to H1/H3 findings rather than creating another severity or implementation task.

Recommendation and validation: Reuse H1/H3 recommendations when warranted. Do not generate a duplicate speed remedy or claim engagement improvement from timing measurements alone.

