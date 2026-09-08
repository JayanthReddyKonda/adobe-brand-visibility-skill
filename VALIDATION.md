# Validation Record

Executed 2026-09-08 on Linux x86_64 with Python 3.12 pure standard library runtime.

- `./scripts/qa_check.sh`: Complete QA Pipeline passed 100% green across all 5 verification phases:
  - Phase 1: Ruff linter & formatter (0 errors).
  - Phase 2: Flake8 strict style checker (0 errors, 140 max line length).
  - Phase 3: MyPy static type checker (Success across all 8 skills).
  - Phase 4: JSON integrity & Draft-07 schema gate (All manifests and schemas valid).
  - Phase 5: Pytest test suite (**315 passed, 9 subtests passed in 39.73s**).
- `pytest tests/test_marketplace_compliance.py -v`: **36 passed in 0.09s** (100% pass rate) covering:
  - Robots RFC 9309 tests (7 tests: allow exception, tie precedence, crawl delay, octet decoding, repeated groups, terminal wildcard).
  - Safety & SSRF tests (4 tests: query identity, missing vs unreachable robots, scheme/credentials, unsafe route filtering).
  - Detector tests (5 tests: cross-domain canonicals, JSON-LD syntax, noindex handling, optional absences, multiple entities).
  - Report gating & schema compliance (11 tests: catalogue ID reconciliation, bad counts rejection, editorial queueing, dropped findings for missing artifacts/quotes/wrong locators, blocked remedy severity retention).
  - Ranking formula & DAG ordering (7 tests: priority index formula $5 \times \text{band} + 6 - \text{difficulty}$, severity over effort, effort within band, prerequisite chains, dependency cycle rejection, unknown dependency rejection).
  - End-to-end integration & package validation (3 tests).
- `python tests/validate_package.py src`: validated 8 skills, 134 checks, single entrypoint, frontmatter limits, and relative links.
- `python tests/validate_package.py build/brand-ai-readiness-audit.zip`: validated single root folder `brand-ai-readiness-audit/`, uncompressed size ~2.3 MB (well below 50 MB limit).
- `python tests/fixtures/fixture_audit.py`: synthetic site produced confirmed medium defects (malformed JSON-LD, repeated 404), informational observations for allowed robots and 404 recovery affordances, with zero invalid findings and Draft-07 schema validation.

Tests use synthetic transport and never mutate live sites. The example report is clearly labeled synthetic. The suite checks meaningful outcomes: robots exceptions/group merging/octet precedence, redirect rechecking, private-address rejection, risky route exclusion, conservative errors, counterexamples, evidence grounding, invalid locators, no unsupported difficulty, dependency cycles and missing prerequisites, queue separation, deduplication, schema/count invariants, and end-to-end composition.

These results do not establish a false-positive rate, unseen-site recall, traffic uplift, conversion changes, correctness of every future agent interpretation, or full runtime compliance on all hosts. Review the explicit remaining limits in COMPLIANCE.md.
