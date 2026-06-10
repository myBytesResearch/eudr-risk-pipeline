# Pipeline run snapshot - 2026-06-08

This directory is the **primary reproducibility snapshot** for the
companion articles
[`eudr-pixel-auditierbarkeit`](https://mybytes.com/research/eudr-pixel-auditierbarkeit)
and
[`eudr-update-2026`](https://mybytes.com/research/eudr-update-2026).
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
- **Threshold τ**: 0.5 on the FDP cocoa probability band.
- **Hansen lossyear cut-off**: ≥ 21 (= 2021 calendar year and later).
- **Tree-cover-2000 threshold**: 30 % (Hansen `treecover2000` band).
- **Run timestamp**: 2026-06-08T00:00:00Z

## Files

- `area_summary.csv` - one row per (AOI × Hansen-vintage) with
  plantation area, EUDR-risk area, risk share, topology annotation,
  and full provenance fields.
- `vintage_drift.csv` - one row per AOI with the 2024-vs-2025 vintage
  comparison and the Δ in percentage points.
- `audit_trail_sample.csv` - five real EUDR-Risk pixels from the
  Soubré AOI (Hansen 2025 vintage), sampled with seed 42, with full
  per-pixel provenance.

## Licence pitfall - read this before publishing the snapshot numbers

The Forest Data Partnership cocoa-probability layer is licensed under
**[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**
(non-commercial). Every risk-share number in `area_summary.csv`,
`vintage_drift.csv` and every per-pixel `plantation_probability` in
`audit_trail_sample.csv` is derived from this NC-licensed layer and
**carries the same NC restriction**:

- Non-commercial use (internal monitoring, research, academic
  publication, blog posts that do not directly monetise these
  numbers): permitted with attribution to FDP.
- Commercial use (paid vendor product, paid report, paid compliance
  service that resells these numbers): **prohibited** without a
  separate sub-licence from the Forest Data Partnership.

The pipeline code (`src/`, `notebooks/`, `scripts/`) is MIT-licensed
and not affected. The Hansen-derived loss numbers, the Sentinel-2
figures and the AOI registry are also not affected.

## Reproduction caveats

The treecover2000 threshold of 30 % is a Hansen-standard
convention but the article's risk-share results are sensitive to it.
See `docs/methodology.md` for the threshold-sensitivity discussion.
