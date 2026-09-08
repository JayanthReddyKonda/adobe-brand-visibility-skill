"""
safe_fetch.py - Re-export shim pointing to canonical implementation in web-scraper.
"""
import importlib.util
import sys
from pathlib import Path

if "web_scraper_safe_fetch" in sys.modules:
    _mod = sys.modules["web_scraper_safe_fetch"]
else:
    _canonical_file = Path(__file__).resolve().parent.parent.parent / "web-scraper" / "scripts" / "safe_fetch.py"
    _spec = importlib.util.spec_from_file_location("web_scraper_safe_fetch", str(_canonical_file))
    if _spec is None or _spec.loader is None:
        raise ImportError(f"Cannot load canonical safe_fetch from {_canonical_file}")
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["web_scraper_safe_fetch"] = _mod
    _spec.loader.exec_module(_mod)

# Explicit re-exports for static analyzers, IDEs, and linters
DEFAULT_USER_AGENT = _mod.DEFAULT_USER_AGENT
MAX_HTML_BYTES = _mod.MAX_HTML_BYTES
BLOCKED_NETWORKS = _mod.BLOCKED_NETWORKS
safe_fetch = _mod.safe_fetch
safe_check_status = _mod.safe_check_status
SafeHTTPConnection = _mod.SafeHTTPConnection
SafeHTTPSConnection = _mod.SafeHTTPSConnection
SafeHTTPHandler = _mod.SafeHTTPHandler
SafeHTTPSHandler = _mod.SafeHTTPSHandler
SafeRedirectHandler = _mod.SafeRedirectHandler
_is_safe_host = _mod._is_safe_host
_decompress_bounded = _mod._decompress_bounded

# Ensure any additional attributes are re-exported
for _k, _v in _mod.__dict__.items():
    if not _k.startswith("__") and _k not in globals():
        globals()[_k] = _v

__all__ = [
    "MAX_HTML_BYTES",
    "DEFAULT_USER_AGENT",
    "BLOCKED_NETWORKS",
    "safe_fetch",
    "safe_check_status",
    "SafeHTTPConnection",
    "SafeHTTPSConnection",
    "SafeHTTPHandler",
    "SafeHTTPSHandler",
    "SafeRedirectHandler",
    "_is_safe_host",
    "_decompress_bounded",
]

# Ensure sys.modules points to canonical module for coherent monkeypatching in test suites
if __name__ in sys.modules:
    sys.modules[__name__] = _mod
