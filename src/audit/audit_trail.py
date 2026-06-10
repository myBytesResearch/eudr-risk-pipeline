# =============================================================================
#                     ____        __
#    ____ ___  __  __/ __ )__  __/ /____  _____
#   / __ `__ \/ / / / __  / / / / __/ _ \/ ___/
#  / / / / / / /_/ / /_/ / /_/ / /_/  __(__  )
# /_/ /_/ /_/\__, /_____/\__, /\__/\___/____/
#           /____/      /____/
#
#  myBytes.com
#  Copyright (c) 2026 myBytes GmbH. All rights reserved.
#  Proprietary and confidential.
#
#  File: audit_trail.py | Project: eudr-risk-pipeline | Author: Guido Winger
# =============================================================================

"""Per-pixel audit trail records.

For every risk pixel returned by the AND operation, an auditor must be able
to reconstruct the value from public sources. This module emits one record
per risk pixel containing the minimum set of provenance fields:

  * geographic coordinates (lat, lon)
  * Hansen.lossyear (the raw integer Hansen returned at this pixel)
  * GFC tile identifier + dataset version
  * plantation-probability layer value at this pixel
  * plantation-layer identifier + version
  * threshold tau used at evaluation time
  * optional RADD alert identifier (when present)

The records are intentionally serialised as a pandas DataFrame so that the
companion notebook can render them as the article's Plot 3.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AuditPixel:
    """One row of the per-pixel audit trail."""

    lat: float
    lon: float
    lossyear: int
    gfc_tile_id: str
    gfc_version: str
    plantation_probability: float
    plantation_layer_id: str
    plantation_layer_version: str
    threshold_tau: float
    radd_alert_id: str | None


def _affine_pixel_to_lonlat(
    rows: np.ndarray,
    cols: np.ndarray,
    *,
    transform: tuple[float, float, float, float, float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Apply a six-element affine transform (rasterio convention) to pixel
    coordinates and return ``(lon, lat)`` arrays.

    The convention here matches rasterio's ``Affine`` six-tuple
    ``(a, b, c, d, e, f)`` where ``lon = a*col + b*row + c`` and
    ``lat = d*col + e*row + f``. The default identity-like transform is
    sufficient for the synthetic demo; production callers pass the actual
    raster's transform.
    """
    a, b, c, d, e, f = transform
    lon = a * cols + b * rows + c
    lat = d * cols + e * rows + f
    return lon, lat


def build_audit_trail(
    risk_mask: np.ndarray,
    lossyear: np.ndarray,
    plantation_probability: np.ndarray,
    *,
    gfc_tile_id: str,
    gfc_version: str,
    plantation_layer_id: str,
    plantation_layer_version: str,
    threshold_tau: float,
    transform: tuple[float, float, float, float, float, float] = (1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
    radd_alert_ids: np.ndarray | None = None,
    max_records: int | None = None,
) -> pd.DataFrame:
    """Build the audit trail DataFrame for all risk pixels.

    Args:
        risk_mask: Boolean array — Mask_A ∧ Mask_B.
        lossyear: 2D integer array — Hansen GFC lossyear values, same shape
            as risk_mask.
        plantation_probability: 2D float array of plantation probability,
            same shape as risk_mask.
        gfc_tile_id: Hansen tile identifier covering this AOI.
        gfc_version: Hansen GFC dataset version string.
        plantation_layer_id: Identifier of the plantation-probability layer.
        plantation_layer_version: Version stamp of the plantation layer.
        threshold_tau: Threshold used for Mask B.
        transform: Six-element affine transform mapping pixel (row, col) to
            (lon, lat). Defaults to identity-like for the demo.
        radd_alert_ids: Optional 2D array of strings — RADD alert IDs per
            pixel, or None.
        max_records: If set, truncate the output to this many rows. Useful
            for the article's Plot 3 which only displays 5 example pixels.

    Returns:
        A DataFrame with one row per risk pixel and one column per
        provenance field.
    """
    rows, cols = np.nonzero(risk_mask)
    if max_records is not None:
        rows, cols = rows[:max_records], cols[:max_records]
    lon, lat = _affine_pixel_to_lonlat(rows, cols, transform=transform)

    if radd_alert_ids is not None:
        radd_vals: Iterable[str | None] = [str(radd_alert_ids[r, c]) if radd_alert_ids[r, c] else None for r, c in zip(rows, cols)]
    else:
        radd_vals = [None] * len(rows)

    records = [
        AuditPixel(
            lat=float(lat[i]),
            lon=float(lon[i]),
            lossyear=int(lossyear[r, c]),
            gfc_tile_id=gfc_tile_id,
            gfc_version=gfc_version,
            plantation_probability=float(plantation_probability[r, c]),
            plantation_layer_id=plantation_layer_id,
            plantation_layer_version=plantation_layer_version,
            threshold_tau=threshold_tau,
            radd_alert_id=radd_id,
        )
        for i, (r, c, radd_id) in enumerate(zip(rows, cols, radd_vals))
    ]
    return pd.DataFrame([asdict(p) for p in records])