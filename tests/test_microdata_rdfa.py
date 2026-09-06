"""Legacy test forwarder for Microdata and RDFa tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_entity_content_unit import TestEntityContentUnit

__all__ = ["TestEntityContentUnit"]

if __name__ == "__main__":
    unittest.main()
