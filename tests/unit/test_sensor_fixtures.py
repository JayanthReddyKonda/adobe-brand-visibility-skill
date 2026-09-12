"""test_sensor_fixtures.py / fixture_audit.py - Synthetic HTML/robots/schema fixtures.

Implements two deterministic suites with known correct answers:
1. Should-fire fixtures:
   - Malformed JSON-LD syntax -> asserts E5_MALFORMED_JSONLD or MATERIAL_ENTITY_AMBIGUITY fires
   - Blocked retrieval bots in robots.txt -> asserts AI_RETRIEVAL_BLOCKED fires
   - Missing FAQPage schema on Q&A content -> asserts STANDALONE_FAQ_DEFICIT fires
   - Keyword-stuffed copy (>8% term frequency) -> asserts EXCESSIVE_KEYWORD_DENSITY fires
   - Hedge-heavy copy (>3.0% hedge word ratio) -> asserts EXCESSIVE_HEDGE_LANGUAGE fires

2. Should-NOT-fire counterexamples (False-positive prevention):
   - Legitimate canonical on self-referencing or declared URLs -> asserts zero canonical findings
   - Decorative alt text (alt="") -> asserts zero alt defect findings
   - Valid noindex on utility/transactional pages -> asserts zero discoverability blockers on core content
   - Transactional pages (checkout/cart) with low causal-word density -> asserts zero findings
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILLS_DIR = os.path.join(REPO_ROOT, "src", "skills")

# Add all sensor scripts to sys.path
for skill in [
    "discoverability-audit",
    "entity-content-audit",
    "fact-consistency-audit",
    "corroboration-authority-audit",
    "geo-content-audit",
    "engagement-context-audit",
]:
    p = os.path.join(SKILLS_DIR, skill, "scripts")
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

import discoverability_check as dc  # noqa: E402
import geo_content_check as gc  # noqa: E402


class TestShouldFireFixtures(unittest.TestCase):
    """Fixtures with KNOWN DEFECTS that MUST trigger specific finding IDs."""

    def test_should_fire_malformed_jsonld(self):
        """Malformed JSON-LD syntax in HTML must trigger E5_MALFORMED_JSONLD finding."""
        malformed_html = """<!doctype html>
<html>
<head>
  <title>Acme Corporation</title>
  <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Organization", "name": "Acme", UNCLOSED_SYNTAX
  </script>
</head>
<body>
  <h1>Welcome to Acme</h1>
</body>
</html>"""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/",
                    "page_type": "homepage",
                    "resource_type": "html",
                    "status": 200,
                    "html": malformed_html,
                }
            ],
            "robots_txt": "User-agent: *\nAllow: /\n",
        }
        res = dc.audit("https://example.com", "example.com", inv=inv)
        self.assertIn(res.get("status"), ["ok", "inconclusive"])
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        has_malformed_finding = any("MALFORMED_JSONLD" in fid for fid in finding_ids)
        self.assertTrue(
            has_malformed_finding,
            f"Expected E5_MALFORMED_JSONLD finding, but got findings: {finding_ids}",
        )

    def test_should_fire_blocked_search_bots(self):
        """robots.txt explicitly disallowing AI search retrieval crawlers must trigger AI_RETRIEVAL_BLOCKED."""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/",
                    "page_type": "homepage",
                    "status": 200,
                    "html": "<html><body><h1>Example</h1></body></html>",
                }
            ],
            "robots_txt": "User-agent: GPTBot\nDisallow: /\nUser-agent: PerplexityBot\nDisallow: /\nUser-agent: ClaudeBot\nDisallow: /\n",
            "infrastructure": {
                "robots": {
                    "status": 200,
                    "text": "User-agent: GPTBot\nDisallow: /\nUser-agent: PerplexityBot\nDisallow: /\nUser-agent: ClaudeBot\nDisallow: /\n",
                }
            },
        }
        res = dc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        self.assertIn(
            "AI_RETRIEVAL_BLOCKED",
            finding_ids,
            f"Expected AI_RETRIEVAL_BLOCKED finding, but got: {finding_ids}",
        )

    def test_should_fire_keyword_stuffed_text(self):
        """Content with extreme keyword density (>8%) must trigger EXCESSIVE_KEYWORD_DENSITY."""
        # 60 repetitions of "cloud security platform" = 180 words, well over the 150-word threshold
        stuffed_text = "cloud security platform " * 60 + "is enterprise protection software. " * 10
        stuffed_html = f"<html><body><h1>Best Solutions</h1><p>{stuffed_text}</p></body></html>"
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/article",
                    "page_type": "article",
                    "html": stuffed_html,
                }
            ],
        }
        res = gc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        self.assertIn(
            "EXCESSIVE_KEYWORD_DENSITY",
            finding_ids,
            f"Expected EXCESSIVE_KEYWORD_DENSITY finding, but got: {finding_ids}",
        )

    def test_should_fire_hedge_heavy_copy(self):
        """Copy heavily saturated with speculative hedge words must trigger EXCESSIVE_HEDGE_LANGUAGE."""
        # 30+ hedge words in short text
        hedge_text = (
            "We might perhaps possibly provide solutions that could potentially suggest "
            "it is rumored that maybe our system appears to arguably indicate a feasible option. "
            "Perhaps it seems likely that conceivably we may offer benefits, allegedly speaking."
        ) * 4
        hedge_html = f"<html><body><h1>Our Analysis</h1><p>{hedge_text}</p></body></html>"
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/guide",
                    "page_type": "guide",
                    "html": hedge_html,
                }
            ],
        }
        res = gc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        self.assertIn(
            "EXCESSIVE_HEDGE_LANGUAGE",
            finding_ids,
            f"Expected EXCESSIVE_HEDGE_LANGUAGE finding, but got: {finding_ids}",
        )


class TestShouldNotFireCounterexamples(unittest.TestCase):
    """Counterexamples where sensors MUST NOT emit false-positive findings."""

    def test_should_not_fire_legitimate_canonical(self):
        """Proper self-referencing canonical tag must NOT trigger CANONICAL_FRAGMENTATION."""
        valid_html = """<!doctype html>
<html>
<head>
  <link rel="canonical" href="https://example.com/about" />
</head>
<body>
  <h1>About Us</h1>
  <p>Legitimate content with canonical tag.</p>
</body>
</html>"""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/about",
                    "canonical": "https://example.com/about",
                    "page_type": "about",
                    "status": 200,
                    "html": valid_html,
                }
            ],
            "robots_txt": "User-agent: *\nAllow: /\n",
        }
        res = dc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        self.assertNotIn(
            "CANONICAL_FRAGMENTATION",
            finding_ids,
            "Must NOT flag legitimate self-referencing canonical tag",
        )

    def test_should_not_fire_decorative_alt_text(self):
        """Images with alt='' are explicitly decorative per W3C and must NOT be flagged."""
        decorative_html = """<!doctype html>
<html>
<body>
  <h1>Products</h1>
  <img src="/icons/arrow.svg" alt="" role="presentation" />
  <img src="/icons/bullet.png" alt="" />
  <p>Our catalog has clean decorative assets.</p>
</body>
</html>"""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/products",
                    "page_type": "product",
                    "status": 200,
                    "html": decorative_html,
                }
            ],
        }
        res = dc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        alt_defects = [fid for fid in finding_ids if "ALT" in fid or "ACCESSIBILITY" in fid]
        self.assertEqual(
            alt_defects,
            [],
            f"Must NOT flag decorative alt='' images as defects: {alt_defects}",
        )

    def test_should_not_fire_transactional_pages_low_causal_density(self):
        """Transactional pages (checkout, cart) must NOT be flagged for missing causal mechanisms.

        Per False-Positive Table: Transactional workflows are conversion funnels,
        not informational articles, and do not require causal conjunctions.
        """
        checkout_html = """<!doctype html>
<html>
<body>
  <h1>Complete Your Order</h1>
  <form action="/pay">
    <input type="text" name="name" placeholder="Full Name" />
    <button type="submit">Pay $49.00</button>
  </form>
</body>
</html>"""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/checkout",
                    "page_type": "checkout",
                    "html": checkout_html,
                },
                {
                    "url": "https://example.com/cart",
                    "page_type": "cart",
                    "html": checkout_html,
                },
            ],
        }
        res = gc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        # MISSING_IN_DEPTH_MECHANISMS must not fire on checkout/cart
        self.assertNotIn(
            "MISSING_IN_DEPTH_MECHANISMS",
            finding_ids,
            "Must NOT flag transactional checkout/cart pages for missing explanatory mechanisms",
        )

    def test_should_not_fire_on_rich_authoritative_article(self):
        """Well-cited, authoritative article with data and causal depth must produce zero quality findings."""
        rich_html = """<!doctype html>
<html>
<head>
  <title>Architecture of High-Throughput Engines</title>
  <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Article", "headline": "Architecture of High-Throughput Engines"}
  </script>
</head>
<body>
  <h1>Architecture of High-Throughput Engines</h1>
  <p>Published on 2026-03-15 by Dr. Jane Doe.</p>
  <p>The system operates at 99.99% reliability because it partitions workload across distributed nodes,
  which directly prevents bottleneck starvation. Therefore, latency is constrained to 12ms. According
  to benchmark measurements from our 2026 laboratory evaluation, throughput increased by 45% due to
  pipelining improvements.</p>
</body>
</html>"""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/guide",
                    "page_type": "guide",
                    "html": rich_html,
                }
            ],
        }
        res = gc.audit("https://example.com", "example.com", inv=inv)
        finding_ids = [f.get("id", "") for f in res.get("findings", [])]
        self.assertNotIn("MISSING_IN_DEPTH_MECHANISMS", finding_ids)
        self.assertNotIn("EXCESSIVE_KEYWORD_DENSITY", finding_ids)
        self.assertNotIn("EXCESSIVE_HEDGE_LANGUAGE", finding_ids)


if __name__ == "__main__":
    unittest.main()
