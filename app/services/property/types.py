"""Strawberry GraphQL types for the property feature.
"""
from __future__ import annotations

from typing import Optional

import strawberry


# ─── Inputs ──────────────────────────────────────────────────────────────────


@strawberry.input(name="BoundingBoxInput")
class BoundingBoxInput:
    sw_lng: float
    sw_lat: float
    ne_lng: float
    ne_lat: float


@strawberry.input(name="ActiveFilterInput")
class ActiveFilterInput:
    key: str
    values: list[str]


# ─── Filter result types ─────────────────────────────────────────────────────


@strawberry.type(name="FilterValue")
class FilterValue:
    value: str
    count: int
    label: Optional[str] = None  # null means use raw value


@strawberry.type(name="FilterGroup")
class FilterGroup:
    key: str
    type: str  # "enum" | "boolean" | "range"
    values: list[FilterValue]
    label: Optional[str] = None


@strawberry.type(name="PropertyLayout")
class PropertyLayout:
    id: str
    geometry: str  # GeoJSON geometry string


@strawberry.type(name="AvailableFiltersResult")
class AvailableFiltersResult:
    filters: list[FilterGroup]
    total_count: int
    layouts: list[PropertyLayout]


# ─── Per-building detail ─────────────────────────────────────────────────────


@strawberry.type(name="KeyValue")
class KeyValue:
    key: str
    value: str


@strawberry.type(name="PropertyFeatures")
class PropertyFeatures:
    osm_attributes: list[KeyValue]
    subtype: Optional[str] = None
    # `class` is a Python keyword — use the name= override to expose it as
    # `class` in the GraphQL schema while keeping a valid Python attribute.
    class_: Optional[str] = strawberry.field(name="class", default=None)
    height: Optional[float] = None
    num_floors: Optional[int] = None
    roof_material: Optional[str] = None
    roof_shape: Optional[str] = None
    roof_height: Optional[float] = None
    roof_area: Optional[float] = None
    facade_material: Optional[str] = None
    facade_color: Optional[str] = None
    is_underground: Optional[bool] = None
