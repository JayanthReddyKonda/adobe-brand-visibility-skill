# Validation record

Executed 2026-09-08 on Windows with Python from the bundled runtime.

- `python -m unittest discover -s tests -v`: **41 tests passed**, including 20 severity/effort combinations inside the ranking test. Final recorded suite duration: 0.176 seconds.
- `python tests/validate_package.py`: manifest, six frontmatters/relative links, all 134 joined IDs and uncompressed size passed.
- `python tests/fixture_audit.py examples/synthetic-audit-report.json`: synthetic site produced two confirmed medium defects (malformed JSON-LD and repeated broken reference). Noindex remained an observation, cross-domain canonical and decorative image produced no false defect, and 404 recovery was inventoried. Agent finalization integration added one separately tagged grounded advisory, with zero rejected valid fixture candidates.
- `python .../audit.py collect https://example.com --out ... --pages 2 --seconds 30 --browser`: public HTTP smoke test completed in **2.719 seconds**, one HTML page and three responses (robots 404, page 200, repeated page 200), zero findings and no skipped requests. Output was schema-valid. This simple site is not a typical complex-site benchmark or a precision estimate.
- The initial restricted-sandbox socket failure produced blocked coverage and zero invented findings. After permitted network access, the same packaged collector completed the live smoke test.
- Optional Playwright was **not installed** in the test runtime. Its unavailable-capability path was exercised; actual Chromium rendering, screenshots and the route adapter were not integration-tested here. Browser-specific production coverage remains a stated limitation, not a claimed passing test.

Tests use synthetic transport and never mutate live sites. The example report is clearly labeled synthetic. The suite checks meaningful outcomes: robots exceptions/group merging/octet precedence, redirect rechecking, private-address rejection, risky route exclusion, conservative errors, counterexamples, evidence grounding, invalid locators, no unsupported difficulty, dependency cycles and missing prerequisites, queue separation, deduplication, schema/count invariants, and end-to-end composition.

These results do not establish a false-positive rate, unseen-site recall, traffic uplift, conversion changes, correctness of every future agent interpretation, or full runtime compliance on all hosts. Review the explicit remaining limits in COMPLIANCE.md.
