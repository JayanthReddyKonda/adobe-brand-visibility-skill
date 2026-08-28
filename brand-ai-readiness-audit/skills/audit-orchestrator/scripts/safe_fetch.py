"""
safe_fetch.py - Zero-dependency SSRF-safe HTTP/HTTPS fetching utility.

Enforces:
  1. Scheme restriction (http/https only).
  2. DNS / IP pre-resolution and filtering against private, loopback, link-local,
     multicast, and cloud-metadata ranges.
  3. Bounded redirect following with re-validation of target IP at every hop.
  4. Hard response body size caps (prevents memory exhaustion / DoS).
"""

import sys
import socket
import ipaddress
import urllib.request
import urllib.parse
import urllib.error

DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"

# IPv4 and IPv6 blocked networks
BLOCKED_NETWORKS = [
    # IPv4
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),   # CGNAT
    ipaddress.ip_network("198.18.0.0/15"),   # Benchmark tests
    ipaddress.ip_network("224.0.0.0/4"),     # Multicast
    ipaddress.ip_network("240.0.0.0/4"),     # Reserved
    # IPv6
    ipaddress.ip_network("::/128"),          # Unspecified
    ipaddress.ip_network("::1/128"),        # Loopback
    ipaddress.ip_network("fc00::/7"),        # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),       # Link-local
    ipaddress.ip_network("::ffff:0:0/96"),   # IPv4-mapped IPv6
    ipaddress.ip_network("ff00::/8"),        # Multicast
]


def is_ip_allowed(ip_str):
    """Return True if IP is public and not in any reserved/private range."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    # Check builtin properties
    if (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or
            ip_obj.is_multicast or ip_obj.is_reserved or ip_obj.is_unspecified):
        return False

    # Check explicit blocked networks
    for net in BLOCKED_NETWORKS:
        if ip_obj in net:
            return False
    return True


def validate_hostname_ips(hostname, port=80):
    """Resolve hostname and ensure all resolved IP addresses are safe/public.
    Returns (is_safe, error_message, list_of_ips).
    """
    if not hostname:
        return False, "Empty hostname", []
    
    # Check if hostname itself is directly an IP literal
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if not is_ip_allowed(str(ip_obj)):
            return False, f"Target IP {ip_obj} belongs to a private/reserved network (SSRF blocked)", [str(ip_obj)]
        return True, None, [str(ip_obj)]
    except ValueError:
        pass

    try:
        addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        resolved_ips = []
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            resolved_ips.append(ip_str)
            if not is_ip_allowed(ip_str):
                return False, f"Hostname '{hostname}' resolved to private/reserved IP {ip_str} (SSRF blocked)", resolved_ips
        if not resolved_ips:
            return False, f"Could not resolve hostname '{hostname}'", []
        return True, None, list(set(resolved_ips))
    except socket.gaierror as e:
        return False, f"DNS resolution failed for '{hostname}': {e}", []
    except Exception as e:
        return False, f"Socket error resolving '{hostname}': {e}", []


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Custom redirect handler that validates target URL safety before following."""
    def __init__(self, max_redirects=5):
        super().__init__()
        self.max_redirects = max_redirects
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > self.max_redirects:
            raise urllib.error.HTTPError(req.full_url, code, f"Exceeded maximum redirects ({self.max_redirects})", headers, fp)

        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme.lower() not in ("http", "https"):
            raise urllib.error.HTTPError(req.full_url, code, f"Forbidden redirect scheme: {parsed.scheme}", headers, fp)

        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        is_safe, err_msg, _ = validate_hostname_ips(parsed.hostname, port)
        if not is_safe:
            raise urllib.error.HTTPError(req.full_url, code, f"Blocked redirect to unsafe host: {err_msg}", headers, fp)

        return super().redirect_request(req, fp, code, msg, headers, newurl)


def safe_fetch(url, timeout=10, max_bytes=2 * 1024 * 1024, user_agent=DEFAULT_USER_AGENT, method="GET"):
    """Safely fetch a URL with SSRF protection, timeout, and response body size limit.

    Args:
        url: URL string to fetch.
        timeout: Socket timeout in seconds.
        max_bytes: Maximum response body bytes to read.
        user_agent: User-Agent header string.
        method: HTTP method (GET or HEAD).

    Returns:
        (status_code, body_str, headers_dict, error_message)
    """
    if not url or not isinstance(url, str):
        return None, "", {}, "Invalid URL"

    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in ("http", "https"):
        return None, "", {}, f"Unsupported scheme '{parsed.scheme}'; only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return None, "", {}, "Missing hostname in URL"

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    is_safe, err_msg, _ = validate_hostname_ips(hostname, port)
    if not is_safe:
        return None, "", {}, err_msg

    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent},
        method=method.upper()
    )

    opener = urllib.request.build_opener(SafeRedirectHandler(max_redirects=5))

    try:
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            headers = dict(resp.headers)
            if method.upper() == "HEAD":
                return status, "", headers, None

            # Stream response up to max_bytes
            chunks = []
            bytes_read = 0
            while True:
                chunk = resp.read(min(65536, max_bytes - bytes_read + 1))
                if not chunk:
                    break
                chunks.append(chunk)
                bytes_read += len(chunk)
                if bytes_read > max_bytes:
                    break

            raw_body = b"".join(chunks)[:max_bytes]
            # Handle gzip decompression
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if "gzip" in encoding or raw_body.startswith(b"\x1f\x8b") or url.lower().split("?")[0].endswith((".gz", ".xml.gz")):
                try:
                    import gzip
                    raw_body = gzip.decompress(raw_body)
                except Exception:
                    pass

            charset = resp.headers.get_content_charset() or "utf-8"
            body = raw_body.decode(charset, errors="ignore")
            return status, body, headers, None

    except urllib.error.HTTPError as e:
        status = e.code
        headers = dict(e.headers or {})
        try:
            raw_body = e.read(max_bytes)
            encoding = (e.headers.get("Content-Encoding") or "").lower()
            if "gzip" in encoding or raw_body.startswith(b"\x1f\x8b") or url.lower().split("?")[0].endswith((".gz", ".xml.gz")):
                try:
                    import gzip
                    raw_body = gzip.decompress(raw_body)
                except Exception:
                    pass
            body = raw_body.decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        return status, body, headers, str(e)


    except Exception as e:
        return None, "", {}, str(e)


def safe_check_status(url, timeout=5, max_bytes=65536, user_agent=DEFAULT_USER_AGENT):
    """Probes status code of a URL using HEAD with fallback to GET."""
    status, _, _, err = safe_fetch(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent, method="HEAD")
    if status is not None:
        return status
    # Some servers reject HEAD requests (e.g. 405 Method Not Allowed or 403); retry GET with small max_bytes
    status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent, method="GET")
    return status

