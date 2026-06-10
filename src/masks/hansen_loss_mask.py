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
#  File: hansen_loss_mask.py | Project: eudr-risk-pipeline | Author: Guido Winger
# =============================================================================

"""Mask A — historical forest loss after the EUDR cut-off date.

Mask A in this pipeline implicitly combines TWO Hansen bands:

  1. ``treecover2000`` — only pixels that were forest (>= 30 % cover) at the
     year-2000 baseline. This excludes savanna, cropland, water and built-up
     pixels from the loss accounting.
  2. ``lossyear`` — restrict to pixels whose loss event occurred after the
     EUDR cut-off (Hansen encodes 2021 as the integer 21).

The combined condition is::

    Mask_A(x) = (treecover2000(x) >= 30 %)  AND  (lossyear(x) >= 21)

This matches the upstream internal myBytes pipeline implementation in
``src/data/forest_loss/cocoa_conversion.py`` (function ``conversion_layers``).

The function in this module is data-source agnostic: it takes pre-loaded
NumPy arrays and returns a boolean mask. Loading the rasters from Hansen
via Google Earth Engine, Microsoft Planetary Computer or local TIFFs is
the caller's responsibility — see ``notebooks/02_live_gee_pipeline.ipynb``
for an example.

Reference
---------
Hansen et al. (2013) "High-Resolution Global Maps of 21st-Century Forest
Cover Change" *Science* 342 (6160), 850-853.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

EUDR_CUTOFF_LOSSYEAR_ENCODING = 21
HANSEN_NODATA_LOSSYEAR = 0
TREECOVER_THRESHOLD_PCT = 30


@dataclass(frozen=True)
class HansenLossPixel:
    """Provenance record for a single pixel from Mask A."""

    row: int
    col: int
    lossyear: int
    treecover2000_pct: int
    gfc_tile_id: str
    gfc_version: str

    def to_dict(self) -> dict[str, object]:
        return {
            "row": self.row,
            "col": self.col,
            "lossyear": int(self.lossyear),
            "lossyear_full": 2000 + int(self.lossyear) if self.lossyear else None,
            "treecover2000_pct": int(self.treecover2000_pct),
            "gfc_tile_id": self.gfc_tile_id,
            "gfc_version": self.gfc_version,
        }


def hansen_loss_mask(
    lossyear: np.ndarray,
    treecover2000: np.ndarray | None = None,
    *,
    cutoff_encoded: int = EUDR_CUTOFF_LOSSYEAR_ENCODING,
    treecover_threshold_pct: int = TREECOVER_THRESHOLD_PCT,
) -> np.ndarray:
    """Compute Mask A — forest loss after EUDR cut-off on year-2000 forest.

    Args:
        lossyear: 2D integer array of Hansen ``lossyear`` values, with 0 for
            "no detected loss in observation window".
        treecover2000: Optional 2D integer/float array of ``treecover2000``
            percentages. If provided, pixels with cover below
            ``treecover_threshold_pct`` are excluded. **Recommended** —
            without this filter, Mask A counts loss of non-forest classes.
        cutoff_encoded: Earliest ``lossyear`` value counted as post-cut-off.
            Default 21 (= 2021), matching VO (EU) 2023/1115 Art. 2.
        treecover_threshold_pct: Minimum 2000 tree-cover percentage to count
            a pixel as "was forest at baseline". Default 30 %, Hansen
            convention.

    Returns:
        Boolean array of the same shape as ``lossyear``.
    """
    if lossyear.ndim != 2:
        raise ValueError(f"lossyear must be 2-D, got shape {lossyear.shape}")
    if not (1 <= cutoff_encoded <= 99):
        raise ValueError(f"cutoff_encoded must be in [1, 99], got {cutoff_encoded}")

    loss_after_cutoff = (lossyear >= cutoff_encoded) & (lossyear != HANSEN_NODATA_LOSSYEAR)

    if treecover2000 is None:
        # Caller chose to omit the forest baseline filter — return loss-only
        # mask, but the result is methodologically weaker.
        return loss_after_cutoff

    if treecover2000.shape != lossyear.shape:
        raise ValueError(
            f"treecover2000 shape {treecover2000.shape} must match "
            f"lossyear shape {lossyear.shape}"
        )
    was_forest = treecover2000 >= treecover_threshold_pct
    return loss_after_cutoff & was_forest