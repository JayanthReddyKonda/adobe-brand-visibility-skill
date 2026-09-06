"""CLI runner helper for executing skill entrypoints with strict parity checking."""

import json
import os
import subprocess
import sys
from typing import Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILLS_DIR = os.path.join(PROJECT_ROOT, "src", "skills")


class CLIResult:
    """Encapsulates the result of a CLI script invocation."""

    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self._parsed_json: Optional[Any] = None

    @property
    def is_success(self) -> bool:
        return self.returncode == 0

    @property
    def json(self) -> Any:
        """Parses stdout as JSON, caching the result."""
        if self._parsed_json is None:
            self._parsed_json = json.loads(self.stdout)
        return self._parsed_json

    def json_safe(self) -> Optional[Any]:
        """Tries to parse stdout as JSON, returning None on failure."""
        try:
            return self.json
        except Exception:
            return None


def run_skill_script(
    skill_name: str,
    script_file: str,
    args: List[str],
    stdin_data: Optional[str] = None,
    timeout: float = 30.0,
    cwd: Optional[str] = None,
) -> CLIResult:
    """Runs a Python script from src/skills/<skill_name>/scripts/<script_file>."""
    script_path = os.path.join(SKILLS_DIR, skill_name, "scripts", script_file)
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script does not exist: {script_path}")

    cmd = [sys.executable, script_path] + args
    res = subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd or PROJECT_ROOT,
        check=False,
    )
    return CLIResult(returncode=res.returncode, stdout=res.stdout, stderr=res.stderr)


def run_validator(report_dict_or_json: Any, filepath: Optional[str] = None) -> CLIResult:
    """Invokes validate_report.py either via stdin or with a file path."""
    val_script = os.path.join(SKILLS_DIR, "audit-orchestrator", "scripts", "validate_report.py")
    if filepath:
        cmd = [sys.executable, val_script, filepath]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    else:
        cmd = [sys.executable, val_script, "-"]
        data = report_dict_or_json if isinstance(report_dict_or_json, str) else json.dumps(report_dict_or_json)
        res = subprocess.run(cmd, input=data, capture_output=True, text=True, check=False)
    return CLIResult(returncode=res.returncode, stdout=res.stdout, stderr=res.stderr)
