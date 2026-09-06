"""Legacy test forwarder for Specialist Sensors tests."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.integration.test_specialist_contracts import TestSpecialistContracts

__all__ = ["TestSpecialistContracts"]

if __name__ == "__main__":
    unittest.main()
