"""Zero-Trust SSRF Security Policy and Network Guardrails.

Enforces strict scheme validation, DNS resolution, and IP classification
blocking loopback, RFC 1918 private, link-local (cloud metadata), carrier-grade NAT,
and IPv4-mapped IPv6 addresses.
Pure Python standard library (socket, ipaddress, urllib.parse).
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Optional, Set, Tuple
from urllib.parse import urljoin, urlparse


class SecurityValidationError(ValueError):
    """Raised when a URL or IP fails security validation."""


class SecurityPolicy:
    """Zero-trust SSRF validation policy for web requests and redirects."""

    ALLOWED_SCHEMES: Set[str] = {"http", "https"}

    # Cloud metadata and hazardous IP literals
    BLOCKED_IPS: Set[str] = {
        "169.254.169.254",  # AWS/GCP/Azure link-local metadata
        "169.254.170.2",    # AWS ECS task metadata
        "100.100.100.200",  # Alibaba Cloud metadata
        "0.0.0.0",
        "255.255.255.255",
    }

    # Hazardous hostnames
    BLOCKED_HOSTNAMES: Set[str] = {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "instance-data",
    }

    def __init__(
        self,
        allow_private_ips: bool = False,
        require_https: bool = False,
        allow_downgrade_redirects: bool = False,
    ) -> None:
        self.allow_private_ips = allow_private_ips
        self.require_https = require_https
        self.allow_downgrade_redirects = allow_downgrade_redirects

    def is_ip_safe(self, ip_str: str) -> Tuple[bool, str]:
        """Classify an IP string against SSRF blacklists."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Malformed IP address literal: {ip_str}"

        # Check explicit blacklisted IPs
        if ip_str in self.BLOCKED_IPS:
            return False, f"Blocked metadata or reserved IP address: {ip_str}"

        # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
            mapped_ipv4 = ip_obj.ipv4_mapped
            return self.is_ip_safe(str(mapped_ipv4))

        if not self.allow_private_ips:
            if ip_obj.is_loopback:
                return False, f"Loopback address rejected: {ip_str}"
            if ip_obj.is_private:
                return False, f"Private address (RFC 1918 / RFC 4193) rejected: {ip_str}"
            if ip_obj.is_link_local:
                return False, f"Link-local address rejected: {ip_str}"
            if ip_obj.is_reserved:
                return False, f"Reserved address rejected: {ip_str}"
            if ip_obj.is_multicast:
                return False, f"Multicast address rejected: {ip_str}"
            if ip_obj.is_unspecified:
                return False, f"Unspecified address rejected: {ip_str}"

            # Check Carrier-Grade NAT (RFC 6598: 100.64.0.0/10)
            if isinstance(ip_obj, ipaddress.IPv4Address):
                cgnat = ipaddress.IPv4Network("100.64.0.0/10")
                if ip_obj in cgnat:
                    return False, f"Carrier-grade NAT address (RFC 6598) rejected: {ip_str}"

        return True, "IP address is permissible"

    def resolve_and_verify_host(self, host: str, port: int = 443) -> Tuple[bool, str, Optional[str]]:
        """Pre-resolve hostname via DNS and check all returned IPs for safety."""
        clean_host = host.strip().lower()
        if not clean_host:
            return False, "Empty hostname", None

        if clean_host in self.BLOCKED_HOSTNAMES or clean_host.endswith(".internal") or clean_host.endswith(".local"):
            return False, f"Blocked internal hostname: {clean_host}", None

        # If host is already an IP address
        try:
            ip_obj = ipaddress.ip_address(clean_host)
            safe, reason = self.is_ip_safe(str(ip_obj))
            return safe, reason, str(ip_obj)
        except ValueError:
            pass  # It's a hostname, proceed to DNS resolution

        # Resolve via DNS
        try:
            addr_info = socket.getaddrinfo(
                clean_host,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        except (socket.gaierror, socket.herror, OSError) as e:
            return False, f"DNS resolution failed for {clean_host}: {e}", None

        if not addr_info:
            return False, f"No DNS records found for {clean_host}", None

        resolved_ip: Optional[str] = None
        for _, _, _, _, sockaddr in addr_info:
            ip_str = str(sockaddr[0])
            safe, reason = self.is_ip_safe(ip_str)
            if not safe:
                return False, f"Host {clean_host} resolved to disallowed IP ({ip_str}): {reason}", None
            if resolved_ip is None:
                resolved_ip = ip_str

        return True, "Host resolution verified safe", resolved_ip

    def validate_url(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """Validate target URL for scheme, hostname, and IP safety."""
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Failed to parse URL: {e}", None

        scheme = parsed.scheme.lower()
        if scheme not in self.ALLOWED_SCHEMES:
            return False, f"Disallowed URL scheme: {scheme} (only HTTP/HTTPS permitted)", None

        if self.require_https and scheme != "https":
            return False, "HTTPS is strictly required by policy", None

        host = parsed.hostname
        if not host:
            return False, "Missing hostname in URL", None

        port = parsed.port or (443 if scheme == "https" else 80)
        return self.resolve_and_verify_host(host, port)

    def validate_redirect(
        self, original_url: str, new_location: str
    ) -> Tuple[bool, str, str, Optional[str]]:
        """Validate a redirect target URL and prevent scheme downgrade or SSRF evasion."""
        resolved_new_url = urljoin(original_url, new_location)
        orig_parsed = urlparse(original_url)
        new_parsed = urlparse(resolved_new_url)

        # Prevent HTTPS to HTTP downgrade if policy prohibits
        if not self.allow_downgrade_redirects and orig_parsed.scheme == "https" and new_parsed.scheme == "http":
            return False, "Insecure scheme downgrade from HTTPS to HTTP blocked", resolved_new_url, None

        safe, reason, ip = self.validate_url(resolved_new_url)
        if not safe:
            return False, f"Redirect target rejected: {reason}", resolved_new_url, None

        return True, "Redirect target is safe", resolved_new_url, ip
