import unittest
import json
from src.core.telemetry import TelemetryResponse, TelemetryFact

class TestTelemetry(unittest.TestCase):
    def test_serialization(self):
        fact = TelemetryFact(fact_type="test", evidence="some evidence", metadata={"key": "val"})
        resp = TelemetryResponse(status="ok", telemetry={"count": 1}, raw_extracted_facts=[fact])
        
        j = resp.to_json()
        d = json.loads(j)
        self.assertEqual(d["status"], "ok")
        self.assertEqual(d["telemetry"]["count"], 1)
        self.assertEqual(d["raw_extracted_facts"][0]["fact_type"], "test")

if __name__ == "__main__":
    unittest.main()
