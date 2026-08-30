"""
safe_fetch.py - Zero-dependency SSRF-safe HTTP/HTTPS fetching utility.
Enforces strict redirect boundaries, IP validation per hop, bounded decompression, and DNS TOCTOU pinning.
"""

import socket
import ipaddress
import urllib.request
import urllib.parse
import urllib.error
import time
import gzip
import zlib
import threading
from io import BytesIO

DEFAULT_USER_AGENT = "Brand-AI-Readiness-Audit/2.0"

BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_orig_getaddrinfo = socket.getaddrinfo
_dns_pinning = threading.local()

def _safe_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    cache = getattr(_dns_pinning, "cache", {})
    if host in cache:
        results = []
        for sf in cache[host]:
            ip = sf[4][0]
            if len(sf[4]) == 2:
                sockaddr = (ip, port)
            else:
                sockaddr = (ip, port, sf[4][2], sf[4][3])
            results.append((sf[0], sf[1], sf[2], sf[3], sockaddr))
        return results
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _safe_getaddrinfo

def _is_safe_host(hostname):
    try:
        ip_info = _orig_getaddrinfo(hostname, 80, proto=socket.IPPROTO_TCP)
        safe_ips = []
        for sf in ip_info:
            ip_obj = ipaddress.ip_address(sf[4][0])
            is_blocked = False
            for blocked in BLOCKED_NETWORKS:
                if ip_obj in blocked:
                    is_blocked = True
                    break
            if is_blocked:
                return False, f"IP {sf[4][0]} is in blocked network", []
            safe_ips.append(sf)
        
        if not safe_ips:
            return False, "No valid public IPs resolved", []
            
        return True, "", safe_ips
    except Exception as e:
        return False, f"DNS resolution failed: {e}", []

class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, max_redirects=3):
        self.max_redirects = max_redirects
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects += 1
        if self.redirects > self.max_redirects:
            raise urllib.error.URLError("Too many redirects")
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme not in ("http", "https"):
            raise urllib.error.URLError(f"Disallowed redirect scheme: {parsed.scheme}")
            
        is_safe, err, safe_ips = _is_safe_host(parsed.hostname)
        if not is_safe:
            raise urllib.error.URLError(f"SSRF blocked on redirect: {err}")
            
        if not hasattr(_dns_pinning, "cache"): _dns_pinning.cache = {}
        _dns_pinning.cache[parsed.hostname] = safe_ips
        
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def _decompress_bounded(response, max_bytes):
    encoding = response.headers.get("Content-Encoding", "").lower()
    if encoding == "gzip":
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    elif encoding == "deflate":
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    else:
        return response.read(max_bytes)
        
    out = bytearray()
    while len(out) < max_bytes:
        chunk = response.read(8192)
        if not chunk:
            break
        try:
            decompressed = decompressor.decompress(chunk)
            out.extend(decompressed)
            if len(out) >= max_bytes:
                return bytes(out[:max_bytes])
        except Exception:
            break
    return bytes(out)


def safe_fetch(url, timeout=10, max_bytes=5*1024*1024, user_agent=None, method="GET", deadline=None):
    if deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0.1:
            return None, "", {}, "Global deadline exceeded"
        timeout = min(timeout, remaining)

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None, "", {}, f"Disallowed scheme: {parsed.scheme}"
    
    is_safe, err, safe_ips = _is_safe_host(parsed.hostname)
    if not is_safe:
        return None, "", {}, f"SSRF blocked: {err}"
        
    if not hasattr(_dns_pinning, "cache"): _dns_pinning.cache = {}
    _dns_pinning.cache[parsed.hostname] = safe_ips

    opener = urllib.request.build_opener(SafeRedirectHandler(max_redirects=3))
    urllib.request.install_opener(opener)
    
    ua = user_agent if user_agent else DEFAULT_USER_AGENT
    headers = {
        "User-Agent": ua, 
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate"
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            resp_headers = {k.lower(): v for k, v in response.getheaders()}
            
            if method == "HEAD":
                return status, "", resp_headers, ""
                
            content = _decompress_bounded(response, max_bytes)
            
            try:
                charset = response.headers.get_content_charset() or 'utf-8'
                html = content.decode(charset, errors='replace')
            except Exception:
                html = content.decode('utf-8', errors='replace')
                
            return status, html, resp_headers, ""
    except urllib.error.HTTPError as e:
        return e.code, "", {}, str(e)
    except Exception as e:
        return None, "", {}, str(e)

def safe_check_status(url, timeout=5, deadline=None):
    status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=1024, method="HEAD", deadline=deadline)
    return status
