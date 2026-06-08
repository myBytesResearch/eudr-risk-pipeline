# Methodology — the Two-Mask Operation in Detail

## The regulatory anchor

EU Regulation 2023/1115 on deforestation-free products (EUDR) imposes
three core obligations on operators that place relevant commodities on
the EU market:

- **Article 2 (Definitions)** — establishes the cut-off date of
  **31 December 2020**: a product is non-compliant if it was produced
  on land deforested or degraded after that date.
- **Article 9 (Information requirements)** — requires operators to
  collect, store, and provide geolocation data for every plot of land
  where the relevant commodity was produced.
- **Article 10 (Risk assessment)** — requires a documented risk
  assessment per plot, demonstrating that the risk of non-compliance is
  *negligible*.

This methodology operationalises Article 10 at pixel granularity.

## Timeline (current as of June 2026)

The original effective dates of 30 December 2024 (large operators) and
30 June 2025 (SMEs) were postponed by twelve months in late 2024 and
again by twelve months in December 2025. Current effective dates:

| Operator class | Effective date | Sources |
|---|---|---|
| Large operators and traders | **30 December 2026** | EU Parliament 17.12.2025; Council 18.12.2025 |
| SMEs (<50 employees, <€10 M turnover) | **30 June 2027** | same |

The December 2025 targeted revision also concentrated the
Due-Diligence-Statement obligation on the *first placer* of a relevant
product on the EU market. Downstream operators and traders are
administratively relieved, but as the companion article §1.5 argues, the
*commercial* exposure of downstream buyers remains and is in some
respects amplified.

## The two masks

### Mask A — Hansen Loss Mask with implicit forest baseline

Mask A combines TWO Hansen bands. The forest baseline is not optional —
without it, Mask A would count loss of non-forest land cover (savanna,
cropland, water, built-up) which is not what EUDR Art. 2 requires.

```
Mask_A(x) = (Hansen.treecover2000(x) >= 30 %)
            AND
            (Hansen.lossyear(x) >= 21)
```

- The `treecover2000 >= 30 %` clause uses the Hansen-standard convention
  for "was forest at the year-2000 baseline".
- Hansen encodes year `2000+k` as the integer `k`. `lossyear >= 21`
  selects loss events from calendar year 2021 onward.

The default cut-off (`21` = year 2021) matches the EUDR cut-off "after
31 December 2020".

### Mask B — Plantation Probability Mask

For a per-pixel plantation-probability layer `P(x) ∈ [0, 1]` the
condition is

```
Mask_B(x) = (P(x) >= τ)
```

For cocoa in West Africa, the reference plantation layer used by the
upstream internal myBytes pipeline is the **Forest Data Partnership
Cocoa Model 2025a**, hosted on Google Earth Engine at
`projects/forestdatapartnership/assets/cocoa/model_2025a`. The FDP
model is built on the methodology of Kalischek et al. 2023 *Nature Food*
and is maintained as a separately curated Google asset.

**Licence note** — the FDP cocoa layer is licensed **CC-BY-4.0-NC**
(non-commercial). Derived numerical values may not be redistributed for
commercial purposes without separate licensing arrangements. The
methodology and the code are freely usable; only the *layer values*
carry the NC restriction.

Analogous layers exist for the other six EUDR commodities — MapBiomas
plus Trase for Brazilian soy, Descals et al. 2024 for oil palm, FAO
Forest Resources Assessment connections for timber and rubber. See the
README source table.

The threshold `τ = 0.50` is the default used by the upstream internal
pipeline. Production deployments must:

1. Calibrate `τ` against an independent ground-truth set following
   Olofsson et al. 2014 *RSE* good practice for area estimation.
2. Publish a threshold-sensitivity analysis showing how the EUDR-risk
   share changes across a range of `τ`.
3. Document the chosen `τ` in the per-pixel audit trail.

### The AND operation

```
EUDR-Risk(x) = A(x) ∧ B(x)
```

That is the entire operation. The methodological substance is in the
per-pixel auditability that follows from it, not in the operation
itself.

## The audit trail

`src/audit/audit_trail.py` emits one row per EUDR-risk pixel with the
following fields:

| Field | Source |
|---|---|
| `lat`, `lon` | computed from pixel `(row, col)` via the source raster's affine transform |
| `lossyear` | Hansen GFC raw value at this pixel |
| `gfc_tile_id`, `gfc_version` | Hansen tile and dataset version |
| `plantation_probability` | plantation-layer raw value at this pixel |
| `plantation_layer_id`, `plantation_layer_version` | layer identifier and dataset version stamp |
| `threshold_tau` | the threshold used at evaluation time |
| `radd_alert_id` | optional — RADD alert identifier if a near-real-time alert overlaps |

Every field references a public dataset and the value can be
reconstructed by an external auditor by querying the same dataset.

## Limitations

The article §4 lists the substantive limitations in plain language. The
methodological short list:

1. **Sensor-limitation cloud cover.** Optical layers degrade under
   persistent cloud, which is exactly the climate of the West African
   cocoa belt. SAR-based layers partially mitigate but introduce
   speckle.
2. **Threshold sensitivity.** A `τ` change of 0.05 can swing the risk
   share materially. Quote ranges, not point estimates.
3. **Smallholder-polygon granularity.** Aggregating risk over a
   region-of-interest is a different statistical object than aggregating
   over a supplier polygon. Both are valid; their meanings differ.
4. **Forest vs plantation classification at forest edges.** False
   positives concentrate near plantation–forest transitions; an IoU
   audit at the edge cohort is mandatory.
5. **Temporal mismatch between Hansen annual and RADD weekly.** Use
   RADD for near-real-time, Hansen for the annual historical baseline,
   and document the reconciliation rule.

## References

- Hansen et al. 2013 — "High-Resolution Global Maps of 21st-Century
  Forest Cover Change" *Science* 342 (6160), 850–853.
- Kalischek et al. 2023 — "Cocoa plantations are associated with
  deforestation in West Africa" *Nature Food* 4, 384–393.
- Reiche et al. 2021 — "Forest disturbance alerts for the Congo Basin
  using Sentinel-1" *Environmental Research Letters* 16.
- Reiche et al. 2024 — RADD documentation and validation updates,
  *Remote Sensing of Environment*.
- Olofsson et al. 2014 — "Good practices for estimating area and
  assessing accuracy of land change" *RSE* 148, 42–57.
- Stehman 2014 — "Estimating area and map accuracy for stratified random
  sampling" *RSE* 144, 159–169.
- Curtis et al. 2018 — "Classifying drivers of global forest loss"
  *Science* 361 (6407), 1108–1111.
- Verordnung (EU) 2023/1115 — Amtsblatt der Europäischen Union L 150/206,
  9 June 2023.
- EU Parliament press release 17.12.2025 — second targeted revision.
- Council of the EU 18.12.2025 — formal adoption of targeted revision.
