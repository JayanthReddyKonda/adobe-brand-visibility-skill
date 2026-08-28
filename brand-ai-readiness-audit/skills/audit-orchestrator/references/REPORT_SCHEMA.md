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

## Example Clean Production Report

```json
{
  "site": "frescopa.coffee",
  "audited_at": "2026-08-28T16:52:37Z",
  "summary": {
    "total_findings": 2,
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "Product price is inconsistent across first-party surfaces",
      "severity": "high",
      "category": "fact-integrity",
      "root_cause": "The same product is represented with different current prices on the product and category pages.",
      "confidence": "high",
      "evidence": "Product page: ₹5,499. Category page: ₹4,999. Both refer to the same product and offer context.",
      "suggested_action": {
        "summary": "Establish one authoritative offer value and synchronize visible content and structured data across affected pages.",
        "priority": "high"
      }
    },
    {
      "id": "F-002",
      "title": "Important product information is difficult to retrieve",
      "severity": "medium",
      "category": "discoverability",
      "root_cause": "Material product facts are absent from the initial machine-readable representation of sampled product pages.",
      "confidence": "medium",
      "evidence": "Across sampled product pages, key factual attributes were unavailable in the initial HTML representation.",
      "suggested_action": {
        "summary": "Expose core product facts directly in crawlable HTML and keep structured representation consistent.",
        "priority": "medium"
      }
    }
  ],
  "proactive_actions": [
    {
      "title": "Strengthen canonical brand identity",
      "summary": "Maintain a consistent organization identity, canonical name, logo and authoritative external references across major brand surfaces.",
      "priority": "low"
    }
  ]
}
```

