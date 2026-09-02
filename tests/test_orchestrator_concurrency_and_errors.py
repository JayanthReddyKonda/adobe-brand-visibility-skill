import unittest
import json
import subprocess
import os
import tempfile

class TestOrchestratorConcurrencyAndErrors(unittest.TestCase):
    def setUp(self):
        self.orch_script = "src/skills/audit-orchestrator/scripts/orchestrator.py"
        self.val_script = "src/skills/audit-orchestrator/scripts/validate_report.py"

    def test_orchestrator_handles_missing_target_gracefully(self):
        # Invalid / unreachable target URL returns exit code 0 with partial or failed status
        res = subprocess.run(["python3", self.orch_script, "--site", "https://invalid-unreachable-target-domain-99999.xyz"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        report = json.loads(res.stdout)
        self.assertIn("audit_status", report)
        self.assertIn("summary", report)

    def test_orchestrator_preserves_custom_output_flag(self):
        out_path = "/tmp/custom_orchestrator_report.json"
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [{"url": "https://testbrand.com/", "status": 200, "content_type": "text/html", "page_type": "homepage", "html": "<html><body><h1>Test</h1><p>Test offers plans starting at $49/mo because algorithms improve speed by 30%.</p></body></html>"}],
            "robots_txt": "User-agent: *\nAllow: /\n",
            "sitemaps": []
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(inv_data, tf)
            tf_path = tf.name
        try:
            res = subprocess.run(["python3", self.orch_script, "--site", "https://testbrand.com", "--inventory", tf_path, "--output", out_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, "r") as f:
                saved_report = json.load(f)
            self.assertEqual(saved_report["site"], "https://testbrand.com")
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    def test_orchestrator_maps_all_dual_track_remediations(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {"url": "https://testbrand.com/", "status": 200, "content_type": "text/html", "page_type": "homepage", "html": "<html><body><h2>Cloud Pro</h2><p>$10/mo</p></body></html>"},
                {"url": "https://testbrand.com/pricing", "status": 200, "content_type": "text/html", "page_type": "pricing", "html": "<html><body><h2>Cloud Pro</h2><p>$50/mo</p></body></html>"}
            ],
            "robots_txt": "User-agent: OAI-SearchBot\nDisallow: /\n",
            "sitemaps": []
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(inv_data, tf)
            tf_path = tf.name
        try:
            res = subprocess.run(["python3", self.orch_script, "--site", "https://testbrand.com", "--inventory", tf_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            report = json.loads(res.stdout)
            for f in report.get("findings", []):
                act = f.get("suggested_action", {})
                self.assertIn("technical_fix", act)
                self.assertIn("creative_fix", act)
                self.assertIn("verification", act)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_orchestrator_sub_5_second_execution(self):
        import time
        t0 = time.time()
        inv_data = {"site": "https://speedtest.com", "pages": [{"url": "https://speedtest.com/", "status": 200, "content_type": "text/html", "page_type": "homepage", "html": "<html><body><h1>Speed Test</h1><p>Starting at $10/mo because our platform is fast.</p></body></html>"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(inv_data, tf)
            tf_path = tf.name
        try:
            res = subprocess.run(["python3", self.orch_script, "--site", "https://speedtest.com", "--inventory", tf_path], capture_output=True, text=True)
            elapsed = time.time() - t0
            self.assertEqual(res.returncode, 0)
            self.assertLess(elapsed, 5.0, f"Execution must be < 5.0s, actual {elapsed:.2f}s")
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_orchestrator_schema_pipe_integrity(self):
        inv_data = {"site": "https://testpipe.com", "pages": [{"url": "https://testpipe.com/", "status": 200, "content_type": "text/html", "page_type": "homepage", "html": "<html><body><h1>Pipe Test</h1></body></html>"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(inv_data, tf)
            tf_path = tf.name
        try:
            orch_res = subprocess.run(["python3", self.orch_script, "--site", "https://testpipe.com", "--inventory", tf_path], capture_output=True, text=True)
            val_res = subprocess.run(["python3", self.val_script, "-"], input=orch_res.stdout, capture_output=True, text=True)
            self.assertEqual(val_res.returncode, 0)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

if __name__ == "__main__":
    unittest.main()
