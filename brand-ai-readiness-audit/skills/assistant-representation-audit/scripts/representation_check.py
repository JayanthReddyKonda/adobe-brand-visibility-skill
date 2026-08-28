#!/usr/bin/env python3
"""
representation_check.py - Assistant representation layer (optional enrichment).

Causal Root Causes:
  - REPRESENTATION.ACCURACY: AI_FACT_CONFLICT, AI_UNSUPPORTED_CLAIM, AI_CITATION_GAP
"""
import sys
import os
import json
import re
import argparse
from urllib.parse import urlparse
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ORCHESTRATOR_SCRIPTS = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "audit-orchestrator", "scripts"))
if os.path.isdir(ORCHESTRATOR_SCRIPTS) and ORCHESTRATOR_SCRIPTS not in sys.path:
    sys.path.insert(0, ORCHESTRATOR_SCRIPTS)

from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT

PRICE_PATTERN = re.compile(r'(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?(\d[\d,]*(?:\.\d{1,2})?)', re.IGNORECASE)


class TextDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_depth = 0
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style", "noscript"):
            self.skip_depth += 1
        elif tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "noscript") and self.skip_depth > 0:
            self.skip_depth -= 1
        elif tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        elif self.skip_depth == 0 and data.strip():
            self.text.append(data.strip())


def build_fact_snapshot(site, inv=None):
    """Build a comprehensive baseline first-party fact snapshot from all sampled HTML pages."""
    html_pages = []
    if inv is not None:
        html_pages = [p for p in inv.get("pages", []) if p.get("resource_type", "html") == "html" and p.get("html")]
    else:
        status, html, _, _ = safe_fetch(site, timeout=10, max_bytes=2*1024*1024)
        if html:
            html_pages = [{"url": site, "html": html}]

    if not html_pages:
        return {"status": "inconclusive", "error": f"could not reach {site}"}

    all_prices = []
    all_years = []
    full_texts = []
    primary_title = ""

    for page in html_pages:
        dom = TextDOMParser()
        try:
            dom.feed(page.get("html", ""))
        except Exception:
            pass
        if not primary_title and dom.title:
            primary_title = dom.title
        p_text = " ".join(dom.text)
        full_texts.append(p_text)
        all_prices.extend(PRICE_PATTERN.findall(p_text))
        all_years.extend(re.findall(r'\b(20\d{2})\b', p_text))

    combined_text = " ".join(full_texts)
    return {
        "status": "ok",
        "site": site,
        "title": primary_title,
        "prices_visible": sorted(set(all_prices)),
        "years_visible": sorted(set(all_years))[:10],
        "word_count": len(combined_text.split()),
        "full_text": combined_text[:20000]
    }



def parse_price_num(raw):
    try:
        clean = re.sub(r"[^\d.]", "", str(raw).replace(",", ""))
        return float(clean) if clean else None
    except (ValueError, TypeError):
        return None



def compare_assistant_observations(snapshot, observations_data):
    """Compare observed AI assistant outputs against the on-site fact snapshot."""

    findings = []
    observational_notes = []

    obs_list = []
    if isinstance(observations_data, dict):
        obs_list = observations_data.get("observations") or observations_data.get("responses") or []
    elif isinstance(observations_data, list):
        obs_list = observations_data

    site_prices = snapshot.get("prices_visible", [])
    site_num_prices = [parse_price_num(p) for p in site_prices if parse_price_num(p) is not None]

    for idx, obs in enumerate(obs_list):
        assistant_name = obs.get("assistant") or obs.get("model") or f"Assistant-{idx+1}"
        prompt = obs.get("prompt", "General brand query")
        mentioned = obs.get("mentioned", True)
        cited = obs.get("cited", True)

        if not mentioned:
            observational_notes.append({
                "assistant": assistant_name,
                "prompt": prompt,
                "signal": "Brand was omitted from assistant response (observational signal)"
            })
            continue

        if not cited:
            observational_notes.append({
                "assistant": assistant_name,
                "prompt": prompt,
                "signal": "Brand was mentioned without a direct web citation link"
            })

        for claim in obs.get("claims", []):
            fact_str = str(claim.get("fact") or claim.get("text") or "")
            topic = str(claim.get("topic") or "general")

            # Price contradiction check (using numerical float comparison)
            claim_prices = PRICE_PATTERN.findall(fact_str)
            for cp in claim_prices:
                claim_num = parse_price_num(cp)
                if claim_num is not None and site_num_prices and not any(abs(claim_num - sv) < 0.01 for sv in site_num_prices):
                    findings.append({
                        "category": "representation",
                        "title": f"{assistant_name} states conflicting pricing for brand",
                        "severity": "high",
                        "confidence": "high",
                        "root_cause": f"The AI assistant asserts a price ({cp}) that does not match any current on-site pricing.",
                        "cause_family": "REPRESENTATION.ACCURACY",
                        "cause_id": "AI_FACT_CONFLICT",
                        "impact": "Users interacting with AI assistants receive inaccurate commercial terms before landing on the site.",
                        "evidence": f"{assistant_name} asserted '{fact_str}' for prompt '{prompt}'. Visible site prices: {', '.join(sorted(site_prices)[:5])}.",
                        "suggested_action": {
                            "summary": "Publish canonical pricing in JSON-LD and OpenGraph metadata to ground assistant retrieval.",
                            "priority": "high",
                            "verification": "Re-run assistant prompt and verify the quoted price matches on-site Product schema."
                        }
                    })

    return findings, observational_notes


def audit(base, domain, responses_file=None, inv=None):
    snapshot = build_fact_snapshot(base, inv=inv)
    if snapshot.get("status") == "inconclusive":
        return snapshot

    findings = []
    observational_notes = []

    if responses_file and os.path.exists(responses_file):
        try:
            with open(responses_file, "r", encoding="utf-8") as f:
                observations_data = json.load(f)
            f_findings, notes = compare_assistant_observations(snapshot, observations_data)
            findings.extend(f_findings)
            observational_notes.extend(notes)
        except Exception as e:
            return {"status": "failed", "error": f"failed to parse responses file: {e}"}
    else:
        observational_notes.append({
            "signal": "No observed responses file provided. Generated first-party fact baseline snapshot."
        })

    recommendations = []
    if not responses_file:
        recommendations.append({
            "title": "Supply observed assistant responses for empirical grounding",
            "category": "representation",
            "rationale": "Without logged assistant responses, the representation layer cannot detect empirical hallucinations.",
            "suggested_action": "Pass a JSON file of observed answers via --responses to cross-check brand representation."
        })

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observational_notes": observational_notes,
        "snapshot": {
            "title": snapshot.get("title"),
            "prices_visible": snapshot.get("prices_visible"),
            "years_visible": snapshot.get("years_visible"),
            "word_count": snapshot.get("word_count")
        },
        "coverage": {
            "mode": "empirical-comparison" if responses_file else "baseline-snapshot-only",
            "prices_tracked": len(snapshot.get("prices_visible", []))
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Assistant representation cross-check layer.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--responses", "--observations", dest="responses", help="JSON file of observed assistant outputs to cross-check")
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    args = parser.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    res = audit(base, p.netloc, responses_file=args.responses, inv=inv)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
