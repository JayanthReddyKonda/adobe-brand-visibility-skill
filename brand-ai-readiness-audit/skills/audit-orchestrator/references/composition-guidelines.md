# Composition, Evidence & Severity Guidelines

How `audit-orchestrator` acquires evidence, composes specialist outputs, gates
findings, enforces global deadlines, and reports root causes. This document describes the *implemented*
orchestrator — SKILL.md, this reference, and `scripts/orchestrator.py` are one
methodology, not three opinions.

---

## 1. Specialist Responsibilities

| Skill | Owns | Does NOT own |
| :--- | :--- | :--- |
| `discoverability-audit` | Access, crawler rules (distinguishing retrieval vs training bots), noindex, canonical, rendering risk, discovery aids | Structured data, page content |
| `entity-content-audit` | Entity identity, structured schema (JSON-LD), Answerability Engine, material attribute completeness | Crawler access rules |
| `fact-consistency-audit` | Fact ledger, scoped volatile facts (prices, contacts), cross-page contradictions, freshness timestamps | Entity identity correctness |
| `corroboration-authority-audit` | Independent source verification of first-party claims (sameAs, external profiles) | First-party content quality |
| `engagement-context-audit` | Intent orientation (5-second test), heading information scent, navigation continuity on landing pages | Technical crawlability |
| `assistant-representation-audit` | Cross-checking *observed* AI assistant outputs against first-party facts (opt-in enrichment) | Site-side crawl rules |

---

## 2. Global Wall-Clock Deadline (< 5 Minutes)

The orchestrator enforces a strict total runtime budget (default 300 seconds):
- **Phase 1 (Acquisition Crawl):** Bounded to ≤ 60 seconds.
- **Phase 2 (Specialist Execution):** Dynamic allocation where each specialist receives `(remaining_time - buffer) / remaining_specialists`.
- **Budget Expiry:** If remaining time is ≤ 5s, remaining specialists are marked with `status: "not_run"` and `reason: "Execution skipped: global time budget exhausted"`. Tool failure is never converted into zero findings.

---

## 3. SSRF Protection & Bounded Streaming

Every network fetch in the orchestrator and all specialist tools enforces:
1. **Scheme Validation:** `http` and `https` only.
2. **DNS & IP Validation:** Rejection of private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`, `fe80::/10`), and cloud-metadata addresses.
3. **Bounded Redirects:** Max 5 redirects with target IP re-validation on every hop.
4. **Hard Size Caps:** HTML pages (max 2 MB), robots.txt (max 512 KB), sitemaps (max 2 MB), external authority probes (max 512 KB).
5. **Same-Origin Crawling:** Sitemaps and priority links must match the target domain origin.

---

## 4. Crawler Matrix Semantics

- **Retrieval Bots:** `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `anthropic-ai`. Blocking on public content = `critical` / `high` finding.
- **Training Bots:** `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`. Blocking = `info` / `low` observation (training opt-out, not AI search retrieval failure).
- **User Fetch:** `ChatGPT-User`. User-initiated browsing token.

---

## 5. Eligibility Gate & Deduplication

Before a specialist finding enters `findings[]`:
1. It must cite concrete evidence (≥ 8 characters of gathered evidence). Evidence-less assertions become `proactive_actions[]`.
2. High/critical severity with low confidence is demoted to a recommendation.
3. Overlapping findings and recommendations are deduplicated using normalized fingerprints (`category:title` and `(action_category, action_title)`).

---

## 6. Taxonomy-Driven Root-Cause Clustering

Findings are clustered by standardized taxonomy families:
- `DISCOVERY.ACCESS`: HTTP availability, noindex, crawler disallow.
- `DISCOVERY.RENDERING`: Initial HTML text absence, client-side rendering dependency.
- `DISCOVERY.CANONICAL`: Canonical host consolidation discrepancies.
- `ENTITY.IDENTITY`: Missing Organization / Brand structured identity.
- `ENTITY.ANSWERABILITY`: Material attribute gaps across product, pricing, service pages.
- `FACT.CONSISTENCY`: Cross-page price, contact, or brand contradictions.
- `FACT.FRESHNESS`: Stale copyright years, missing modification timestamps.
- `AUTHORITY.CORROBORATION`: Broken sameAs authority profiles.
- `EXPERIENCE.CONTINUITY`: Heading information scent, missing navigation, orientation gaps.
- `REPRESENTATION.ACCURACY`: Divergence between observed AI claims and first-party facts.

---

## 7. Objective Audit Metrics

Synthetic point deduction scores are avoided. The orchestrator emits objective metrics:
- `pages_sampled`: Count of URLs audited.
- `page_types_covered`: Breakdown of page types evaluated.
- `critical_blockers`: Total count of critical access/indexing blockers.
- `confidence_distribution`: High, medium, and low confidence evidence counts.
- `answerability_index`: Average material attribute coverage across sampled pages.
