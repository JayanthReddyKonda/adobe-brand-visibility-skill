# Benchmarking, Evals & Automated Quality Assurance

**Author:** Jayanth Reddy Konda
**Version:** 2.0.0
**Standard:** `agentskills.io` Evaluation Specification

---

## 1. Machine-Readable Evals Suite (`evals/evals.json`)

Each skill in the marketplace contains a self-contained `evals/evals.json` fixture providing deterministic test cases for skill-level evaluation:

```json
{
  "skill_name": "discoverability-audit",
  "evals": [
    {
      "id": "eval-disc-01",
      "prompt": "Audit robots.txt and indexing directives for a site blocking OAI-SearchBot",
      "expected_status": "ok",
      "assertions": [
        {"type": "has_findings", "expected": true},
        {"type": "finding_contains", "field": "cause_id", "value": "AI_RETRIEVAL_BLOCKED"}
      ]
    }
  ]
}
```

---

## 2. Automated Unit Test Suite

The `tests/` directory contains 58 unit tests across 15 test files providing full regression coverage of every specialist skill's extraction logic.

| Test File | What It Covers |
|---|---|
| `tests/test_fetch_security.py` | SSRF filters, IPv4-mapped IPv6 bypass protection, private network blocking |
| `tests/test_safe_fetch_unit.py` | safe_fetch unit behaviour: redirect limits, decompression bounds |
| `tests/test_discoverability.py` | robots.txt parsing, OAI-SearchBot vs GPTBot classification, noindex detection, canonical check |
| `tests/test_dom_parsers.py` | HTML parser edge cases: malformed tags, nested structures, encoding |
| `tests/test_entity_content.py` | JSON-LD @graph extraction (Organization/Product), answerability attribute scoring |
| `tests/test_fact_consistency.py` | Cross-page price contradiction, contact email conflict, copyright year drift |
| `tests/test_fact_extractor_deep.py` | Scoped fact ledger extraction: currency normalisation, entity matching |
| `tests/test_price_and_currency_utils.py` | Price parsing across locales, currency symbol normalisation |
| `tests/test_corroboration_deep.py` | sameAs identity link verification, HTTP 200 corroboration, broken authority detection |
| `tests/test_geo_content.py` | Causal conjunction scoring, statistical evidence detection, question heading detection |
| `tests/test_geo_scoring_engine.py` | Deep GEO: passage chunk analysis, pronoun density, direct answer lead |
| `tests/test_engagement.py` | H1 information scent, CTA reachability, navigation element count |
| `tests/test_engagement_deep.py` | Multilingual scent anchoring, granular page classifier, intent handoff |
| `tests/test_schema_validation.py` | Report schema validation gate: required fields, enum values, additionalProperties |
| `tests/test_schema_edge_cases.py` | Schema edge cases: empty arrays, null fields, boundary severities |

---

## 3. Running the Test Suite

```bash
# Run all 58 unit tests
python3 -m unittest discover -s tests

# Run a specific test file
python3 -m pytest tests/test_discoverability.py -v

# Run with production QA pipeline (ruff + mypy + pytest)
./scripts/qa_check.sh
```

---

## 4. Continuous Verification Architecture

All specialist scripts expose a `--format json` flag for machine-readable deterministic output. This makes them trivially testable via `subprocess` from any test harness:

```python
result = subprocess.run([
    "python3", "src/skills/discoverability-audit/scripts/discoverability_check.py",
    "--site", "https://testbrand.com",
    "--inventory", "test_inv.json",
    "--format", "json"
], capture_output=True, text=True)
data = json.loads(result.stdout)
assert data["status"] == "ok"
```

The `acquire_inventory.py` script accepts a pre-built `--inventory` fixture to enable fast offline testing without live network calls.
