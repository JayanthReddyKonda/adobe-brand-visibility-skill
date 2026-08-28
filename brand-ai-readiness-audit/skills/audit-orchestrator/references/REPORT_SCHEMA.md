# Brand AI-Readiness Audit Report Schema

This document specifies the structure, validation constraints, and field semantics for the audit report emitted by `audit-orchestrator`.

---

## Top-Level Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `site` | String | Yes | Target domain or URL (e.g., `example.com` or `https://example.com`) |
| `audited_at` | String (ISO 8601) | Yes | UTC timestamp in ISO 8601 format (e.g., `2026-09-20T14:32:00Z`) |
| `summary` | Object | Yes | Aggregate counts of findings categorized by severity |
| `findings` | Array | Yes | Ordered list of detected defects with supporting evidence |
| `specialists` | Object | No | Execution status (`ok`, `failed`, `inconclusive`, `not_run`) and diagnostics per specialist |
| `audit_metrics` | Object | No | Objective audit measurements (`pages_sampled`, `page_types_covered`, `critical_blockers`, `confidence_distribution`, `answerability_index`) |
| `root_causes` | Array | No | Clustered root causes mapped to standardized taxonomy families (`cause_family`, `cause_id`) |
| `proactive_actions` | Array | No | Deduplicated proactive opportunities (e.g. sitemap creation, /llms.txt experiments) |
| `observations` | Array | No | Evidence ledger entries (e.g. crawler matrix breakdown, answerability ratios) |
| `coverage` | Object | No | Sampled URLs and extraction metadata per specialist |
| `limitations` | Array | No | Explicit scope constraints noted during the run |

---

## Summary Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `total_findings` | Integer | Yes | Total count of items in `findings` |
| `critical` | Integer | Yes | Count of findings with severity `critical` |
| `high` | Integer | Yes | Count of findings with severity `high` |
| `medium` | Integer | Yes | Count of findings with severity `medium` |
| `low` | Integer | No | Count of findings with severity `low` |

---

## Finding Object

Each entry in the `findings` array represents a verified, evidence-backed defect.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | String | Yes | Unique finding identifier (e.g., `F-001`, `F-002`) |
| `title` | String | Yes | Concise, human-readable summary of the defect |
| `severity` | Enum | Yes | `critical` \| `high` \| `medium` \| `low` \| `info` |
| `evidence` | String | Yes | Concrete data, observed metrics, or reproduction steps verifying the finding |
| `suggested_action` | Object | Yes | Actionable, mechanism-sound remediation plan |
| `confidence` | Enum | No | `high` \| `medium` \| `low` |
| `category` | String | No | Functional category (e.g. `access`, `entity-integrity`, `fact-consistency`, `orientation`) |
| `cause_family` | String | No | Standardized taxonomy family (`DISCOVERY.ACCESS`, `ENTITY.IDENTITY`, etc.) |
| `cause_id` | String | No | Specific root cause identifier |
| `impact` | String | No | Explanation of downstream impact on AI citations and user retention |
| `verification` | String | No | Procedure to verify resolution |

### Suggested Action Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `summary` | String | Yes | Clear instruction on what to change and how to resolve the root cause |
| `priority` | Enum | Yes | `critical` \| `high` \| `medium` \| `low` |
| `verification` | String | No | Method to test that the fix worked |
| `implementation_guidance` | String | No | Optional code snippet, schema template, or configuration directive |

---

## Root Cause Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `cause_family` | String | Yes | Standard taxonomy family (e.g. `DISCOVERY.ACCESS`, `FACT.CONSISTENCY`) |
| `cause_id` | String | Yes | Specific root cause identifier |
| `root_cause` | String | Yes | Descriptive explanation of underlying failure |
| `finding_ids` | Array of Strings | Yes | Associated finding IDs grouped under this cause |
| `max_severity` | Enum | Yes | Highest severity among grouped findings |
| `suggested_priority` | Enum | Yes | Recommended resolution priority |

---

## Example Composed Report

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 2,
    "critical": 1,
    "high": 1,
    "medium": 0,
    "low": 0
  },
  "specialists": {
    "discoverability-audit": { "label": "Access, robots.txt & rendering risk", "status": "ok" },
    "entity-content-audit": { "label": "Entity identity & offer extractability", "status": "ok" },
    "fact-consistency-audit": { "label": "Fact ledger & cross-page consistency", "status": "ok" },
    "corroboration-authority-audit": { "label": "Declared authority link verification", "status": "ok" },
    "engagement-context-audit": { "label": "Orientation & journey continuity", "status": "ok" }
  },
  "findings": [
    {
      "id": "F-001",
      "title": "robots.txt blocks AI search retrieval crawlers",
      "severity": "critical",
      "confidence": "high",
      "cause_family": "DISCOVERY.ACCESS",
      "cause_id": "DISC-ROBOTS-RETRIEVAL-BLOCKED",
      "evidence": "robots.txt (HTTP 200) disallows '/' for retrieval crawler(s): OAI-SearchBot, PerplexityBot.",
      "suggested_action": {
        "summary": "Allow AI search retrieval crawlers (OAI-SearchBot, PerplexityBot) to crawl public content.",
        "priority": "critical"
      }
    },
    {
      "id": "F-002",
      "title": "Conflicting pricing published for 'Velocity X9'",
      "severity": "high",
      "confidence": "high",
      "cause_family": "FACT.CONSISTENCY",
      "cause_id": "FACT-PRICE-CONTRADICTION",
      "evidence": "2 page(s) publish conflicting figures for 'Velocity X9': 4999 on https://example.com/legacy; 5499 on https://example.com/products/x9.",
      "suggested_action": {
        "summary": "Establish a single canonical price for 'Velocity X9' and synchronize across all product listings.",
        "priority": "high"
      }
    }
  ],
  "audit_metrics": {
    "execution_time_seconds": 12.4,
    "pages_sampled": 5,
    "page_types_covered": { "homepage": 1, "product": 2, "pricing": 1, "about": 1 },
    "critical_blockers": 1,
    "confidence_distribution": { "high": 2, "medium": 0, "low": 0 },
    "answerability_index": 0.85
  },
  "root_causes": [
    {
      "cause_family": "DISCOVERY.ACCESS",
      "cause_id": "DISC-ROBOTS-RETRIEVAL-BLOCKED",
      "root_cause": "robots.txt rules disallow AI search retrieval crawlers from accessing the site root.",
      "finding_ids": ["F-001"],
      "max_severity": "critical",
      "suggested_priority": "critical"
    },
    {
      "cause_family": "FACT.CONSISTENCY",
      "cause_id": "FACT-PRICE-CONTRADICTION",
      "root_cause": "Different price values for 'Velocity X9' are published across separate first-party pages.",
      "finding_ids": ["F-002"],
      "max_severity": "high",
      "suggested_priority": "high"
    }
  ]
}
```
