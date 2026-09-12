"""Synthetic end-to-end public-site fixture; transport replacement only, no network.

Pure Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
ORCH_DIR = ROOT / "src/skills/audit-orchestrator/scripts"
SCRAPER_DIR = ROOT / "src/skills/web-scraper/scripts"
for p in (ORCH_DIR, SCRAPER_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from assemble_report import assemble

PAGES: Dict[str, tuple[int, str, str]] = {
    "https://fixture.invalid/robots.txt": (200, "text/plain", "User-agent: *\nAllow: /"),
    "https://fixture.invalid/": (
        200,
        "text/html",
        """<!doctype html><html><head>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://publisher.invalid/original">
<script type="application/ld+json">{"@type":"Organization","name":}</script>
</head><body><h1>North Studio</h1><p>We design public gardens.</p>
<a href="/retired">Garden guide</a><img alt="" src="/ornament.svg"></body></html>""",
    ),
    "https://fixture.invalid/retired": (404, "text/html", '<h1>Guide not found</h1><a href="/">Return home</a>'),
}

CHECKS_PATH = ROOT / "src/skills/audit-orchestrator/references/checks.json"


def make_synthetic_records() -> List[Dict[str, Any]]:
    """Generate collection response records for evidence verification."""
    records = []
    idx = 1
    for url, (status, ctype, text) in PAGES.items():
        body = text.encode("utf-8")
        rec = {
            "artifact": f"response-{idx:04d}",
            "url": url,
            "status": status,
            "headers": [["Content-Type", ctype]],
            "text": text,
            "complete": True,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "source": {
                "text": text,
                "canonicals": ["https://publisher.invalid/original"] if "canonical" in text else [],
            },
        }
        records.append(rec)
        idx += 1
    return records


def make_synthetic_inventory() -> Dict[str, Any]:
    """Generate structured single-pass inventory matching the fixture pages."""
    pages_data = []
    for url, (status, ctype, text) in PAGES.items():
        if url.endswith("/robots.txt"):
            continue
        pages_data.append(
            {
                "url": url,
                "status_code": status,
                "content_type": ctype,
                "raw_html": text,
                "text": text,
                "h1": ["North Studio"] if status == 200 and "North Studio" in text else ["Guide not found"],
                "headings": [{"level": 1, "text": "North Studio" if status == 200 else "Guide not found"}],
                "links": [{"href": "/retired", "text": "Garden guide", "is_internal": True}],
                "canonical_url": "https://publisher.invalid/original" if "canonical" in text else None,
                "json_ld": [{"@type": "Organization", "name": ""}] if "application/ld+json" in text else [],
                "meta_robots": "noindex" if "noindex" in text else None,
                "page_type": "home" if url == "https://fixture.invalid/" else "error",
            }
        )

    return {
        "site": "https://fixture.invalid",
        "crawled_at": "2026-09-08T12:00:00Z",
        "total_pages": len(pages_data),
        "pages": pages_data,
        "robots_txt": {
            "status_code": 200,
            "outcome": "robots_ok",
            "content": "User-agent: *\nAllow: /",
            "sitemaps": [],
            "groups_count": 1,
            "ai_bots_matrix": {},
        },
        "sitemaps": [],
    }


def run_synthetic_audit(out_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Execute synthetic audit returning full structured report."""
    checks = json.loads(CHECKS_PATH.read_text(encoding="utf-8"))
    records = make_synthetic_records()
    candidates = [
        {
            "check_id": "E5",
            "title": "Invalid JSON-LD Syntax",
            "actual_band": "S2",
            "finding_kind": "confirmed_problem",
            "scope": "https://fixture.invalid/",
            "observation": "Malformed JSON-LD syntax on page",
            "severity_reason": "Machine parsers cannot extract entity statements",
            "collection_complete_for_scope": True,
            "remedy_readiness": "ready",
            "candidate": '<script type="application/ld+json">{"@type":"Organization","name":"North Studio"}</script>',
            "validation_results": ["Valid JSON-LD schema"],
            "difficulty": 1,
            "difficulty_reason": "Isolated syntax fix in static template",
            "evidence_refs": [
                {
                    "artifact": "response-0002",
                    "locator": "source.text",
                    "quote": '{"@type":"Organization","name":}',
                }
            ],
        },
        {
            "check_id": "B4",
            "title": "Repeated 404/5xx Responses Encountered",
            "actual_band": "S4",
            "finding_kind": "confirmed_problem",
            "scope": "https://fixture.invalid/retired",
            "observation": "HTTP 404 encountered for discovered link",
            "severity_reason": "Broken internal links cause dead ends for AI crawlers",
            "collection_complete_for_scope": True,
            "remedy_readiness": "ready",
            "resolved_context": {"owner_intent": "redirect_to_guide"},
            "candidate": "Fix or redirect broken link /retired",
            "validation_results": ["404 confirmed"],
            "suggested_action": {"summary": "Redirect /retired to active guide"},
            "difficulty": 2,
            "difficulty_reason": "Single HTTP 301 redirect configuration",
            "evidence_refs": [
                {
                    "artifact": "response-0003",
                    "locator": "status",
                    "quote": "404",
                }
            ],
        },
        {
            "check_id": "B1",
            "title": "Robots.txt Evaluated",
            "actual_band": "S0",
            "finding_kind": "informational_observation",
            "scope": "https://fixture.invalid/robots.txt",
            "observation": "Robots.txt allows AI crawlers",
            "severity_reason": "Informational",
            "collection_complete_for_scope": True,
            "evidence_refs": [
                {
                    "artifact": "response-0001",
                    "locator": "source.text",
                    "quote": "User-agent: *\nAllow: /",
                }
            ],
        },
        {
            "check_id": "J9",
            "title": "404 Recovery Affordance Present",
            "actual_band": "S0",
            "finding_kind": "informational_observation",
            "scope": "https://fixture.invalid/retired",
            "observation": "404 error page provides return link to home",
            "severity_reason": "Observation",
            "collection_complete_for_scope": True,
            "evidence_refs": [
                {
                    "artifact": "response-0003",
                    "locator": "source.text",
                    "quote": '<a href="/">Return home</a>',
                }
            ],
        },
    ]

    coverage_meta = {
        "total_catalogue_checks": len(checks),
        "observed_checks": 4,
        "needs_agent_review": 12,
        "blocked_checks": 0,
        "not_possible_checks": 2,
    }

    report = assemble(
        site="https://fixture.invalid",
        candidates=candidates,
        records=records,
        checks=checks,
        coverage=coverage_meta,
    )

    if out_dir is not None:
        target = Path(out_dir)
        out_path = target if target.suffix == ".json" else target / "audit-report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    out_target = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "examples/synthetic-audit-report.json")
    rep = run_synthetic_audit(Path(out_target))
    print(f"Generated synthetic fixture report at: {out_target}")
