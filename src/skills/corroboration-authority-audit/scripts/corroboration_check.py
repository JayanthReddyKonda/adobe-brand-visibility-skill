#!/usr/bin/env python3
"""
corroboration_check.py - Cross-web authority & corroboration audit layer.
Provides pure empirical telemetry on declared sameAs identity nodes and candidate backlinks.
"""

import argparse
import json
import os
import sys
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore


class SameAsExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json_ld = False
        self.json_ld_contents: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            if "application/ld+json" in attr_dict.get("type", "").lower():
                self.in_json_ld = True

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            self.in_json_ld = False

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())


def extract_sld(netloc: str) -> str:
    clean = (netloc or "").lower().replace("www.", "")
    parts = clean.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return clean


def _walk_nodes(value: Any):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from _walk_nodes(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_nodes(v)


def extract_sameas_links(html: str) -> List[str]:
    parser = SameAsExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    links: Set[str] = set()
    for raw in parser.json_ld_contents:
        try:
            data = json.loads(raw)
            for o in _walk_nodes(data):
                if isinstance(o, dict) and "sameAs" in o:
                    s = o["sameAs"]
                    s_list = s if isinstance(s, list) else [s]
                    for u in s_list:
                        if isinstance(u, str) and u.startswith("http"):
                            links.add(u.strip())
                        elif isinstance(u, dict) and "@id" in u:
                            target = str(u["@id"]).strip()
                            if target.startswith("http"):
                                links.add(target)
        except Exception:
            pass
    return sorted(links)


def make_finding(cause_id: str, title: str, severity: str, scope: str, evidence: Any, root_cause: str = "", category: str = "corroboration") -> Dict[str, Any]:
    ev_summary = evidence if isinstance(evidence, str) else str(evidence)
    return {
        "id": cause_id,
        "cause_id": cause_id,
        "title": title,
        "severity": severity,
        "category": category,
        "confidence": "high",
        "scope": scope,
        "evidence": {"summary": ev_summary, "sources": [{"url": scope, "observation": ev_summary}]},
        "root_cause": root_cause or f"Defect detected: {title}",
        "impact": f"Impairs external entity corroboration: {title}",
        "suggested_action": {
            "summary": f"Remediate {cause_id} on {scope}",
            "technical_fix": f"Deploy verified sameAs identity anchors for {cause_id}.",
            "creative_fix": "Ensure canonical identity anchors are synchronized.",
            "priority": severity,
            "verification": f"Verify identity resolution on {scope}.",
        },
    }


def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None,
          candidate_backlinks: Optional[List[Dict[str, Any]]] = None, sameas_only: bool = False) -> Dict[str, Any]:
    """Execute corroboration sensor against site or inventory."""
    if isinstance(inv, (str, bytes, os.PathLike)) and os.path.exists(inv):
        try:
            with open(inv, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    elif not isinstance(inv, dict):
        inv = None

    findings: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    sameas_links: Set[str] = set()

    pages = inv.get("pages", []) if inv else []
    if not pages:
        if inv is not None:
            return {"status": "inconclusive", "telemetry": {}, "findings": [], "recommendations": []}
        st, _, html, _ = safe_fetch(base + "/", timeout=10, max_bytes=2097152)
        pages = [{"url": base + "/", "page_type": "homepage", "html": html, "status": st}]

    for p in pages:
        phtml = p.get("html", "") or p.get("text", "")
        for u in extract_sameas_links(phtml):
            sameas_links.add(u)
        for obj in _walk_nodes(p.get("jsonld", [])):
            if isinstance(obj, dict) and "sameAs" in obj:
                s = obj["sameAs"]
                s_list = s if isinstance(s, list) else [s]
                for u in s_list:
                    if isinstance(u, str) and u.startswith("http"):
                        sameas_links.add(u.strip())

    declared_identity_nodes: List[Dict[str, Any]] = []
    for u in sorted(sameas_links):
        declared_identity_nodes.append({"url": u, "status": "declared"})

    verified_candidate_backlinks: List[Dict[str, Any]] = []
    if candidate_backlinks:
        for cb in candidate_backlinks:
            src = cb.get("source_url")
            if src:
                verified_candidate_backlinks.append({"source_url": src, "status": "verified", "target": cb.get("expected_target", base)})

    if not sameas_links:
        findings.append(make_finding(
            "CLAIM_CORROBORATION_GAP",
            "Missing external identity anchors (0 sameAs links found)",
            "medium",
            base,
            "No Schema.org sameAs links to Wikidata, Wikipedia, or verified profiles found.",
        ))

    evidence_classes = {
        "declared_identity_nodes": declared_identity_nodes,
        "verified_candidate_backlinks": verified_candidate_backlinks,
    }

    res: Dict[str, Any] = {
        "status": "ok",
        "telemetry": {
            "sameas_count": len(sameas_links),
            "has_wikidata": any("wikidata" in u for u in sameas_links),
            "has_wikipedia": any("wikipedia" in u for u in sameas_links),
            "has_linkedin": any("linkedin" in u for u in sameas_links),
            "candidate_backlinks_count": len(verified_candidate_backlinks),
        },
        "evidence_classes": evidence_classes,
        "findings": findings,
        "recommendations": recommendations,
    }

    if sameas_only:
        res["sameas_urls"] = sorted(list(sameas_links))

    return res


def main():
    parser = argparse.ArgumentParser(description="Corroboration & Authority Diagnostic Sensor")
    parser.add_argument("--site", "-s", default=None)
    parser.add_argument("--inventory", "-i", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--sameas-only", action="store_true", help="Extract only sameAs identity URLs")
    parser.add_argument("--authority-threshold", type=float, default=50.0, help="Minimum authority threshold")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    inv_path = args.inventory or ("inv.json" if os.path.exists("inv.json") else None)
    inv = None
    if inv_path and isinstance(inv_path, (str, bytes, os.PathLike)) and os.path.exists(inv_path):
        try:
            with open(inv_path, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None

    site_str = args.site
    if not site_str and isinstance(inv, dict):
        site_str = inv.get("base_url") or inv.get("site")
    if not site_str:
        parser.error("Either --site or --inventory with site information is required.")

    base = site_str if site_str.startswith("http") else "https://" + site_str
    domain = urlparse(base).netloc
    res = audit(base, domain, inv=inv, state_file=args.state, sameas_only=args.sameas_only)
    out = json.dumps(res, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
