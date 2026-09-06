"""Standalone Command-Line Interface for the Zero-Dependency Audit Web Engine.

Usage:
    python3 -m crawler.cli --site https://example.com --output output.json --format both
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from .engine import WebAuditEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-Dependency Audit Web Engine CLI")
    parser.add_argument("--site", required=True, help="Target website URL to audit")
    parser.add_argument("--output", default="-", help="Output file path (default: stdout)")
    parser.add_argument("--max-pages", type=int, default=25, help="Maximum pages ceiling")
    parser.add_argument("--timeout", type=float, default=120.0, help="Audit timeout in seconds")
    parser.add_argument(
        "--format",
        choices=["inventory", "evidence", "both"],
        default="both",
        help="Output payload format",
    )
    parser.add_argument(
        "--allow-private-ips",
        action="store_true",
        help="Allow private IP addresses (for local test fixtures only)",
    )

    args = parser.parse_args()

    engine = WebAuditEngine(
        time_limit_sec=args.timeout,
        max_pages=args.max_pages,
        allow_private_ips=args.allow_private_ips,
    )

    try:
        evidence = engine.crawl(args.site)
    except Exception as e:
        sys.stderr.write(f"Crawl execution failed: {e}\n")
        sys.exit(1)

    if args.format == "inventory":
        result_payload: Dict[str, Any] = engine.to_inventory_dict()
    elif args.format == "evidence":
        result_payload = evidence.to_dict()
    else:
        result_payload = {
            "inventory": engine.to_inventory_dict(),
            "evidence": evidence.to_dict(),
        }

    output_json = json.dumps(result_payload, indent=2)

    if args.output == "-":
        sys.stdout.write(output_json + "\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        sys.stderr.write(f"Successfully audited {args.site} ({len(engine.pages)} pages). Saved to {args.output}\n")


if __name__ == "__main__":
    main()
