import argparse
import urllib.parse
from http import safe_fetch
from telemetry import TelemetryResponse, TelemetryFact
from dom import UnifiedDOMParser

def audit(base_url):
    status, html, _, _ = safe_fetch(base_url + "/")
    if not html:
        return TelemetryResponse(status="inconclusive", telemetry={}, raw_extracted_facts=[], error="No HTML")
        
    dom = UnifiedDOMParser()
    dom.feed(html)
    
    text = " ".join(dom.visible_text).lower()
    
    # Check for causal conjunctions
    causal_words = ["because", "therefore", "results in", "enables", "mechanism", "how it works"]
    found_causal = [w for w in causal_words if w in text]
    
    telemetry = {
        "causal_conjunctions_found": found_causal,
        "word_count": len(text.split())
    }
    
    facts = []
    if len(found_causal) < 2:
        facts.append(TelemetryFact(
            fact_type="shallow_mechanisms",
            evidence=f"Text lacks sufficient causal/mechanistic depth. Found: {found_causal}",
            metadata={"found": found_causal}
        ))
        
    return TelemetryResponse(status="ok", telemetry=telemetry, raw_extracted_facts=facts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory")
    args = parser.parse_args()
    base, _ = urllib.parse.urlparse(args.site.strip() if args.site.startswith("http") else "https://" + args.site.strip())
    res = audit(f"{base.scheme}://{base.netloc}")
    print(res.to_json())
