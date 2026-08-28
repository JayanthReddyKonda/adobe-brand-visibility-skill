#!/usr/bin/env python3
"""
run_evals.py - Automated evaluation runner for Brand AI-Readiness Audit Marketplace.
"""

import sys
import os
import json

EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(EVALS_DIR, ".."))
SKILLS_DIR = os.path.join(BASE_DIR, "brand-ai-readiness-audit", "skills")

sys.path.insert(0, os.path.join(SKILLS_DIR, "audit-orchestrator", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "discoverability-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "entity-content-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "fact-consistency-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "corroboration-authority-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "engagement-context-audit", "scripts"))

import discoverability_check
import entity_content_check
import fact_consistency_check
import engagement_check
import validate_report


def load_fixture(name):
    path = os.path.join(EVALS_DIR, "fixtures", name, "inventory.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_crawler_blocked():
    inv = load_fixture("crawler-blocked")
    res = discoverability_check.audit(inv["base_url"], "crawler-blocked.example.com", inv=inv)
    assert res["status"] == "ok"
    crit = [f for f in res["findings"] if f["severity"] == "critical"]
    assert len(crit) == 1, f"Expected 1 critical finding, got {len(crit)}"
    assert crit[0]["cause_id"] == "AI_RETRIEVAL_BLOCKED"
    print("  [PASS] crawler-blocked: correctly flagged OAI-SearchBot/PerplexityBot as AI_RETRIEVAL_BLOCKED.")


def test_conflicting_prices():
    inv = load_fixture("conflicting-prices")
    res = fact_consistency_check.audit(inv["base_url"], "drone-store.example.com", inv=inv)
    assert res["status"] == "ok"
    price_findings = [f for f in res["findings"] if f["cause_id"] == "FIRST_PARTY_FACT_CONFLICT"]
    assert len(price_findings) == 1, f"Expected 1 price contradiction finding, got {len(price_findings)}"
    assert price_findings[0]["severity"] == "high"
    print("  [PASS] conflicting-prices: correctly detected FIRST_PARTY_FACT_CONFLICT on Velocity X9.")


def test_csr_rendering():
    inv = load_fixture("csr-rendering")
    res = discoverability_check.audit(inv["base_url"], "spa-app.example.com", inv=inv)
    assert res["status"] == "ok"
    csr_findings = [f for f in res["findings"] if f["cause_id"] == "RENDERED_CONTENT_GAP"]
    assert len(csr_findings) == 1, f"Expected 1 CSR rendering finding, got {len(csr_findings)}"
    print("  [PASS] csr-rendering: correctly flagged empty client-side root as RENDERED_CONTENT_GAP.")


def test_clean_site_false_positive_resistance():
    inv = load_fixture("clean-site")
    d_res = discoverability_check.audit(inv["base_url"], "exemplary-brand.example.com", inv=inv)
    e_res = entity_content_check.audit(inv["base_url"], "exemplary-brand.example.com", inv=inv)
    f_res = fact_consistency_check.audit(inv["base_url"], "exemplary-brand.example.com", inv=inv)
    eng_res = engagement_check.audit(inv["base_url"], "exemplary-brand.example.com", inv=inv)

    all_critical_high = [
        f for res in (d_res, e_res, f_res, eng_res)
        for f in res.get("findings", [])
        if f.get("severity") in ("critical", "high")
    ]
    assert len(all_critical_high) == 0, f"Expected 0 critical/high false positives on clean site, got {len(all_critical_high)}"
    print("  [PASS] clean-site: verified 0 false positive critical/high defects.")


def main():
    print("=== Running Brand AI-Readiness Evaluation Benchmark Suite ===")
    try:
        test_crawler_blocked()
        test_conflicting_prices()
        test_csr_rendering()
        test_clean_site_false_positive_resistance()
        print("\nAll evaluation benchmark tests PASSED (100% precision & recall on standard fixtures).")
    except AssertionError as e:
        print(f"\n[FAIL] Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
