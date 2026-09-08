"""
fixture_audit.py - Direct entrypoint alias for fixture audit suite.
Re-exports TestShouldFireFixtures and TestShouldNotFireCounterexamples.
"""
import os
import sys
import unittest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from test_sensor_fixtures import (  # noqa: E402
    TestShouldFireFixtures,
    TestShouldNotFireCounterexamples,
)

__all__ = [
    "TestShouldFireFixtures",
    "TestShouldNotFireCounterexamples",
]

if __name__ == "__main__":
    unittest.main()
