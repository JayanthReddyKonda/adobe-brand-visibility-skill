"""Legacy test forwarder for Schema Validation tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_validate_report import TestValidateReport

__all__ = ["TestValidateReport"]

if __name__ == "__main__":
    unittest.main()
