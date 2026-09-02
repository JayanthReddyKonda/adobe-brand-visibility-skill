from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class TelemetryFact:
    fact_type: str
    evidence: str
    metadata: dict[str, Any]


@dataclass
class TelemetryResponse:
    status: str  # "ok", "inconclusive", "failed"
    telemetry: dict[str, Any]
    raw_extracted_facts: list[TelemetryFact]
    error: str | None = None
    limitations: list[str] | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
