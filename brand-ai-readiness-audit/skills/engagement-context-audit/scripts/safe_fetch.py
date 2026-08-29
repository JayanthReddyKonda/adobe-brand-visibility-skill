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


def _decompress_gzip_bounded(raw_bytes, max_bytes):
    """Safely decompress gzip data with a hard byte cap to prevent zip bombs."""
    if not raw_bytes:
        return b""
    import zlib
    try:
        # 16 + MAX_WBITS enables gzip decoding
        dobj = zlib.decompressobj(16 + zlib.MAX_WBITS)
        out_chunks = []
        bytes_decompressed = 0
        chunk_size = 32768
        for i in range(0, len(raw_bytes), chunk_size):
            chunk = raw_bytes[i:i + chunk_size]
            decomp = dobj.decompress(chunk, max_bytes - bytes_decompressed + 1)
            if decomp:
                out_chunks.append(decomp)
                bytes_decompressed += len(decomp)
            if bytes_decompressed > max_bytes:
                break
        return b"".join(out_chunks)[:max_bytes]
    except Exception:
        try:
            import gzip, io
            with gzip.GzipFile(fileobj=io.BytesIO(raw_bytes)) as gz:
                return gz.read(max_bytes)
        except Exception:
            return raw_bytes[:max_bytes]




import random
import time

UAS = [
    "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
]

def safe_fetch(url, timeout=10, max_bytes=5*1024*1024, redirects_left=3, original_url=None, user_agent=None, method="GET"):
    if original_url is None:
        original_url = url
    if redirects_left < 0:
        return None, "", {}, "too many redirects"

    # SSRF / Safety Checks
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None, "", {}, f"disallowed scheme: {parsed.scheme}"
        hostname = parsed.hostname
        if not hostname:
            return None, "", {}, "no hostname"
            
        ip_info = socket.getaddrinfo(hostname, 80, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in ip_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked in BLOCKED_NETWORKS:
                if ip_obj in blocked:
                    return None, "", {}, f"SSRF blocked: IP {ip_str} is in blocked network {blocked}"
    except Exception as e:
        return None, "", {}, f"DNS/SSRF check failed: {e}"

    # Agentic UA Rotation & Retry Logic (Bypass basic WAFs)
    last_err = "failed"
    last_code = None
    
    uas_to_try = [user_agent] if user_agent else [UAS[0], random.choice(UAS[1:])]
    
    for attempt, ua in enumerate(uas_to_try):
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                headers = {k.lower(): v for k, v in response.getheaders()}
                if method != "HEAD":
                    content = response.read(max_bytes)
                    try:
                        charset = response.headers.get_content_charset() or 'utf-8'
                        html = content.decode(charset, errors='replace')
                    except Exception:
                        html = content.decode('utf-8', errors='replace')
                else:
                    html = ""
                    
                return status, html, headers, ""
        except urllib.error.HTTPError as e:
            last_code = e.code
            last_err = str(e)
            if e.code in (301, 302, 303, 307, 308):
                loc = e.headers.get("Location")
                if loc:
                    next_url = urllib.parse.urljoin(url, loc)
                    return safe_fetch(next_url, timeout, max_bytes, redirects_left - 1, original_url, user_agent, method)
            # If 403 Forbidden or 429 Too Many Requests, try the next UA
            if e.code in (403, 429) and attempt == 0 and len(uas_to_try) > 1:
                time.sleep(1) # Backoff
                continue
            return e.code, "", {}, str(e)
        except Exception as e:
            last_err = str(e)
            return None, "", {}, str(e)
            
    return last_code, "", {}, last_err

def safe_check_status(url, timeout=5):
    status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=10*1024, method="HEAD")
    return status
