import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TelemetryFact:
    fact_type: str
    evidence: str
    metadata: Dict[str, Any]


@dataclass
class TelemetryResponse:
    status: str  # "ok", "inconclusive", "failed"
    telemetry: Dict[str, Any]
    raw_extracted_facts: List[TelemetryFact]
    error: Optional[str] = None
    limitations: Optional[List[str]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
