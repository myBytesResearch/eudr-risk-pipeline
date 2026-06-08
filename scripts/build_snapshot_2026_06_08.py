"""Build the 2026-06-08 reproducibility snapshot from a live GEE run.

For each AOI (civ_soubre_33km, gha_sefwi_wiawso_33km) and each
Hansen-vintage (v2024_v1_12, v2025_v1_13), compute the EUDR-Risk
area share. Additionally, sample five real risk pixels from the
Soubré AOI (Hansen 2025 vintage) with full per-pixel provenance for
the audit-trail companion CSV.

Writes:
    data/runs/2026-06-08/area_summary.csv
    data/runs/2026-06-08/vintage_drift.csv
    data/runs/2026-06-08/audit_trail_sample.csv
    data/runs/2026-06-08/README.md
"""

from __future__ import annotations

import csv
from pathlib import Path

import ee
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "runs" / "2026-06-08"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ee.Initialize(project="mybytes-research-2026")

RUN_TIMESTAMP = "2026-06-08T00:00:00Z"
TAU = 0.50
TREECOVER_THRESHOLD = 30
LOSSYEAR_CUTOFF = 21

AOIS = {
    "civ_soubre_33km": {
        "aoi_name": "Soubré, CIV",
        "country": "CIV",
        "center_lon": -6.6033,
        "center_lat": 5.7833,
        "topology": "smallholder_mosaic",
        "radd_activity_level": "low",
    },
    "gha_sefwi_wiawso_33km": {
        "aoi_name": "Sefwi-Wiawso, GHA",
        "country": "GHA",
        "center_lon": -2.5000,
        "center_lat": 6.2000,
        "topology": "commercial_large_blocks",
        "radd_activity_level": "high",
    },
}
HALF_KM = 33.0 / 2

VINTAGES = {
    "hansen_v2024_v1_12": "UMD/hansen/global_forest_change_2024_v1_12",
    "hansen_v2025_v1_13": "UMD/hansen/global_forest_change_2025_v1_13",
}


def bbox(lon: float, lat: float) -> ee.Geometry:
    dlon = HALF_KM / (111.0 * np.cos(np.deg2rad(lat)))
    dlat = HALF_KM / 111.0
    return ee.Geometry.Rectangle([lon - dlon, lat - dlat, lon + dlon, lat + dlat])


def fdp_image() -> ee.Image:
    coll = ee.ImageCollection("projects/forestdatapartnership/assets/cocoa/model_2025a")
    img = ee.Image(coll.sort("system:time_start", False).first())
    bands = img.bandNames().getInfo()
    band = next(
        (b for b in bands if "prob" in b.lower() or "cocoa" in b.lower()), bands[0]
    )
    return img.select(band)


print("Loading FDP layer ...")
fdp = fdp_image()
mask_b = fdp.gte(TAU)
pixel_area = ee.Image.pixelArea()


def reduce_ha(image: ee.Image, region: ee.Geometry) -> float:
    masked_area = pixel_area.updateMask(image)
    res = masked_area.reduceRegion(
        reducer=ee.Reducer.sum(), geometry=region, scale=30,
        maxPixels=1e10, bestEffort=True,
    )
    return res.get("area").getInfo() / 10_000.0


# ---------------------------------------------------------------------------
# Area summary + vintage drift
# ---------------------------------------------------------------------------
area_rows = []
drift_rows = []
for aoi_id, meta in AOIS.items():
    roi = bbox(meta["center_lon"], meta["center_lat"])
    plant_ha = reduce_ha(mask_b, roi)
    print(f"\n{aoi_id}: plantation_ha = {plant_ha:,.0f}")
    per_vintage: dict[str, float] = {}
    for vintage_id, asset in VINTAGES.items():
        h = ee.Image(asset)
        mask_a = (
            h.select("treecover2000").gte(TREECOVER_THRESHOLD)
            .And(h.select("lossyear").gte(LOSSYEAR_CUTOFF))
        )
        risk_ha = reduce_ha(mask_a.And(mask_b), roi)
        share = 100 * risk_ha / plant_ha if plant_ha else float("nan")
        per_vintage[vintage_id] = share
        print(f"  {vintage_id}: risk_ha = {risk_ha:,.0f}  share = {share:.2f} %")
        area_rows.append({
            "aoi_id": aoi_id,
            "aoi_name": meta["aoi_name"],
            "country": meta["country"],
            "window_size_km": 33,
            "center_lon": meta["center_lon"],
            "center_lat": meta["center_lat"],
            "hansen_vintage": vintage_id,
            "gfc_asset": asset,
            "plantation_layer_id": "projects/forestdatapartnership/assets/cocoa/model_2025a",
            "plantation_layer_version": "2025a",
            "plantation_threshold_tau": TAU,
            "treecover2000_threshold_pct": TREECOVER_THRESHOLD,
            "hansen_lossyear_cutoff": LOSSYEAR_CUTOFF,
            "plantation_ha": round(plant_ha, 1),
            "risk_ha": round(risk_ha, 1),
            "risk_share_pct": round(share, 2),
            "topology": meta["topology"],
            "radd_activity_level": meta["radd_activity_level"],
            "run_timestamp": RUN_TIMESTAMP,
        })
    drift_rows.append({
        "aoi_id": aoi_id,
        "aoi_name": meta["aoi_name"],
        "risk_share_2024_pct": round(per_vintage["hansen_v2024_v1_12"], 2),
        "risk_share_2025_pct": round(per_vintage["hansen_v2025_v1_13"], 2),
        "delta_pp": round(
            per_vintage["hansen_v2025_v1_13"] - per_vintage["hansen_v2024_v1_12"], 2
        ),
        "run_timestamp": RUN_TIMESTAMP,
    })


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


write_csv(OUT_DIR / "area_summary.csv", area_rows)
write_csv(OUT_DIR / "vintage_drift.csv", drift_rows)


# ---------------------------------------------------------------------------
# Sample five real EUDR-Risk pixels from Soubré (Hansen 2025 vintage)
# ---------------------------------------------------------------------------
print("\nSampling five Soubré risk pixels ...")
soubre = AOIS["civ_soubre_33km"]
roi = bbox(soubre["center_lon"], soubre["center_lat"])
h25 = ee.Image("UMD/hansen/global_forest_change_2025_v1_13")
mask_a = h25.select("treecover2000").gte(TREECOVER_THRESHOLD).And(
    h25.select("lossyear").gte(LOSSYEAR_CUTOFF)
)
risk_mask = mask_a.And(mask_b)

sample_image = risk_mask.rename("risk").addBands(
    h25.select("lossyear").rename("lossyear")
).addBands(
    h25.select("treecover2000").rename("treecover2000")
).addBands(
    fdp.rename("plantation_probability")
)

sample = sample_image.updateMask(risk_mask).stratifiedSample(
    numPoints=5, classBand="risk", region=roi, scale=30,
    geometries=True, seed=42,
).getInfo()

audit_rows = []
for feat in sample["features"]:
    coords = feat["geometry"]["coordinates"]
    props = feat["properties"]
    audit_rows.append({
        "aoi_id": "civ_soubre_33km",
        "lat": round(coords[1], 4),
        "lon": round(coords[0], 4),
        "lossyear": int(props["lossyear"]),
        "treecover2000_pct": int(props["treecover2000"]),
        "gfc_tile_id": "10N_010W",
        "gfc_version": "UMD/hansen/global_forest_change_2025_v1_13",
        "plantation_probability": round(float(props["plantation_probability"]), 4),
        "plantation_layer_id": "projects/forestdatapartnership/assets/cocoa/model_2025a",
        "plantation_layer_version": "2025a",
        "threshold_tau": TAU,
        "run_timestamp": RUN_TIMESTAMP,
    })

write_csv(OUT_DIR / "audit_trail_sample.csv", audit_rows)


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------
README = f"""# Pipeline run snapshot — 2026-06-08

This directory is the **primary reproducibility snapshot** for the
companion articles
[`eudr-pixel-auditierbarkeit`](https://mybytes.com/research/notes/eudr-pixel-auditierbarkeit)
and
[`eudr-update-2026`](https://mybytes.com/research/notes/eudr-update-2026).
Every risk-share number quoted in either article reproduces from this
snapshot via `notebooks/00_reproduce_article_numbers.ipynb`.

## Run parameters

- **AOIs**: two 33 × 33 km bounding boxes, centred on Soubré (CIV,
  −6.6033, 5.7833) and Sefwi-Wiawso (GHA, −2.5000, 6.2000).
- **Hansen GFC versions** (both, for the vintage-drift comparison):
  `UMD/hansen/global_forest_change_2024_v1_12` (forest-loss data up to
  2023) and `UMD/hansen/global_forest_change_2025_v1_13` (up to 2024).
- **Plantation layer**: `projects/forestdatapartnership/assets/cocoa/model_2025a`
  (Forest Data Partnership cocoa probability, 2025a release; builds on
  Kalischek et al. 2023 *Nature Food*).
- **Threshold τ**: {TAU} on the FDP cocoa probability band.
- **Hansen lossyear cut-off**: ≥ {LOSSYEAR_CUTOFF} (= 2021 calendar year and later).
- **Tree-cover-2000 threshold**: {TREECOVER_THRESHOLD} % (Hansen `treecover2000` band).
- **Run timestamp**: {RUN_TIMESTAMP}

## Files

- `area_summary.csv` — one row per (AOI × Hansen-vintage) with
  plantation area, EUDR-risk area, risk share, topology annotation,
  and full provenance fields.
- `vintage_drift.csv` — one row per AOI with the 2024-vs-2025 vintage
  comparison and the Δ in percentage points.
- `audit_trail_sample.csv` — five real EUDR-Risk pixels from the
  Soubré AOI (Hansen 2025 vintage), sampled with seed 42, with full
  per-pixel provenance.

## Reproduction caveats

The Forest Data Partnership cocoa layer is licensed **CC-BY-4.0-NC**
(non-commercial). Commercial users must verify their licensing position
before redistributing derived numbers. The article's figures may
therefore not be redistributed for commercial purposes without that
clearance — see the FDP licence terms.

The treecover2000 threshold of {TREECOVER_THRESHOLD} % is a Hansen-standard
convention but the article's risk-share results are sensitive to it.
See `docs/methodology.md` for the threshold-sensitivity discussion.
"""

(OUT_DIR / "README.md").write_text(README)
print(f"Wrote {OUT_DIR / 'README.md'}")
print("\nSnapshot complete.")
