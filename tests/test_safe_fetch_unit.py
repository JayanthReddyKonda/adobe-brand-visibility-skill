"""Legacy test forwarder for Safe Fetch unit tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_safe_fetch import TestSafeFetch

__all__ = ["TestSafeFetch"]

if __name__ == "__main__":
    unittest.main()
