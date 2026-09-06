"""Legacy test forwarder for Web Scraper Skill tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.integration.test_crawler_pipeline import TestCrawlerPipeline

__all__ = ["TestCrawlerPipeline"]

if __name__ == "__main__":
    unittest.main()
