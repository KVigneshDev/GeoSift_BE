"""Property feature utility functions.

- `validate_bbox` — input validation
- `to_label` — pretty-print enum values

"""
from __future__ import annotations

from app.core.errors import ValidationError
from app.services.property.constants import HEX_TO_COLORS, LABEL_OVERRIDES


def to_label(filter_key: str, value: str | None) -> str | None:
    """Generate a human-friendly label for an enum filter value."""
    if not value:
        return None

    # 1. Context-aware override (e.g. "yes" → "Wheelchair Accessible")
    overrides = LABEL_OVERRIDES.get(filter_key)
    if overrides and value in overrides:
        return overrides[value]

    # 2. Hex color → cached human name (best-effort)
    if value.startswith("#"):
        lower = value.lower()
        if lower in HEX_TO_COLORS:
            return HEX_TO_COLORS[lower]
        name = f"Color {lower}"
        HEX_TO_COLORS[lower] = name  # cache for this session
        return name

    # 3. Default: snake_case → Title Case
    return value.replace("_", " ").title()


def validate_bbox(bbox: dict[str, float]) -> None:
    """Validate a bounding box; raises `ValidationError` on bad input."""
    sw_lng = bbox["sw_lng"]
    sw_lat = bbox["sw_lat"]
    ne_lng = bbox["ne_lng"]
    ne_lat = bbox["ne_lat"]

    if sw_lng >= ne_lng or sw_lat >= ne_lat:
        raise ValidationError(
            "Invalid bounding box: SW corner must be less than NE corner."
        )
    if sw_lng < -180 or ne_lng > 180 or sw_lat < -90 or ne_lat > 90:
        raise ValidationError(
            "Bounding box coordinates are out of valid geographic range."
        )
    if (ne_lng - sw_lng) > 5 or (ne_lat - sw_lat) > 5:
        raise ValidationError(
            "Bounding box is too large. Please zoom in further."
        )
