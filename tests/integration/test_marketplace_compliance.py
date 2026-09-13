"""Comprehensive Marketplace & Architectural Compliance Test Suite.

Ports all verification contracts, safety invariants, detector behaviors, ranking formulas,
and schema gates from ADOBE-Hackathon into the 8-skill architecture.
Pure Python standard library (unittest, json, re, pathlib).
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH_DIR = ROOT / "src/skills/audit-orchestrator/scripts"
SCRAPER_DIR = ROOT / "src/skills/web-scraper/scripts"
DISC_DIR = ROOT / "src/skills/discoverability-audit/scripts"
ENTITY_DIR = ROOT / "src/skills/entity-content-audit/scripts"

for p in (ORCH_DIR, SCRAPER_DIR, DISC_DIR, ENTITY_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from crawler.links import normalize, safe_path
from crawler.robots import Robots
from discoverability_check import audit as discoverability_audit
from entity_content_check import audit as entity_audit
from orchestrator import assemble, sort_tasks, validate_report
from plan import plan

from tests.fixtures.fixture_audit import run_synthetic_audit

CHECKS = json.loads((ROOT / "src/skills/audit-orchestrator/references/checks.json").read_text(encoding="utf-8"))
CAT = {c["check_id"]: c for c in CHECKS}


def record(text: str = "<h1>A short complete page</h1>", status: int = 200) -> dict:
    return {
        "artifact": "response-0001",
        "url": "https://example.org/",
        "status": status,
        "headers": [["Content-Type", "text/html"]],
        "text": text,
        "complete": True,
        "elapsed_ms": 20,
        "source": {"text": text, "canonicals": []},
    }


def candidate(check: str = "E5", band: str = "S2", kind: str = "confirmed_problem") -> dict:
    return {
        "check_id": check,
        "title": "Fixture finding",
        "actual_band": band,
        "finding_kind": kind,
        "scope": "https://example.org/",
        "observation": "A short complete page",
        "severity_reason": "Fixture activation with complete evidence",
        "collection_complete_for_scope": True,
        "evidence_refs": [{"artifact": "response-0001", "locator": "source.text", "quote": "A short complete page"}],
    }


class RobotsComplianceTests(unittest.TestCase):
    """RFC 9309 crawler permissions, rule precedence, and edge cases."""

    def test_allow_exception(self):
        r = Robots("User-agent: *\nDisallow: /\nAllow: /public")
        self.assertTrue(r.allowed("https://x/public/a"))
        self.assertFalse(r.allowed("https://x/private"))

    def test_repeated_specific_groups(self):
        r = Robots(
            "User-agent: ReadinessAudit\nDisallow: /a\nUser-agent: ReadinessAudit\nDisallow: /b\nUser-agent: *\nDisallow: /c"
        )
        self.assertFalse(r.allowed("https://x/a"))
        self.assertFalse(r.allowed("https://x/b"))
        self.assertTrue(r.allowed("https://x/c"))

    def test_allow_tie(self):
        self.assertTrue(Robots("User-agent: *\nDisallow: /a\nAllow: /a").allowed("https://x/a"))

    def test_wildcard_terminal(self):
        r = Robots("User-agent: *\nDisallow: /*.pdf$")
        self.assertFalse(r.allowed("https://x/a.pdf"))
        self.assertTrue(r.allowed("https://x/a.pdf?q=1"))

    def test_octets(self):
        r = Robots("User-agent: *\nDisallow: /caf%C3%A9\nDisallow: /a%2Fb\nDisallow: /%7Euser")
        self.assertFalse(r.allowed("https://x/café"))
        self.assertFalse(r.allowed("https://x/~user"))
        self.assertTrue(r.allowed("https://x/a/b"))

    def test_empty_disallow(self):
        self.assertTrue(Robots("User-agent: *\nDisallow:").allowed("https://x/"))

    def test_crawl_delay(self):
        self.assertEqual(Robots("User-agent: *\nCrawl-delay: 9").delay, 9.0)


class SafetyComplianceTests(unittest.TestCase):
    """Zero-trust crawler safety, URL validation, and network boundaries."""

    def test_scheme_and_credentials(self):
        for url in ("file:///etc/passwd", "https://u:p@example.org/", "ftp://x/", "http://x:8080/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize(url)

    def test_query_identity(self):
        self.assertEqual(
            normalize("https://Example.org/product?id=123#description"),
            "https://example.org/product?id=123",
        )

    def test_unsafe_routes(self):
        for path in ("/logout", "/?action=delete", "/checkout", "/account", "/?token=abc", "/unsubscribe"):
            self.assertFalse(safe_path("https://x" + path))
        self.assertTrue(safe_path("https://x/product?id=123"))

    def test_robots_missing_vs_unreachable(self):
        for status, allowed in ((404, True), (410, True), (500, False), (403, False), (429, False)):
            with self.subTest(status=status):
                r = Robots("", status_code=status)
                self.assertEqual(r.allowed("https://example.org/"), allowed)


class DetectorComplianceTests(unittest.TestCase):
    """Diagnostic detectors, false-positive prevention, and author intent."""

    def test_optional_absences_not_defects(self):
        inv = {
            "site": "https://example.org",
            "pages": [
                {
                    "url": "https://example.org/",
                    "status_code": 200,
                    "raw_html": '<h1>Open 9 to 5</h1><img alt="" src="decoration.png">',
                    "text": "Open 9 to 5",
                    "json_ld": [],
                }
            ],
        }
        res = entity_audit("https://example.org", "example.org", inv=inv)
        findings = res.get("findings", [])
        # Missing optional fields like openingHours or decorative images without alt should not be confirmed defects
        self.assertFalse(any(f.get("finding_kind") == "confirmed_problem" and f.get("check_id") == "F1" for f in findings))

    def test_jsonld_syntax_error_detected(self):
        inv = {
            "site": "https://example.org",
            "pages": [
                {
                    "url": "https://example.org/",
                    "status_code": 200,
                    "raw_html": '<script type="application/ld+json">{"name":}</script>',
                    "text": "test",
                    "json_ld": [],
                }
            ],
        }
        res = discoverability_audit("https://example.org", "example.org", inv=inv)
        findings = res.get("findings", [])
        self.assertTrue(any("JSONLD" in f.get("cause_id", "") or f.get("check_id") == "E5" for f in findings))

    def test_valid_multiple_entities_accepted(self):
        inv = {
            "site": "https://example.org",
            "pages": [
                {
                    "url": "https://example.org/",
                    "status_code": 200,
                    "raw_html": '<script type="application/ld+json">[{"@type":"Product","name":"A"},{"@type":"Product","name":"B"}]</script>',
                    "text": "products",
                    "json_ld": [{"@type": "Product", "name": "A"}, {"@type": "Product", "name": "B"}],
                }
            ],
        }
        res = discoverability_audit("https://example.org", "example.org", inv=inv)
        findings = res.get("findings", [])
        self.assertFalse(any(f.get("check_id") == "E5" for f in findings))

    def test_noindex_is_observation_not_unmitigated_defect(self):
        inv = {
            "site": "https://example.org",
            "pages": [
                {
                    "url": "https://example.org/",
                    "status_code": 200,
                    "raw_html": '<meta name="robots" content="noindex">',
                    "meta_robots": "noindex",
                    "text": "private page",
                }
            ],
        }
        res = discoverability_audit("https://example.org", "example.org", inv=inv)
        findings = res.get("findings", [])
        for f in findings:
            if "NOINDEX" in f.get("cause_id", ""):
                self.assertIn(f.get("actual_band", "S2"), ("U", "S2", "S1"))

    def test_cross_domain_canonical_is_not_defect(self):
        inv = {
            "site": "https://example.org",
            "pages": [
                {
                    "url": "https://example.org/",
                    "status_code": 200,
                    "raw_html": '<link rel="canonical" href="https://syndicated-publisher.org/">',
                    "canonical_url": "https://syndicated-publisher.org/",
                    "text": "syndicated content",
                }
            ],
        }
        res = discoverability_audit("https://example.org", "example.org", inv=inv)
        findings = res.get("findings", [])
        # Valid single cross-domain canonical is author intent, not a competing canonical defect
        self.assertFalse(any(f.get("check_id") == "B3" for f in findings))


class ReportComplianceTests(unittest.TestCase):
    """Evidence gate, locator resolution, counts, and schema validation."""

    def report(self, items):
        return assemble("https://example.org", items, [record()], CHECKS, {})

    def test_missing_evidence_dropped(self):
        c = candidate()
        c["evidence_refs"][0]["quote"] = "invented quote"
        r = self.report([c])
        self.assertEqual(r["findings"], [])
        self.assertTrue(r["dropped_findings"])

    def test_missing_artifact_dropped(self):
        c = candidate()
        c["evidence_refs"][0]["artifact"] = "fictional"
        self.assertTrue(self.report([c])["dropped_findings"])

    def test_wrong_locator_dropped_even_when_quote_exists(self):
        c = candidate()
        c["evidence_refs"][0]["locator"] = "source.nonexistent"
        self.assertTrue(self.report([c])["dropped_findings"])

    def test_incomplete_scope_dropped(self):
        c = candidate()
        c["collection_complete_for_scope"] = False
        self.assertTrue(self.report([c])["dropped_findings"])

    def test_unknown_difficulty_unscored(self):
        f = self.report([candidate()])["findings"][0]
        self.assertIsNone(f["priority_index"])
        self.assertEqual(f["queue"], "investigation")

    def test_serious_blocked_remedy_retains_severity(self):
        c = candidate("B4", "S4")
        f = self.report([c])["findings"][0]
        self.assertEqual(f["severity"], "critical")
        self.assertEqual(f["queue"], "investigation")

    def test_unassessable_not_problem(self):
        self.assertTrue(self.report([candidate(band="U")])["dropped_findings"])

    def test_editorial_not_confirmed(self):
        c = candidate("N1", "S1", "advisory")
        f = self.report([c])["findings"][0]
        self.assertEqual(f["disposition"], "editorial_draft")
        self.assertEqual(f["queue"], "advisory")

    def test_bad_counts_rejected(self):
        r = self.report([])
        r["summary"]["critical"] = 1
        with self.assertRaises(ValueError):
            validate_report(r)

    def test_all_ids_accounted_in_catalogue(self):
        self.assertEqual(len(CHECKS), 134)
        check_ids = {c["check_id"] for c in CHECKS}
        self.assertEqual(len(check_ids), 134)


class RankingComplianceTests(unittest.TestCase):
    """Topological task sorting, cycle detection, and priority index formula."""

    def task(self, name, band="S2", difficulty=1, queue="confirmed", deps=None):
        return {
            "id": name,
            "actual_band": band,
            "difficulty": difficulty,
            "queue": queue,
            "scope": "https://example.org",
            "depends_on": deps or [],
        }

    def test_severity_over_effort(self):
        res = sort_tasks([self.task("low", "S1", 1), self.task("high", "S4", 5)])
        self.assertEqual(res[0]["id"], "high")

    def test_effort_within_band(self):
        res = sort_tasks([self.task("hard", difficulty=5), self.task("easy", difficulty=1)])
        self.assertEqual(res[0]["id"], "easy")

    def test_advisory_after_confirmed(self):
        res = sort_tasks([self.task("advice", "S4", 1, "advisory"), self.task("fix", "S1", 5)])
        self.assertEqual(res[0]["id"], "fix")

    def test_prerequisite_before_high_severity(self):
        res = sort_tasks([self.task("high", "S4", deps=["prep"]), self.task("prep", "S1")])
        self.assertEqual([x["id"] for x in res], ["prep", "high"])

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            sort_tasks([self.task("a", deps=["b"]), self.task("b", deps=["a"])])

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):
            sort_tasks([self.task("a", deps=["unknown"])])

    def test_formula_all_bands_efforts(self):
        for severity in range(1, 5):
            for difficulty in range(1, 6):
                c = candidate("J9", "S" + str(severity))
                c.update(
                    remedy_readiness="ready",
                    candidate="<p>404</p>",
                    validation_results=["Parsed fixture"],
                    difficulty=difficulty,
                )
                self.assertEqual(plan(c, CAT["J9"])["priority_index"], 5 * severity + 6 - difficulty)


class IntegrationComplianceTests(unittest.TestCase):
    """Synthetic end-to-end audit verification."""

    def test_synthetic_audit_pipeline(self):
        with tempfile.TemporaryDirectory() as out_dir:
            report = run_synthetic_audit(Path(out_dir))
            self.assertEqual(report["site"], "https://fixture.invalid")
            self.assertIn("findings", report)
            self.assertEqual(len(report["findings"]), 2)
            self.assertEqual({f["check_id"] for f in report["findings"]}, {"E5", "B4"})
            self.assertFalse(report["dropped_findings"])
            self.assertTrue(any(o["check_id"] == "B1" for o in report["observations"]))
            self.assertTrue(any(o["check_id"] == "J9" for o in report["observations"]))


class PackageValidationComplianceTests(unittest.TestCase):
    """Package manifest, skill frontmatters, 134 catalogue IDs, and distribution size."""

    def test_marketplace_manifest(self):
        manifest_path = ROOT / "src/marketplace.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(sum(s.get("entrypoint") is True for s in manifest["skills"]), 1)
        self.assertEqual(len({s["id"] for s in manifest["skills"]}), len(manifest["skills"]))
        # Exact 8 skills architecture
        self.assertEqual(len(manifest["skills"]), 8)

    def test_catalogue_integrity(self):
        self.assertEqual(len(CHECKS), 134)
        for c in CHECKS:
            for k in ("detection", "activation", "solution", "solution_level", "reference_band"):
                self.assertIn(k, c)
                self.assertTrue(bool(c[k]), f"Check {c['check_id']} missing required key {k}")


if __name__ == "__main__":
    unittest.main()
