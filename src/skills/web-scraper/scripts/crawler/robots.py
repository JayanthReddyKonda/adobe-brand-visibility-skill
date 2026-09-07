"""RFC 9309 compliant robots.txt auditor and permission evaluator.

Features:
- Longest-match rule precedence per RFC 9309 section 2.2.2.
- 500 KiB parsing ceiling (CR04).
- Status outcome classification (robots_ok, robots_not_found, robots_server_error fail-closed, etc.).
- 16 AI crawler bots permission matrix.
- Declared sitemap extraction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

AI_CRAWLER_BOTS: List[str] = [
    "OAI-SearchBot",
    "Claude-SearchBot",
    "PerplexityBot",
    "Amazonbot",
    "cohere-ai",
    "Meta-ExternalAgent",
    "Claude-User",
    "Perplexity-User",
    "ChatGPT-User",
    "GPTBot",
    "ClaudeBot",
    "Bytespider",
    "Applebot-Extended",
    "Google-Extended",
    "CCBot",
    "*",
]

# Max bytes to parse per RFC 9309 section 2.1 (500 KiB)
MAX_ROBOTS_BYTES = 500 * 1024


class RobotsOutcome:
    OK = "robots_ok"
    NOT_FOUND = "robots_not_found"
    TIMEOUT = "robots_timeout"
    SERVER_ERROR = "robots_server_error"
    PARSE_ERROR = "robots_parse_error"


class RobotsRule:
    """Represents an Allow or Disallow rule with longest-match pattern matching."""

    def __init__(self, is_allow: bool, pattern: str) -> None:
        self.is_allow = is_allow
        self.pattern = pattern
        self._compiled_regex = self._compile(pattern)

    def _compile(self, pattern: str) -> re.Pattern[str]:
        # RFC 9309 pattern matching: * is wildcard, $ is end of string
        escaped = re.escape(pattern).replace(r"\*", ".*")
        if escaped.endswith(r"\$"):
            escaped = escaped[:-2] + "$"
        return re.compile("^" + escaped)

    def matches(self, path: str) -> bool:
        return bool(self._compiled_regex.match(path))

    @property
    def length(self) -> int:
        return len(self.pattern)


class RobotsGroup:
    """A collection of rules belonging to one or more user-agent identifiers."""

    def __init__(self) -> None:
        self.user_agents: Set[str] = set()
        self.rules: List[RobotsRule] = []
        self.crawl_delay: Optional[float] = None

    def applies_to(self, target_agent: str) -> bool:
        target_lower = target_agent.lower()
        return any(ua.lower() == target_lower or ua == "*" for ua in self.user_agents)


class RobotsAuditor:
    """Parser and evaluator for robots.txt files conforming to RFC 9309."""

    def __init__(self, content: str = "", status_code: int = 200, outcome: str = RobotsOutcome.OK) -> None:
        self.raw_content = content[:MAX_ROBOTS_BYTES]
        self.status_code = status_code
        self.outcome = outcome
        self.groups: List[RobotsGroup] = []
        self.sitemaps: List[str] = []
        self._parse()

    def _parse(self) -> None:
        if not self.raw_content or self.status_code == 404:
            return

        current_group: Optional[RobotsGroup] = None
        lines = self.raw_content.splitlines()

        for line in lines:
            line = line.strip()
            # Strip comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue

            field, value = [p.strip() for p in line.split(":", 1)]
            field_lower = field.lower()

            if field_lower == "user-agent":
                if current_group is None or current_group.rules:
                    current_group = RobotsGroup()
                    self.groups.append(current_group)
                current_group.user_agents.add(value)

            elif field_lower == "disallow":
                if current_group is not None and value:
                    current_group.rules.append(RobotsRule(is_allow=False, pattern=value))

            elif field_lower == "allow":
                if current_group is not None and value:
                    current_group.rules.append(RobotsRule(is_allow=True, pattern=value))

            elif field_lower == "crawl-delay":
                if current_group is not None:
                    try:
                        current_group.crawl_delay = float(value)
                    except ValueError:
                        pass

            elif field_lower == "sitemap":
                if value and value not in self.sitemaps:
                    self.sitemaps.append(value)

    def is_allowed(self, user_agent: str, url_or_path: str = "") -> bool:
        """Determines whether a given user agent is allowed to access the path.

        Follows RFC 9309 rule precedence:
        1. Specific user-agent match takes precedence over wildcard (*).
        2. Within the group, longest matching rule wins.
        3. If same length, Allow takes precedence over Disallow.
        4. Default is Allow if no rules match or on 404.
        """
        # Support both (user_agent, url_or_path) and (url_or_path, user_agent)
        if user_agent.startswith(("http://", "https://", "/")) and not url_or_path.startswith(("http://", "https://", "/")):
            user_agent, url_or_path = url_or_path, user_agent
        # If robots.txt returned 5xx, fail-closed per RFC 9309 section 2.3.1.2
        if self.outcome == RobotsOutcome.SERVER_ERROR or self.status_code >= 500:
            return False

        # If robots.txt returned 404, full access is granted (fail-open)
        if self.outcome == RobotsOutcome.NOT_FOUND or self.status_code == 404:
            return True

        parsed = urlparse(url_or_path)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        # Step 1: Find best matching group (specific agent preferred over '*')
        target_group: Optional[RobotsGroup] = None
        wildcard_group: Optional[RobotsGroup] = None

        agent_lower = user_agent.lower()
        for group in self.groups:
            for ua in group.user_agents:
                if ua.lower() == agent_lower:
                    target_group = group
                    break
                elif ua == "*":
                    wildcard_group = group
            if target_group:
                break

        active_group = target_group or wildcard_group
        if not active_group or not active_group.rules:
            return True

        # Step 2: Apply longest-match rule
        best_match: Optional[RobotsRule] = None
        for rule in active_group.rules:
            if rule.matches(path):
                if best_match is None or rule.length > best_match.length:
                    best_match = rule
                elif rule.length == best_match.length and rule.is_allow and not best_match.is_allow:
                    # RFC 9309: If lengths are equal, Allow takes precedence
                    best_match = rule

        if best_match is None:
            return True
        return best_match.is_allow

    def evaluate_ai_bots_matrix(self, path: str = "/") -> Dict[str, Dict[str, Any]]:
        """Evaluate access permissions across all standard 16 AI crawler bots."""
        matrix: Dict[str, Dict[str, Any]] = {}
        for bot in AI_CRAWLER_BOTS:
            allowed = self.is_allowed(bot, path)
            matrix[bot] = {
                "allowed": allowed,
                "status": "allowed" if allowed else "blocked",
            }
        return matrix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "outcome": self.outcome,
            "sitemaps": self.sitemaps,
            "groups_count": len(self.groups),
            "ai_bots_matrix": self.evaluate_ai_bots_matrix("/"),
        }


def load_bot_registry() -> Dict[str, Any]:
    """Load authoritative bot registry from references/bot-registry.json if available."""
    import json
    import os

    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "references",
        "bot-registry.json",
    )
    if os.path.exists(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"version": "2026-09-01", "bots": []}
