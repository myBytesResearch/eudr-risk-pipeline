"""Localized (EN/PL) renders of the localizable 3A1-01 (eudr-pixel) plots.

Covers plot2_region_comparison and plot3_audit_trail. The four satellite/mask
plots (plot1_two_mask_schema, plot1a/1b/1c) are NOT covered here: they are
rendered by 3A1-01_render_plot1_rgb.py which needs a live Google Earth Engine
call and cannot run in the sandbox.

PL labels are a first draft for Mariusz review. Numbers are unchanged.

Output: ~/myBytes-workplace/articles/eudr-pixel-auditability/figures/plot{2,3}_*.<loc>.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "common"))

from executive_plots import (  # noqa: E402
    RegionRiskRow,
    executive_audit_trail_table,
    executive_region_comparison_bars,
    set_source_prefix,
)

OUT_DIR = Path(__file__).resolve().parents[1] / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_CSV = (
    PROJECT_ROOT
    / "data" / "runs" / "2026-06-08" / "audit_trail_sample.csv"
)
AUDIT_ROWS = pd.read_csv(SNAPSHOT_CSV)
AUDIT_ROWS = AUDIT_ROWS[AUDIT_ROWS["aoi_id"] == "civ_soubre_33km"].reset_index(drop=True)
AUDIT_COLUMNS = ["lat", "lon", "lossyear", "gfc_tile_id", "plantation_probability",
                 "plantation_layer_id", "threshold_tau"]
AUDIT_COLUMN_WIDTHS = [0.07, 0.08, 0.08, 0.10, 0.13, 0.46, 0.08]

LOCALES: dict[str, dict] = {
    "en": {
        "source_prefix": "Source: ",
        "region_title": "What share of today's plantation counts as risk area under the EUDR definition",
        "region_caption": ("Sefwi-Wiawso has more than twice as much EUDR risk area per plantation "
                           "hectare as Soubré, and on top of that a completely different spatial topology."),
        "region_source": ("myBytes satellite monitoring 2026-06-08 on Hansen GFC v2025_v1_13 × "
                          "FDP Cocoa Probability 2025a, AOI 33 × 33 km around town center"),
        "legend_labels": ("EUDR-compliant (plantation without loss cut-off hit)", "EUDR risk area (A ∧ B)"),
        "region_xlabel": "Plantation area · hectares",
        "of_word": "of",
        "regions": [
            ("Soubré, CIV (33 × 33 km)", 73_523.0, 2_013.0, "smallholder mosaic · low RADD activity"),
            ("Sefwi-Wiawso, GHA (33 × 33 km)", 76_523.0, 4_633.0, "commercial large estates · high RADD activity"),
        ],
        "audit_title": "What an auditor must be able to reconstruct per risk pixel",
        "audit_caption": ("Every row traceable to a public source dataset. That is the difference "
                          "from a pretty map."),
        "audit_source": ("own pipeline output; source data: UMD Hansen GFC v2025, FDP Cocoa Model "
                         "2025a (builds on Kalischek 2023), Wageningen RADD"),
    },
    "pl": {
        "source_prefix": "Źródło: ",
        "region_title": "Jaki udział dzisiejszej plantacji liczy się jako obszar ryzyka według definicji EUDR",
        "region_caption": ("Sefwi-Wiawso ma ponad dwukrotnie większy obszar ryzyka EUDR na hektar "
                           "plantacji niż Soubré, a do tego zupełnie inną topologię przestrzenną."),
        "region_source": ("myBytes monitoring satelitarny 2026-06-08 na Hansen GFC v2025_v1_13 × "
                          "FDP Cocoa Probability 2025a, AOI 33 × 33 km wokół centrum miasta"),
        "legend_labels": ("Zgodne z EUDR (plantacja bez trafienia w próg utraty)", "Obszar ryzyka EUDR (A ∧ B)"),
        "region_xlabel": "Powierzchnia plantacji · hektary",
        "of_word": "z",
        "regions": [
            ("Soubré, CIV (33 × 33 km)", 73_523.0, 2_013.0, "mozaika drobnych gospodarstw · niska aktywność RADD"),
            ("Sefwi-Wiawso, GHA (33 × 33 km)", 76_523.0, 4_633.0, "komercyjne duże gospodarstwa · wysoka aktywność RADD"),
        ],
        "audit_title": "Co audytor musi być w stanie odtworzyć dla każdego piksela ryzyka",
        "audit_caption": ("Każdy wiersz możliwy do prześledzenia do publicznego zbioru źródłowego. "
                          "To różni się od ładnej mapy."),
        "audit_source": ("własny wynik pipeline'u; dane źródłowe: UMD Hansen GFC v2025, FDP Cocoa "
                         "Model 2025a (oparty na Kalischek 2023), Wageningen RADD"),
    },
}


def render_locale(loc: str, L: dict) -> None:
    set_source_prefix(L["source_prefix"])

    rows = [RegionRiskRow(region_name=n, plantation_ha=p, risk_ha=r, topology=t)
            for n, p, r, t in L["regions"]]
    fig2, _ = executive_region_comparison_bars(
        rows,
        title=L["region_title"],
        caption=L["region_caption"],
        source=L["region_source"],
        legend_labels=L["legend_labels"],
        x_axis_label=L["region_xlabel"],
        of_word=L["of_word"],
    )
    fig2.savefig(OUT_DIR / f"plot2_region_comparison.{loc}.png", dpi=160, bbox_inches="tight")

    fig3, _ = executive_audit_trail_table(
        AUDIT_ROWS,
        columns=AUDIT_COLUMNS,
        column_widths=AUDIT_COLUMN_WIDTHS,
        title=L["audit_title"],
        caption=L["audit_caption"],
        source=L["audit_source"],
    )
    fig3.savefig(OUT_DIR / f"plot3_audit_trail.{loc}.png", dpi=160, bbox_inches="tight", pad_inches=0.25)


if __name__ == "__main__":
    for loc, L in LOCALES.items():
        render_locale(loc, L)
    set_source_prefix("Quelle: ")
    print(f"Rendered EN/PL eudr-pixel plots to {OUT_DIR}")
    for p in sorted(OUT_DIR.glob("*.??.png")):
        print(f"  {p.name} ({p.stat().st_size / 1024:.1f} KB)")
