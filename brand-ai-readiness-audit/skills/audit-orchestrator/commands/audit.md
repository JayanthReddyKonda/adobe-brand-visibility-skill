---
description: Run a full AI discoverability and on-site engagement audit on a website
argument-hint: <site-url-or-domain>
---

Run a complete Brand AI-Readiness Audit on the provided site and emit the final schema-compliant JSON report.

## Arguments

- `site` (required): The domain or URL to audit, e.g. `https://example.com`.

## Procedure

1. Normalize and validate the provided site URL.
2. Compose the marketplace's specialist skills via the `audit-orchestrator` procedure:
   - `crawl-render-audit` — bot access, SSR/CSR rendering, machine-readable content, Schema.org JSON-LD.
   - `freshness-corroboration` — temporal freshness, cross-page consistency, entity `sameAs` grounding.
   - `engagement-audit` — above-the-fold orientation, heading hierarchy, information scent.
3. Reconcile and deduplicate overlapping findings; reassign sequential IDs (`F-001`, ...).
4. Calibrate severity (`critical` / `high` / `medium` / `low`) and prioritise suggested actions.
5. Synthesize proactive opportunities even when no fatal defect is present.
6. Emit the final JSON report matching `references/REPORT_SCHEMA.md` and validate it with `scripts/validate_report.py`.

## Optional flags

- `--mock` — run offline with simulated signals (no network) for verification.
- `--output <path>` — write the report to a specific file instead of printing.