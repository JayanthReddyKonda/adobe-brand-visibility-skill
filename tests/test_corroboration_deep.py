"""Legacy test forwarder for Corroboration Authority tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_corroboration_unit import TestCorroborationUnit

__all__ = ["TestCorroborationUnit"]

if __name__ == "__main__":
    unittest.main()
