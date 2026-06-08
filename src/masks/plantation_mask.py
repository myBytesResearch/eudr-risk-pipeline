"""Mask B — present-day plantation probability.

For cocoa in West Africa, the reference plantation-probability layer used
by the upstream internal myBytes pipeline is the **Forest Data Partnership
Cocoa Model 2025a**, available on Google Earth Engine at::

    projects/forestdatapartnership/assets/cocoa/model_2025a

The FDP model is built on the methodology of Kalischek et al. 2023
*Nature Food* and is maintained as a separately curated Google-hosted
asset.

LICENCE NOTE — IMPORTANT
========================
The FDP cocoa layer is licensed **CC-BY-4.0-NC** (non-commercial). Pixel
values, derived statistics, and downstream figures produced with this
layer may not be redistributed for commercial purposes without separate
licensing arrangements with Forest Data Partnership. The methodology
itself is freely usable; only the *layer values* carry the NC restriction.

For other EUDR commodities, replace this layer with the appropriate
plantation-probability source (MapBiomas + Trase for Brazilian soy,
Descals et al. 2024 for oil palm, etc.).

Threshold choice
================
``tau = 0.50`` matches the internal default. Production
deployments must calibrate against ground truth using Olofsson et al. 2014
area estimation good practice and publish a sensitivity analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DEFAULT_THRESHOLD = 0.50
PLANTATION_NODATA = np.float32(-1.0)


@dataclass(frozen=True)
class PlantationPixel:
    """Provenance record for a single pixel from Mask B.

    Attributes:
        row: Row index within the source tile.
        col: Column index within the source tile.
        probability: Plantation probability in [0, 1].
        layer_id: Source layer identifier (e.g. ``"kalischek_2023_cocoa_v1"``).
        layer_version: Specific dataset version stamp.
        threshold_used: The tau threshold applied at evaluation time.
    """

    row: int
    col: int
    probability: float
    layer_id: str
    layer_version: str
    threshold_used: float

    def to_dict(self) -> dict[str, object]:
        return {
            "row": self.row,
            "col": self.col,
            "probability": float(self.probability),
            "layer_id": self.layer_id,
            "layer_version": self.layer_version,
            "threshold_used": float(self.threshold_used),
        }


def plantation_mask(
    probability: np.ndarray,
    threshold: float = DEFAULT_THRESHOLD,
    nodata_value: float = PLANTATION_NODATA,
) -> np.ndarray:
    """Compute Mask B — present-day plantation at probability >= threshold.

    Args:
        probability: 2D float array in [0, 1] of plantation probability.
            Nodata pixels are marked with ``nodata_value`` (default -1.0).
        threshold: Decision threshold tau. Default 0.50. Must be in (0, 1).
        nodata_value: Sentinel value for nodata pixels in the probability layer.

    Returns:
        Boolean array of the same shape, True where plantation probability
        meets or exceeds the threshold AND the pixel is not nodata.
    """
    if probability.ndim != 2:
        raise ValueError(f"probability must be 2-D, got shape {probability.shape}")
    if not 0.0 < threshold < 1.0:
        raise ValueError(f"threshold must lie in (0, 1), got {threshold}")
    valid = probability != nodata_value
    return valid & (probability >= threshold)


def threshold_sensitivity(
    probability: np.ndarray,
    thresholds: list[float] | tuple[float, ...] = (0.30, 0.40, 0.50, 0.60, 0.70),
    nodata_value: float = PLANTATION_NODATA,
) -> dict[float, int]:
    """Return the count of mask-positive pixels for each candidate threshold.

    This is the "sensitivity" output that the article's §4 requires every
    vendor to publish. A threshold whose tiny shift swings the area by an
    order of magnitude is a threshold that is not yet calibrated.
    """
    return {
        float(t): int(plantation_mask(probability, threshold=t, nodata_value=nodata_value).sum())
        for t in thresholds
    }
