"""Legacy test forwarder for Engagement Deep tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_engagement_unit import TestEngagementUnit

__all__ = ["TestEngagementUnit"]

if __name__ == "__main__":
    unittest.main()
