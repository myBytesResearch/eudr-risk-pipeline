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

"""Mask operations — the AND that turns two layers into auditable risk."""

from .eudr_risk import eudr_risk_mask, area_summary

__all__ = ["eudr_risk_mask", "area_summary"]