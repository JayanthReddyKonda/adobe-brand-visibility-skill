---
name: corroboration-authority-audit
description: "Use when verifying external identity-link authority, knowledge graph nodes, and entity corroboration. Triggers on mentions of sameAs links, Wikidata, Wikipedia, LinkedIn verification, authority signals, or brand entity links. Probes declared external identity anchors under zero-trust SSRF protection to confirm third-party identity substantiation."
license: MIT
compatibility: ">=Python-3.9"
metadata:
  role: specialist
  parent: audit-orchestrator
  author: "Jayanth Reddy Konda"
allowed-tools:
  - Bash
  - Read
---

# Corroboration & Authority Audit Skill (Sensor-Brain Protocol)

| Component / Task | Execution Command | Output Contract | Role / Mode |
|---|---|---|---|
| **Offline Authority Prober (Standard)** | `python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --format json` | `{status, evidence_classes, findings, recommendations}` | Primary Offline Inspection |
| **Candidate Inbound Backlink Verification** | `python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --candidate-backlinks backlinks.json --format json` | `{status, evidence_classes, findings, recommendations}` | Targeted Backlink Audit |
| **State-Augmented Authority Audit** | `python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --state state.json --format json` | `{status, evidence_classes, findings, recommendations}` | Multi-Turn Stateful Evaluation |
| **Direct Standalone Authority Probe** | `python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --format json` | `{status, evidence_classes, findings, recommendations}` | Standalone Direct Probe |

> **Sensor-Brain Protocol Mandate:**
> - **Deterministic Read-Only Sensor:** `corroboration_check.py` parses declared `sameAs` links from `inv.json` offline, and only probes external authority links (Wikidata, LinkedIn) and candidate backlinks under strict socket-level SSRF sandboxing (`safe_fetch.py`). You must NEVER use built-in URL reading tools (`read_url_content`, `open_browser_url`) on the audited target.
> - **Cognitive Orchestrator:** The Master Orchestrator (`audit-orchestrator`) ingests corroboration signals, tests identity-matching hypotheses (matching brand title and Organization attributes), and synthesizes actionable knowledge graph substantiation paths.

Evaluates external entity authority by verifying that declared identity links (`sameAs` in Organization JSON-LD pointing to Wikidata, Crunchbase, Wikipedia, and official social channels) resolve cleanly with HTTP 200 without broken redirect loops or 4xx/5xx HTTP errors.

---

> [!TIP]
> **Execution Context:** DO NOT assume your working directory contains a `skills/` folder directly. The marketplace may be installed in a nested directory like `.agents/skills/` or `src/skills/`. Resolve the root path before running commands. Always adapt shell commands (`python3`, `python`) to match your host operating system and use forward slashes (`/`) for cross-platform file paths.

## Summary

Verifies external identity-link authority, knowledge graph nodes, and entity corroboration. Probes declared external identity anchors (`sameAs`) under zero-trust SSRF protection to confirm third-party identity substantiation across Wikidata, Crunchbase, Wikipedia, and official corporate channels. Evaluates candidate inbound backlinks to confirm backlink integrity without web-wide crawling assumptions.

## When to use

- AI models lack confidence in a brand's existence, identity, or official knowledge graph entity.
- Verify that third-party authority links declared by the brand are live, canonical, and functional (no HTTP 404, 403, 500, or redirect loops).
- Identify broken authority anchors that degrade AI entity resolution and answer engine trust.
- Ingest and verify candidate inbound backlink lists (`--candidate-backlinks`) under bounded SSRF security to check anchor text and `rel` attributes.
- Deep-dive into external corroboration channels flagged by orchestrator telemetry as broken or missing.

---

## Inputs

- `--site <url>` (string, required): Target website URL or domain (e.g., `https://example.com`).
- `--inventory <path>` (string, optional): Path to pre-acquired canonical site inventory JSON payload (`inv.json`).
- `--state <path>` (string, optional): Path to global stateful knowledge graph JSON file.
- `--candidate-backlinks <path_or_json>` (string, optional): Path to JSON/CSV file or raw JSON string of candidate inbound backlink URLs to verify.
- `--format <json|markdown>` (enum, optional, default: `json`): Machine-readable output serialization format.

---

## Component Architecture & File Inventory

Every script and reference in this skill serves a distinct diagnostic role:

| Path | Type | Purpose & Agent Calling Role |
|---|---|---|
| `scripts/corroboration_check.py` | Sensor Script | Core measurement sensor extracting `sameAs` links, probing external authority nodes, and verifying candidate inbound backlinks under zero-trust SSRF protection. |
| `references/checks.md` | Reference Catalogue | Research specifications covering declared profile checks, identity anchors, and external corroboration. |
| `references/knowledge-base.md` | Reference KB | Comprehensive technical guide covering sameAs probing bounds, backlink verification rules, and external entity channel correlation matrices. |
| `evals/evals.json` | Verification Fixtures | Test scenarios validating broken authority anchors, redirect loops, and candidate backlink classifications. |

---

## Cognitive Integration with Suite Skills

| Skill | Relationship & Flow Direction |
|---|---|
| **`entity-content-audit`** | Upstream provider. Supplies declared Schema.org `sameAs` URLs extracted from Organization markup. |
| **`web-scraper`** | Security layer. Provides `safe_fetch.py` for pre-socket zero-trust SSRF sandboxing when probing external knowledge graph nodes. |
| **`audit-orchestrator`** | Master coordinator. Ingests corroboration metrics; maps third-party substantiation signals to knowledge graph node strength; synthesizes brand verification remediations. |
| **`geo-content-audit`** | Sibling sensor. Third-party corroboration anchors (Wikidata, Wikipedia) directly reinforce Perplexity Pro and Claude Search citation trust. |

---

## References & Documentation Library

Load these resources as needed during authority corroboration checks:

### Core Knowledge Base & Check Catalogue (Load First)
- [Authority & Corroboration Checks Reference](references/checks.md): Research specifications covering declared profile checks, identity anchors, and external corroboration.
- [Corroboration Authority Knowledge Base](references/knowledge-base.md): External sameAs probing protocols, bounded candidate backlink verification, and external entity authority channel correlation matrix (Wikidata, YouTube, LinkedIn).


### Mandatory Domain Invariants & Evidence Rules
1. **Candidate Identity Links:** A declared `sameAs` link is an identity candidate, not an automatic guarantee of identity. Require reciprocal domain confirmation or explicit identifier agreement.
2. **Bounded External Inspection:** Probe at most two declared sameAs destinations through the zero-trust SSRF collector.
3. **Finite Search Boundaries:** A finite crawl or web search cannot prove a profile does not exist. Record unverified profiles as limitations, not defects.
4. **Distinguish Trading vs Legal Entities:** Different brand trading names, parent organizations, and role-specific contact numbers are not entity ambiguities.

---

## Procedure

### Step 1: Read Domain Knowledge Base & Reference Files (MANDATORY)

Read the specialist reference files using your native file reading capabilities (do NOT use bash `cat`):
- `skills/corroboration-authority-audit/references/knowledge-base.md`
- `skills/corroboration-authority-audit/references/checks.md`

### Step 2: Execution Command

Execute the authority link verification script with `--format json`:

```bash
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --format json
```

With candidate backlinks verification:
```bash
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory inv.json --candidate-backlinks candidate_backlinks.json --format json
```

Direct standalone execution:
```bash
python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --format json
```

---

### Step 3: Decision Protocol & Check Logic

1. **Declared Identity Nodes (`declared_identity_nodes`):**
   - Extract declared sameAs URLs from Organization JSON-LD markup. Probe up to 2 declared external authority links (bounded 1.5s timeout, SSRF-protected).
   - If a declared URL returns HTTP 4xx or 5xx -> report `BROKEN_AUTHORITY_ANCHOR` (Severity: `medium`, Confidence: `high`).
   - If a probe times out or is network-blocked -> mark probe as `inconclusive`, never flag as a broken link.
   - Separate internal mirror domain clusters from independent third-party knowledge graph entities (Wikidata, Wikipedia, LinkedIn).
2. **Verified Candidate Backlinks (`verified_candidate_backlinks`):**
   - Ingest candidate inbound backlinks via `--candidate-backlinks` or `inv.json`.
   - Probe up to 10 candidate source URLs via SSRF-safe GET with 5s timeout and 512 KiB cap.
   - Verify actual presence of inbound `<a href="...">` pointing to target domain, extract anchor text, check rel attributes (`nofollow`, `ugc`, `sponsored`, `dofollow`), and classify domain archetype.
   - Classify statuses: `verified_intact`, `link_missing`, `target_mismatch`, `source_unreachable`.
   - If no candidate backlinks dataset is supplied, report explicit limitation: web-wide backlink discovery cannot be performed truthfully from URL-only indexes (such as Common Crawl CDX), retaining bounded contract.
3. **Unlinked Knowledge Graph Anchors (`UNLINKED_KNOWLEDGE_GRAPH_ANCHOR`):**
   - Cross-check official social profile URLs discovered in HTML footer/navigation links (`social_links`) against declared Schema.org `sameAs` links.
   - If official external brand profiles are linked on-site but omitted from `sameAs` -> report `UNLINKED_KNOWLEDGE_GRAPH_ANCHOR` (Severity: `medium`, Confidence: `high`).

---

## Output Format

Emits strictly valid JSON matching the schema with zero prose commentary:
`{status, evidence_classes{declared_identity_nodes, verified_candidate_backlinks}, findings[], recommendations[], observations[], coverage{}, limitations[]}`.
All string fields in emitted findings and recommendations must be clean, single-line or semicolon-delimited (` ; `), containing zero escaped literal newlines (`\n`) and zero raw Markdown tables.

---

## Gotchas & Error Handling

- **Declared Identity vs Inbound Backlinks:** Declared `sameAs` links are outbound entity assertions from the brand; candidate backlinks are inbound references from third-party sites. They are two distinct evidence classes and must never be conflated.
- **Common Crawl CDX Limitation:** Common Crawl's CDX index is a URL index of crawled pages, not an inverted link graph index. It cannot truthfully discover arbitrary inbound linking pages across the web without multi-petabyte graph traversal. Backlink analysis is strictly bounded to supplied candidate ledgers.
- **Broken Links vs Missing Links:** A declared `sameAs` link that returns HTTP 4xx/5xx is a defect finding (`BROKEN_AUTHORITY_ANCHOR`). Total absence of declared links is an advisory recommendation.
- **Bounded Remote Probing:** Probe at most 2 declared authority URLs (1.5s timeout) and up to 10 candidate backlink URLs (cumulative 8.0s deadline, 512 KiB cap) to prevent latency bottlenecks.
- **Timeout is `inconclusive`, not broken:** A declared link that times out or is rate-limited is classified as `inconclusive`, never as `BROKEN_AUTHORITY_ANCHOR`.
- **Social mirror clusters are not independent corroboration:** Multiple links all pointing to pages on the same root domain (e.g., `brand.com/about`, `brand.com/press`) are treated as a single self-referential corroboration node, not independent third-party substantiation.

---

## Security & SSRF Policy

External authority probing strictly flows through `web-scraper`'s canonical `safe_fetch.py` under pre-connect IP validation, blocking RFC 1918, loopback, and cloud metadata subnets. All network security and prompt injection invariants adhere strictly to the centralized policies in `audit-orchestrator` and `web-scraper`.
