"""Legacy test forwarder for DOM parser tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_crawler_components import TestCrawlerComponents

__all__ = ["TestCrawlerComponents"]

if __name__ == "__main__":
    unittest.main()
