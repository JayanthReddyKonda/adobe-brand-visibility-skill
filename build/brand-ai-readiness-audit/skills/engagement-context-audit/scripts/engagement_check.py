import argparse
import urllib.parse
from telemetry import TelemetryResponse, TelemetryFact

def audit(base_url):
    telemetry = {"h1_tags": [], "call_to_actions": []}
    return TelemetryResponse(status="ok", telemetry=telemetry, raw_extracted_facts=[])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory")
    args = parser.parse_args()
    print(audit(args.site).to_json())
