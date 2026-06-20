"""Localized (DE/EN/PL) render of the 4 satellite/mask plots for 3A1-01.

Fetches the GEE layers ONCE (Sentinel-2 RGB, Hansen Mask A, FDP Mask B, AND),
then re-renders the matplotlib layout per language. Needs Google Earth Engine.

Plots: plot1_two_mask_schema (3-panel) + plot1a_mask_a, plot1b_mask_b, plot1c_and.
DE = plot_*.png canonical, EN/PL = plot_*.<loc>.png (PL draft -> Mariusz).
"""

from __future__ import annotations

import io
from pathlib import Path

import ee
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image

OUT_DIR = Path(__file__).resolve().parents[1] / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LON, LAT = -6.6033, 5.7833
HALF_DEG_LON = (33.0 / 2) / (111.0 * np.cos(np.deg2rad(LAT)))
HALF_DEG_LAT = (33.0 / 2) / 111.0
WEST, SOUTH = LON - HALF_DEG_LON, LAT - HALF_DEG_LAT
EAST, NORTH = LON + HALF_DEG_LON, LAT + HALF_DEG_LAT
EXTENT = [WEST, EAST, SOUTH, NORTH]

ee.Initialize(project="mybytes-research-2026")
roi = ee.Geometry.Rectangle([WEST, SOUTH, EAST, NORTH])


def mask_s2_clouds(img: ee.Image) -> ee.Image:
    qa = img.select("QA60")
    cloud = qa.bitwiseAnd(1 << 10).eq(0)
    cirrus = qa.bitwiseAnd(1 << 11).eq(0)
    return img.updateMask(cloud.And(cirrus)).divide(10000)


print("Building Sentinel-2 composite ...")
s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(roi).filterDate("2024-11-01", "2025-04-30")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    .map(mask_s2_clouds).median()
)
rgb = s2.select(["B4", "B3", "B2"]).visualize(min=0.02, max=0.30, gamma=1.2)

hansen = ee.Image("UMD/hansen/global_forest_change_2024_v1_12")
mask_a = hansen.select("treecover2000").gte(30).And(hansen.select("lossyear").gte(21))

fdp_coll = ee.ImageCollection("projects/forestdatapartnership/assets/cocoa/model_2025a")
fdp_img = ee.Image(fdp_coll.sort("system:time_start", False).first())
fdp_bands = fdp_img.bandNames().getInfo()
fdp_band = next((b for b in fdp_bands if "prob" in b.lower() or "cocoa" in b.lower()), fdp_bands[0])
fdp = fdp_img.select(fdp_band)
mask_b = fdp.gte(0.50)
mask_and = mask_a.And(mask_b)


def fetch_png(image: ee.Image, dim: int = 1200) -> np.ndarray:
    url = image.getThumbURL({"region": roi, "dimensions": dim, "format": "png"})
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return np.asarray(Image.open(io.BytesIO(r.content)).convert("RGBA"))


print("Fetching tiles ...")
rgb_arr = fetch_png(rgb)
mask_a_arr = fetch_png(mask_a.updateMask(mask_a).visualize(palette=["FFD400"], opacity=0.85))
mask_b_arr = fetch_png(mask_b.updateMask(mask_b).visualize(palette=["B388FF"], opacity=0.32))
mask_and_arr = fetch_png(mask_and.updateMask(mask_and).visualize(palette=["E53935"], opacity=1.0))


def composite(base: np.ndarray, *overlays: np.ndarray) -> np.ndarray:
    out = base.astype(np.float32) / 255.0
    for ov in overlays:
        ov_f = ov.astype(np.float32) / 255.0
        a = ov_f[..., 3:4]
        out[..., :3] = ov_f[..., :3] * a + out[..., :3] * (1 - a)
    return np.clip(out * 255, 0, 255).astype(np.uint8)


panel_1 = rgb_arr
panel_2 = composite(rgb_arr, mask_a_arr)
panel_3 = composite(rgb_arr, mask_a_arr, mask_b_arr, mask_and_arr)

TITLE_COLOR, SUBTLE = "#1a1a1a", "#666666"

LOCALES: dict[str, dict] = {
    "de": {
        "lon": "Längengrad °E", "lat": "Breitengrad °N",
        "suptitle": "Wie eine EUDR-konforme Risk-Monitoring-Karte auf Sat-Pixel-Niveau tatsächlich funktioniert",
        "subtitle": "AOI 33 × 33 km um Soubré (CIV). Drei Layer, eine UND-Verknüpfung, ein auditierbarer Überblick über wahrscheinliche EUDR-Verstöße auf 10 × 10 m Pixel.",
        "panels": [
            ("1 · Sentinel-2 RGB", "Wald-/Plantagen-Mosaik um Soubré (Median 11/2024 - 04/2025)"),
            ("2 · + Maske A: Hansen-Wald-Verlust", "Gelb: treecover2000 ≥ 30 %  ∧  lossyear ≥ 2021"),
            ("3 · + Maske B & UND-Verknüpfung", "Lila-Schleier: FDP P ≥ 0,50  ·  Rot: EUDR-Risk (A ∧ B)"),
        ],
        "leg": ["Maske A - Hansen-Wald-Verlust", "Maske B - FDP-Kakao P ≥ 0,50", "EUDR-Risk (A ∧ B)"],
        "src": "Quellen: Sentinel-2 SR Harmonized (Copernicus / ESA);  Hansen GFC v2024 (UMD);  FDP Cocoa Probability 2025a (Forest Data Partnership, CC-BY-4.0-NC).  myBytes Satelliten-Monitoring, AOI civ_soubre_33km, abgerufen 2026-06-08.",
        "single": [
            ("Maske A - Hansen-Wald-Verlust nach Cut-off", "Gelb: treecover2000 ≥ 30 % UND lossyear ≥ 2021"),
            ("Maske B - FDP-Kakao-Wahrscheinlichkeit", "Lila-Schleier: FDP P ≥ 0,50"),
            ("UND-Verknüpfung - EUDR-Risiko-Pixel", "Rot: Maske A ∧ Maske B  ·  die eigentlich auditierbare Aussage"),
        ],
        "single_src": "Quelle: myBytes Satelliten-Monitoring, Soubré-AOI 33 × 33 km, abgerufen 2026-06-08.",
    },
    "en": {
        "lon": "Longitude °E", "lat": "Latitude °N",
        "suptitle": "How an EUDR-compliant risk-monitoring map actually works at satellite-pixel level",
        "subtitle": "AOI 33 × 33 km around Soubré (CIV). Three layers, one AND operation, one auditable overview of likely EUDR breaches at 10 × 10 m pixels.",
        "panels": [
            ("1 · Sentinel-2 RGB", "Forest/plantation mosaic around Soubré (median 11/2024 - 04/2025)"),
            ("2 · + Mask A: Hansen forest loss", "Yellow: treecover2000 ≥ 30 %  ∧  lossyear ≥ 2021"),
            ("3 · + Mask B & AND operation", "Purple veil: FDP P ≥ 0.50  ·  Red: EUDR risk (A ∧ B)"),
        ],
        "leg": ["Mask A - Hansen forest loss", "Mask B - FDP cocoa P ≥ 0.50", "EUDR risk (A ∧ B)"],
        "src": "Sources: Sentinel-2 SR Harmonized (Copernicus / ESA);  Hansen GFC v2024 (UMD);  FDP Cocoa Probability 2025a (Forest Data Partnership, CC-BY-4.0-NC).  myBytes satellite monitoring, AOI civ_soubre_33km, retrieved 2026-06-08.",
        "single": [
            ("Mask A - Hansen forest loss after cut-off", "Yellow: treecover2000 ≥ 30 % AND lossyear ≥ 2021"),
            ("Mask B - FDP cocoa probability", "Purple veil: FDP P ≥ 0.50"),
            ("AND operation - EUDR risk pixels", "Red: Mask A ∧ Mask B  ·  the actually auditable statement"),
        ],
        "single_src": "Source: myBytes satellite monitoring, Soubré AOI 33 × 33 km, retrieved 2026-06-08.",
    },
    "pl": {
        "lon": "Długość geogr. °E", "lat": "Szerokość geogr. °N",
        "suptitle": "Jak naprawdę działa zgodna z EUDR mapa monitoringu ryzyka na poziomie piksela satelitarnego",
        "subtitle": "AOI 33 × 33 km wokół Soubré (CIV). Trzy warstwy, jedna operacja AND, jeden audytowalny przegląd prawdopodobnych naruszeń EUDR na pikselach 10 × 10 m.",
        "panels": [
            ("1 · Sentinel-2 RGB", "Mozaika las/plantacja wokół Soubré (mediana 11/2024 - 04/2025)"),
            ("2 · + Maska A: utrata lasu Hansen", "Żółty: treecover2000 ≥ 30 %  ∧  lossyear ≥ 2021"),
            ("3 · + Maska B i operacja AND", "Fioletowa mgiełka: FDP P ≥ 0,50  ·  Czerwony: ryzyko EUDR (A ∧ B)"),
        ],
        "leg": ["Maska A - utrata lasu Hansen", "Maska B - kakao FDP P ≥ 0,50", "ryzyko EUDR (A ∧ B)"],
        "src": "Źródła: Sentinel-2 SR Harmonized (Copernicus / ESA);  Hansen GFC v2024 (UMD);  FDP Cocoa Probability 2025a (Forest Data Partnership, CC-BY-4.0-NC).  myBytes monitoring satelitarny, AOI civ_soubre_33km, pobrano 2026-06-08.",
        "single": [
            ("Maska A - utrata lasu Hansen po dacie granicznej", "Żółty: treecover2000 ≥ 30 % ORAZ lossyear ≥ 2021"),
            ("Maska B - prawdopodobieństwo kakao FDP", "Fioletowa mgiełka: FDP P ≥ 0,50"),
            ("Operacja AND - piksele ryzyka EUDR", "Czerwony: Maska A ∧ Maska B  ·  właściwie audytowalne stwierdzenie"),
        ],
        "single_src": "Źródło: myBytes monitoring satelitarny, AOI Soubré 33 × 33 km, pobrano 2026-06-08.",
    },
}

PANEL_IMGS = [panel_1, panel_2, panel_3]
SINGLE_IMGS = [composite(rgb_arr, mask_a_arr), composite(rgb_arr, mask_b_arr), panel_3]
SINGLE_NAMES = ["plot1a_mask_a", "plot1b_mask_b", "plot1c_and"]
LEG_COLORS = ["#FFD400", "#B388FF", "#E53935"]


def render_three_panel(loc: str, L: dict) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 7.2), dpi=160)
    fig.patch.set_facecolor("white")
    for ax, img, (t, sub) in zip(axes, PANEL_IMGS, L["panels"]):
        ax.imshow(img, extent=EXTENT, origin="upper")
        ax.text(0.0, 1.085, t, transform=ax.transAxes, fontsize=13, fontweight="bold", color=TITLE_COLOR, va="bottom")
        ax.text(0.0, 1.025, sub, transform=ax.transAxes, fontsize=9.5, color=SUBTLE, va="bottom")
        ax.tick_params(labelsize=8, colors=SUBTLE)
        ax.set_xlabel(L["lon"], fontsize=8.5, color=SUBTLE)
        ax.set_ylabel(L["lat"], fontsize=8.5, color=SUBTLE)
        for spine in ax.spines.values():
            spine.set_color("#cccccc")
    fig.suptitle(L["suptitle"], fontsize=15.5, fontweight="bold", color=TITLE_COLOR, x=0.02, y=0.985, ha="left")
    fig.text(0.02, 0.935, L["subtitle"], fontsize=10.5, color=SUBTLE, ha="left")
    handles = [mpatches.Patch(color=c, label=lbl) for c, lbl in zip(LEG_COLORS, L["leg"])]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(0.5, 0.06))
    fig.text(0.02, 0.02, L["src"], fontsize=8, color=SUBTLE, ha="left")
    plt.subplots_adjust(left=0.04, right=0.99, top=0.76, bottom=0.16, wspace=0.12)
    suffix = "" if loc == "de" else f".{loc}"
    fig.savefig(OUT_DIR / f"plot1_two_mask_schema{suffix}.png", dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def render_singles(loc: str, L: dict) -> None:
    for arr, name, (title, sub) in zip(SINGLE_IMGS, SINGLE_NAMES, L["single"]):
        f, a = plt.subplots(figsize=(7.5, 6.4), dpi=160)
        f.patch.set_facecolor("white")
        a.imshow(arr, extent=EXTENT, origin="upper")
        a.text(0.0, 1.075, title, transform=a.transAxes, fontsize=12.5, fontweight="bold", color=TITLE_COLOR, va="bottom")
        a.text(0.0, 1.018, sub, transform=a.transAxes, fontsize=9.5, color=SUBTLE, va="bottom")
        a.tick_params(labelsize=8, colors=SUBTLE)
        a.set_xlabel(L["lon"], fontsize=8.5, color=SUBTLE)
        a.set_ylabel(L["lat"], fontsize=8.5, color=SUBTLE)
        for spine in a.spines.values():
            spine.set_color("#cccccc")
        f.text(0.02, 0.015, L["single_src"], fontsize=7.5, color=SUBTLE)
        f.subplots_adjust(left=0.10, right=0.98, top=0.86, bottom=0.10)
        suffix = "" if loc == "de" else f".{loc}"
        f.savefig(OUT_DIR / f"{name}{suffix}.png", dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(f)


if __name__ == "__main__":
    for loc, L in LOCALES.items():
        render_three_panel(loc, L)
        render_singles(loc, L)
    print(f"Rendered DE/EN/PL mask plots to {OUT_DIR}")
    for p in sorted(OUT_DIR.glob("plot1*.png")):
        print(f"  {p.name} ({p.stat().st_size / 1024:.1f} KB)")
