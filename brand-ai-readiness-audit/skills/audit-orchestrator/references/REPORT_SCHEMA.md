# Brand AI-Readiness Audit Report Schema

This document specifies the required structure, validation constraints, and field semantics for the audit report emitted by `audit-orchestrator`.

---

## Top-Level Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `site` | String | Yes | Target domain or URL (e.g., `example.com` or `https://example.com`) |
| `audited_at` | String (ISO 8601) | Yes | UTC timestamp in ISO 8601 format (e.g., `2026-09-20T14:32:00Z`) |
| `summary` | Object | Yes | Aggregate counts of findings categorized by severity |
| `findings` | Array | Yes | Ordered list of detected defects and proactive improvement recommendations |

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

Each entry in the `findings` array represents either a detected failure mode or a high-value proactive recommendation.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | String | Yes | Unique finding identifier (e.g., `F-001`, `CR-001`, `FC-002`, `ENG-003`) |
| `title` | String | Yes | Concise, human-readable summary of the defect or opportunity |
| `severity` | Enum | Yes | `critical` \| `high` \| `medium` \| `low` \| `info` |
| `evidence` | String | Yes | Concrete data, observed metrics, or reproduction steps verifying the finding |
| `suggested_action` | Object | Yes | Actionable, mechanism-sound remediation plan |

### Suggested Action Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `summary` | String | Yes | Clear instruction on what to change and how to resolve the root cause |
| `priority` | Enum | Yes | `critical` \| `high` \| `medium` \| `low` |
| `implementation_guidance` | String | No | Optional code snippet, schema template, or configuration directive |

---

## Example Report

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "Disallow directive blocks AI search indexers in robots.txt",
      "severity": "critical",
      "evidence": "robots.txt contains 'User-agent: GPTBot Disallow: /' and 'User-agent: ClaudeBot Disallow: /'.",
      "suggested_action": {
        "summary": "Update robots.txt to explicitly allow GPTBot and ClaudeBot to crawl public marketing and documentation pages.",
        "priority": "critical"
      }
    },
    {
      "id": "F-002",
      "title": "Missing Organization and Product Schema.org JSON-LD markup",
      "severity": "high",
      "evidence": "Inspected home and catalog pages; 0/5 pages contain JSON-LD structured data.",
      "suggested_action": {
        "summary": "Implement schema.org/Organization with sameAs entity links on home page, and schema.org/Product on item pages.",
        "priority": "high"
      }
    },
    {
      "id": "F-003",
      "title": "Stale copyright year and missing modified timestamps",
      "severity": "medium",
      "evidence": "Footer copyright reads '© 2021', and meta dateModified tags are absent on key product pages.",
      "suggested_action": {
        "summary": "Automate footer copyright year and expose ISO 8601 dateModified in JSON-LD and OpenGraph metadata.",
        "priority": "medium"
      }
    }
  ]
}
```

