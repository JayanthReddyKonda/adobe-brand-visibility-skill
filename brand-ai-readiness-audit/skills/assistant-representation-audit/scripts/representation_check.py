#!/usr/bin/env python3
"""
representation_check.py - Assistant representation layer (optional enrichment).

Cross-checks OBSERVED assistant responses (supplied as JSON by the operator or
another agent - never queried live from this script) against the brand's
first-party fact snapshot. Detects conditions under which an assistant's
representation would diverge from the brand's own evidence: factual conflicts,
unsupported claims, and missing-mention signals.

Input format (--responses file):
{
  "site": "example.com",
  "observations": [
    {
      "assistant": "ChatGPT",
      "prompt": "best specialty coffee subscriptions",
      "mentioned": true,
      "cited": false,
      "claims": [{"fact": "Frescopa ships monthly at $4,999", "topic": "pricing"}]
    }
  ]
}

Run without --responses to receive a site-side snapshot that OTHER systems
can compare responses against.
"""
import sys, json, argparse
import urllib.request
from urllib.parse import urlparse
from html.parser import HTMLParser

PRICE_RE = None  # compiled lazily


class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())


def fact_snapshot(site):
    """First-party fact snapshot used as the comparison baseline."""
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    try:
        with urllib.request.urlopen(urllib.request.Request(
                base + "/", headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0)"}),
                timeout=10) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception as e:
        return {"status": "inconclusive", "error": f"could not reach {base}: {e}"}
    dom = Dom()
    try:
        dom.feed(html)
    except Exception:
        pass
    prices, dates = [], []
    text = " ".join(dom.text)
    import re
    prices = re.findall(r'(?:₹|Rs\.?|\$|€|£)\s?\d[\d,]*(?:\.\d{1,2})?', text)
    dates = re.findall(r'\b(20\d{2})\b', text)
    return {"status": "ok", "site": base, "prices_visible": sorted(set(prices))[:20],
            "years_visible": sorted(set(dates))[:10], "word_count": len(text.split())}


def compare(snapshot, responses):
    """Flag only provable conflicts between observed claims and site facts."""
    findings, notes = [], []
    prices = set(snapshot.get("prices_visible", []))
    for obs in responses.get("observations", []):
        who = obs.get("assistant", "assistant")
        if not obs.get("mentioned"):
            notes.append(dict(assistant=who, prompt=obs.get("prompt"),
                              signal="brand not mentioned (observational, not a site defect)"))
            continue
        if not obs.get("cited"):
            notes.append(dict(assistant=who, prompt=obs.get("prompt"),
                              signal="mentioned but not cited"))
        for claim in obs.get("claims", []):
            fact = str(claim.get("fact", ""))
            for price in prices:
                # conflicting price: assistant names a price absent from the site
                digits = "".join(c for c in price if c.isdigit())
                if digits and digits in fact and price not in fact:
                    findings.append(dict(
                        category="representation", title="Assistant-stated price conflicts with first-party facts",
                        severity="high", confidence="medium",
                        root_cause="The assistant asserts a price that does not appear on the brand's own site, while the site states a different figure.",
                        impact="Users receive wrong commercial information; the site's page failed to be the canonical source.",
                        evidence=f"{who} claimed '{fact}'; site's visible prices include {price} but not the asserted figure.",
                        suggested_action=dict(
                            summary="Make canonical pricing explicit in initial HTML and Product JSON-LD so assistants extract, not infer, prices.",
                            priority="high",
                            verification="Re-pose the prompt after republishing and confirm the quoted price matches the site.")))
                    break
    return findings, notes


def main():
    ap = argparse.ArgumentParser(description="Assistant representation cross-check layer.")
    ap.add_argument("--site", required=True)
    ap.add_argument("--responses", help="JSON file of observed assistant responses to cross-check")
    args = ap.parse_args()

    snapshot = fact_snapshot(args.site)
    out = {"status": snapshot.get("status", "ok"), "snapshot": snapshot}
    if args.responses:
        try:
            with open(args.responses) as f:
                responses = json.load(f)
        except Exception as e:
            out["status"] = "inconclusive"
            out["error"] = f"could not read responses file: {e}"
        else:
            if snapshot.get("status") == "ok":
                findings, notes = compare(snapshot, responses)
                out["findings"] = findings
                out["observational_notes"] = notes
            else:
                out["error"] = "site snapshot unavailable; cannot cross-check responses"
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
