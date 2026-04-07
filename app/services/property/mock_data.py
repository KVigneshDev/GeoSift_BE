"""Property mock data — STUB.

You said you'll port `services/property/mockData.js` to Python yourself.
This file exists only so the rest of the property service can import `rows`
and the application boots cleanly.

Expected shape: a list of dicts where each dict represents one building
row with the same keys as the BigQuery query output (`id`, `geometry`,
`height`, `num_floors`, plus every field defined in UNIFIED_SCHEMA, plus
every boolean column).
"""
from __future__ import annotations

from typing import Any

rows: list[dict[str, Any]] = []
