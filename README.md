# eudr-risk-pipeline

Companion repository to the article
**"EUDR ohne Bauchgefühl - wie eine auditierbare Risk-Maske pro Pixel funktioniert"**
([mybytes.com/research/eudr-pixel-auditierbarkeit](https://mybytes.com/research/eudr-pixel-auditierbarkeit)).

This repository contains the public-data version of the EUDR risk-mask
methodology that produced the article's Soubré (2.3 %) and
Sefwi-Wiawso (6.0 %) numbers. Every quantitative claim in the article
can be reproduced from the published snapshot in `data/runs/`.

## Where the numbers in the article come from

| Article claim | Source file | Reproduce with |
|---|---|---|
| Soubré, CIV - 2.74 % EUDR-risk share | `data/runs/2026-06-08/area_summary.csv` | `notebooks/00_reproduce_article_numbers.ipynb` |
| Sefwi-Wiawso, GHA - 6.05 % EUDR-risk share | `data/runs/2026-06-08/area_summary.csv` | `notebooks/00_reproduce_article_numbers.ipynb` |
| Five example audit-trail pixels (Plot 3) | `data/runs/2026-06-08/audit_trail_sample.csv` | `notebooks/01_reproduce_audit_trail.ipynb` |
| Two-mask AND operation | `src/masks/` and `src/operations/eudr_risk.py` | unit-level inspection |
| Live-GEE recomputation on any AOI | - | `notebooks/02_live_gee_pipeline.ipynb` (requires GEE auth) |

The article numbers come from the **myBytes pipeline run of 2026-06-08**,
documented in the upstream research project as
`docs/executive_summary_eudr.md`. The CSV snapshots in this repository
are the canonical export of that run for the two AOIs cited in the
article.

## The two-mask operation in one line

```
Mask_A(x)  =  (treecover2000(x) >= 30 %)  AND  (lossyear(x) >= 21)
Mask_B(x)  =  (FDP_cocoa_probability(x) >= 0.50)
EUDR-Risk(x)  =  Mask_A(x)  AND  Mask_B(x)
```

This is generalisable. For other EUDR commodities, replace
`FDP_cocoa_probability` with the appropriate plantation-probability
layer (MapBiomas + Trase for Brazilian soy, Descals et al. 2024 for oil
palm, etc.) and the same auditability applies.

## Repository contents

```
eudr-risk-pipeline/
├── README.md
├── LICENSE                 ← MIT (code) + CC BY 4.0 (content)
├── CITATION.cff
├── requirements.txt
├── docs/
│   └── methodology.md      ← the 2-mask operation in detail, with anchors
├── data/
│   ├── runs/2026-06-08/    ← published snapshot - canonical source of article numbers
│   │   ├── area_summary.csv
│   │   ├── audit_trail_sample.csv
│   │   └── README.md
│   └── aoi/                ← AOI GeoJSON exports
├── src/
│   ├── aois.py             ← AOI registry (CIV + GHA cocoa zones, USDA / ICCO sized)
│   ├── masks/
│   │   ├── hansen_loss_mask.py    ← Mask A
│   │   └── plantation_mask.py     ← Mask B
│   ├── operations/
│   │   └── eudr_risk.py           ← AND + area_summary
│   ├── audit/
│   │   └── audit_trail.py         ← per-pixel provenance records
│   ├── io/
│   │   └── snapshots.py           ← load published run snapshots
│   └── gee/
│       └── conversion_layers.py   ← live Earth Engine path
└── notebooks/
    ├── 00_reproduce_article_numbers.ipynb   ← loads snapshot, asserts article values
    ├── 01_reproduce_audit_trail.ipynb       ← loads audit trail, renders Plot 3
    └── 02_live_gee_pipeline.ipynb           ← recompute on any AOI (needs GEE auth)
```

## Quick start (no GEE access required)

```bash
git clone https://github.com/myBytesResearch/eudr-risk-pipeline.git
cd eudr-risk-pipeline
python -m pip install -r requirements.txt
jupyter notebook notebooks/00_reproduce_article_numbers.ipynb
```

The notebook will load the published snapshot, render Plot 2 of the
article, and assert that the snapshot numbers match the article's
quoted Soubré 2.3 % and Sefwi-Wiawso 6.0 %.

## Live recomputation (requires GEE access)

```bash
python -m pip install earthengine-api geemap
earthengine authenticate
jupyter notebook notebooks/02_live_gee_pipeline.ipynb
```

This path uses the same Hansen and FDP assets the upstream pipeline
uses. Replace the AOI with any entry in `src/aois.py::AOIS` and rerun.

## Data sources

| Layer | GEE asset / source | Resolution | Licence |
|---|---|---|---|
| Forest loss historical, 2024 vintage | `UMD/hansen/global_forest_change_2024_v1_12` (Hansen 2013) | 30 m | open, attribution. Commercial reuse OK. |
| Forest loss historical, 2025 vintage | `UMD/hansen/global_forest_change_2025_v1_13` (Hansen 2013) | 30 m | open, attribution. Commercial reuse OK. |
| Forest loss near-real-time | `projects/radar-wur/raddalert/v1` (Reiche 2021, 2024) | 10 m | open for monitoring; commercial redistribution of alert IDs requires confirmation with Wageningen |
| Cocoa plantation probability | `projects/forestdatapartnership/assets/cocoa/model_2025a` (FDP, building on Kalischek 2023) | 10 m | **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) - non-commercial** |
| Sentinel-2 SR Harmonized (used in figures) | `COPERNICUS/S2_SR_HARMONIZED` (ESA / Copernicus) | 10 m | [Copernicus License](https://sentinel.esa.int/web/sentinel/terms-conditions). Commercial reuse OK with attribution. |
| AOI bounding boxes | `src/aois.py` - USDA FAS PSD 2023 + ICCO 2023 sized + town-centred 33 × 33 km AOIs | varies | own work, CC BY 4.0 |

### License pitfall - read before commercial use

The cocoa-plantation-probability layer of the Forest Data Partnership is
licensed under **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**.
**Concretely this means:**

- You **may** reproduce the methodology and run it on your own input
  data for **internal use, research, monitoring or non-commercial
  publication** with attribution to FDP.
- You **may not** publish, redistribute or sell the derived numerical
  results (such as the Soubré 2.74 % and Sefwi-Wiawso 6.05 % values
  documented here) **commercially** without a separate licensing
  agreement with the Forest Data Partnership.
- The pipeline **code** in this repository, the AOI registry, the
  documentation, the Hansen-derived values and the Sentinel-2 figures
  are **not** affected by the NC clause and can be used commercially
  under the licences above.

If you are a commercial operator or a vendor and want to reuse the
FDP-derived numbers in a paid product, contact the
[Forest Data Partnership](https://www.forestdatapartnership.org/) and
clear a sub-licence before you ship.

## What this repository does NOT contain

- The upstream myBytes proprietary trained LightGBM cocoa-probability
  model (`lgbm_cocoa.joblib`), CV checkpoints (`mask_29NQG_cv.ckpt`),
  and Soubré probability grids. These are sales-level deliverables of
  the myBytes internal pilot and not in scope of the public methodology
  release. The article's published numbers come from the public FDP
  layer, not from the proprietary trained model.
- Operator-side supplier-polygon data. The AOIs here are administrative
  bounding boxes; production deployments take operator-provided polygons
  per VO (EU) 2023/1115 Art. 9.
- Legal advice. The repository computes a methodologically defensible
  geospatial evidence layer that an operator's Due Diligence Statement
  may rest on. Compliance determinations remain a legal matter.

## Attribution

This repository re-issues, for public reproducibility, the EUDR
methodology developed in the internal myBytes research project
(internal codename withheld). The AOI registry and the
two-mask AND operation are direct re-implementations of the
internal pipeline's public-data path. The proprietary trained-model
path is not part of this release.

## Licence

Three distinct licences apply - read each before reusing the material.

- **Code** (everything under `src/`, `notebooks/`, `scripts/`):
  [MIT](LICENSE). Commercial reuse allowed with attribution.
- **Documentation, README, schemas, AOI definitions** (everything
  under `docs/`, this README, `src/aois.py`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Commercial reuse allowed with attribution.
- **FDP-derived numerical values** (the cocoa probability layer
  itself, and every derived number that comes from it - including the
  Soubré and Sefwi-Wiawso risk-share values published here):
  **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)** -
  upstream Forest Data Partnership. **Commercial redistribution
  prohibited without FDP sub-licence**, see the License-pitfall
  section above.

Hansen-derived numbers, Sentinel-2 figures and the methodology itself
are not affected by the FDP NC clause.

## Citation

See `CITATION.cff` for machine-readable metadata.

## Issues, PRs, criticism

The repository is open for critique. Particularly valued: ground-truth
comparisons, threshold-sensitivity analyses on other commodities, RADD
near-real-time reconciliation studies, replication on soy, palm and
rubber.
