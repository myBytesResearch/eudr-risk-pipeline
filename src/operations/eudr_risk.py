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
#  File: eudr_risk.py | Project: eudr-risk-pipeline | Author: Guido Winger
# =============================================================================

"""The two-mask AND operation that defines EUDR-risk pixels.

For each pixel x:

    EUDR_Risk(x)  =  Mask_A(x)  ∧  Mask_B(x)
                  =  "x lost forest cover at or after the cut-off"
                     AND
                     "x is today classified as plantation with prob >= tau"

The operation is intentionally trivial. Its value is not algorithmic
sophistication, it is provenance: each ``True`` pixel can be rebuilt
from public source records (Hansen GFC + Kalischek 2023 / analogous
layer) by an external auditor.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Hansen GFC pixel ~ 30 m at the equator. For aggregate area reporting
# in tropical AOIs we use the canonical conversion.
HANSEN_PIXEL_AREA_HA = 0.09  # 30 m * 30 m = 900 m^2 = 0.09 ha


@dataclass(frozen=True)
class AreaSummary:
    """Per-region summary of mask areas in hectares.

    Attributes:
        aoi_name: Human-readable AOI identifier.
        plantation_ha: Total area where Mask B is True.
        risk_ha: Total area where Mask A ∧ Mask B is True.
        risk_share_pct: ``risk_ha / plantation_ha * 100``. 0 if no plantation.
        threshold_tau: Threshold used for Mask B.
        gfc_version: Hansen GFC dataset version.
        plantation_layer_id: Identifier of the plantation-probability layer.
        run_timestamp: ISO-8601 timestamp of the pipeline run.
    """

    aoi_name: str
    plantation_ha: float
    risk_ha: float
    risk_share_pct: float
    threshold_tau: float
    gfc_version: str
    plantation_layer_id: str
    run_timestamp: str

    def to_dict(self) -> dict[str, object]:
        return {
            "aoi_name": self.aoi_name,
            "plantation_ha": round(self.plantation_ha, 1),
            "risk_ha": round(self.risk_ha, 1),
            "risk_share_pct": round(self.risk_share_pct, 2),
            "threshold_tau": self.threshold_tau,
            "gfc_version": self.gfc_version,
            "plantation_layer_id": self.plantation_layer_id,
            "run_timestamp": self.run_timestamp,
        }


def eudr_risk_mask(mask_a: np.ndarray, mask_b: np.ndarray) -> np.ndarray:
    """Apply the AND operation to two boolean masks of equal shape.

    Args:
        mask_a: Boolean array from Mask A (forest loss post cut-off).
        mask_b: Boolean array from Mask B (present-day plantation).

    Returns:
        Boolean array, True where both masks are True.

    Raises:
        ValueError: If the two masks have incompatible shapes.
    """
    if mask_a.shape != mask_b.shape:
        raise ValueError(
            f"mask shape mismatch: A={mask_a.shape}, B={mask_b.shape} — "
            "re-project or resample to a common grid before AND."
        )
    return mask_a.astype(bool) & mask_b.astype(bool)


def area_summary(
    *,
    aoi_name: str,
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    threshold_tau: float,
    gfc_version: str,
    plantation_layer_id: str,
    run_timestamp: str,
    pixel_area_ha: float = HANSEN_PIXEL_AREA_HA,
) -> AreaSummary:
    """Compute the area summary used in the article's Plot 2 and §3 table.

    The function does not silently swallow shape mismatches — it propagates
    the ``ValueError`` from ``eudr_risk_mask`` so that a mis-aligned grid
    fails loud, not silently.
    """
    risk = eudr_risk_mask(mask_a, mask_b)
    plantation_px = int(mask_b.sum())
    risk_px = int(risk.sum())
    plantation_ha = plantation_px * pixel_area_ha
    risk_ha = risk_px * pixel_area_ha
    risk_share = (risk_ha / plantation_ha * 100.0) if plantation_ha > 0 else 0.0
    return AreaSummary(
        aoi_name=aoi_name,
        plantation_ha=plantation_ha,
        risk_ha=risk_ha,
        risk_share_pct=risk_share,
        threshold_tau=threshold_tau,
        gfc_version=gfc_version,
        plantation_layer_id=plantation_layer_id,
        run_timestamp=run_timestamp,
    )