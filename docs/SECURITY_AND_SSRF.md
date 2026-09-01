# SSRF Defense & Network Security Architecture

**Author:** Jayanth Reddy Konda  
**Version:** 1.0.0  
**Module:** `safe_fetch.py`  
**Security Level:** Zero-Trust Hermetic Boundary

---

## 1. Threat Model & Mitigation Strategy

Automated web auditing systems face severe Server-Side Request Forgery (SSRF) threats when probing user-supplied URLs or crawling external `sameAs` authority links:
1. **Loopback & Cloud Metadata Exploitation:** Probing `127.0.0.1`, `localhost`, or AWS/GCP instance metadata (`169.254.169.254`).
2. **Private Network Pivot (RFC-1918):** Probing internal intranet services (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
3. **IPv4-Mapped IPv6 Bypass:** Wrapping forbidden IPv4 addresses inside IPv6 notations (e.g. `::ffff:127.0.0.1` or `::ffff:169.254.169.254`).
4. **DNS Rebinding & TOCTOU:** Resolving a safe IP during validation but connecting to an internal IP during the actual socket handshake.
5. **Decompression Bombs (Zip Bombs / Gzip Bombs):** Maliciously compressed payloads designed to exhaust memory.

---

## 2. Zero-Dependency Invariant Protections in `safe_fetch.py`

### A. Pre-Flight IP Validation & Dual-Stack Resolution
Every hostname is resolved via `socket.getaddrinfo(hostname, 80, proto=socket.IPPROTO_TCP)`. Every resolved IP address is validated against `BLOCKED_NETWORKS`:
- `0.0.0.0/8` (Current network)
- `10.0.0.0/8` (Private RFC-1918)
- `127.0.0.0/8` (Loopback)
- `169.254.0.0/16` (Link-local & Cloud Metadata)
- `172.16.0.0/12` (Private RFC-1918)
- `192.168.0.0/16` (Private RFC-1918)
- `::1/128` (IPv6 Loopback)
- `fc00::/7` (IPv6 Unique Local)
- `fe80::/10` (IPv6 Link-local)

### B. IPv4-Mapped IPv6 Normalization
```python
ip_obj = ipaddress.ip_address(sf[4][0])
if getattr(ip_obj, "ipv4_mapped", None):
    ip_obj = ip_obj.ipv4_mapped
```

### C. Socket-Level DNS TOCTOU Pinning
`SafeHTTPConnection` and `SafeHTTPSConnection` override standard socket initialization. The socket connects directly to the validated IP address rather than re-resolving the hostname, completely mitigating DNS rebinding attacks.

### D. Strict Redirect Sandbox & Bounded Decompression
- Redirects are limited to a maximum of 5 hops with per-hop IP validation.
- Decompression (`gzip`, `deflate`) enforces a strict buffer cap (default 2 MB) using `zlib.decompressobj()`, preventing memory exhaustion from gzip bombs.
