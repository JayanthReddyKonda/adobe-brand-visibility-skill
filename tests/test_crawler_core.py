"""Comprehensive unit tests for the Zero-Dependency Audit Web Engine (src/crawler/).

Validates:
- Zero-trust SSRF security policy & redirect re-validation.
- Budget constraints, monotonic deadlines, and byte caps.
- RFC 9309 robots parser with longest-match precedence and fail-closed 5xx handling.
- XML sitemaps and resilient regex fallback.
- Priority frontier route scoring and deduplication.
- Streaming HTML parser, metadata, and JSON-LD graph flattening.
- Trafilatura boilerplate stripping, SNR, and sparse SPA detection.
- High-level Agent Query API.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
SCRAPER_SCRIPTS_DIR = os.path.join(SRC_DIR, "skills", "web-scraper", "scripts")
ORCH_SCRIPTS_DIR = os.path.join(SRC_DIR, "skills", "audit-orchestrator", "scripts")
for p in [SRC_DIR, SCRAPER_SCRIPTS_DIR, ORCH_SCRIPTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from crawler import (
    Budget,
    BudgetExhaustedError,
    EvidenceExtractor,
    Frontier,
    JsonLdExtractor,
    LinkProcessor,
    MetadataProcessor,
    PageClassifier,
    RobotsAuditor,
    RobotsOutcome,
    SecurityPolicy,
    SitemapParser,
    WebAuditEngine,
)
from crawler.parser import StreamingHTMLParser


class TestCrawlerSecurityPolicy(unittest.TestCase):
    """Zero-trust SSRF sandboxing test suite."""

    def setUp(self):
        self.policy = SecurityPolicy()

    def test_blocks_loopback_ipv4_and_ipv6(self):
        safe, reason = self.policy.is_ip_safe("127.0.0.1")
        self.assertFalse(safe)
        self.assertIn("Loopback", reason)

        safe, reason = self.policy.is_ip_safe("::1")
        self.assertFalse(safe)
        self.assertIn("Loopback", reason)

    def test_blocks_rfc1918_private_ips(self):
        for ip in ["10.0.0.1", "172.16.5.10", "192.168.1.1"]:
            safe, reason = self.policy.is_ip_safe(ip)
            self.assertFalse(safe, f"Should block RFC 1918 IP: {ip}")
            self.assertIn("Private", reason)

    def test_blocks_cloud_metadata_link_local(self):
        safe, reason = self.policy.is_ip_safe("169.254.169.254")
        self.assertFalse(safe)

    def test_blocks_cgnat_ips(self):
        safe, reason = self.policy.is_ip_safe("100.64.0.1")
        self.assertFalse(safe)
        self.assertIn("Carrier-grade NAT", reason)

    def test_blocks_ipv4_mapped_ipv6_exploits(self):
        safe, reason = self.policy.is_ip_safe("::ffff:127.0.0.1")
        self.assertFalse(safe)
        self.assertIn("Loopback", reason)

        safe, reason = self.policy.is_ip_safe("::ffff:169.254.169.254")
        self.assertFalse(safe)

    def test_blocks_disallowed_schemes(self):
        for bad_url in [
            "file:///etc/passwd",
            "ftp://ftp.example.com",
            "gopher://gopher.floodgap.com",
            "data:text/html,<html></html>",
        ]:
            safe, reason, _ = self.policy.validate_url(bad_url)
            self.assertFalse(safe)
            self.assertIn("Disallowed URL scheme", reason)

    def test_blocks_insecure_redirect_downgrade(self):
        safe, reason, _, _ = self.policy.validate_redirect(
            "https://example.com/checkout", "http://example.com/login"
        )
        self.assertFalse(safe)
        self.assertIn("downgrade", reason.lower())


class TestCrawlerBudget(unittest.TestCase):
    """Audit deadline and resource limits test suite."""

    def test_tracks_and_exhausts_pages_limit(self):
        budget = Budget(time_limit_sec=60.0, max_pages=3)
        self.assertTrue(budget.can_fetch_page())
        budget.record_page()
        budget.record_page()
        self.assertFalse(budget.is_exhausted())
        budget.record_page()
        self.assertTrue(budget.is_exhausted())
        self.assertFalse(budget.can_fetch_page())

    def test_tracks_and_exhausts_byte_limit(self):
        budget = Budget(time_limit_sec=60.0, max_pages=10, max_total_bytes=1000)
        budget.record_bytes(600)
        self.assertFalse(budget.is_exhausted())
        budget.record_bytes(500)
        self.assertTrue(budget.is_exhausted())
        with self.assertRaises(BudgetExhaustedError):
            budget.check_or_raise()


class TestCrawlerRobots(unittest.TestCase):
    """RFC 9309 parser and status outcome test suite."""

    def test_longest_match_rule_precedence(self):
        robots_txt = """
User-agent: *
Disallow: /private/
Allow: /private/public-report$
"""
        auditor = RobotsAuditor(content=robots_txt, status_code=200)
        # Longest match wins: /private/public-report is allowed even though /private/ is disallowed
        self.assertTrue(auditor.is_allowed("BrandAuditBot", "/private/public-report"))
        self.assertFalse(auditor.is_allowed("BrandAuditBot", "/private/secret.html"))

    def test_rfc9309_fail_closed_on_5xx(self):
        auditor = RobotsAuditor(content="", status_code=503, outcome=RobotsOutcome.SERVER_ERROR)
        # Fail-closed per RFC 9309 section 2.3.1.2 during server errors
        self.assertFalse(auditor.is_allowed("BrandAuditBot", "/anything"))

    def test_rfc9309_fail_open_on_404(self):
        auditor = RobotsAuditor(content="", status_code=404, outcome=RobotsOutcome.NOT_FOUND)
        # Fail-open when robots.txt is not found
        self.assertTrue(auditor.is_allowed("BrandAuditBot", "/anything"))

    def test_ai_bots_matrix_evaluation(self):
        robots_txt = """
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: OAI-SearchBot
Allow: /
"""
        auditor = RobotsAuditor(content=robots_txt, status_code=200)
        matrix = auditor.evaluate_ai_bots_matrix("/")
        self.assertFalse(matrix["GPTBot"]["allowed"])
        self.assertFalse(matrix["ClaudeBot"]["allowed"])
        self.assertTrue(matrix["OAI-SearchBot"]["allowed"])


class TestCrawlerFrontierAndLinks(unittest.TestCase):
    """Frontier priority queue and link processor test suite."""

    def test_route_priority_scoring(self):
        frontier = Frontier()
        frontier.push("https://example.com/blog/2026/01/post", depth=2)
        frontier.push("https://example.com/pricing", depth=1)
        frontier.push("https://example.com/", depth=0)

        # Highest priority pops first: homepage, then pricing, then deep blog
        first = frontier.pop()
        self.assertEqual(first.url, "https://example.com/")
        second = frontier.pop()
        self.assertEqual(second.url, "https://example.com/pricing")
        third = frontier.pop()
        self.assertEqual(third.url, "https://example.com/blog/2026/01/post")

    def test_frontier_deduplication(self):
        frontier = Frontier()
        pushed1 = frontier.push("https://example.com/products")
        pushed2 = frontier.push("https://example.com/products")
        self.assertTrue(pushed1)
        self.assertFalse(pushed2)
        self.assertEqual(frontier.size(), 1)

    def test_link_processor_filters_assets(self):
        self.assertFalse(LinkProcessor.is_crawlable_html_url("https://example.com/brochure.pdf"))
        self.assertFalse(LinkProcessor.is_crawlable_html_url("https://example.com/image.png"))
        self.assertTrue(LinkProcessor.is_crawlable_html_url("https://example.com/about-us"))

    def test_sitemap_parser_and_regex_fallback(self):
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/pricing</loc>
    <priority>0.8</priority>
  </url>
</urlset>"""
        urls, indices = SitemapParser.parse_sitemap(valid_xml)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].loc, "https://example.com/pricing")
        self.assertEqual(urls[0].priority, 0.8)

        malformed_xml = """<invalid> <loc>https://example.com/broken-xml</loc> </invalid>"""
        f_urls, _ = SitemapParser.parse_sitemap(malformed_xml)
        self.assertEqual(len(f_urls), 1)
        self.assertEqual(f_urls[0].loc, "https://example.com/broken-xml")


class TestCrawlerParserAndJsonLd(unittest.TestCase):
    """Streaming HTML parser, metadata, and JSON-LD test suite."""

    def test_streaming_parser_collects_structures(self):
        html = """<!doctype html>
<html lang="en">
<head>
  <title>Acme Corp | Enterprise AI</title>
  <meta name="description" content="Leading AI solutions for enterprises.">
  <meta name="robots" content="index, follow, nosnippet">
  <link rel="canonical" href="https://example.com/">
</head>
<body>
  <header><nav><a href="/pricing">Pricing</a></nav></header>
  <main>
    <h1>Next-Gen Intelligence</h1>
    <h2>Enterprise Tier</h2>
    <p>Deploy AI securely in your VPC.</p>
    <table>
      <tr><th>Feature</th><th>Availability</th></tr>
      <tr><td>SSO</td><td>Included</td></tr>
    </table>
    <code>import acme; acme.init()</code>
  </main>
</body>
</html>"""
        parser = StreamingHTMLParser()
        parser.feed(html)

        self.assertEqual(parser.title, "Acme Corp | Enterprise AI")
        self.assertEqual(parser.canonical, "https://example.com/")
        self.assertEqual(len(parser.headings), 2)
        self.assertEqual(parser.headings[0].text, "Next-Gen Intelligence")
        self.assertIn("main", parser.semantic_landmarks)
        self.assertEqual(len(parser.tables), 1)
        self.assertEqual(parser.tables[0].headers, ["Feature", "Availability"])

        metadata, obs = MetadataProcessor.process_metadata(parser.meta_tags, "https://example.com/")
        self.assertIn("nosnippet", metadata["robots_directives"])
        self.assertTrue(any(o.value == "nosnippet_detected" for o in obs))

    def test_jsonld_flattening_and_provenance(self):
        jsonld_content = """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "name": "Acme Global",
      "telephone": "+1-800-555-0199",
      "email": "contact@acmeglobal.com"
    },
    {
      "@type": "Product",
      "name": "Cloud Pro",
      "offers": {
        "@type": "Offer",
        "price": "99.00",
        "priceCurrency": "USD"
      }
    }
  ]
}"""
        raw_blocks = [(jsonld_content, "head", 0)]
        schemas, facts, obs = JsonLdExtractor.parse_blocks(raw_blocks, "https://example.com/product")

        self.assertEqual(len(schemas), 2)
        self.assertEqual(schemas[0]["_provenance"]["block_index"], 0)
        self.assertEqual(schemas[0]["_provenance"]["location"], "head")

        # Verify atomic fact candidates
        prices = [f for f in facts if f.attribute == "price"]
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0].value, 99.0)
        self.assertEqual(prices[0].currency, "USD")
        self.assertEqual(prices[0].locator, "[0].Product.offers[0].price")


class TestCrawlerEvidenceAndAgentAPI(unittest.TestCase):
    """Trafilatura boilerplate, SNR, rendering observation, and Agent API test suite."""

    def test_trafilatura_boilerplate_stripping_and_snr(self):
        html = """<html>
<head><style>.header { color: red; }</style></head>
<body>
  <header><nav><a href="/">Home</a><a href="/about">About</a></nav></header>
  <main>
    <p>This is the genuine substance of the page that AI engines must extract.</p>
  </main>
  <footer><p>Copyright 2026 Acme Corp. All rights reserved.</p></footer>
  <script>console.log("analytics");</script>
</body>
</html>"""
        clean = EvidenceExtractor.strip_boilerplate(html)
        self.assertIn("genuine substance", clean)
        self.assertNotIn("console.log", clean)
        self.assertNotIn("Copyright 2026", clean)

        snr = EvidenceExtractor.calculate_snr(clean, html)
        self.assertGreater(snr, 0.0)

    def test_detects_sparse_spa_shell(self):
        empty_spa_html = """<!doctype html>
<html>
<head><title>Modern React App</title></head>
<body>
  <div id="root"></div>
  <script src="/bundle.js"></script>
</body>
</html>"""
        clean_text = EvidenceExtractor.strip_boilerplate(empty_spa_html)
        obs = EvidenceExtractor.detect_rendering_limitations(empty_spa_html, clean_text, "https://example.com/app")
        self.assertTrue(any(o.value == "server_html_appears_sparse" for o in obs))

    def test_page_classifier(self):
        self.assertEqual(PageClassifier.classify("https://example.com/")["value"], "homepage")
        self.assertEqual(PageClassifier.classify("https://example.com/pricing")["value"], "pricing")
        self.assertEqual(PageClassifier.classify("https://example.com/products/cloud-pro")["value"], "product_detail")
        self.assertEqual(PageClassifier.classify("https://example.com/contact-us")["value"], "contact")

    def test_web_audit_engine_agent_api(self):
        engine = WebAuditEngine()
        # Mock inject a page model
        from crawler.models import FactCandidate, PageModel

        mock_page = PageModel(
            url="https://example.com/pricing",
            final_url="https://example.com/pricing",
            status=200,
            title="Transparent Pricing",
            clean_markdown="# Pricing\n\nPlans start at $49/mo",
            page_type={"value": "pricing", "confidence": 0.9},
            facts=[
                FactCandidate(
                    attribute="price",
                    value=49.0,
                    currency="USD",
                    interval="month",
                    source_url="https://example.com/pricing",
                )
            ],
        )
        engine.pages.append(mock_page)
        engine.all_facts.extend(mock_page.facts)

        # Agent Query API tests
        site_map = engine.map_site()
        self.assertEqual(len(site_map), 1)
        self.assertEqual(site_map[0]["type"], "pricing")

        pricing_pages = engine.find_pages("pricing")
        self.assertEqual(len(pricing_pages), 1)

        facts = engine.find_attribute("price")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].value, 49.0)

        inv_dict = engine.to_inventory_dict()
        self.assertIn("pages", inv_dict)
        self.assertEqual(len(inv_dict["pages"]), 1)
        self.assertIn("infrastructure", inv_dict)
        self.assertIn("ai_agent_scrapeability_summary", inv_dict["infrastructure"])

    def test_acquire_inventory_integration(self):
        import acquire_inventory
        self.assertTrue(hasattr(acquire_inventory, "build_inventory"))
        self.assertTrue(hasattr(acquire_inventory, "extract_clean_content"))
        # Test extract_clean_content on sample semantic markup
        html = "<main><h1>Product Title</h1><p>High SNR substantive description.</p></main>"
        res = acquire_inventory.extract_clean_content(html)
        self.assertTrue(res["has_main"])
        self.assertIn("Product Title", res["clean_text"])


if __name__ == "__main__":
    unittest.main()
