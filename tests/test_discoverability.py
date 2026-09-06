"""Legacy test forwarder for Discoverability Audit tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_discoverability_unit import TestDiscoverabilityUnit

__all__ = ["TestDiscoverabilityUnit"]

if __name__ == "__main__":
    unittest.main()
