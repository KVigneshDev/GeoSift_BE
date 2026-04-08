"""BigQuery SQL builders for the property feature..
"""
from __future__ import annotations

# from typing import Any

from google.cloud import bigquery

from app.services.property.constants import (
    OSM_BOOLEAN_COLUMNS,
    UNIFIED_SCHEMA,
)


def _bbox_params(bbox: dict[str, float]) -> list[bigquery.ScalarQueryParameter]:
    """Build BQ named parameters from a bbox dict.

    BigQuery's Python client requires `ScalarQueryParameter` objects rather
    than a plain dict; the SQL still references them as `@swLng` etc.
    """
    return [
        bigquery.ScalarQueryParameter("swLng", "FLOAT64", bbox["sw_lng"]),
        bigquery.ScalarQueryParameter("swLat", "FLOAT64", bbox["sw_lat"]),
        bigquery.ScalarQueryParameter("neLng", "FLOAT64", bbox["ne_lng"]),
        bigquery.ScalarQueryParameter("neLat", "FLOAT64", bbox["ne_lat"]),
    ]


# ---------------------------------------------------------------------------
# Pre-computed SQL fragments — built once at import time, identical to JS.
# ---------------------------------------------------------------------------

_OSM_SCHEMA_FIELDS = [f for f in UNIFIED_SCHEMA if f.get("osm")]


def _build_osm_raw_extractions() -> str:
    parts: list[str] = []
    for f in _OSM_SCHEMA_FIELDS:
        keys = ", ".join(f"'{k}'" for k in f["osm"])
        parts.append(
            f"(SELECT ANY_VALUE(t.value) FROM UNNEST(all_tags) t "
            f"WHERE t.key IN ({keys})) AS {f['key']}"
        )
    for b in OSM_BOOLEAN_COLUMNS:
        parts.append(
            f"(SELECT 'true' FROM UNNEST(all_tags) t "
            f"WHERE t.key = '{b['key']}' AND t.value = '{b['osmValue']}' "
            f"LIMIT 1) AS {b['key']}"
        )
    return ",\n             ".join(parts)


def _build_osm_aggregates() -> str:
    parts: list[str] = []
    for f in _OSM_SCHEMA_FIELDS:
        parts.append(f"MAX(osm.{f['key']}) AS {f['key']}")
    for b in OSM_BOOLEAN_COLUMNS:
        parts.append(f"MAX(osm.{b['key']}) AS {b['key']}")
    return ",\n         ".join(parts)


def _build_coalesced_selects() -> str:
    parts: list[str] = []
    for f in UNIFIED_SCHEMA:
        if f.get("overture") and f.get("osm"):
            parts.append(
                f"COALESCE(NULLIF(TRIM(CAST(ob.{f['overture']} AS STRING)), ''), "
                f"osm.{f['key']}) AS {f['key']}"
            )
        elif f.get("overture"):
            parts.append(f"CAST(ob.{f['overture']} AS STRING) AS {f['key']}")
        else:
            parts.append(f"osm.{f['key']} AS {f['key']}")
    return ",\n        ".join(parts)


def _build_osm_bool_selects() -> str:
    return ",\n        ".join(
        f"osm.{b['key']} AS {b['key']}" for b in OSM_BOOLEAN_COLUMNS
    )


_OSM_RAW_EXTRACTIONS = _build_osm_raw_extractions()
_OSM_AGGREGATES = _build_osm_aggregates()
_COALESCED_SELECTS = _build_coalesced_selects()
_OSM_BOOL_SELECTS = _build_osm_bool_selects()


# ---------------------------------------------------------------------------
# Public query builders
# ---------------------------------------------------------------------------


def get_properties_for_filtering_query(
    bbox: dict[str, float],
) -> tuple[str, list[bigquery.ScalarQueryParameter]]:
    """Build the bbox-filtered building extraction query."""
    params = _bbox_params(bbox)

    query = f"""
    WITH overture_subset AS (
        SELECT
            id,
            geometry,
            height,
            num_floors,
            roof_height,
            ST_AREA(geometry) AS roof_area,
            is_underground,
            roof_material,
            roof_shape,
            facade_material,
            facade_color,
            subtype,
            class
        FROM `bigquery-public-data.overture_maps.building`
        -- bbox column pre-filter: leverages BQ clustering to prune partitions cheaply
        WHERE bbox.xmin >= @swLng AND bbox.xmax <= @neLng
            AND bbox.ymin >= @swLat AND bbox.ymax <= @neLat
            -- exact geometry check after the fast pre-filter
            AND ST_INTERSECTS(geometry, ST_GEOGFROMTEXT(CONCAT(
                'POLYGON((',
                CAST(@swLng AS STRING), ' ', CAST(@swLat AS STRING), ', ',
                CAST(@neLng AS STRING), ' ', CAST(@swLat AS STRING), ', ',
                CAST(@neLng AS STRING), ' ', CAST(@neLat AS STRING), ', ',
                CAST(@swLng AS STRING), ' ', CAST(@neLat AS STRING), ', ',
                CAST(@swLng AS STRING), ' ', CAST(@swLat AS STRING),
                '))')
            ))
        LIMIT 10000
    ),

    osm_raw AS (
        -- Extract each OSM schema field as a flat column; geometry kept for spatial join
        SELECT
            geometry,
            {_OSM_RAW_EXTRACTIONS}
        FROM `bigquery-public-data.geo_openstreetmap.planet_features`
        WHERE feature_type IN ('polygons', 'multipolygons')
            AND ST_INTERSECTS(geometry, ST_GEOGFROMTEXT(CONCAT(
                'POLYGON((',
                CAST(@swLng AS STRING), ' ', CAST(@swLat AS STRING), ', ',
                CAST(@neLng AS STRING), ' ', CAST(@swLat AS STRING), ', ',
                CAST(@neLng AS STRING), ' ', CAST(@neLat AS STRING), ', ',
                CAST(@swLng AS STRING), ' ', CAST(@neLat AS STRING), ', ',
                CAST(@swLng AS STRING), ' ', CAST(@swLat AS STRING),
                '))')
            ))
    ),

    osm_per_building AS (
        -- For each building, collapse ALL overlapping OSM polygons into one row.
        -- MAX() ignores NULLs: if any matching polygon has a value for a field,
        -- that value is preserved — even when it comes from a different polygon
        -- than the one that supplies another field. This maximises OSM coverage.
        SELECT
            ob.id,
            {_OSM_AGGREGATES}
        FROM overture_subset ob
        JOIN osm_raw osm ON ST_INTERSECTS(ob.geometry, osm.geometry)
        GROUP BY ob.id
    )

    SELECT
        ob.id,
        ST_ASGEOJSON(geometry) AS geometry,
        ob.height,
        ob.num_floors,
        ob.roof_height,
        ob.roof_area,
        CAST(ob.is_underground AS STRING) AS is_underground,
        {_COALESCED_SELECTS},
        {_OSM_BOOL_SELECTS}
    FROM overture_subset ob
    LEFT JOIN osm_per_building osm ON ob.id = osm.id
    """

    return query, params


def get_property_features_query(
    property_id: str,
) -> tuple[str, list[bigquery.ScalarQueryParameter]]:
    """Build the per-building detail query."""
    params = [bigquery.ScalarQueryParameter("id", "STRING", property_id)]

    osm_specific_fields = ",\n          ".join(
        (
            f"(SELECT ANY_VALUE(t.value) FROM UNNEST(all_tags) t "
            f"WHERE t.key IN ({', '.join(repr(k) for k in f['osm'])})) AS {f['key']}"
        )
        for f in UNIFIED_SCHEMA
        if f.get("osm")
    )

    osm_boolean_fields = ",\n          ".join(
        (
            f"(SELECT 'true' FROM UNNEST(all_tags) t "
            f"WHERE t.key = '{b['key']}' AND t.value = '{b['osmValue']}' "
            f"LIMIT 1) AS {b['key']}"
        )
        for b in OSM_BOOLEAN_COLUMNS
    )

    projection_field_parts: list[str] = []
    for f in UNIFIED_SCHEMA:
        overture_col = (
            f"NULLIF(TRIM(CAST(ob.{f['overture']} AS STRING)), '')"
            if f.get("overture")
            else None
        )
        osm_col = f"osm.mapped_data.{f['key']}"
        if overture_col and f.get("osm"):
            projection_field_parts.append(
                f"COALESCE({overture_col}, {osm_col}) AS {f['key']}"
            )
        elif overture_col:
            projection_field_parts.append(f"{overture_col} AS {f['key']}")
        else:
            projection_field_parts.append(f"{osm_col} AS {f['key']}")
    projection_fields = ",\n        ".join(projection_field_parts)

    osm_bool_selects = ",\n        ".join(
        f"osm.bool_data.{b['key']} AS {b['key']}" for b in OSM_BOOLEAN_COLUMNS
    )

    query = f"""
    WITH target_building AS (
        SELECT *
        FROM `bigquery-public-data.overture_maps.building`
        WHERE id = @id
        LIMIT 1
    ),
    target_osm_ranked AS (
        SELECT
            STRUCT({osm_specific_fields}) AS mapped_data,
            STRUCT({osm_boolean_fields}) AS bool_data,
            all_tags,
            (
                SELECT COUNT(1) FROM UNNEST(all_tags) t
                WHERE t.key IN ('building', 'amenity', 'shop', 'leisure',
                                'man_made', 'addr:housenumber', 'addr:street')
            ) AS relevance_score
        FROM `bigquery-public-data.geo_openstreetmap.planet_features` osm, target_building ob
        WHERE osm.feature_type IN ('polygons', 'multipolygons')
          AND ST_INTERSECTS(osm.geometry, ob.geometry)
          AND NOT (
              EXISTS(
                  SELECT 1 FROM UNNEST(all_tags) t
                  WHERE t.key IN ('boundary', 'admin_level')
                     OR (t.key = 'type' AND t.value = 'boundary')
              )
              AND NOT EXISTS(
                  SELECT 1 FROM UNNEST(all_tags) t
                  WHERE t.key IN ('building', 'amenity', 'shop', 'leisure', 'man_made')
              )
          )
        ORDER BY relevance_score DESC
        LIMIT 1
    ),
    target_osm AS (
        SELECT
            mapped_data,
            bool_data,
            all_tags,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'addr:housenumber' LIMIT 1) AS addr_housenumber,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'addr:street'      LIMIT 1) AS addr_street,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'addr:city'        LIMIT 1) AS addr_city,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'addr:postcode'    LIMIT 1) AS addr_postcode,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'addr:country'     LIMIT 1) AS addr_country,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'name'             LIMIT 1) AS name,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'operator'         LIMIT 1) AS operator,
            (SELECT t.value FROM UNNEST(all_tags) t WHERE t.key = 'owner'            LIMIT 1) AS owner
        FROM target_osm_ranked
    )
    SELECT
        ob.height,
        ob.num_floors,
        ob.roof_height,
        CAST(ST_AREA(ob.geometry) AS FLOAT64) AS roof_area,
        ob.is_underground                      AS isUnderground,
        {projection_fields},
        {osm_bool_selects},
        osm.addr_housenumber,
        osm.addr_street,
        osm.addr_city,
        osm.addr_postcode,
        osm.addr_country,
        osm.name,
        osm.operator,
        osm.owner,
        ARRAY(SELECT AS STRUCT key, value FROM UNNEST(osm.all_tags)) AS osmAttributes
    FROM target_building ob
    LEFT JOIN target_osm osm ON TRUE
    """

    return query, params
