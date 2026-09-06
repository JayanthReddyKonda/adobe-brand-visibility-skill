"""Legacy test forwarder for Security Policy tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.unit.test_security_policy import TestSecurityPolicy

__all__ = ["TestSecurityPolicy"]

if __name__ == "__main__":
    unittest.main()
