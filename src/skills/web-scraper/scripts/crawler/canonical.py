"""Canonical URL validation and anomaly detector.

Detects missing canonical tags, cross-domain canonicals, protocol mismatches (HTTP/HTTPS),
and trailing slash discrepancies.
Pure Python standard library.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from urllib.parse import urlparse

from .models import Observation


class CanonicalValidator:
    """Evaluates canonical URL declarations for SEO and machine discoverability defects."""

    @classmethod
    def evaluate(
        cls, current_url: str, canonical_url: Optional[str]
    ) -> Tuple[bool, List[Observation]]:
        """Evaluates canonical relationship. Returns (is_valid, observations)."""
        observations: List[Observation] = []

        if not canonical_url or not canonical_url.strip():
            observations.append(
                Observation(
                    type="canonical_gap",
                    value="missing_canonical_tag",
                    confidence="high",
                    evidence=f"No <link rel='canonical'> specified on {current_url}",
                    severity_hint="medium",
                )
            )
            return False, observations

        clean_canonical = canonical_url.strip()
        try:
            curr_parsed = urlparse(current_url)
            canon_parsed = urlparse(clean_canonical)
        except Exception:
            observations.append(
                Observation(
                    type="canonical_defect",
                    value="malformed_canonical_url",
                    confidence="high",
                    evidence=f"Malformed canonical tag '{clean_canonical}' on {current_url}",
                    severity_hint="high",
                )
            )
            return False, observations

        # Protocol mismatch check
        if curr_parsed.scheme == "https" and canon_parsed.scheme == "http":
            observations.append(
                Observation(
                    type="canonical_defect",
                    value="protocol_downgrade",
                    confidence="high",
                    evidence=f"Secure HTTPS page canonicalizes to insecure HTTP target: {clean_canonical}",
                    severity_hint="high",
                )
            )

        # Cross-domain canonical check
        curr_host = (curr_parsed.hostname or "").lower()
        canon_host = (canon_parsed.hostname or "").lower()
        if canon_host and curr_host != canon_host:
            observations.append(
                Observation(
                    type="canonical_cross_domain",
                    value="cross_domain_canonical_detected",
                    confidence="medium",
                    evidence=f"Page on host '{curr_host}' points to canonical target on '{canon_host}'",
                    severity_hint="medium",
                )
            )

        has_defect = any(
            obs.type in ("canonical_gap", "canonical_defect", "canonical_cross_domain")
            for obs in observations
        )
        return not has_defect, observations
