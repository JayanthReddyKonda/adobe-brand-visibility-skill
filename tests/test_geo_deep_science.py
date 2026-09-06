import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

# Dynamic import of geo_content_check module
GEO_SCRIPT_PATH = os.path.abspath("src/skills/geo-content-audit/scripts/geo_content_check.py")
spec = importlib.util.spec_from_file_location("geo_content_check", GEO_SCRIPT_PATH)
if spec and spec.loader:
    geo_mod = importlib.util.module_from_spec(spec)
    sys.modules["geo_content_check"] = geo_mod
    spec.loader.exec_module(geo_mod)
else:
    raise ImportError(f"Could not load module from {GEO_SCRIPT_PATH}")


class TestGeoDeepScience(unittest.TestCase):
    def setUp(self):
        self.script_path = GEO_SCRIPT_PATH
        self.test_inv = os.path.join(tempfile.gettempdir(), "test_geo_deep_inv.json")
        self.test_state = os.path.join(tempfile.gettempdir(), "test_geo_deep_state.json")

    def tearDown(self):
        for p in [self.test_inv, self.test_state]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

    def test_extract_attributed_quotations_direct(self):
        """Tests Princeton KDD 2024 Attributed Quotations extraction (+40.9% lift)."""
        html_with_quotes = """
        <html><body>
        <blockquote>
            "Distributed tracing cuts mean time to resolution by 60%," explained Dr. Jane Smith.
        </blockquote>
        <p>According to Professor Alan Turing, "Machines will take us by surprise with great frequency."</p>
        <p>Unattributed quote: "This is just a random marketing phrase with no expert named."</p>
        </body></html>
        """
        dom = geo_mod.GEODOMParser()
        dom.feed(html_with_quotes)

        results = geo_mod.extract_attributed_quotations(html_with_quotes, dom.extracted_text)
        self.assertGreaterEqual(results["attributed_quotes"], 1)
        self.assertTrue(results["has_named_expert"])
        self.assertGreaterEqual(results["total_quotes"], 2)

    def test_unattributed_quotes_low_score(self):
        """Unattributed quotes or raw text without expert attribution should have 0 attributed quotes."""
        html_no_attribution = """
        <html><body>
        <p>Here is some plain text without any expert quotes or citations whatsoever.</p>
        <p>"Just some words in quotes without anyone saying it."</p>
        </body></html>
        """
        dom = geo_mod.GEODOMParser()
        dom.feed(html_no_attribution)

        results = geo_mod.extract_attributed_quotations(html_no_attribution, dom.extracted_text)
        self.assertEqual(results["attributed_quotes"], 0)
        self.assertFalse(results["has_named_expert"])

    def test_analyze_evidence_genres_direct(self):
        """Tests Zhang et al. 2026 5 High-Influence Evidence Genres."""
        html_content = """
        <html><body>
        <h1>Architecture Specification</h1>
        <p>A microservice architecture is defined as a collection of loosely coupled services.</p>
        <pre><code>
        def calculate_latency(hops):
            return sum(h.duration for h in hops)
        </code></pre>
        <p>Benchmark results indicate a 45.2% reduction in memory overhead and $1,200 monthly savings.</p>
        <table>
            <thead><tr><th>Tier</th><th>Throughput</th></tr></thead>
            <tbody><tr><td>Base</td><td>10k req/s</td></tr></tbody>
        </table>
        <ol>
            <li>Provision the cluster instances.</li>
            <li>Apply the Helm chart configuration.</li>
            <li>Verify cluster ingress endpoints.</li>
        </ol>
        </body></html>
        """
        dom = geo_mod.GEODOMParser()
        dom.feed(html_content)

        genres = geo_mod.analyze_evidence_genres(html_content, dom.extracted_text, dom)
        self.assertIn("code", genres["genres_detected"])
        self.assertIn("statistics", genres["genres_detected"])
        self.assertIn("definition_copula", genres["genres_detected"])
        self.assertIn("comparison_table", genres["genres_detected"])
        self.assertIn("procedural_steps", genres["genres_detected"])
        self.assertEqual(genres["genre_count"], 5)
        self.assertFalse(genres["standalone_faq_deficit"])

    def test_standalone_faq_deficit_trigger(self):
        """Pure FAQ structure with 0 code/tables/stats triggers standalone FAQ deficit (-5.7% penalty)."""
        html_pure_faq = """
        <html><body>
        <h1>Frequently Asked Questions</h1>
        <details>
            <summary>What is this platform?</summary>
            <p>This platform provides customer relationship management features.</p>
        </details>
        <details>
            <summary>How can I sign up?</summary>
            <p>You can sign up by visiting our registration portal.</p>
        </details>
        <dl>
            <dt>Who are the users?</dt>
            <dd>Enterprise teams and small businesses use our solutions.</dd>
        </dl>
        </body></html>
        """
        dom = geo_mod.GEODOMParser()
        dom.feed(html_pure_faq)

        genres = geo_mod.analyze_evidence_genres(html_pure_faq, dom.extracted_text, dom)
        self.assertTrue(genres["standalone_faq_deficit"])
        self.assertTrue(genres["has_qa_format"])

    def test_detect_keyword_stuffing_direct(self):
        """Token repetition density > 4.5% triggers EXCESSIVE_KEYWORD_DENSITY."""
        stuffed_text = (
            "Enterprise CRM enterprise crm solution for enterprise CRM analytics. "
            "Our enterprise crm provides enterprise crm capabilities for enterprise crm workflows. "
            "Choose enterprise crm for best enterprise crm management and enterprise crm tracking. "
        ) * 15
        res = geo_mod.detect_keyword_stuffing(stuffed_text)
        self.assertTrue(res["is_stuffed"])
        self.assertGreater(res["max_density"], 0.045)
        self.assertTrue(any(w in ["enterprise", "crm"] for w, _ in res["top_repeated_words"]))

        # Natural diverse text should NOT be stuffed
        diverse_text = (
            "Modern distributed applications require robust telemetry, automated scaling policies, "
            "and secure identity propagation across cluster namespaces. Developers configure declarative manifests "
            "to orchestrate containerized workloads with minimal latency overhead. High availability systems distribute "
            "incoming traffic across multi-region availability zones using deterministic consistent hashing algorithms. "
            "Observability platforms collect distributed traces, structured logs, and Prometheus metrics to guarantee "
            "sub-millisecond incident response times for mission-critical enterprise infrastructure. Engineering teams "
            "continuously optimize query execution paths, database indexing strategies, and caching layers to minimize "
            "end-user round-trip network delays and maintain operational excellence under heavy load spikes."
        )
        res_clean = geo_mod.detect_keyword_stuffing(diverse_text)
        self.assertFalse(res_clean["is_stuffed"])
        self.assertLess(res_clean["max_density"], 0.045)

    def test_bluf_placement_primacy(self):
        """BLUF verification: core answer in top 30% vs buried in bottom."""
        # Page with clear BLUF definition right at start
        bluf_early_text = (
            "Antigravity is an automated generative engine optimization platform that accelerates agent indexing. "
            + ("Here is secondary supporting context explaining general industry background and nuances in detail. " * 30)
        )
        words_early = len(bluf_early_text.split())
        res_early = geo_mod.analyze_bluf_placement(bluf_early_text, words_early)
        self.assertTrue(res_early["bluf_present_in_top30"])
        self.assertLess(res_early["first_answer_position_pct"], 0.30)

        # Page with answer delayed deep in body
        bluf_late_text = (
            ("Introductory background discussion detailing history from 1995 to 2020 without defining subject. " * 40)
            + "Antigravity provides an automated generative engine optimization platform."
        )
        words_late = len(bluf_late_text.split())
        res_late = geo_mod.analyze_bluf_placement(bluf_late_text, words_late)
        self.assertFalse(res_late["bluf_present_in_top30"])
        self.assertGreater(res_late["first_answer_position_pct"], 0.50)

    def test_end_to_end_audit_with_all_deep_geo_signals(self):
        """End-to-end CLI execution checks recommendations and summary keys."""
        inv_data = {
            "site": "https://deepgeotest.com",
            "pages": [
                {
                    "url": "https://deepgeotest.com/docs/latency",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "documentation",
                    "html": """
                    <html><body>
                    <h1>Latency Optimization</h1>
                    <p>Antigravity optimizes sub-millisecond query pipelines by caching intermediate AST tokens. Therefore, pipeline latency decreases by 52.4%.</p>
                    <blockquote>"Token caching reduces pipeline memory thrashing," said Dr. Marcus Vance, Chief Architect.</blockquote>
                    <pre><code>
                    def fetch_ast(node_id):
                        return cache.get(node_id)
                    </code></pre>
                    <table>
                        <thead><tr><th>Mode</th><th>Latency</th></tr></thead>
                        <tbody><tr><td>Warm</td><td>0.8ms</td></tr></tbody>
                    </table>
                    <ol>
                        <li>Initialize persistent cache.</li>
                        <li>Hydrate schema tokens.</li>
                    </ol>
                    </body></html>
                    """,
                },
                {
                    "url": "https://deepgeotest.com/stuffed-seo",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": "<html><body><h1>SEO Hacks</h1><p>" + ("keyword stuffing keyword stuffing keyword stuffing keyword " * 50) + "</p></body></html>",
                },
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump({"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f)

        res = subprocess.run(
            ["python3", self.script_path, "--site", "https://deepgeotest.com", "--inventory", self.test_inv, "--state", self.test_state],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "ok")

        # Must include geo_citability_summary
        self.assertIn("geo_citability_summary", data)
        summary = data["geo_citability_summary"]
        self.assertIn("average_citability_score", summary)
        self.assertIn("pages_analyzed", summary)
        self.assertIn("evidence_genres_distribution", summary)

        # Stuffed page should trigger EXCESSIVE_KEYWORD_DENSITY
        cause_ids = [f.get("cause_id") for f in data.get("findings", [])]
        self.assertIn("EXCESSIVE_KEYWORD_DENSITY", cause_ids)

        # Verify page improvement plans include empirical dimensions
        self.assertIn("page_improvement_plans", data)
        doc_plan = next(p for p in data["page_improvement_plans"] if "/docs/latency" in p["url"])
        self.assertIn("evidence_genres", doc_plan)
        self.assertIn("attributed_quotations", doc_plan)
        self.assertIn("bluf_placement", doc_plan)


if __name__ == "__main__":
    unittest.main()
