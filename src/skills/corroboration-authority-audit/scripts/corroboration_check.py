import argparse
import urllib.parse
from http import safe_check_status
from telemetry import TelemetryResponse, TelemetryFact

def audit(base_url):
    telemetry = {"sameas_links_found": [], "broken_links": []}
    return TelemetryResponse(status="ok", telemetry=telemetry, raw_extracted_facts=[])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory")
    args = parser.parse_args()
    print(audit(args.site).to_json())
