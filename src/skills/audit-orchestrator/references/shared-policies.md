# Shared Architectural Policies & Operational Standards

Canonical reference for cross-cutting security, architectural, and epistemic policies across all 8 skills in the Brand AI-Readiness multi-skill suite.

---

## 1. Zero-Trust Socket-Level SSRF Hard Boundary

All network requests across all skills flow strictly through `web-scraper/scripts/safe_fetch.py`. Direct agent URL reading tools (`read_url_content`, `open_browser_url`, `browser_subagent`) and unvalidated shell commands (`curl`, `wget`) are strictly prohibited during autonomous execution.

### Policy Invariants:
1. **Pre-Socket DNS TOCTOU Resolution:** Target hostnames are resolved via `socket.getaddrinfo()` and every returned IP is evaluated before socket binding.
2. **Blocked Subnets:**
   - RFC 1918 Private networks: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
   - Loopback interfaces: `127.0.0.0/8`, `::1/128`
   - Link-local and cloud metadata: `169.254.0.0/16`, `169.254.169.254`, `169.254.170.2`
   - Carrier-grade NAT (CGNAT): `100.64.0.0/10`, `100.100.100.200`
   - IPv4-mapped IPv6 addresses (`::ffff:0:0/96`)
3. **Redirect Evaluation:** Redirects (up to 5 max) trigger full IP re-validation on every hop. If any redirect target resolves to a private or blocked subnet, the request terminates immediately with `URLError("SSRF blocked on redirect")`.
4. **Transparent User-Agent:** All HTTP requests emit the transparent identifier `Brand-AI-Readiness-Audit/1.0.0 (compatible; public audit sensor)`. Browser impersonation headers (`Sec-Ch-Ua`, `Sec-Fetch-*`) are omitted to maintain audit integrity.

---

## 2. Sensor-Brain Acquisition Protocol (Single-Pass Crawl)

To eliminate crawl redundancy, network amplification, and sensor drift:
1. **Single-Pass Invariant:** The target site is crawled exactly once by `web-scraper` / `acquire_inventory.py`, emitting a canonical `inv.json` site inventory.
2. **Offline Specialist Analysis:** All 6 diagnostic specialists (`discoverability-audit`, `entity-content-audit`, `fact-consistency-audit`, `corroboration-authority-audit`, `geo-content-audit`, `engagement-context-audit`) execute offline analysis against `inv.json`.
3. **External Authority Probing:** Only `corroboration-authority-audit` performs bounded, SSRF-guarded external requests to verify declared `sameAs` entity links (Wikidata, Wikipedia, LinkedIn).
4. **Deterministic Sensors vs. Cognitive Brain:** Specialist Python sensors measure observable empirical facts. The AI orchestrator evaluates business context, applies 5-Whys causal root cause synthesis, and prescribes dual-track remediation.

---

## 3. Epistemic Qualification & Deterministic Evidence Standard

Every finding emitted into the audit report must satisfy the False-Positive Prevention Invariant:
1. **Zero Evidence Fabrication:** Findings must link directly to observable DOM text, HTTP headers, robots.txt directives, or Schema.org JSON-LD snippets extracted during the single-pass crawl.
2. **False-Positive Prevention Matrix:**
   - Decorative images with `alt=""` are compliant with W3C standards and must never trigger accessibility defects.
   - Self-referencing or legitimate external canonical tags must not be flagged as canonical fragmentation.
   - Transactional pages (`checkout`, `cart`, `login`) are conversion funnels and must never be flagged for low causal conjunction density.
   - Blanket `Disallow: /` in robots.txt is evaluated in the context of specific retrieval bots; legitimate governance choices are observations, not automatic defects.
3. **Graceful Sensor Degradation:** If a target site is unreachable or an empty inventory is supplied, sensors must return:
   ```json
   {
     "status": "inconclusive",
     "findings": [],
     "recommendations": []
   }
   ```
   Sensors must never crash or raise unhandled exceptions on unexpected input.

---

## 4. Resource Ceilings & Size Constants

Defined in `web-scraper/scripts/safe_fetch.py`:
- `MAX_HTML_BYTES = 2 * 1024 * 1024` (2 MB HTML response ceiling)
- Sitemaps: 2 MB buffer cap
- `robots.txt`: 512 KB buffer cap
- External authority probes: 512 KB cap
- Decompression bomb protection: `zlib.decompressobj()` with bounded buffer chunks
