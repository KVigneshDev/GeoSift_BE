"""Property feature constants.
 `HEX_TO_COLORS` is mutable — `to_label()` writes new entries into it as
  it discovers them at runtime.
"""
from __future__ import annotations

from typing import Any

# ============================================================================
# Keys where "yes" / "no" are meaningful enum values
# (not to be filtered out as generic)
# ============================================================================

PRESERVE_GENERIC_VALUES: set[str] = {
    "wheelchair",
    "lit",
    "covered",
    "lighting",
    "surveillance",
    "is_underground",
    "access",
}

# ============================================================================
# UNIFIED FILTER SCHEMA
# ============================================================================

UNIFIED_SCHEMA: list[dict[str, Any]] = [
    # ─── STRUCTURE / GEOMETRY ─────────────────────────────────────────────
    {"key": "roof_material",   "label": "Roof Material",    "overture": "roof_material",   "osm": ["roof:material"]},
    {"key": "roof_shape",      "label": "Roof Shape",       "overture": "roof_shape",      "osm": ["roof:shape"]},
    {"key": "roof_color",      "label": "Roof Color",       "overture": None,              "osm": ["roof:colour"]},

    {"key": "facade_material", "label": "Facade Material",  "overture": "facade_material", "osm": ["building:material", "facade:material"]},
    {"key": "facade_color",    "label": "Facade Color",     "overture": "facade_color",    "osm": ["building:colour"]},

    {"key": "subtype",         "label": "Subtype",          "overture": "subtype",         "osm": ["building:part", "building:use"]},
    {"key": "class",           "label": "Class",            "overture": "class",           "osm": ["building"]},

    # ─── AMENITIES ────────────────────────────────────────────────────────
    {"key": "amenity",         "label": "Amenities",          "overture": None, "osm": ["amenity"]},
    {"key": "leisure",         "label": "Leisure Facilities", "overture": None, "osm": ["leisure", "sport"]},
    {"key": "shop",            "label": "Retail",             "overture": None, "osm": ["shop"]},

    # ─── LANDSCAPING / UTILITIES ──────────────────────────────────────────
    {"key": "landscaping",     "label": "Landscaping", "overture": None, "osm": ["natural", "garden:type", "surface", "water"]},
    {"key": "utilities",       "label": "Utilities",   "overture": None, "osm": ["man_made", "power"]},
    {"key": "commercial",      "label": "Commercial",  "overture": None, "osm": ["camera:type", "surveillance", "advertising", "information"]},

    # ─── ACCESSIBILITY ─────────────────────────────────────────────────────
    {"key": "access",          "label": "Access", "overture": None, "osm": ["access", "wheelchair", "parking", "entrance", "door", "barrier"]},
]

# ============================================================================
# RANGE FILTERS
# ============================================================================

RANGE_COLUMNS: list[dict[str, Any]] = [
    {"key": "height",      "label": "Building Height",  "computed": False, "expr": "ob.height",            "rawExpr": "height"},
    {"key": "num_floors",  "label": "Number of Floors", "computed": False, "expr": "ob.num_floors",        "rawExpr": "num_floors"},
    {"key": "roof_height", "label": "Roof Height",      "computed": False, "expr": "ob.roof_height",       "rawExpr": "roof_height"},
    {"key": "roof_area",   "label": "Roof Area",        "computed": True,  "expr": "ST_AREA(ob.geometry)", "rawExpr": "ST_AREA(geometry)"},
]

# ============================================================================
# BOOLEAN FILTERS
# ============================================================================

OVERTURE_BOOLEAN_COLUMNS: list[dict[str, Any]] = [
    {"key": "is_underground", "label": "Is Underground"},
]

OSM_BOOLEAN_COLUMNS: list[dict[str, Any]] = [
    {"key": "lit",        "label": "Street Lighting",       "osmValue": "yes"},
    {"key": "covered",    "label": "Covered Area",          "osmValue": "yes"},
    {"key": "wheelchair", "label": "Wheelchair Accessible", "osmValue": "yes"},
]

# ============================================================================
# LABEL OVERRIDES
# ============================================================================

LABEL_OVERRIDES: dict[str, dict[str, str]] = {
    # ─── STRUCTURE / GEOMETRY ─────────────────────────────────────────────
    "roof_material": {
        "metal":      "Metal Roof",
        "slate":      "Slate Roof",
        "tile":       "Tile Roof",
        "roof_tiles": "Roof Tiles",
        "concrete":   "Concrete",
        "glass":      "Glass",
        "zinc":       "Zinc",
        "copper":     "Copper",
        "gravel":     "Gravel",
        "grass":      "Green/Grass Roof",
    },
    "roof_shape": {
        "flat":              "Flat Roof",
        "gabled":            "Gabled Roof",
        "hipped":            "Hipped Roof",
        "half-hipped":       "Half-Hipped Roof",
        "gambrel":           "Gambrel (Barn Style)",
        "mansard":           "Mansard Roof",
        "saltbox":           "Saltbox Roof",
        "double_saltbox":    "Double Saltbox",
        "quadruple_saltbox": "Quadruple Saltbox",
        "skillion":          "Skillion/Shed Roof",
        "pyramidal":         "Pyramidal Roof",
        "dome":              "Dome",
        "round":             "Round Roof",
        "round_gabled":      "Round Gabled",
    },
    "facade_material": {
        "concrete": "Concrete",
        "glass":    "Glass",
        "metal":    "Metal",
        "wood":     "Wood",
        "brick":    "Brick",
    },

    # ─── BUILDING CLASSIFICATION ──────────────────────────────────────────
    "class": {
        "yes":         "Generic Building",
        "apartments":  "Apartment Building",
        "house":       "House",
        "residential": "Residential",
        "retail":      "Retail/Shop",
        "commercial":  "Commercial",
        "office":      "Office Building",
        "industrial":  "Industrial",
        "warehouse":   "Warehouse",
        "hotel":       "Hotel",
        "school":      "School",
        "university":  "University",
        "hospital":    "Hospital",
        "church":      "Church",
        "cathedral":   "Cathedral",
        "chapel":      "Chapel",
        "temple":      "Temple",
        "synagogue":   "Synagogue",
        "mosque":      "Mosque",
        "shed":        "Shed",
        "garage":      "Garage",
        "garages":     "Garages",
        "greenhouse":  "Greenhouse",
        "hut":         "Hut",
        "cabin":       "Cabin",
    },
    "subtype": {
        "yes": "Generic Subtype",
    },

    # ─── AMENITIES ────────────────────────────────────────────────────────
    "amenity": {
        "restaurant":       "Restaurant",
        "cafe":             "Café",
        "fast_food":        "Fast Food",
        "bar":              "Bar",
        "pub":              "Pub",
        "bank":             "Bank",
        "atm":              "ATM",
        "pharmacy":         "Pharmacy",
        "hospital":         "Hospital",
        "clinic":           "Clinic",
        "doctors":          "Doctor's Office",
        "dentist":          "Dentist",
        "school":           "School",
        "kindergarten":     "Kindergarten",
        "college":          "College",
        "university":       "University",
        "library":          "Library",
        "theatre":          "Theatre",
        "cinema":           "Cinema",
        "arts_centre":      "Arts Centre",
        "community_centre": "Community Centre",
        "social_facility":  "Social Facility",
        "place_of_worship": "Place of Worship",
        "parking":          "Parking",
        "bicycle_parking":  "Bicycle Parking",
        "charging_station": "EV Charging Station",
        "fuel":             "Gas Station",
        "post_office":      "Post Office",
        "police":           "Police Station",
        "fire_station":     "Fire Station",
        "townhall":         "Town Hall",
    },
    "leisure": {
        "park":           "Park",
        "garden":         "Garden",
        "playground":     "Playground",
        "sports_centre":  "Sports Centre",
        "fitness_centre": "Fitness Centre",
        "swimming_pool":  "Swimming Pool",
        "pitch":          "Sports Pitch",
        "marina":         "Marina",
        "escape_game":    "Escape Room",
    },

    # ─── LANDSCAPING / UTILITIES ──────────────────────────────────────────
    "landscaping": {
        # Surfaces
        "asphalt":         "Asphalt",
        "paved":           "Paved",
        "paving_stones":   "Paving Stones/Pavers",
        "sett":            "Cobblestone/Sett",
        "concrete":        "Concrete",
        "concrete:plates": "Concrete Plates",
        "gravel":          "Gravel",
        "fine_gravel":     "Fine Gravel",
        "compacted":       "Compacted",
        "tartan":          "Tartan (Synthetic)",
        "ground":          "Ground/Dirt",
        # Landuse / Vegetation
        "grass":           "Grass/Lawn",
        "forest":          "Forest",
        "allotments":      "Allotments/Community Gardens",
        "residential":     "Residential Area",
        "commercial":      "Commercial Area",
        "industrial":      "Industrial Area",
        "retail":          "Retail Area",
        "military":        "Military",
        "education":       "Educational",
        "construction":    "Under Construction",
    },

    # ─── COMMERCIAL / UTILITIES ───────────────────────────────────────────
    "commercial": {
        "outdoor":     "Outdoor Surveillance",
        "indoor":      "Indoor Surveillance",
        "public":      "Public Surveillance",
        "advertising": "Advertising",
        "information": "Information",
    },

    # ─── ACCESSIBILITY ────────────────────────────────────────────────────
    "access": {
        "yes":          "Wheelchair Accessible",
        "no":           "Not Wheelchair Accessible",
        "limited":      "Limited Accessibility",
        "designated":   "Designated Accessible",
        "surface":      "Surface Parking",
        "underground":  "Underground Parking",
        "multi-storey": "Multi-Story Parking",
        "street_side":  "Street-Side Parking",
    },
}

# ============================================================================
# HEX → COLOR NAME CACHE
# ============================================================================
# Seeded with the standard CSS named colors. `to_label()` writes new entries
# into this dict at runtime as it discovers unknown hex codes — keep it
# mutable, do not freeze.

HEX_TO_COLORS: dict[str, str] = {
    "#f0f8ff": "aliceblue",
    "#faebd7": "antiquewhite",
    "#00ffff": "cyan",
    "#7fffd4": "aquamarine",
    "#f0ffff": "azure",
    "#f5f5dc": "beige",
    "#ffe4c4": "bisque",
    "#000000": "black",
    "#ffebcd": "blanchedalmond",
    "#0000ff": "blue",
    "#8a2be2": "blueviolet",
    "#a52a2a": "brown",
    "#deb887": "burlywood",
    "#5f9ea0": "cadetblue",
    "#7fff00": "chartreuse",
    "#d2691e": "chocolate",
    "#ff7f50": "coral",
    "#6495ed": "cornflowerblue",
    "#fff8dc": "cornsilk",
    "#dc143c": "crimson",
    "#00008b": "darkblue",
    "#008b8b": "darkcyan",
    "#b8860b": "darkgoldenrod",
    "#a9a9a9": "darkgray",
    "#006400": "darkgreen",
    "#bdb76b": "darkkhaki",
    "#8b008b": "darkmagenta",
    "#556b2f": "darkolivegreen",
    "#ff8c00": "darkorange",
    "#9932cc": "darkorchid",
    "#8b0000": "darkred",
    "#e9967a": "darksalmon",
    "#8fbc8f": "darkseagreen",
    "#483d8b": "darkslateblue",
    "#2f4f4f": "darkslategray",
    "#00ced1": "darkturquoise",
    "#9400d3": "darkviolet",
    "#ff1493": "deeppink",
    "#00bfff": "deepskyblue",
    "#696969": "dimgray",
    "#1e90ff": "dodgerblue",
    "#b22222": "firebrick",
    "#fffaf0": "floralwhite",
    "#228b22": "forestgreen",
    "#ff00ff": "magenta",
    "#dcdcdc": "gainsboro",
    "#f8f8ff": "ghostwhite",
    "#ffd700": "gold",
    "#daa520": "goldenrod",
    "#808080": "gray",
    "#008000": "green",
    "#adff2f": "greenyellow",
    "#f0fff0": "honeydew",
    "#ff69b4": "hotpink",
    "#cd5c5c": "indianred",
    "#4b0082": "indigo",
    "#fffff0": "ivory",
    "#f0e68c": "khaki",
    "#e6e6fa": "lavender",
    "#fff0f5": "lavenderblush",
    "#7cfc00": "lawngreen",
    "#fffacd": "lemonchiffon",
    "#add8e6": "lightblue",
    "#f08080": "lightcoral",
    "#e0ffff": "lightcyan",
    "#fafad2": "lightgoldenrodyellow",
    "#d3d3d3": "lightgray",
    "#90ee90": "lightgreen",
    "#ffb6c1": "lightpink",
    "#ffa07a": "lightsalmon",
    "#20b2aa": "lightseagreen",
    "#87cefa": "lightskyblue",
    "#778899": "lightslategray",
    "#b0c4de": "lightsteelblue",
    "#ffffe0": "lightyellow",
    "#00ff00": "lime",
    "#32cd32": "limegreen",
    "#faf0e6": "linen",
    "#800000": "maroon",
    "#66cdaa": "mediumaquamarine",
    "#0000cd": "mediumblue",
    "#ba55d3": "mediumorchid",
    "#9370db": "mediumpurple",
    "#3cb371": "mediumseagreen",
    "#7b68ee": "mediumslateblue",
    "#00fa9a": "mediumspringgreen",
    "#48d1cc": "mediumturquoise",
    "#c71585": "mediumvioletred",
    "#191970": "midnightblue",
    "#f5fffa": "mintcream",
    "#ffe4e1": "mistyrose",
    "#ffe4b5": "moccasin",
    "#ffdead": "navajowhite",
    "#000080": "navy",
    "#fdf5e6": "oldlace",
    "#808000": "olive",
    "#6b8e23": "olivedrab",
    "#ffa500": "orange",
    "#ff4500": "orangered",
    "#da70d6": "orchid",
    "#eee8aa": "palegoldenrod",
    "#98fb98": "palegreen",
    "#afeeee": "paleturquoise",
    "#db7093": "palevioletred",
    "#ffefd5": "papayawhip",
    "#ffdab9": "peachpuff",
    "#cd853f": "peru",
    "#ffc0cb": "pink",
    "#dda0dd": "plum",
    "#b0e0e6": "powderblue",
    "#800080": "purple",
    "#663399": "rebeccapurple",
    "#ff0000": "red",
    "#bc8f8f": "rosybrown",
    "#4169e1": "royalblue",
    "#8b4513": "saddlebrown",
    "#fa8072": "salmon",
    "#f4a460": "sandybrown",
    "#2e8b57": "seagreen",
    "#fff5ee": "seashell",
    "#a0522d": "sienna",
    "#c0c0c0": "silver",
    "#87ceeb": "skyblue",
    "#6a5acd": "slateblue",
    "#708090": "slategray",
    "#fffafa": "snow",
    "#00ff7f": "springgreen",
    "#4682b4": "steelblue",
    "#d2b48c": "tan",
    "#008080": "teal",
    "#d8bfd8": "thistle",
    "#ff6347": "tomato",
    "#40e0d0": "turquoise",
    "#ee82ee": "violet",
    "#f5deb3": "wheat",
    "#ffffff": "white",
    "#f5f5f5": "whitesmoke",
    "#ffff00": "yellow",
    "#9acd32": "yellowgreen",
}
