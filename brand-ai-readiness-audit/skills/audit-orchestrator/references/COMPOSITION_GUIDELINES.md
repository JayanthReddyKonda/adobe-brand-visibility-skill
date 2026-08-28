# Composition, Evidence & Severity Guidelines

How `audit-orchestrator` acquires evidence, composes specialist outputs, gates
findings, and reports root causes. This document describes the *implemented*
orchestrator — SKILL.md, this reference, and `scripts/orchestrator.py` are one
methodology, not three opinions.

---

## 1. Specialist responsibilities (v2 skill set)

| Skill | Owns | Does NOT own |
| :--- | :--- | :--- |
| `discoverability-audit` | Access, crawl rules (robots/ai-robots), noindex, canonical, rendering risk, discovery aids | Structured data, page content |
| `entity-content-audit` | Entity identity, attributes, structured representation, answerability gaps | Crawler access rules |
| `fact-consistency-audit` | Fact ledger, volatile facts, cross-page contradictions, freshness of *facts* (not copyright years) | Entity identity correctness |
| `corroboration-authority-audit` | Independent source verification of first-party claims (sameAs, external profiles) | First-party content quality |
| `engagement-context-audit` | Intent orientation, navigation continuity, context preservation on landing pages | Technical crawlability |
| `assistant-representation-audit` | Classification of *observed* AI assistant outputs (optional enrichment; never run unprompted) | Site-side checks |

## 2. Shared site inventory

The orchestrator performs ONE bounded acquisition pass and hands every
specialist the same evidence snapshot via `--inventory <file>`:

- Mandatory: homepage, robots.txt, sitemap (index sitemaps expanded one level).
- Priority selection: 10–20 URLs classified by page type
  (product, pricing, service, category, contact, location, about,
  documentation, article) — never a bulk crawl. Small sites may be covered
  fully; large sites are sampled by type. Time-budgeted (~90s).
- Specialists fall back to independent fetching when no inventory is supplied,
  and report `coverage.source: shared-inventory | independent-fetch` either way.

## 3. Evidence contract

Every specialist output is:

```json
{
  "status": "ok | failed | not_run | inconclusive",
  "coverage": {},
  "observations": [],
  "findings": [],
  "recommendations": [],
  "limitations": []
}
```

Findings carry `category, title, severity, confidence, evidence, root_cause,
impact, suggested_action{summary, priority, verification}`. The orchestrator
aggregates observations into the final report and never converts an
`inconclusive` specialist into a clean result — failure must never become
"clean".

## 4. Eligibility gate (finding → final report)

Before a specialist finding enters `findings[]`:

1. It must cite concrete evidence (≥ 10 chars of specific, gathered evidence).
   Evidence-less assertions become `proactive_actions[]`, never silent drops.
2. `critical`/`high` severity with `low` confidence is demoted to a
   recommendation ("potentially serious, insufficient evidence"). Severity and
   confidence are separate axes; low confidence never auto-becomes a high
   defect.
3. Duplicates (normalized title fingerprint) are collapsed, keeping the
   highest-severity instance.

## 5. Root-cause layer

Findings sharing a `root_cause` are clustered into `root_causes[]` with
contributing `finding_ids`, categories, and max severity — so the report
recommends one prioritized action per cause instead of N scattered defects.

## 6. Diagnostic dimensions (not a visibility score)

`diagnostic_dimensions` (crawlability, entity clarity, fact integrity,
citation readiness, context continuity) are internal diagnostic indices
derived from THIS run's findings only. They are explicitly not a predictive
ranking of AI-assistant visibility; no single number predicts assistant
behavior across platforms.

## 7. Severity rubric (calibrated, evidence-gated)

| Level | Criteria |
| :--- | :--- |
| `critical` | Site inaccessible or fully excluded from retrieval (verified: blanket AI-crawler `Disallow: /`, hard 4xx/5xx on core pages) |
| `high` | Verified defect with direct retrieval/answer impact and adequate confidence |
| `medium` | Verified degradation (missing discovery aids, weak orientation) |
| `low` / `info` | Minor gaps, polish |

Any "expected best practice" without site-specific evidence is a
`recommendation`, not a finding. Absence of a file the site never promised
(`llms.txt`, FAQ schema) is a proactive suggestion at most.


