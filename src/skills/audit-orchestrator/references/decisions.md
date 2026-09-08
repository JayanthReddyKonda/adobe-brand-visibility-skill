# Pipeline decisions and source reconciliation

1. The contest PDF has precedence for layout, schema floor, guardrails, runtime and rubric. The research is retained under references and joined by ID; no research row was replaced by the PDF's illustrative sample finding.
2. Six concerns: evidence collection; technical discoverability; content/corroboration; bridge/engagement; remediation; orchestration/validation. Scripts implement each concern in its owning skill. The single entrypoint imports those scripts and routes semantic interpretation through those skill instructions.
3. Collection happens once before the conceptual GEO -> bridge -> engagement passes to prevent inconsistent repeated snapshots. Reproduction requests still use one shared budget. Validation follows all passes, then deduplication/order, then final schema validation.
4. All 134 checks retain detection feasibility, reference band, activation condition, solution level and validation guidance. The severity JSON already in the repository was not treated as extra authority; the joined catalogue derives from the three named markdown documents. Coverage distinguishes scripted observations from agent review and unavailable capabilities.
5. Informational observations do not become implementation tasks. U does not mean low severity. High confirmed defects with blocked remedies remain visible in investigation. Known effort never hides unknown-effort serious tasks below minor issues. Root-cause grouping is conservative, scoped and never sums channel impact.
6. The core needs only Python's standard library; optional browser dependencies are supplied by the execution environment, not bulky binaries in the submission zip. Rendering is deliberately constrained. It supports positive observations and visual advice; it cannot prove absence on a fully functional live page. Existing host-browser evidence can be reviewed under the same contract but must not bypass collection guardrails.
7. No additional checks were invented. Appendix A-C maps to A-H/N/I; D to entity/profile corroboration; E to scoped identity/locale and I1/I2 continuity; F to F1/F3/F4 textual-equivalent reasoning. Website input does not establish email contents or actual user-personalization outcomes.
8. Safety is layered: public-IP connection pinning; destination checks on redirects; conservative robots failures; no credentials/cookies; only GET; risky route exclusions; byte/page/request/time bounds; no retries after 429/503; optional browser traffic routed through the collector. These are guardrails, not a formal proof that every poorly designed GET endpoint is side-effect-free. The execution environment must sandbox and restrict network access as required by the contest.
9. Sitemaps above the collector byte budget, gzip/XML entities, expanded JSON-LD contexts, rich-result eligibility, OCR, authenticated flows, historical truth and full independent profile discovery are explicitly unassessed. Libraries cannot fill missing intent or business truth.

## Standards consulted

- Contest: supplied Round 3 updated handout, pages 1-6, especially schema p2, manifest p3, evaluation/rubric p4, guardrails p5 and appendix p6.
- Agent Skills specification: https://agentskills.io/specification (reviewed 2026-09-08).
- Robots protocol: https://www.rfc-editor.org/rfc/rfc9309.html (reviewed 2026-09-08). Rules combine exact user-agent groups, prefer specific over wildcard, use longest octet match and Allow on ties. Other 4xx responses are conservatively denied except 404/410; this is stricter than optional RFC access.
- Browser request interception: https://playwright.dev/python/docs/network and https://playwright.dev/python/docs/api/class-browsercontext (reviewed 2026-09-08). Service workers blocked; WebSocket routing requires at least 1.48.

These are implementation references, not evidence that a real site's citations or engagement improved.
