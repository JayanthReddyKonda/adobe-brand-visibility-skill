# Benchmarking, Evals & Automated Quality Assurance

**Author:** Jayanth Reddy Konda  
**Version:** 1.0.0  
**Standard:** `agentskills.io` Evaluation Specification

---

## 1. Machine-Readable Evals Suite (`evals/evals.json`)

Each skill in the marketplace contains a self-contained `evals/evals.json` fixture providing deterministic test cases:

```json
{
  "skill_name": "discoverability-audit",
  "evals": [
    {
      "id": "eval-disc-01",
      "prompt": "Audit robots.txt and indexing directives for a site blocking GPTBot",
      "expected_status": "ok",
      "assertions": [
        {"type": "has_findings", "expected": true},
        {"type": "finding_contains", "field": "cause_id", "value": "ROBOTS_TXT_BLOCKED"}
      ]
    }
  ]
}
```

---

## 2. Continuous Verification Architecture

The test suite in `tests/` provides full regression coverage:
- `tests/test_fetch_security.py`: Verifies SSRF filters and IPv4-mapped IPv6 protection.
- `tests/test_discoverability.py`: Verifies crawlability, status codes, and robots.txt parsing.
- `tests/test_entity_content.py`: Verifies Schema.org extraction and Answerability scoring.
- `tests/test_fact_consistency.py`: Verifies cross-page price and contact contradiction detection.
- `tests/test_geo_content.py`: Verifies causal conjunction scoring and statistical evidence detection.
- `tests/test_corroboration.py`: Verifies sameAs identity authority node scoring.
- `tests/test_engagement.py`: Verifies information scent and CTA continuity.
- `tests/test_integration.py`: Verifies end-to-end orchestration and schema compliance.
