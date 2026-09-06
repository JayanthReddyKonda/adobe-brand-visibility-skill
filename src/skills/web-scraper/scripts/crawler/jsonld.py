"""JSON-LD schema parser, graph flattener, and entity/fact candidate extractor.

Normalizes single objects, arrays, and @graph structures, preserving block provenance
and locator paths (e.g., Product.offers[0].price).
Pure Python standard library (json).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from .models import FactCandidate, Observation


class JsonLdExtractor:
    """Parses and normalizes Schema.org JSON-LD scripts with provenance tracking."""

    @classmethod
    def parse_blocks(
        cls,
        raw_blocks: List[Tuple[str, str, int]],
        source_url: str = "",
    ) -> Tuple[List[Dict[str, Any]], List[FactCandidate], List[Observation]]:
        """Parses a list of (raw_json_text, location, block_index) tuples.

        Returns:
            normalized_schemas: List of top-level schema dicts.
            facts: Extracted structured fact candidates with locators.
            observations: Schema-related technical observations.
        """
        schemas: List[Dict[str, Any]] = []
        facts: List[FactCandidate] = []
        observations: List[Observation] = []

        if not raw_blocks:
            observations.append(
                Observation(
                    type="schema_gap",
                    value="no_jsonld_structured_data_found",
                    confidence="high",
                    evidence=f"No <script type='application/ld+json'> blocks found on {source_url}",
                    severity_hint="high",
                )
            )
            return schemas, facts, observations

        for raw_text, location, block_idx in raw_blocks:
            clean_text = raw_text.strip()
            if not clean_text:
                continue

            try:
                parsed_data = json.loads(clean_text)
            except json.JSONDecodeError as e:
                observations.append(
                    Observation(
                        type="schema_syntax_error",
                        value="jsonld_parse_failure",
                        confidence="high",
                        evidence=f"Block #{block_idx} ({location}) failed to parse as JSON: {e}",
                        severity_hint="high",
                    )
                )
                continue

            # Flatten objects, arrays, and @graph containers
            flattened = cls._flatten_jsonld(parsed_data)
            for item in flattened:
                if isinstance(item, dict):
                    item["_provenance"] = {
                        "block_index": block_idx,
                        "location": location,
                        "source_url": source_url,
                    }
                    schemas.append(item)
                    cls._extract_facts_from_schema(item, source_url, block_idx, facts)

        return schemas, facts, observations

    @classmethod
    def _flatten_jsonld(cls, data: Any) -> List[Dict[str, Any]]:
        """Flattens a JSON-LD structure into a list of entity dictionaries."""
        results: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for element in data:
                results.extend(cls._flatten_jsonld(element))
        elif isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                for element in data["@graph"]:
                    results.extend(cls._flatten_jsonld(element))
            else:
                results.append(data)
        return results

    @classmethod
    def _extract_facts_from_schema(
        cls,
        schema: Dict[str, Any],
        source_url: str,
        block_idx: int,
        facts: List[FactCandidate],
    ) -> None:
        """Extracts atomic commercial and identity facts from schema dicts."""
        schema_type = schema.get("@type")
        if not schema_type:
            return

        type_names = [schema_type] if isinstance(schema_type, str) else schema_type

        # Organization facts
        if any("Organization" in t or "Corporation" in t for t in type_names):
            org_name = schema.get("name")
            if org_name:
                facts.append(
                    FactCandidate(
                        attribute="entity_name",
                        value=org_name,
                        entity=org_name,
                        source_url=source_url,
                        locator=f"[{block_idx}].Organization.name",
                        mechanism="jsonld",
                    )
                )

            telephone = schema.get("telephone")
            if telephone:
                facts.append(
                    FactCandidate(
                        attribute="phone",
                        value=str(telephone).strip(),
                        entity=org_name,
                        source_url=source_url,
                        locator=f"[{block_idx}].Organization.telephone",
                        mechanism="jsonld",
                    )
                )

            email = schema.get("email")
            if email:
                facts.append(
                    FactCandidate(
                        attribute="email",
                        value=str(email).strip(),
                        entity=org_name,
                        source_url=source_url,
                        locator=f"[{block_idx}].Organization.email",
                        mechanism="jsonld",
                    )
                )

        # Product & Offer facts
        if any("Product" in t for t in type_names):
            prod_name = schema.get("name", "")
            offers = schema.get("offers")
            offer_list: List[Dict[str, Any]] = []
            if isinstance(offers, dict):
                offer_list = [offers]
            elif isinstance(offers, list):
                offer_list = [o for o in offers if isinstance(o, dict)]

            for o_idx, offer in enumerate(offer_list):
                price = offer.get("price")
                currency = offer.get("priceCurrency")
                if price is not None:
                    try:
                        clean_price = float(str(price).replace(",", "").replace("$", "").strip())
                    except ValueError:
                        clean_price = price

                    facts.append(
                        FactCandidate(
                            attribute="price",
                            value=clean_price,
                            currency=str(currency).upper() if currency else None,
                            entity=prod_name or "Product",
                            source_url=source_url,
                            locator=f"[{block_idx}].Product.offers[{o_idx}].price",
                            mechanism="jsonld",
                        )
                    )
