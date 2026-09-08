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
    BLOCKED = "robots_blocked"
    SERVER_ERROR = "robots_server_error"
    TIMEOUT = "robots_timeout"
    PARSE_ERROR = "robots_parse_error"


BOT_TAXONOMY: Dict[str, Dict[str, str]] = {
    "OAI-SearchBot": {"role": "search_crawler", "provider": "OpenAI", "description": "Search indexation crawler for ChatGPT Search"},
    "Claude-SearchBot": {"role": "search_crawler", "provider": "Anthropic", "description": "Search indexation crawler for Claude"},
    "PerplexityBot": {"role": "search_crawler", "provider": "Perplexity", "description": "Search retrieval crawler for Perplexity AI"},
    "Amazonbot": {"role": "search_crawler", "provider": "Amazon", "description": "Web crawler for Alexa and Amazon AI"},
    "cohere-ai": {"role": "training_bot", "provider": "Cohere", "description": "Model pretraining web crawler"},
    "Meta-ExternalAgent": {"role": "search_crawler", "provider": "Meta", "description": "Search crawler for Meta AI"},
    "Claude-User": {"role": "user_directed_fetch", "provider": "Anthropic", "description": "On-demand user request fetcher for Claude"},
    "Perplexity-User": {"role": "user_directed_fetch", "provider": "Perplexity", "description": "On-demand user query fetcher for Perplexity"},
    "ChatGPT-User": {"role": "user_directed_fetch", "provider": "OpenAI", "description": "On-demand browsing fetcher for ChatGPT"},
    "GPTBot": {"role": "training_bot", "provider": "OpenAI", "description": "AI model training and fine-tuning crawler"},
    "ClaudeBot": {"role": "training_bot", "provider": "Anthropic", "description": "AI model training crawler"},
    "Bytespider": {"role": "training_bot", "provider": "ByteDance", "description": "AI model training crawler"},
    "Applebot-Extended": {"role": "training_bot", "provider": "Apple", "description": "Control token for Apple Intelligence model training"},
    "Google-Extended": {"role": "control_token", "provider": "Google", "description": "Control token for Gemini and Vertex AI training"},
    "CCBot": {"role": "training_bot", "provider": "Common Crawl", "description": "Open web crawl repository for pretraining"},
    "*": {"role": "wildcard", "provider": "Universal", "description": "Default crawler fallback directive"},
}


def robot_octets(value: str) -> str:
    """Compare UTF-8 octets; decode only percent-encoded ASCII unreserved bytes."""
    from urllib.parse import quote

    value = quote(value, safe="/%*?$&=:@!+,'();~-._")

    def replace(match: Any) -> str:
        c = chr(int(match.group(1), 16))
        return c if c.isascii() and (c.isalnum() or c in "-._~") else "%" + match.group(1).upper()

    return re.sub(r"%([0-9a-fA-F]{2})", replace, value)


class RobotsRule:
    """Represents an Allow or Disallow rule with longest-match pattern matching."""

    def __init__(self, is_allow: bool, pattern: str) -> None:
        self.is_allow = is_allow
        self.raw_pattern = pattern
        self.pattern = robot_octets(pattern)
        self.terminal = self.pattern.endswith("$")
        pat_clean = self.pattern[:-1] if self.terminal else self.pattern
        regex = "^" + ".*".join(re.escape(x) for x in pat_clean.split("*")) + ("$" if self.terminal else "")
        self._compiled_regex = re.compile(regex)

    def matches(self, path: str) -> bool:
        norm_path = robot_octets(path)
        return bool(self._compiled_regex.search(norm_path))

    @property
    def length(self) -> int:
        pat = self.pattern[:-1] if self.terminal else self.pattern
        return len(re.sub(r"%[A-F0-9]{2}", "x", pat.replace("*", "")))


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
        1. 401/403: restricted access, fail-closed (Disallow all).
        2. 5xx / 429 / SERVER_ERROR: fail-closed per RFC 9309 section 2.3.1.2.
        3. 404 / NOT_FOUND: fail-open (Allow all).
        4. Multiple matching user-agent groups are combined per RFC 9309 section 2.2.1.
        5. Specific user-agent match takes precedence over wildcard (*).
        6. Within the combined group, longest matching rule wins.
        7. If same length, Allow takes precedence over Disallow.
        8. Default is Allow if no rules match.
        """
        # Support both (user_agent, url_or_path) and (url_or_path, user_agent)
        if user_agent.startswith(("http://", "https://", "/")) and not url_or_path.startswith(("http://", "https://", "/")):
            user_agent, url_or_path = url_or_path, user_agent

        # RFC 9309 section 2.3.1.1: 401/403 restricted access -> fail closed
        if self.outcome == RobotsOutcome.BLOCKED or self.status_code in (401, 403):
            return False

        # RFC 9309 section 2.3.1.2: 5xx / 429 server error -> fail closed
        if self.outcome == RobotsOutcome.SERVER_ERROR or self.status_code >= 500 or self.status_code == 429:
            return False

        # RFC 9309 section 2.3.1.3: 404 not found -> fail open
        if self.outcome == RobotsOutcome.NOT_FOUND or self.status_code == 404:
            return True

        parsed = urlparse(url_or_path)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        matching_rules: List[RobotsRule] = []
        agent_lower = user_agent.lower()

        # Step 1: Combine rules from ALL groups matching the user-agent product token (RFC 9309 section 2.2.1)
        matched_specific = False
        for group in self.groups:
            for ua in group.user_agents:
                ua_clean = ua.strip().lower()
                if ua_clean != "*" and (ua_clean == agent_lower or ua_clean in agent_lower or agent_lower in ua_clean):
                    matching_rules.extend(group.rules)
                    matched_specific = True
                    break

        # Step 2: Fall back to wildcard (*) groups if no specific agent matched
        if not matched_specific:
            for group in self.groups:
                for ua in group.user_agents:
                    if ua.strip() == "*":
                        matching_rules.extend(group.rules)
                        break

        if not matching_rules:
            return True

        # Step 3: Apply longest-match rule per RFC 9309 section 2.2.2
        best_match: Optional[RobotsRule] = None
        for rule in matching_rules:
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
        """Evaluate access permissions across all standard 16 AI crawler bots with taxonomy metadata."""
        matrix: Dict[str, Dict[str, Any]] = {}
        for bot in AI_CRAWLER_BOTS:
            allowed = self.is_allowed(bot, path)
            tax = BOT_TAXONOMY.get(bot, {"role": "unknown", "provider": "Unknown", "description": "AI bot"})
            matrix[bot] = {
                "allowed": allowed,
                "status": "allowed" if allowed else "blocked",
                "role": tax.get("role", "unknown"),
                "provider": tax.get("provider", "Unknown"),
                "description": tax.get("description", ""),
            }
        return matrix

    @property
    def delay(self) -> float:
        delays = [g.crawl_delay for g in self.groups if g.crawl_delay is not None]
        return max(delays) if delays else 1.0

    def allowed(self, url_or_path: str, user_agent: str = "ReadinessAudit") -> bool:
        return self.is_allowed(user_agent, url_or_path)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "outcome": self.outcome,
            "sitemaps": self.sitemaps,
            "groups_count": len(self.groups),
            "ai_bots_matrix": self.evaluate_ai_bots_matrix("/"),
        }


# Standard alias for compatibility with test harnesses and single-pass collectors
Robots = RobotsAuditor


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
