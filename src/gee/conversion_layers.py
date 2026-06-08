"""Live Earth Engine constructors for the EUDR two-mask AND operation.

This module is the public-data-only form of the EUDR two-mask AND
operation as developed by myBytes. It exposes the three ``ee.Image`` constructors a
reader needs to recompute Mask A, Mask B and the conversion mask on any
AOI in Google Earth Engine.

Usage::

    import ee
    ee.Initialize(project=os.environ["EE_PROJECT"])
    from src.gee import conversion_mask
    from src.aois import ee_geometry

    geom = ee_geometry("civ_soubre_33km")
    risk_image = conversion_mask(geom)

For the article's reproducibility chain you do not need GEE: the
published snapshot CSVs in ``data/runs/2026-06-08/`` contain the
quantitative results. Use this module only when you want to recompute on
a new AOI or with different thresholds.

LICENCE NOTE
============
The FDP cocoa probability layer is CC-BY-4.0-NC. Commercial use of
derived numbers requires separate licensing from Forest Data Partnership.
"""

from __future__ import annotations

# Hansen GFC vintage default. v2025_v1_13 carries loss data through 2024
# and is the vintage used in the published snapshot 2026-06-08. Pass an
# explicit ``hansen_asset`` to ``recent_loss_mask`` / ``conversion_mask``
# to reproduce an older vintage (e.g. v2024_v1_12 for the drift-study
# "2024 vintage" baseline).
HANSEN_ASSET = "UMD/hansen/global_forest_change_2025_v1_13"
FDP_COCOA_ASSET = "projects/forestdatapartnership/assets/cocoa/model_2025a"
RADD_ASSET = "projects/radar-wur/raddalert/v1"

TREECOVER_THRESHOLD_PCT = 30
EUDR_LOSS_YEAR = 21  # Hansen lossyear encoding for 2021
DEFAULT_COCOA_THRESHOLD = 0.50


def recent_loss_mask(
    geom,
    *,
    loss_from_year: int = EUDR_LOSS_YEAR,
    treecover_pct: int = TREECOVER_THRESHOLD_PCT,
    hansen_asset: str = HANSEN_ASSET,
):
    """Return Mask A as an ``ee.Image`` clipped to ``geom``.

    Mask A = ``(treecover2000 >= treecover_pct) AND (lossyear >= loss_from_year)``.

    ``hansen_asset`` defaults to Hansen GFC v2025_v1_13. Pass an older
    vintage string (e.g. ``"UMD/hansen/global_forest_change_2024_v1_12"``)
    to reproduce drift-study baselines.
    """
    import ee  # type: ignore[import-untyped]

    h = ee.Image(hansen_asset)
    forest = h.select("treecover2000").gte(treecover_pct)
    recent_loss = h.select("lossyear").gte(loss_from_year).And(forest)
    return recent_loss.clip(geom)


def plantation_probability_image(geom):
    """Return the most recent FDP cocoa probability image clipped to ``geom``.

    The function inspects the available bands and returns the first
    band whose name contains ``"prob"`` or ``"cocoa"``.
    """
    import ee  # type: ignore[import-untyped]

    coll = ee.ImageCollection(FDP_COCOA_ASSET).sort("system:time_start", False)
    img = ee.Image(coll.first())
    bands = img.bandNames().getInfo()
    band_name = next((b for b in bands if "prob" in b.lower() or "cocoa" in b.lower()), bands[0])
    return img.select(band_name).clip(geom)


def conversion_mask(
    geom,
    *,
    loss_from_year: int = EUDR_LOSS_YEAR,
    treecover_pct: int = TREECOVER_THRESHOLD_PCT,
    cocoa_threshold: float = DEFAULT_COCOA_THRESHOLD,
    hansen_asset: str = HANSEN_ASSET,
):
    """Return the EUDR-risk conversion mask as an ``ee.Image``.

    Conversion = ``Mask_A  AND  (FDP_cocoa_probability >= cocoa_threshold)``.
    """
    mask_a = recent_loss_mask(
        geom, loss_from_year=loss_from_year, treecover_pct=treecover_pct,
        hansen_asset=hansen_asset,
    )
    prob = plantation_probability_image(geom)
    cocoa_now = prob.gte(cocoa_threshold)
    return mask_a.And(cocoa_now)
