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
#  File: __init__.py | Project: eudr-risk-pipeline | Author: Guido Winger
# =============================================================================

"""Earth Engine layer constructors for the live EUDR pipeline path.

These functions return ``ee.Image`` objects. They lazy-import the
``earthengine-api`` library so the rest of the package does not require
it. The caller is responsible for calling ``ee.Initialize(...)`` with a
valid GEE project before invoking any of these functions.
"""

from .conversion_layers import (
    FDP_COCOA_ASSET,
    HANSEN_ASSET,
    RADD_ASSET,
    conversion_mask,
    plantation_probability_image,
    recent_loss_mask,
)

__all__ = [
    "HANSEN_ASSET",
    "FDP_COCOA_ASSET",
    "RADD_ASSET",
    "recent_loss_mask",
    "plantation_probability_image",
    "conversion_mask",
]