"""Metadata normalization and extraction for OpenGraph, Twitter, Dublin Core, and Robots directives.

Pure Python standard library.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .models import Observation


class MetadataProcessor:
    """Normalizes raw HTML meta tags into structured OpenGraph, Twitter, and indexer directives."""

    @classmethod
    def process_metadata(
        cls, meta_tags: List[Dict[str, str]], source_url: str = ""
    ) -> Tuple[Dict[str, Any], List[Observation]]:
        """Transforms raw meta tag list into organized metadata dictionary and observations."""
        structured: Dict[str, Any] = {
            "standard": {},
            "opengraph": {},
            "twitter": {},
            "dublin_core": {},
            "robots_directives": [],
        }
        observations: List[Observation] = []

        for item in meta_tags:
            name = item.get("name", "").strip().lower()
            content = item.get("content", "").strip()
            if not name or not content:
                continue

            # Robots directives
            if name in {"robots", "googlebot", "bingbot"}:
                directives = [d.strip().lower() for d in content.split(",") if d.strip()]
                structured["robots_directives"].extend(directives)

                if "nosnippet" in directives:
                    observations.append(
                        Observation(
                            type="indexer_restriction",
                            value="nosnippet_detected",
                            confidence="high",
                            evidence=f"Meta tag '{name}' contains 'nosnippet' directive on {source_url}",
                            severity_hint="critical",
                        )
                    )
                if "noindex" in directives:
                    observations.append(
                        Observation(
                            type="indexer_restriction",
                            value="noindex_detected",
                            confidence="high",
                            evidence=f"Meta tag '{name}' contains 'noindex' directive on {source_url}",
                            severity_hint="critical",
                        )
                    )

            # OpenGraph
            elif name.startswith("og:"):
                key = name[3:]
                structured["opengraph"][key] = content

            # Twitter
            elif name.startswith("twitter:"):
                key = name[8:]
                structured["twitter"][key] = content

            # Dublin Core
            elif name.startswith("dc.") or name.startswith("dc:"):
                key = name[3:]
                structured["dublin_core"][key] = content

            # Standard
            else:
                structured["standard"][name] = content

        return structured, observations
