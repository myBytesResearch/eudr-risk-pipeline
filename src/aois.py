"""Cocoa AOI registry — Côte d'Ivoire and Ghana production zones.

The AOIs in this registry are the same units used in the upstream myBytes
research pipeline .
They are bounding-box approximations of administrative sub-regions, sized
to the dominant cocoa production zones per country.

This is the *public-data* re-issue. The geography is public, the area
estimates come from USDA FAS PSD 2023 and ICCO Annual Report 2023, and
the bounding boxes are the same ones we run the pipeline against
internally.

For supplier-polygon-level work, replace these bounding boxes with the
actual GeoJSON polygons your operator provides under VO (EU) 2023/1115
Art. 9. The mask and operation code in ``src/masks/`` and
``src/operations/`` is geometry-agnostic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class AOI:
    """Area of Interest definition.

    Attributes:
        aoi_id: Unique slug, snake_case.
        country: ISO-3 country code (CIV, GHA).
        region: Free-text region name.
        level: 0 = country bounding box, 1 = sub-region.
        bbox: ``(west, south, east, north)`` in EPSG:4326.
        expected_area_ha: Rough cocoa-area estimate (USDA / ICCO).
        notes: Phenology / CSSVD status / methodology notes.
    """

    aoi_id: str
    country: str
    region: str
    level: int
    bbox: tuple[float, float, float, float]
    expected_area_ha: int | None
    notes: str

    @property
    def centroid(self) -> tuple[float, float]:
        w, s, e, n = self.bbox
        return ((w + e) / 2, (s + n) / 2)


# ─── Côte d'Ivoire (~2.2 Mt/year, ~38 % of world cocoa production) ─────────
# ─── Ghana (~700 kt/year, ~14 % of world cocoa production) ─────────────────
# Source: USDA FAS PSD 2023, ICCO Annual Report 2023, plus internal myBytes
# methodology notes from the upstream internal myBytes research project.
_AOIS: tuple[AOI, ...] = (
    AOI("cocoa_civ", "CIV", "Côte d'Ivoire (entire country)", 0,
        (-7.5, 4.5, -3.5, 7.0), 4_000_000,
        "Country bounding box; matches the GEE NDVI loader."),
    AOI("cocoa_civ_sw", "CIV", "Sud-Ouest (Soubré, San Pedro, Sassandra)", 1,
        (-7.4, 4.6, -5.6, 6.3), 1_600_000,
        "Largest cocoa zone worldwide. Expansion since the 1990s. ENSO-sensitive."),
    AOI("cocoa_civ_cw", "CIV", "Centre-Ouest (Daloa, Bouaflé, Issia)", 1,
        (-7.0, 6.2, -5.5, 7.3), 900_000,
        "Historic cocoa belt centre. Older plantings → CSSVD-prone."),
    AOI("cocoa_civ_east", "CIV", "Est (Abengourou, Aboisso)", 1,
        (-4.5, 5.2, -3.0, 7.0), 600_000,
        "Oldest plantations. High documented CSSVD incidence."),
    AOI("cocoa_civ_west", "CIV", "Ouest (Man, Touba)", 1,
        (-8.3, 6.5, -7.0, 8.5), 350_000,
        "Newer expansion frontier — often on cleared forest → EUDR risk."),
    AOI("cocoa_gha", "GHA", "Ghana (entire country)", 0,
        (-3.0, 5.0, -0.5, 7.5), 1_700_000,
        "Country bounding box; matches the GEE NDVI loader."),
    AOI("cocoa_gha_west", "GHA", "Western Region (Sefwi-Wiawso, Bibiani, Juabeso)", 1,
        (-3.0, 5.5, -2.0, 7.0), 750_000,
        "Largest Ghanaian producer. Borders CIV-East. Commercial large blocks."),
    AOI("cocoa_gha_ashanti", "GHA", "Ashanti (Konongo, Obuasi)", 1,
        (-2.2, 6.0, -0.8, 7.2), 380_000,
        "Historic cocoa region, mixed with gold mining."),
    AOI("cocoa_gha_centraleast", "GHA", "Central + Eastern (Kade, Suhum)", 1,
        (-1.5, 5.5, -0.3, 6.7), 270_000,
        "Oldest Ghanaian plantations. CSSVD epicentre since 1936."),
    AOI("cocoa_gha_brong", "GHA", "Brong-Ahafo (Goaso, Sunyani)", 1,
        (-2.8, 6.8, -1.0, 8.2), 220_000,
        "Northern frontier, newer expansion."),
    # ─── 33 × 33 km town-centred AOIs used in the companion articles ──────
    # Geometry: bounding box of half-side 16.5 km converted to degrees at
    # the local latitude. Used in `data/runs/2026-06-08/area_summary.csv`
    # and reproduced in `notebooks/00_reproduce_article_numbers.ipynb`.
    AOI("civ_soubre_33km", "CIV", "Soubré town centre, 33 × 33 km", 2,
        (-6.7522, 5.6347, -6.4544, 5.9320), None,
        "Article AOI. Centre lon -6.6033, lat 5.7833. Smallholder mosaic."),
    AOI("gha_sefwi_wiawso_33km", "GHA", "Sefwi-Wiawso town centre, 33 × 33 km", 2,
        (-2.6493, 6.0514, -2.3507, 6.3486), None,
        "Article AOI. Centre lon -2.5000, lat 6.2000. Commercial large blocks."),
)

AOIS: dict[str, AOI] = {a.aoi_id: a for a in _AOIS}


def get_aoi(aoi_id: str) -> AOI:
    if aoi_id not in AOIS:
        raise KeyError(f"Unknown AOI {aoi_id!r}. Known: {list(AOIS)}")
    return AOIS[aoi_id]


def list_aois(country: str | None = None, level: int | None = None) -> list[AOI]:
    out: Iterable[AOI] = AOIS.values()
    if country is not None:
        out = (a for a in out if a.country == country)
    if level is not None:
        out = (a for a in out if a.level == level)
    return list(out)


def ee_geometry(aoi_id: str):
    """Earth Engine ``ee.Geometry.Rectangle`` for an AOI. Lazy-imports ``ee``."""
    import ee  # type: ignore[import-untyped]

    a = get_aoi(aoi_id)
    return ee.Geometry.Rectangle(list(a.bbox))


def aoi_table() -> pd.DataFrame:
    """Tabular overview for EDA notebooks."""
    rows = []
    for a in AOIS.values():
        d = asdict(a)
        d["centroid_lon"], d["centroid_lat"] = a.centroid
        d["bbox_w"], d["bbox_s"], d["bbox_e"], d["bbox_n"] = a.bbox
        d["bbox_area_deg2"] = (a.bbox[2] - a.bbox[0]) * (a.bbox[3] - a.bbox[1])
        rows.append(d)
    return pd.DataFrame(rows).set_index("aoi_id")
