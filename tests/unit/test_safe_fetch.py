"""Unit tests for safe_fetch network fetcher across skills."""

import os
import socket
import sys
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
ORCH_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "scripts")
for p in [PROJECT_ROOT, SCRAPER_DIR, ORCH_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import safe_fetch


class TestSafeFetch(unittest.TestCase):
    """Verifies safe_fetch behavior under normal, boundary, and failure conditions."""

    def test_safe_fetch_ssrf_blocked(self):
        """Failure test: Target IP in private range returns None status and blocked message."""
        status, body, final_url, err = safe_fetch.safe_fetch("http://127.0.0.1/admin")
        self.assertIsNone(status)
        self.assertFalse(body)
        self.assertIn("blocked network", err)

    def test_safe_fetch_cloud_metadata_blocked(self):
        """Failure test: Cloud metadata service returns None status."""
        status, body, final_url, err = safe_fetch.safe_fetch("http://169.254.169.254/latest/meta-data/")
        self.assertIsNone(status)
        self.assertFalse(body)
        self.assertIn("blocked network", err)

    def test_safe_fetch_malformed_url(self):
        """Boundary test: Malformed scheme or empty URL handled cleanly without crash."""
        status, body, final_url, err = safe_fetch.safe_fetch("ftp://example.com/file")
        self.assertIsNone(status)
        self.assertTrue("disallowed scheme" in err.lower() or "unsupported scheme" in err.lower())

    @patch("safe_fetch._is_safe_host")
    @patch("http.client.HTTPConnection")
    def test_safe_fetch_timeout_inconclusive(self, mock_conn_cls, mock_safe):
        """Failure/inconclusive test: Socket timeout returns None gracefully without crash."""
        mock_safe.return_value = (True, "OK", [("", "", "", "", ("93.184.216.34", 80))])
        mock_conn = MagicMock()
        mock_conn.getresponse.side_effect = socket.timeout("Timed out")
        mock_conn_cls.return_value = mock_conn

        status, body, final_url, err = safe_fetch.safe_fetch("http://example.com/slow", timeout=1)
        self.assertIsNone(status)
        self.assertFalse(body)

    @patch("safe_fetch._is_safe_host")
    @patch("http.client.HTTPConnection")
    def test_safe_fetch_connection_refused(self, mock_conn_cls, mock_safe):
        """Failure test: Connection refused returns None cleanly."""
        mock_safe.return_value = (True, "OK", [("", "", "", "", ("93.184.216.34", 80))])
        mock_conn = MagicMock()
        mock_conn.request.side_effect = ConnectionRefusedError("Connection refused")
        mock_conn_cls.return_value = mock_conn

        status, body, final_url, err = safe_fetch.safe_fetch("http://example.com/down")
        self.assertIsNone(status)
        self.assertFalse(body)

    def test_safe_fetch_carrier_grade_nat_blocked(self):
        """Failure test: Carrier-Grade NAT (100.64.0.0/10) is blocked."""
        status, body, final_url, err = safe_fetch.safe_fetch("http://100.64.0.1/")
        self.assertIsNone(status)
        self.assertIn("blocked network", err)

    def test_safe_fetch_alibaba_and_ecs_metadata_blocked(self):
        """Failure test: Alibaba and AWS ECS metadata endpoints blocked."""
        status, _, _, err = safe_fetch.safe_fetch("http://100.100.100.200/")
        self.assertIsNone(status)
        self.assertIn("blocked network", err)

        status, _, _, err = safe_fetch.safe_fetch("http://169.254.170.2/")
        self.assertIsNone(status)
        self.assertIn("blocked network", err)

    def test_safe_fetch_bracketed_ipv6_loopback_blocked(self):
        """Failure test: Bracketed IPv6 loopback [::1] is cleanly blocked without DNS error."""
        status, _, _, err = safe_fetch.safe_fetch("http://[::1]/")
        self.assertIsNone(status)
        self.assertIn("blocked network", err)


if __name__ == "__main__":
    unittest.main()
