"""Property service layer.
BigQuery calls run in a thread executor (`asyncio.to_thread`) because the
official `google-cloud-bigquery` SDK is synchronous. This keeps FastAPI's
event loop unblocked.
"""
from __future__ import annotations

import asyncio
import math
from typing import Any
from pathlib import Path
import json

from app.services.cache.service import CacheService
from app.services.property.constants import (
    OSM_BOOLEAN_COLUMNS,
    OVERTURE_BOOLEAN_COLUMNS,
    RANGE_COLUMNS,
    UNIFIED_SCHEMA,
)
from app.services.property.queries import (
    get_properties_for_filtering_query,
    get_property_features_query,
)
from app.services.property.utils import to_label, validate_bbox

_PROPERTY_PATH = Path(__file__).parent / "mock_data.json"
_PROPERTY_DATA = json.loads(_PROPERTY_PATH.read_text())


# ---------------------------------------------------------------------------
# Module-level lookup maps (built once at import time for O(1) access)
# ---------------------------------------------------------------------------

_RANGE_MAP: dict[str, dict[str, Any]] = {r["key"]: r for r in RANGE_COLUMNS}
_OVERTURE_BOOL_MAP: dict[str, dict[str, Any]] = {
    b["key"]: b for b in OVERTURE_BOOLEAN_COLUMNS
}
_OSM_BOOL_MAP: dict[str, dict[str, Any]] = {b["key"]: b for b in OSM_BOOLEAN_COLUMNS}
_UNIFIED_SCHEMA_MAP: dict[str, dict[str, Any]] = {
    s["key"]: s for s in UNIFIED_SCHEMA
}
_ALL_BOOL_KEYS: set[str] = set(_OVERTURE_BOOL_MAP) | set(_OSM_BOOL_MAP)


def _matches_filter(prop: dict[str, Any], filter_: dict[str, Any]) -> bool:
    """Apply a single active filter to a property row."""
    key = filter_["key"]
    values = filter_["values"]

    # --- Range ---
    if key in _RANGE_MAP:
        val = prop.get(key)
        if val is None:
            return False
        return float(values[0]) <= val <= float(values[1])

    # --- Boolean (Overture or OSM) ---
    if key in _ALL_BOOL_KEYS:
        return str(prop.get(key)) == "true"

    # --- Enum (UNIFIED_SCHEMA) ---
    if key in _UNIFIED_SCHEMA_MAP:
        val = prop.get(key)
        return val is not None and str(val) in values

    return False


class PropertyService:
    """Stateless collection of property-related operations."""

    # -------------------------------------------------------------------------
    # getAvailableFilters — bbox + filters → filter groups + layouts + count
    # -------------------------------------------------------------------------

    @staticmethod
    async def get_available_filters(
        bbox: dict[str, float],
        active_filters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        active_filters = active_filters or []
        validate_bbox(bbox)

        # Step 1: fetch raw attribute rows (cached per bbox)
        raw_cache_key = CacheService.create_cache_key(
            {
                "swLng": bbox["sw_lng"],
                "swLat": bbox["sw_lat"],
                "neLng": bbox["ne_lng"],
                "neLat": bbox["ne_lat"],
            },
            "raw_attributes",
        )
        all_properties = await CacheService.get(raw_cache_key)

        if not all_properties:
            # NOTE: the live BQ call is currently
            # short-circuited to mock data. Uncomment the executor call below
            # to hit BigQuery for real.
            #
            # query, params = get_properties_for_filtering_query(bbox)
            # bq = get_bigquery_client()
            # job = await asyncio.to_thread(
            #     bq.query,
            #     query,
            #     job_config=bigquery.QueryJobConfig(query_parameters=params),
            #     location="US",
            # )
            # result = await asyncio.to_thread(lambda: list(job.result()))
            # all_properties = [dict(r) for r in result]

            all_properties = _PROPERTY_DATA
            await CacheService.set(raw_cache_key, all_properties)

        # Step 2: in-memory filtering
        if active_filters:
            filtered_props = [
                p for p in all_properties
                if all(_matches_filter(p, f) for f in active_filters)
            ]
        else:
            filtered_props = all_properties

        # Step 3: aggregate into filter groups
        filters = PropertyService._aggregate_filters(filtered_props)
        total_count = len(filtered_props)
        layouts = [
            {"id": p["id"], "geometry": p["geometry"]}
            for p in filtered_props
        ]

        return {
            "filters": filters,
            "totalCount": total_count,
            "layouts": layouts,
        }

    # -------------------------------------------------------------------------
    # _aggregate_filters — single-pass aggregation of property rows
    # -------------------------------------------------------------------------

    @staticmethod
    def _aggregate_filters(
        properties: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build filter groups from a list of property attribute rows."""
        # Accumulators
        range_stats: dict[str, dict[str, float]] = {
            rc["key"]: {"min": math.inf, "max": -math.inf} for rc in RANGE_COLUMNS
        }
        bool_stats: dict[str, int] = {
            bc["key"]: 0
            for bc in (*OVERTURE_BOOLEAN_COLUMNS, *OSM_BOOLEAN_COLUMNS)
        }
        enum_stats: dict[str, dict[str, int]] = {
            sc["key"]: {} for sc in UNIFIED_SCHEMA
        }

        # Single pass over all properties
        for prop in properties:
            # Ranges
            for rc in RANGE_COLUMNS:
                val = prop.get(rc["key"])
                if val is not None:
                    s = range_stats[rc["key"]]
                    if val < s["min"]:
                        s["min"] = val
                    if val > s["max"]:
                        s["max"] = val

            # Booleans
            for key in bool_stats:
                if str(prop.get(key)) == "true":
                    bool_stats[key] += 1

            # Enums
            for sc in UNIFIED_SCHEMA:
                val = prop.get(sc["key"])
                if val is not None and str(val).strip() != "":
                    str_val = str(val)
                    counts = enum_stats[sc["key"]]
                    counts[str_val] = counts.get(str_val, 0) + 1

        result: list[dict[str, Any]] = []

        # --- Build range groups ---
        for rc in RANGE_COLUMNS:
            s = range_stats[rc["key"]]
            if s["min"] != math.inf and s["max"] != -math.inf and s["min"] != s["max"]:
                result.append(
                    {
                        "key": rc["key"],
                        "label": rc.get("label"),
                        "type": "range",
                        "values": [
                            {"value": "min", "label": None, "count": math.floor(s["min"])},
                            {"value": "max", "label": None, "count": math.ceil(s["max"])},
                        ],
                    }
                )

        # --- Build boolean groups (Overture first, then OSM) ---
        for bc in (*OVERTURE_BOOLEAN_COLUMNS, *OSM_BOOLEAN_COLUMNS):
            count = bool_stats[bc["key"]]
            if count > 0:
                result.append(
                    {
                        "key": bc["key"],
                        "label": bc.get("label"),
                        "type": "boolean",
                        "values": [{"value": "true", "label": None, "count": count}],
                    }
                )

        # --- Build enum groups (sorted highest-count first, stable UI order) ---
        for sc in UNIFIED_SCHEMA:
            counts = enum_stats[sc["key"]]
            if not counts:
                continue

            sorted_values = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
            values = [
                {
                    "value": val,
                    "label": to_label(sc["key"], val),
                    "count": count,
                }
                for val, count in sorted_values
            ]
            result.append(
                {
                    "key": sc["key"],
                    "label": sc.get("label"),
                    "type": "enum",
                    "values": values,
                }
            )

        return result

    # -------------------------------------------------------------------------
    # getPropertyFeatures — detailed attributes for a single building
    # -------------------------------------------------------------------------

    @staticmethod
    async def get_property_features(property_id: str) -> dict[str, Any] | None:
        cache_key = f"insight-{property_id}"
        cached = await CacheService.get(cache_key)
        if cached:
            return cached

        # Lazy import: keeps the BigQuery client out of the import graph for
        # tests / environments that don't need it.
        from google.cloud import bigquery

        from app.core.bigquery_client import get_bigquery_client

        query, params = get_property_features_query(property_id)
        bq = get_bigquery_client()

        def _run() -> list[dict[str, Any]]:
            job = bq.query(
                query,
                job_config=bigquery.QueryJobConfig(query_parameters=params),
                location="US",
            )
            return [dict(r) for r in job.result()]

        rows_result = await asyncio.to_thread(_run)
        if not rows_result:
            return None

        row = rows_result[0]

        # Dynamically collect every UNIFIED_SCHEMA field so nothing is silently dropped
        schema_fields = {f["key"]: row.get(f["key"]) for f in UNIFIED_SCHEMA}

        # OSM boolean flags (lit, covered, wheelchair …)
        boolean_fields = {
            b["key"]: str(row.get(b["key"])) == "true"
            for b in OSM_BOOLEAN_COLUMNS
        }

        # Build a compact address object — only include keys that have a value
        address_parts = {
            "housenumber": row.get("addr_housenumber"),
            "street": row.get("addr_street"),
            "city": row.get("addr_city"),
            "postcode": row.get("addr_postcode"),
            "country": row.get("addr_country"),
        }
        address: dict[str, Any] | None = (
            address_parts
            if any(v is not None for v in address_parts.values())
            else None
        )

        result: dict[str, Any] = {
            # Core dimensions (Overture direct columns)
            "height": row.get("height"),
            "numFloors": row.get("num_floors"),
            "roofHeight": row.get("roof_height"),
            "roofArea": row.get("roof_area"),
            "isUnderground": bool(row.get("isUnderground")),
            # All UNIFIED_SCHEMA enum fields
            **schema_fields,
            # OSM boolean flags
            **boolean_fields,
            # Address & ownership sourced from OSM all_tags
            "address": address,
            "name": row.get("name"),
            "operator": row.get("operator"),
            "owner": row.get("owner"),
            # Raw OSM tags for the inspector panel
            "osmAttributes": row.get("osmAttributes") or [],
        }

        await CacheService.set(cache_key, result)
        return result
