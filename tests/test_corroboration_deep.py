import json
import os
import subprocess
import tempfile
import unittest


class TestCorroborationDeep(unittest.TestCase):
    def setUp(self):
        self.script = "src/skills/corroboration-authority-audit/scripts/corroboration_check.py"
        self.test_inv = os.path.join(tempfile.gettempdir(), "test_corrob_inv.json")
        self.test_state = os.path.join(tempfile.gettempdir(), "test_corrob_state.json")

    def test_corroboration_with_valid_sameas(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": """<!DOCTYPE html><html><head><script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "TestBrand", "sameAs": ["https://twitter.com/testbrand", "https://linkedin.com/company/testbrand"]}</script></head><body><h1>TestBrand</h1></body></html>""",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump(
                {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f
            )

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--state",
                self.test_state,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out["status"], "ok")

    def test_corroboration_missing_sameas_emits_recommendation(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": """<!DOCTYPE html><html><head><title>TestBrand</title></head><body><h1>TestBrand</h1></body></html>""",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump(
                {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f
            )

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--state",
                self.test_state,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        # Should emit recommendation to add sameAs profiles
        recs = [r.get("title") for r in out.get("recommendations", [])]
        self.assertTrue(any("sameAs" in r or "profile" in r.lower() for r in recs))

    def test_broken_sameas_link_detection(self):
        # sameAs with invalid non-existent domain should flag broken anchor
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": """<!DOCTYPE html><html><head><script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "TestBrand", "sameAs": ["https://invalid-non-existent-domain-test-12345.org"]}</script></head><body><h1>TestBrand</h1></body></html>""",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump(
                {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f
            )

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--state",
                self.test_state,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in out.get("findings", [])]
        self.assertIn("BROKEN_AUTHORITY_ANCHOR", cause_ids)

    def test_ssrf_attempt_in_sameas_blocked(self):
        # sameAs pointing to 127.0.0.1 must be safely blocked
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": """<!DOCTYPE html><html><head><script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "TestBrand", "sameAs": ["http://127.0.0.1:8080/admin"]}</script></head><body><h1>TestBrand</h1></body></html>""",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump(
                {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f
            )

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--state",
                self.test_state,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        # 127.0.0.1 is blocked by safe_fetch so treated as broken anchor
        cause_ids = [f.get("cause_id") for f in out.get("findings", [])]
        self.assertIn("BROKEN_AUTHORITY_ANCHOR", cause_ids)

    def test_corroboration_empty_inventory(self):
        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                os.path.join(tempfile.gettempdir(), "non_existent.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

    def test_circular_sameas_mirror_cluster_detection(self):
        inv_data = {
            "site": "https://testbrand.tv",
            "pages": [
                {
                    "url": "https://testbrand.tv/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": """<!DOCTYPE html><html><head><title>TestBrand</title><script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "TestBrand", "sameAs": ["https://testbrand.to", "https://testbrand.bz", "https://testbrand.ru", "https://testbrand.com"]}</script></head><body><h1>TestBrand</h1></body></html>""",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.tv",
                "--inventory",
                self.test_inv,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in out.get("findings", [])]
        self.assertIn("CIRCULAR_SAMEAS_SELF_REFERENCE", cause_ids)

    def test_offsite_third_party_footprint_gap(self):
        # Inventory with no sameAs links on third-party authority hubs
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": '<html><head><script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "TestBrand", "url": "https://testbrand.com", "sameAs": ["https://twitter.com/testbrand"]}</script></head><body><h1>TestBrand</h1></body></html>',
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump(
                {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f
            )
        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--state",
                self.test_state,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        rec_ids = [r.get("id") for r in data.get("recommendations", [])]
        self.assertIn("PROACTIVE.AUTHORITY.OFFSITE_FOOTPRINT_GAP.001", rec_ids)

    def test_evidence_classes_segregation(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": """<!DOCTYPE html><html><head><script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "TestBrand", "sameAs": ["https://twitter.com/testbrand"]}</script></head><body><h1>TestBrand</h1></body></html>""",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump({"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f)

        res = subprocess.run(
            ["python3", self.script, "--site", "https://testbrand.com", "--inventory", self.test_inv, "--state", self.test_state],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("evidence_classes", data)
        ev = data["evidence_classes"]
        self.assertIn("declared_identity_nodes", ev)
        self.assertIn("verified_candidate_backlinks", ev)
        self.assertEqual(ev["declared_identity_nodes"]["count"], 1)

    def test_candidate_backlink_ssrf_rejection(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand</h1></body></html>",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--candidate-backlinks",
                "http://127.0.0.1/private-link,http://169.254.169.254/meta",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("evidence_classes", data)
        backlinks = data["evidence_classes"]["verified_candidate_backlinks"]
        self.assertEqual(backlinks["total_candidates_provided"], 2)
        self.assertEqual(backlinks["source_unreachable_count"], 2)
        for r in backlinks["results"]:
            self.assertIn("SSRF blocked", r["error"])

    def test_inbound_link_extractor_unit(self):
        import sys
        sys.path.insert(0, os.path.dirname(self.script))
        from corroboration_check import InboundLinkExtractor, classify_referring_domain

        extractor = InboundLinkExtractor("targetbrand.com")
        sample_html = """
        <html>
            <body>
                <a href="https://targetbrand.com/products">Target Product</a>
                <a href="https://otherdomain.org/about">Other</a>
                <a href="/relative-link">Relative</a>
            </body>
        </html>
        """
        extractor.feed(sample_html)
        self.assertTrue(len(extractor.found_links) > 0)
        self.assertEqual(extractor.found_links[0]["href"], "https://targetbrand.com/products")
        self.assertTrue(extractor.found_links[0]["is_dofollow"])

        # Test domain classifier
        self.assertEqual(classify_referring_domain("https://en.wikipedia.org/wiki/Entity"), "knowledge_graph")
        self.assertEqual(classify_referring_domain("https://techcrunch.com/article"), "editorial_news")
        self.assertEqual(classify_referring_domain("https://reddit.com/r/technology"), "community_forum")
        self.assertEqual(classify_referring_domain("https://randomsite.xyz/page"), "general_web")


if __name__ == "__main__":
    unittest.main()
