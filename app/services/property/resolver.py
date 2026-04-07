"""Property feature resolvers.
"""
from __future__ import annotations

from typing import Optional

import strawberry
from strawberry.types import Info

from app.context.auth import GraphQLContext
from app.core.errors import AuthError
from app.services.property.service import PropertyService
from app.services.property.types import (
    ActiveFilterInput,
    AvailableFiltersResult,
    BoundingBoxInput,
    FilterGroup,
    FilterValue,
    KeyValue,
    PropertyFeatures,
    PropertyLayout,
)


def _require_user(info: Info[GraphQLContext, None]) -> None:
    if info.context.user is None:
        raise AuthError("Not authenticated")


def _to_filter_group(raw: dict) -> FilterGroup:
    return FilterGroup(
        key=raw["key"],
        type=raw["type"],
        label=raw.get("label"),
        values=[
            FilterValue(
                value=v["value"],
                label=v.get("label"),
                count=v["count"],
            )
            for v in raw["values"]
        ],
    )


def _to_property_features(raw: dict) -> PropertyFeatures:
    return PropertyFeatures(
        subtype=raw.get("subtype"),
        class_=raw.get("class"),
        height=raw.get("height"),
        num_floors=raw.get("numFloors"),
        roof_material=raw.get("roof_material"),
        roof_shape=raw.get("roof_shape"),
        roof_height=raw.get("roofHeight"),
        roof_area=raw.get("roofArea"),
        facade_material=raw.get("facade_material"),
        facade_color=raw.get("facade_color"),
        is_underground=raw.get("isUnderground"),
        osm_attributes=[
            KeyValue(key=kv["key"], value=kv["value"])
            for kv in (raw.get("osmAttributes") or [])
        ],
    )


@strawberry.type
class PropertyQuery:
    @strawberry.field
    async def available_filters(
        self,
        info: Info[GraphQLContext, None],
        bbox: BoundingBoxInput,
        filters: Optional[list[ActiveFilterInput]] = None,
    ) -> AvailableFiltersResult:
        _require_user(info)

        bbox_dict = {
            "sw_lng": bbox.sw_lng,
            "sw_lat": bbox.sw_lat,
            "ne_lng": bbox.ne_lng,
            "ne_lat": bbox.ne_lat,
        }
        active = [{"key": f.key, "values": f.values} for f in (filters or [])]

        result = await PropertyService.get_available_filters(bbox_dict, active)

        return AvailableFiltersResult(
            filters=[_to_filter_group(g) for g in result["filters"]],
            total_count=result["totalCount"],
            layouts=[
                PropertyLayout(id=l["id"], geometry=l["geometry"])
                for l in result["layouts"]
            ],
        )

    @strawberry.field
    async def property_features(
        self,
        info: Info[GraphQLContext, None],
        property_id: str,
    ) -> Optional[PropertyFeatures]:
        _require_user(info)

        raw = await PropertyService.get_property_features(property_id)
        if raw is None:
            return None
        return _to_property_features(raw)
