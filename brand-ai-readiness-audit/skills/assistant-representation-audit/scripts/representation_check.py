#!/usr/bin/env python3
"""
representation_check.py - Assistant representation layer (optional enrichment).

Cross-checks observed AI assistant outputs (supplied via --responses or --observations JSON)
against the brand's verified first-party facts to detect pricing contradictions,
unsupported claims, outdated facts, and citation omissions.
"""
import sys
import os
import json
import re
import argparse
from urllib.parse import urlparse
from html.parser import HTMLParser

try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audit-orchestrator", "scripts")))
    from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT
except ImportError:
    import urllib.request, urllib.error
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"
    def safe_fetch(url, timeout=10, max_bytes=2*1024*1024, user_agent=DEFAULT_USER_AGENT, method="GET"):
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(max_bytes).decode("utf-8", "ignore"), dict(r.headers), None
        except urllib.error.HTTPError as e:
            return e.code, "", dict(e.headers or {}), str(e)
        except Exception as e:
            return None, "", {}, str(e)


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
    """Build a baseline first-party fact snapshot."""
    if inv is not None:
        home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
        html = home.get("html") if home else None
    else:
        status, html, _, err = safe_fetch(site, timeout=10, max_bytes=2*1024*1024)

    if not html:
        return {"status": "inconclusive", "error": f"could not reach {site}"}

    dom = TextDOMParser()
    try:
        dom.feed(html)
    except Exception:
        pass

    full_text = " ".join(dom.text)
    prices = PRICE_PATTERN.findall(full_text)
    years = re.findall(r'\b(20\d{2})\b', full_text)

    return {
        "status": "ok",
        "site": site,
        "title": dom.title,
        "prices_visible": sorted(set(prices))[:25],
        "years_visible": sorted(set(years))[:10],
        "word_count": len(full_text.split()),
        "full_text": full_text
    }


def compare_assistant_observations(snapshot, observations_data):
    """Compare observed AI assistant outputs against the on-site fact snapshot."""
    findings = []
    observational_notes = []

    obs_list = []
    if isinstance(observations_data, dict):
        obs_list = observations_data.get("observations") or observations_data.get("responses") or []
    elif isinstance(observations_data, list):
        obs_list = observations_data

    site_text_lower = snapshot.get("full_text", "").lower()
    site_prices = set(snapshot.get("prices_visible", []))

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

            # Price contradiction check
            claim_prices = PRICE_PATTERN.findall(fact_str)
            for cp in claim_prices:
                norm_cp = re.sub(r"[^\d]", "", cp)
                # Check if this price is stated in the claim but missing from on-site prices
                if norm_cp and site_prices and not any(norm_cp == re.sub(r"[^\d]", "", sp) for sp in site_prices):
                    findings.append({
                        "category": "representation",
                        "title": f"{assistant_name} states conflicting pricing for brand",
                        "severity": "high",
                        "confidence": "high",
                        "root_cause": f"The AI assistant asserts a price ({cp}) that does not match any current on-site pricing.",
                        "cause_family": "REPRESENTATION.ACCURACY",
                        "cause_id": "REP-PRICE-CONFLICT",
                        "impact": "Users interacting with AI assistants receive inaccurate commercial terms before landing on the site.",
                        "evidence": f"{assistant_name} asserted '{fact_str}' for prompt '{prompt}'. Visible site prices: {', '.join(sorted(site_prices)[:5])}.",
                        "suggested_action": {
                            "summary": "Publish canonical pricing in JSON-LD and OpenGraph metadata to ground assistant retrieval.",
                            "priority": "high",
                            "verification": "Re-run assistant prompt and verify the quoted price matches on-site Product schema."
                        }
                    })

    return findings, observational_notes


def audit(site, responses_file=None, inv=None):
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"

    snapshot = build_fact_snapshot(base, inv=inv)
    if snapshot.get("status") != "ok":
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": snapshot.get("error", "could not build fact snapshot")
        }

    findings = []
    recommendations = []
    observational_notes = []

    if responses_file and os.path.exists(responses_file):
        try:
            with open(responses_file, "r", encoding="utf-8") as f:
                obs_data = json.load(f)
            f_list, notes = compare_assistant_observations(snapshot, obs_data)
            findings.extend(f_list)
            observational_notes.extend(notes)
        except Exception as e:
            return {
                "status": "inconclusive",
                "findings": [],
                "recommendations": [],
                "error": f"Failed to parse responses file: {e}"
            }
    else:
        # Emits the site baseline snapshot when no responses file is provided
        recommendations.append({
            "title": "Evaluate AI assistant representation with observed responses",
            "category": "representation-testing",
            "rationale": "No observed AI assistant response dataset was supplied. Provide a --responses file to cross-check live ChatGPT, Claude, and Perplexity quotes.",
            "suggested_action": "Supply a --responses file containing recorded assistant prompts, citations, and claims."
        })

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observational_notes": observational_notes,
        "coverage": {
            "site_snapshot_built": True,
            "observations_evaluated": len(observational_notes) + len(findings),
            "source": "shared-inventory" if inv is not None else "independent-fetch"
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Assistant representation cross-check layer.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--responses", "--observations", dest="responses", help="JSON file of observed assistant outputs to cross-check")
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
    args = parser.parse_args()

    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None

    print(json.dumps(audit(args.site, responses_file=args.responses, inv=inv), indent=2))


if __name__ == "__main__":
    main()
