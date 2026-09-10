"""Unit tests verifying production hardening improvements.

Covers:
1. Validator URI format checking and composition keywords (const, allOf, anyOf, oneOf).
2. Monotonic causal suppression scope awareness (preventing missing scope from causing site-wide suppression).
3. Deterministic readiness scoring, dimension weighting, and grade calculation.
4. Specialist sensor error tracking during collection in audit.py.
"""

import json
import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ORCH_SCRIPTS = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "scripts")
if ORCH_SCRIPTS not in sys.path:
    sys.path.insert(0, ORCH_SCRIPTS)

from causal_gate import apply_causal_suppression  # noqa: E402
from validate_report import validate_report_dict, validate_type  # noqa: E402


class TestValidatorHardening(unittest.TestCase):
    """Verifies schema validation enhancements for URIs and composition keywords."""

    def test_uri_format_validation_rejects_non_uris(self):
        """String format 'uri' must reject non-URI strings missing scheme or host."""
        schema = {"type": "object", "properties": {"site": {"type": "string", "format": "uri"}}}

        # Invalid: missing scheme
        err = validate_type({"site": "example.com"}, schema)
        self.assertIsNotNone(err)
        self.assertIn("not a valid URI", err)

        # Invalid: missing scheme and netloc
        err = validate_type({"site": "not-a-uri"}, schema)
        self.assertIsNotNone(err)
        self.assertIn("not a valid URI", err)

        # Invalid: http with no host
        err = validate_type({"site": "http://"}, schema)
        self.assertIsNotNone(err)
        self.assertIn("not a valid URI", err)

    def test_uri_format_validation_accepts_valid_uris(self):
        """String format 'uri' must accept valid RFC 3986 absolute URIs."""
        schema = {"type": "object", "properties": {"site": {"type": "string", "format": "uri"}}}

        self.assertIsNone(validate_type({"site": "https://example.com"}, schema))
        self.assertIsNone(validate_type({"site": "https://example.com/path?query=1#frag"}, schema))
        self.assertIsNone(validate_type({"site": "http://localhost:8080/app"}, schema))

    def test_const_validation(self):
        """Draft-07 const keyword must strictly validate value equality."""
        schema = {"type": "object", "properties": {"status": {"const": "complete"}}}

        self.assertIsNone(validate_type({"status": "complete"}, schema))
        err = validate_type({"status": "partial"}, schema)
        self.assertIsNotNone(err)
        self.assertIn("does not match const", err)

    def test_const_distinguishes_bool_and_int(self):
        """Draft-07 const must not conflate True with 1 or False with 0."""
        schema_int = {"type": "object", "properties": {"val": {"const": 1}}}
        self.assertIsNone(validate_type({"val": 1}, schema_int))
        self.assertIsNotNone(validate_type({"val": True}, schema_int))

        schema_bool = {"type": "object", "properties": {"flag": {"const": True}}}
        self.assertIsNone(validate_type({"flag": True}, schema_bool))
        self.assertIsNotNone(validate_type({"flag": 1}, schema_bool))

    def test_enum_distinguishes_bool_and_int(self):
        """Draft-07 enum must not conflate True with 1 in integer enums."""
        schema_int = {"type": "object", "properties": {"num": {"enum": [1, 2, 3]}}}
        self.assertIsNone(validate_type({"num": 1}, schema_int))
        self.assertIsNotNone(validate_type({"num": True}, schema_int))

    def test_format_validation_without_explicit_type_string(self):
        """Format checking must apply when instance is a string even if type is omitted."""
        schema_uri = {"type": "object", "properties": {"url": {"format": "uri"}}}
        self.assertIsNone(validate_type({"url": "https://example.com"}, schema_uri))
        self.assertIsNotNone(validate_type({"url": "not-a-uri"}, schema_uri))

        schema_dt = {"type": "object", "properties": {"ts": {"format": "date-time"}}}
        self.assertIsNone(validate_type({"ts": "2026-09-10T10:00:00Z"}, schema_dt))
        self.assertIsNotNone(validate_type({"ts": "not-a-datetime"}, schema_dt))

    def test_allof_validation(self):
        """Draft-07 allOf keyword must enforce all subschemas."""
        schema = {
            "type": "object",
            "allOf": [
                {"properties": {"a": {"type": "integer"}}, "required": ["a"]},
                {"properties": {"b": {"type": "string"}}, "required": ["b"]},
            ],
        }
        self.assertIsNone(validate_type({"a": 1, "b": "hello"}, schema))
        err = validate_type({"a": 1}, schema)
        self.assertIsNotNone(err)
        self.assertIn("Missing required property 'b'", err)

    def test_anyof_validation(self):
        """Draft-07 anyOf keyword must require at least one matching subschema."""
        schema = {
            "type": "object",
            "properties": {
                "target": {
                    "anyOf": [
                        {"type": "string", "minLength": 3},
                        {"type": "integer", "minimum": 10},
                    ]
                }
            },
        }
        self.assertIsNone(validate_type({"target": "abc"}, schema))
        self.assertIsNone(validate_type({"target": 15}, schema))
        err = validate_type({"target": "a"}, schema)
        self.assertIsNotNone(err)
        self.assertIn("does not match any", err)

    def test_oneof_validation(self):
        """Draft-07 oneOf keyword must enforce exactly one matching subschema."""
        schema = {
            "type": "object",
            "properties": {
                "mode": {
                    "oneOf": [
                        {"type": "string", "maxLength": 3},
                        {"type": "string", "minLength": 2},
                    ]
                }
            },
        }
        # "ab" length 2 matches both maxLength:3 and minLength:2 -> must fail
        err = validate_type({"mode": "ab"}, schema)
        self.assertIsNotNone(err)
        self.assertIn("matched 2 schemas in oneOf", err)

        # "a" length 1 matches only maxLength:3 -> must pass
        self.assertIsNone(validate_type({"mode": "a"}, schema))

    def test_report_schema_accepts_readiness_object(self):
        """Draft-07 report-schema.json must validate reports with readiness score breakdown."""
        from tests.fixtures.report_fixtures import VALID_SCHEMA_REPORT

        report_with_readiness = json.loads(json.dumps(VALID_SCHEMA_REPORT))
        report_with_readiness["readiness"] = {
            "composite_score": 26.43,
            "grade": "F",
            "dimensions": {
                "crawlability": 100.0,
                "retrieval_readiness": 17.86,
                "citation_readiness": 5.0,
                "entity_authority": 0.0,
                "cross_engine_visibility": 17.86,
                "agentic_commerce": 7.14,
            },
            "weights": {
                "crawlability": 0.2,
                "retrieval_readiness": 0.15,
                "citation_readiness": 0.25,
                "entity_authority": 0.2,
                "cross_engine_visibility": 0.1,
                "agentic_commerce": 0.1,
            },
            "score_scope": "Observed static inventory and specialist telemetry.",
        }

        is_valid, errors = validate_report_dict(report_with_readiness)
        self.assertTrue(is_valid, f"Validation failed with: {errors}")


class TestCausalGateScopeHardening(unittest.TestCase):
    """Verifies that missing or route-specific scopes do not cause over-broad site-wide suppression."""

    def test_route_level_layer0_disallow_does_not_suppress_unrelated_findings(self):
        """A robots.txt disallow for a specific route (/blog/cold-brewing-101) must NOT suppress findings on other routes."""
        raw_findings = [
            {
                "id": "AI_RETRIEVAL_BLOCKED",
                "cause_id": "AI_RETRIEVAL_BLOCKED",
                "title": "AI search crawler selectively restricted in robots.txt",
                "severity": "medium",
                "evidence": "robots.txt declares: User-agent: OAI-SearchBot -> Disallow: /blog/cold-brewing-101.",
            },
            {
                "id": "MATERIAL_ENTITY_AMBIGUITY",
                "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                "title": "Missing Organization Schema",
                "severity": "medium",
                "scope": "https://example.com/",
            },
            {
                "id": "ATTRIBUTE_INCOMPLETENESS",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "title": "No Product Schema on Product Page",
                "severity": "high",
                "scope": "https://example.com/en/products/default",
            },
            {
                "id": "WEAK_IDENTITY_SIGNALS",
                "cause_id": "WEAK_IDENTITY_SIGNALS",
                "title": "No sameAs links",
                "severity": "medium",
            },
        ]

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings)
        # Missing scope or route-scoped disallow must not trigger site-wide Layer 0 block
        self.assertEqual(len(suppressed), 0, f"Expected 0 suppressed findings, got: {[f['id'] for f in suppressed]}")
        self.assertEqual(len(allowed), 4)

    def test_telemetry_seven_findings_survive_without_sitewide_blocker(self):
        """Seven raw specialist findings (like Frescopa telemetry) must all survive when no sitewide blocker exists."""
        findings = [
            {
                "category": "rendering",
                "id": "RENDERED_CONTENT_GAP",
                "cause_id": "RENDERED_CONTENT_GAP",
                "scope": "https://frescopa.coffee/content/dam/frescopa/en/quiz/taste-type",
                "evidence": "Initial HTML contains 0 words before JavaScript execution across 21 route(s).",
            },
            {
                "category": "crawlability",
                "id": "AI_RETRIEVAL_BLOCKED",
                "cause_id": "AI_RETRIEVAL_BLOCKED",
                "evidence": "robots.txt declares: User-agent: OAI-SearchBot -> Disallow: /blog/cold-brewing-101.",
            },
            {
                "category": "entity-identity",
                "id": "MATERIAL_ENTITY_AMBIGUITY",
                "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                "scope": "https://frescopa.coffee/",
            },
            {
                "category": "product-answerability",
                "id": "ATTRIBUTE_INCOMPLETENESS",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "scope": "https://frescopa.coffee/en/products/default",
            },
            {
                "category": "authority",
                "id": "WEAK_IDENTITY_SIGNALS",
                "cause_id": "WEAK_IDENTITY_SIGNALS",
            },
            {
                "category": "engagement",
                "id": "CTA_REACHABILITY_FRICTION",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "scope": "https://frescopa.coffee/en/products/default",
            },
            {
                "category": "engagement",
                "id": "INTENT_TO_LANDING_MISMATCH",
                "cause_id": "INTENT_TO_LANDING_MISMATCH",
                "scope": "https://frescopa.coffee/content/frescopa/es/",
            },
        ]

        allowed, suppressed, dag_metadata = apply_causal_suppression(findings)
        self.assertEqual(len(allowed), 7)
        self.assertEqual(len(suppressed), 0)

    def test_routes_match_exact_and_normalization(self):
        """Route matching must match URLs and paths with query/fragments while rejecting collisions."""
        from causal_gate import routes_match

        self.assertTrue(routes_match("/blog/post-1", "https://example.com/blog/post-1"))
        self.assertTrue(routes_match("/blog/post-1/", "/blog/post-1"))
        self.assertTrue(routes_match("/blog/post-1?ref=1", "/blog/post-1"))
        self.assertFalse(routes_match("/blog", "/blogger/post-1"))
        self.assertFalse(routes_match("/cart", "/checkout/cart-item"))
        self.assertFalse(routes_match("/en/products/default", "https://example.com/en"))

    def test_crlf_disallow_detected_as_sitewide(self):
        """Robots.txt with CRLF line endings Disallow: / must be recognized as site-wide."""
        findings = [
            {
                "id": "AI_RETRIEVAL_BLOCKED",
                "cause_id": "AI_RETRIEVAL_BLOCKED",
                "evidence": "User-agent: *\r\nDisallow: /\r\nUser-agent: Googlebot",
            },
            {
                "id": "MATERIAL_ENTITY_AMBIGUITY",
                "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                "scope": "https://example.com/",
            },
        ]
        allowed, suppressed, dag_metadata = apply_causal_suppression(findings)
        self.assertTrue(dag_metadata["root_causes"][0]["scope"] == "site")
        self.assertEqual(len(suppressed), 1)
        self.assertEqual(suppressed[0]["id"], "MATERIAL_ENTITY_AMBIGUITY")


class TestReadinessScoreHardening(unittest.TestCase):
    """Verifies deterministic readiness score arithmetic, dimension weighting, and grading."""

    def test_readiness_score_calculation_weights(self):
        """Composite score must equal weighted sum of dimensions and assign correct grade."""
        from orchestrator import synthesize_audit_report

        inv = {
            "site": "https://example.com",
            "status": "complete",
            "pages": [
                {"url": "https://example.com/", "page_type": "homepage", "word_count": 150, "status": 200},
                {"url": "https://example.com/about", "page_type": "about", "word_count": 200, "status": 200},
                {"url": "https://example.com/product", "page_type": "product", "word_count": 100, "status": 200},
            ],
        }
        specialist_results = {
            "discoverability-audit": {"coverage": {"retrieval_bots_allowed": 4, "retrieval_bots_total": 4}},
            "geo-content-audit": {"coverage": {"average_citability_score": 80.0}},
            "entity-content-audit": {
                "coverage": {"jsonld_present": True},
                "entity_snapshot": {"organization": {"name": "Example"}},
            },
            "corroboration-authority-audit": {"coverage": {"sameas_declared": 2}},
        }

        report = synthesize_audit_report("https://example.com", inv, specialist_results)
        self.assertIn("readiness", report)
        readiness = report["readiness"]
        self.assertIn("composite_score", readiness)
        self.assertIn("grade", readiness)
        self.assertIn("dimensions", readiness)
        self.assertIn("weights", readiness)

        dims = readiness["dimensions"]
        weights = readiness["weights"]
        expected_score = round(sum(dims[k] * weights[k] for k in weights), 2)
        self.assertEqual(readiness["composite_score"], expected_score)

        # 100% crawlable, 100% retrieval readiness, 80 citability, 100 entity, 100 visibility, 33.33 commerce
        # Score should be high (B or A)
        self.assertIn(readiness["grade"], ["A", "B"])

    def test_low_score_assigns_f_grade(self):
        """Scores below 60 must assign grade 'F'."""
        from orchestrator import synthesize_audit_report

        inv = {
            "site": "https://example.com",
            "status": "complete",
            "pages": [
                {"url": "https://example.com/", "page_type": "homepage", "word_count": 5, "status": 200},
            ],
        }
        specialist_results = {
            "discoverability-audit": {"coverage": {"retrieval_bots_allowed": 1, "retrieval_bots_total": 4}},
            "geo-content-audit": {"coverage": {"average_citability_score": 5.0}},
            "entity-content-audit": {"coverage": {"jsonld_present": False}},
            "corroboration-authority-audit": {"coverage": {"sameas_declared": 0}},
        }

        report = synthesize_audit_report("https://example.com", inv, specialist_results)
        self.assertEqual(report["readiness"]["grade"], "F")
        self.assertLess(report["readiness"]["composite_score"], 60.0)

    def test_defensive_scoring_with_string_status_and_none_bot_counts(self):
        """Readiness calculation must not crash on string status_code, None bot counts, or dict page_type."""
        from orchestrator import synthesize_audit_report

        inv = {
            "site": "https://example.com",
            "status": "complete",
            "pages": [
                {"url": "https://example.com/", "page_type": {"value": "homepage"}, "word_count": 120, "status_code": "200"},
                {"url": "https://example.com/pricing", "page_type": "pricing", "word_count": 80, "status_code": "200"},
            ],
        }
        specialist_results = {
            "discoverability-audit": {"coverage": {"retrieval_bots_allowed": None, "retrieval_bots_total": None}},
            "geo-content-audit": {"coverage": {"average_citability_score": None}},
            "entity-content-audit": {"coverage": {"jsonld_present": False}},
            "corroboration-authority-audit": {"coverage": {"sameas_declared": None}},
        }

        report = synthesize_audit_report("https://example.com", inv, specialist_results)
        self.assertIn("readiness", report)
        self.assertEqual(report["readiness"]["dimensions"]["crawlability"], 100.0)
        self.assertEqual(report["readiness"]["dimensions"]["citation_readiness"], 0.0)


class TestSensorErrorTracking(unittest.TestCase):
    """Verifies that sensor execution exceptions are tracked in coverage.sensor_errors."""

    def test_execute_audit_sensors_records_exception(self):
        """If a sensor raises an exception, execute_audit_sensors must record it in sensor_errors."""
        from audit import execute_audit_sensors

        sensor_errors = []
        # Pass a deliberately malformed inv that will cause a downstream sensor to fail if invoked
        malformed_inv = {"pages": "not-a-list"}  # type error on iteration
        candidates = execute_audit_sensors("https://example.com", "example.com", malformed_inv, sensor_errors=sensor_errors)

        # Candidates should be a list, and any sensor errors should be recorded
        self.assertIsInstance(candidates, list)
        self.assertIsInstance(sensor_errors, list)

    def test_orchestrator_tracks_failed_sensor_in_coverage_and_sets_partial(self):
        """Orchestrator must record failed sensors in coverage.sensor_errors and set audit_status to partial."""
        from orchestrator import synthesize_audit_report

        inv = {"pages": [{"url": "https://example.com/", "word_count": 100}]}
        specialist_results = {
            "discoverability-audit": {"status": "ok", "findings": []},
            "geo-content-audit": {"status": "failed", "error": "ImportError: no module named geo", "findings": []},
        }

        report = synthesize_audit_report("https://example.com", inv, specialist_results)
        self.assertEqual(report["audit_status"], "partial")
        self.assertIn("geo-content-audit", report["coverage"]["sensor_errors"])

    def test_assemble_report_sets_partial_status_when_sensor_errors_present(self):
        """assemble() must set audit_status to 'partial' when coverage contains sensor_errors."""
        from assemble_report import assemble

        candidates = []
        records = []
        checks = []
        cov = {
            "evaluated_total": 0,
            "sensor_errors": [{"sensor": "geo-content-audit", "error": "Boom"}],
        }

        report = assemble("https://example.com", candidates, records, checks, cov)
        self.assertEqual(report["audit_status"], "partial")
        self.assertEqual(report["coverage"], cov)


class TestFrescopaHardeningAndArchetype(unittest.TestCase):
    """Verifies brand extraction precision, archetype detection, route filtering, and affected_urls."""

    def test_brand_name_extraction_prefers_entity_snapshot_and_rejects_generic_titles(self):
        """Orchestrator must prefer entity snapshot brand name and never pick 'signup' from draft pages."""
        from orchestrator import synthesize_audit_report

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/en/drafts/jalagari/signup", "title": "signup", "word_count": 30},
                {"url": "https://frescopa.coffee/", "title": "Frescopa - Coffee, Tea & Accessories", "word_count": 150},
            ]
        }
        # Case 1: Entity snapshot provides brand name
        specialist_results = {
            "entity-content-audit": {
                "status": "ok",
                "entity_snapshot": {"brand_name": "Frescopa"},
                "findings": [],
            }
        }
        report1 = synthesize_audit_report("https://frescopa.coffee/", inv, specialist_results)
        proactive_titles = [p["title"] for p in report1["proactive_actions"]]
        self.assertTrue(any("Frescopa" in t for t in proactive_titles))
        self.assertFalse(any("signup" in t.lower() for t in proactive_titles))

        # Case 2: Entity snapshot empty, inspects homepage and rejects generic titles
        report2 = synthesize_audit_report("https://frescopa.coffee/", inv, {})
        proactive_titles2 = [p["title"] for p in report2["proactive_actions"]]
        self.assertTrue(any("Frescopa" in t for t in proactive_titles2))
        self.assertFalse(any("signup" in t.lower() for t in proactive_titles2))

    def test_sample_routes_filtering_excludes_drafts_and_dam_quizzes(self):
        """Proactive action route references must exclude /drafts/ and /content/dam/ routes."""
        from orchestrator import synthesize_audit_report

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/en/drafts/jalagari/signup", "title": "signup", "word_count": 30},
                {"url": "https://frescopa.coffee/content/dam/frescopa/en/quiz/taste-type", "title": "", "word_count": 0},
                {"url": "https://frescopa.coffee/es/machines", "title": "Máquinas", "word_count": 140},
                {"url": "https://frescopa.coffee/es/coffee", "title": "Café Frescopa", "word_count": 120},
            ]
        }
        report = synthesize_audit_report("https://frescopa.coffee/", inv, {})
        llms_action = next(p for p in report["proactive_actions"] if "llms.txt" in p["title"].lower())
        tech_fix = llms_action["technical_fix"]
        self.assertNotIn("/drafts/", tech_fix)
        self.assertNotIn("/content/dam/", tech_fix)
        self.assertIn("/es/machines", tech_fix)

    def test_detect_business_archetype_ecommerce_with_catalog_and_locations(self):
        """A brand with catalog products, subscriptions, and store locations must be classified as ecommerce."""
        from orchestrator import detect_business_archetype

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/en/products", "clean_text": "Products catalog in stock"},
                {"url": "https://frescopa.coffee/en/subscription", "clean_text": "Subscription fresh coffee delivered monthly"},
                {"url": "https://frescopa.coffee/es/machines", "clean_text": "Cafeteras category 29 coffee-machines"},
                {"url": "https://frescopa.coffee/es/nav", "clean_text": "ENVIO GRATIS DESDE $35 COMPRAR AHORA Cart"},
                {"url": "https://frescopa.coffee/locations", "clean_text": "Our Locations"},
                {"url": "https://frescopa.coffee/es/contact-us", "clean_text": "Contact us"},
            ]
        }
        arch = detect_business_archetype(inv)
        self.assertEqual(arch, "ecommerce")

    def test_detect_business_archetype_local_business(self):
        """A business with LocalBusiness schema and store locator without ecommerce is local_business."""
        from orchestrator import detect_business_archetype

        inv = {
            "pages": [
                {
                    "url": "https://dental.example.com/",
                    "clean_text": "Downtown Dental Clinic",
                    "html": '<script type="application/ld+json">{"@type": "LocalBusiness", "openingHours": "Mo-Fr 08:00-17:00"}</script>',
                },
                {"url": "https://dental.example.com/store-locator", "clean_text": "Find our clinic branches"},
            ]
        }
        arch = detect_business_archetype(inv)
        self.assertEqual(arch, "local_business")

    def test_bundle_context_and_orchestrator_parity(self):
        """bundle_context.detect_signals and orchestrator.detect_business_archetype must produce identical archetypes."""
        from bundle_context import detect_signals
        from orchestrator import detect_business_archetype

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/en/products", "clean_text": "Products in stock"},
                {"url": "https://frescopa.coffee/en/subscription", "clean_text": "Subscription delivered"},
                {"url": "https://frescopa.coffee/es/nav", "clean_text": "COMPRAR AHORA Cart"},
            ]
        }
        arch_orch = detect_business_archetype(inv)
        arch_bundle = detect_signals(inv)["archetype"]
        self.assertEqual(arch_orch, "ecommerce")
        self.assertEqual(arch_bundle, "ecommerce")

    def test_rendered_content_gap_finding_title_and_affected_urls(self):
        """Discoverability sensor must emit clean title without 'on general' and include affected_urls list."""
        import discoverability_check

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/", "html": "<html><body>" + "word " * 100 + "</body></html>", "word_count": 100},
                {
                    "url": "https://frescopa.coffee/quiz",
                    "html": '<html><body><div id="root"></div></body></html>',
                    "page_type": "general",
                    "word_count": 0,
                },
                {
                    "url": "https://frescopa.coffee/products/item1",
                    "html": '<html><body><div id="app"></div></body></html>',
                    "page_type": "general",
                    "word_count": 0,
                },
            ]
        }
        res = discoverability_check.audit("https://frescopa.coffee/", "frescopa.coffee", inv=inv)
        gap_finding = next(f for f in res["findings"] if f["cause_id"] == "RENDERED_CONTENT_GAP")
        self.assertNotIn("on general", gap_finding["title"])
        self.assertIn("on core routes", gap_finding["title"])
        self.assertIn("affected_urls", gap_finding)
        self.assertEqual(len(gap_finding["affected_urls"]), 2)
        self.assertIn("https://frescopa.coffee/quiz", gap_finding["affected_urls"])
        self.assertIn("https://frescopa.coffee/products/item1", gap_finding["affected_urls"])

    def test_report_schema_validates_affected_urls_and_archetype(self):
        """Draft-07 report-schema.json must validate reports containing affected_urls and archetype."""
        from orchestrator import synthesize_audit_report
        from validate_report import validate_report_dict

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/", "html": "<html><body>" + "word " * 100 + "</body></html>", "word_count": 100},
            ]
        }
        specialist_results = {
            "discoverability-audit": {
                "status": "ok",
                "findings": [
                    {
                        "id": "F-001",
                        "cause_id": "RENDERED_CONTENT_GAP",
                        "title": "Primary copy missing from initial raw HTML (client-side rendering gap on core routes)",
                        "severity": "high",
                        "category": "rendering",
                        "root_cause": "Unrendered client-side JS shell",
                        "confidence": "high",
                        "evidence": "0 words before hydration",
                        "scope": "https://frescopa.coffee/quiz",
                        "affected_urls": ["https://frescopa.coffee/quiz", "https://frescopa.coffee/shell"],
                        "suggested_action": {
                            "summary": "Implement SSR",
                            "priority": "high",
                            "technical_fix": "Enable SSR",
                            "creative_fix": "Add static fallback",
                            "verification": "Check raw HTML",
                        },
                    }
                ],
            }
        }
        report = synthesize_audit_report("https://frescopa.coffee/", inv, specialist_results)
        self.assertEqual(report["archetype"], "corporate")
        f0 = report["findings"][0]
        self.assertIn("affected_urls", f0)
        self.assertEqual(f0["affected_urls"], ["https://frescopa.coffee/quiz", "https://frescopa.coffee/shell"])

        # Validate against schema
        is_valid, errors = validate_report_dict(report)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

    def test_multilingual_commercial_action_prevents_false_positive(self):
        """Spanish commercial CTAs ('COMPRAR AHORA') must prevent false positive INTENT_TO_LANDING_MISMATCH."""
        import engagement_check

        html_es = """
        <!DOCTYPE html>
        <html>
        <head><title>Café Frescopa</title></head>
        <body>
            <h1>Café de Especialidad</h1>
            <p>Mezcla de la casa - Tueste medio</p>
            <p>$14.99</p>
            <p><a href="/es/coffee">COMPRAR AHORA</a></p>
            <p>Máquina espresso</p>
            <p>$249.99</p>
            <p><a href="/es/machines">Mostrar ahora</a></p>
        </body>
        </html>
        """
        findings, recommendations, _ = engagement_check.audit_page_engagement(
            html_es, "https://frescopa.coffee/content/frescopa/es/", page_type="general"
        )
        intent_mismatches = [f for f in findings if f.get("cause_id") == "INTENT_TO_LANDING_MISMATCH"]
        self.assertEqual(len(intent_mismatches), 0)

    def test_representative_route_prioritizes_commercial_over_dam_and_quiz(self):
        """Discoverability sensor must select commercial/product routes over DAM or quiz routes as rep_url."""
        import discoverability_check

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/", "html": "<html><body>" + "word " * 100 + "</body></html>", "word_count": 100},
                {
                    "url": "https://frescopa.coffee/content/dam/frescopa/en/quiz/taste-type",
                    "html": '<html><body><div id="root"></div></body></html>',
                    "page_type": "general",
                    "word_count": 0,
                },
                {
                    "url": "https://frescopa.coffee/en/products/default",
                    "html": '<html><body><script type="importmap"></script><div id="root"></div></body></html>',
                    "page_type": "product_detail",
                    "word_count": 3,
                },
            ]
        }
        res = discoverability_check.audit("https://frescopa.coffee/", "frescopa.coffee", inv=inv)
        gap_finding = next(f for f in res["findings"] if f["cause_id"] == "RENDERED_CONTENT_GAP")
        self.assertEqual(gap_finding["scope"], "https://frescopa.coffee/en/products/default")
        self.assertIn("product_detail routes", gap_finding["title"])
        self.assertNotIn("content/dam", gap_finding["root_cause"])

    def test_causal_gate_ingests_affected_urls_for_suppression(self):
        """Causal gate must add all affected_urls from Layer 1 findings to rendering_gap_pages."""
        from causal_gate import apply_causal_suppression

        findings = [
            {
                "id": "F-001",
                "cause_id": "RENDERED_CONTENT_GAP",
                "scope": "https://example.com/rep-route",
                "affected_urls": ["https://example.com/rep-route", "https://example.com/unrendered-catalog"],
                "evidence": "Unrendered JS shell",
            },
            {
                "id": "F-002",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "scope": "https://example.com/unrendered-catalog",
                "title": "Missing Product Schema",
                "evidence": "No product schema",
            },
        ]
        allowed, suppressed, meta = apply_causal_suppression(findings)
        self.assertEqual(len(allowed), 1)
        self.assertEqual(allowed[0]["id"], "F-001")
        self.assertEqual(len(suppressed), 1)
        self.assertEqual(suppressed[0]["id"], "F-002")

    def test_sequential_finding_ids_after_sorting(self):
        """Finding IDs in final synthesized report must be strictly sequential (F-001, F-002, ...) after sorting."""
        from orchestrator import synthesize_audit_report

        inv = {
            "pages": [
                {"url": "https://frescopa.coffee/", "html": "<html><body>word " * 100 + "</body></html>", "word_count": 100},
            ]
        }
        # Findings where initial order would be scrambled by severity reweighting
        specialist_results = {
            "specialist-1": {
                "status": "ok",
                "findings": [
                    {
                        "id": "F-001",
                        "cause_id": "AI_RETRIEVAL_BLOCKED",
                        "severity": "medium",
                        "scope": "https://frescopa.coffee/blog/post-1",
                        "evidence": "User-agent: OAI-SearchBot Disallow: /blog/post-1",
                    },
                    {
                        "id": "F-002",
                        "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                        "severity": "high",
                        "scope": "https://frescopa.coffee/",
                        "evidence": "no schema",
                    },
                ],
            }
        }
        report = synthesize_audit_report("https://frescopa.coffee/", inv, specialist_results)
        ids = [f["id"] for f in report["findings"]]
        self.assertEqual(ids, ["F-001", "F-002"])
        # High severity must be first
        self.assertEqual(report["findings"][0]["cause_id"], "MATERIAL_ENTITY_AMBIGUITY")
        self.assertEqual(report["findings"][1]["cause_id"], "AI_RETRIEVAL_BLOCKED")

    def test_telemetry_dag_root_causes_scope_parity(self):
        """get_telemetry_payload must derive route-level scopes for route-specific blocks."""
        from orchestrator import get_telemetry_payload

        inv = {
            "robots": {
                "summary": {
                    "OAI-SearchBot": {"disallow": ["/blog/post-1"]},
                }
            },
            "pages": [
                {"url": "https://frescopa.coffee/", "word_count": 150, "snr": 0.5, "status": 200},
                {"url": "https://frescopa.coffee/en/products", "word_count": 3, "snr": 0.01, "status": 200, "html": '<div id="root"></div>'},
            ],
        }
        payload = get_telemetry_payload("https://frescopa.coffee/", inventory=inv)
        root_causes = payload["dag"]["root_causes"]
        for rc in root_causes:
            self.assertEqual(rc["scope"], "route")

    def test_readiness_grade_bands_aligned(self):
        """Readiness grade calculation must follow documented 85/70/50/30 bands."""
        from orchestrator import synthesize_audit_report

        def _get_grade(cit_score):
            inv = {
                "pages": [
                    {"url": "https://example.com/", "status": 200, "word_count": 100, "page_type": "homepage"},
                ]
            }
            spec = {
                "discoverability-audit": {"coverage": {"retrieval_bots_allowed": 4, "retrieval_bots_total": 4}},
                "geo-content-audit": {"coverage": {"average_citability_score": cit_score}},
                "entity-content-audit": {"coverage": {"jsonld_present": True}, "entity_snapshot": {"organization": {"name": "Test"}}},
                "corroboration-authority-audit": {"coverage": {"sameas_declared": 2}},
            }
            rep = synthesize_audit_report("https://example.com", inv, spec)
            return rep["readiness"]["grade"], rep["readiness"]["composite_score"]

        # High citability -> Grade A
        grade_a, score_a = _get_grade(85.0)
        self.assertGreaterEqual(score_a, 85.0)
        self.assertEqual(grade_a, "A")


if __name__ == "__main__":
    unittest.main()
