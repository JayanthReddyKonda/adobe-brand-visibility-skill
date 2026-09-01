import argparse
import urllib.parse
import json
from http import safe_fetch
from telemetry import TelemetryResponse, TelemetryFact
from dom import UnifiedDOMParser

def parse_domain(site):
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urllib.parse.urlparse(s)
    return f"{p.scheme}://{p.netloc}", p.netloc

def extract_json_ld(contents):
    results = []
    for c in contents:
        try:
            parsed = json.loads(c)
            if isinstance(parsed, list):
                results.extend(parsed)
            elif isinstance(parsed, dict):
                if "@graph" in parsed:
                    results.extend(parsed["@graph"])
                else:
                    results.append(parsed)
        except Exception:
            pass
    return results

def audit(base_url, domain):
    status, html, _, _ = safe_fetch(base_url + "/")
    if not html:
        return TelemetryResponse(status="inconclusive", telemetry={}, raw_extracted_facts=[], error="No HTML")
        
    dom = UnifiedDOMParser()
    dom.feed(html)
    
    entities = extract_json_ld(dom.json_ld_contents)
    has_org = any(e.get("@type", "").lower() in ["organization", "corporation", "brand"] for e in entities)
    
    facts = []
    telemetry = {
        "json_ld_blocks": len(entities),
        "has_organization_schema": has_org,
        "og_site_name": dom.og_tags.get("og:site_name")
    }
    
    if not has_org:
        facts.append(TelemetryFact(
            fact_type="missing_organization_schema",
            evidence="No JSON-LD Organization block found on homepage.",
            metadata={}
        ))
        
    return TelemetryResponse(status="ok", telemetry=telemetry, raw_extracted_facts=facts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory")
    args = parser.parse_args()
    base, domain = parse_domain(args.site)
    res = audit(base, domain)
    print(res.to_json())
