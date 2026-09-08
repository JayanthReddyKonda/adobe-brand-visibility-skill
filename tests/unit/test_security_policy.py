"""Unit tests for SSRF defense and network security boundaries."""

import os
import socket
import sys
import unittest
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
ORCH_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "scripts")
for p in [PROJECT_ROOT, SCRAPER_DIR, ORCH_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import safe_fetch
from crawler.policy import SecurityPolicy, SecurityValidationError


class TestSecurityPolicy(unittest.TestCase):
    """Verifies strict zero-trust SSRF policy across all IP classes."""

    def setUp(self):
        self.policy = SecurityPolicy()

    def test_public_ipv4_allowed(self):
        """Success test: Valid public IPv4 addresses are permitted."""
        safe, msg = self.policy.is_ip_safe("93.184.216.34")
        self.assertTrue(safe)
        self.assertIn("Public IP verified", msg)

        safe, _ = self.policy.is_ip_safe("8.8.8.8")
        self.assertTrue(safe)

    def test_public_ipv6_allowed(self):
        """Success test: Valid public global unicast IPv6 addresses are permitted."""
        safe, msg = self.policy.is_ip_safe("2606:2800:220:1:248:1893:25c8:1946")
        self.assertTrue(safe)
        self.assertIn("Public IP verified", msg)

    def test_loopback_ipv4_blocked(self):
        """Failure test: 127.0.0.0/8 loopbacks are strictly blocked."""
        safe, msg = self.policy.is_ip_safe("127.0.0.1")
        self.assertFalse(safe)
        self.assertIn("loopback", msg.lower())

        safe, _ = self.policy.is_ip_safe("127.255.255.255")
        self.assertFalse(safe)

    def test_private_rfc1918_blocked(self):
        """Failure test: RFC 1918 private subnets are strictly blocked."""
        # 10.0.0.0/8
        safe, _ = self.policy.is_ip_safe("10.0.0.1")
        self.assertFalse(safe)
        # 172.16.0.0/12
        safe, _ = self.policy.is_ip_safe("172.16.0.1")
        self.assertFalse(safe)
        # 192.168.0.0/16
        safe, _ = self.policy.is_ip_safe("192.168.1.1")
        self.assertFalse(safe)

    def test_cloud_metadata_link_local_blocked(self):
        """Failure test: Cloud metadata service (169.254.169.254) and link-local blocked."""
        safe, msg = self.policy.is_ip_safe("169.254.169.254")
        self.assertFalse(safe)
        safe, _ = self.policy.is_ip_safe("169.254.0.1")
        self.assertFalse(safe)

    def test_ipv6_loopback_and_private_blocked(self):
        """Failure test: IPv6 loopback (::1) and Unique Local Addresses (fc00::/7) are blocked."""
        safe, _ = self.policy.is_ip_safe("::1")
        self.assertFalse(safe)
        safe, _ = self.policy.is_ip_safe("fe80::1")
        self.assertFalse(safe)
        safe, _ = self.policy.is_ip_safe("fc00::1")
        self.assertFalse(safe)

    def test_ipv4_mapped_ipv6_loopback_blocked(self):
        """Failure test: IPv4-mapped IPv6 loopbacks (::ffff:127.0.0.1) are blocked."""
        safe, _ = self.policy.is_ip_safe("::ffff:127.0.0.1")
        self.assertFalse(safe)
        safe, _ = self.policy.is_ip_safe("::ffff:10.0.0.1")
        self.assertFalse(safe)
        safe, _ = self.policy.is_ip_safe("::ffff:169.254.169.254")
        self.assertFalse(safe)

    def test_validate_url_success(self):
        """Success test: Valid public hostname validates cleanly."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
            ]
            scheme, ip, port = self.policy.validate_url_and_resolve("https://example.com/test")
            self.assertEqual(scheme, "https")
            self.assertEqual(ip, "93.184.216.34")
            self.assertEqual(port, 443)

    def test_validate_url_ssrf_attempt_raises(self):
        """Failure test: Target resolving to private IP raises SecurityValidationError."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))
            ]
            with self.assertRaises(SecurityValidationError):
                self.policy.validate_url_and_resolve("http://internal.service.local/")

    def test_safe_fetch_blocks_ssrf(self):
        """Failure test: safe_fetch utility directly blocks private IP targets."""
        status, _, _, err = safe_fetch.safe_fetch("http://127.0.0.1/")
        self.assertIsNone(status)
        self.assertIn("blocked network", err)

    def test_carrier_grade_nat_blocked(self):
        """Failure test: Carrier-Grade NAT (100.64.0.0/10) is blocked."""
        safe, msg = self.policy.is_ip_safe("100.64.0.1")
        self.assertFalse(safe)
        self.assertIn("carrier-grade nat", msg.lower())

    def test_cloud_metadata_alibaba_and_ecs_blocked(self):
        """Failure test: Alibaba (100.100.100.200) and AWS ECS (169.254.170.2) metadata blocked."""
        safe, _ = self.policy.is_ip_safe("100.100.100.200")
        self.assertFalse(safe)
        safe, _ = self.policy.is_ip_safe("169.254.170.2")
        self.assertFalse(safe)

    def test_bracketed_ipv6_handling(self):
        """Success & failure tests: Bracketed IPv6 addresses are parsed cleanly without DNS error."""
        safe, msg, ip = self.policy.resolve_and_verify_host("[::1]")
        self.assertFalse(safe)
        self.assertIn("loopback", msg.lower())

        safe, msg, ip = self.policy.resolve_and_verify_host("[2606:2800:220:1:248:1893:25c8:1946]")
        self.assertTrue(safe)
        self.assertIn("Public IP verified", msg)


if __name__ == "__main__":
    unittest.main()
