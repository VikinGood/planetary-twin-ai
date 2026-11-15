# Scientific Methodology — Planetary Twin AI

Space Logistics team, NASA Space Apps Challenge 2026.
AI use disclosure: this document was drafted with AI assistance and reviewed by the team.

---

## 1. General scoring principle

An analog score measures **similarity to a reference target**, not "more is better".
The only exceptions are **requirement** characteristics (marked below), where the Moon or Mars
sets an extreme condition and the score rewards proximity to that extreme on Earth.

Every score is in [0, 1].  
A score of 1 means maximum similarity to the target.  
A score of 0 means no similarity; a site with any characteristic score of 0 is eliminated.

### Combination formula

Selected characteristics are combined with a **weighted geometric mean**:

```
score_total = product( score_i ^ w_i )   for all selected i
sum( w_i ) = 1  over the selection
```

A characteristic that scores 0 drives the total to 0, eliminating the site.  
Only the user-selected characteristics enter the product; unselected ones are stored but ignored.

---

## 2. Characteristics

### 2.1 topography

**Comparison rule:** Absolute (same units; different scoring curve per mission type).

**Common DEM baseline (all three bodies — TEAM DECISION):**
Slope, roughness, and local relief are computed from each body's DEM **resampled to a
common 1 km grid** before any derivative is calculated. This ensures like-for-like
comparison. Pre-derived LOLA slope products and the MOLA–HRSC blended DEM are NOT used
for scoring; they are listed in DATASETS.md for reference only.

- **Earth:** Copernicus DEM GLO-30 (30 m native) → bilinear resample to 1 km.
- **Moon:** LOLA LDEM gridded DEM (native ~118 m at 16 ppd) → bilinear resample to 1 km.
- **Mars:** MOLA MEGDR (native ~463 m at 1/128°) → bilinear resample to 1 km.

**Earth variables** (derived from Copernicus DEM GLO-30 reprojected to 1 km baseline):
slope (°: mean of 1 km slopes across the 0.25° cell), slope_std (°: standard deviation of 1 km slopes),
roughness (elevation standard deviation in meters), local relief (elevation range max − min within neighborhood).
High mountain cells with significant relief reach mean slopes well above 10° (e.g., Mount Everest ~18.5°,
Mount Aconcagua ~15.8°, compared to Amazon flatlands ~0.8°).

**Moon variables** (derived from 1 km resampled LOLA LDEM):
slope (°), roughness (m), local relief (m) — same algorithms as Earth side.

**Mars variables** (derived from 1 km resampled MOLA MEGDR):
slope (°), roughness (m), local relief (m) — same algorithms as Earth side.

**Gaussian scoring with sigma floor (TEAM ASSUMPTION):**
`score = exp( −(x − μ_target)² / (2 × σ_eff²) )`
where `σ_eff = max(σ_target, σ_floor)` to avoid near-zero scores from homogeneous targets.
σ_floor values (team assumptions — labeled in UI; to be validated in Phase 6):
- slope: **σ_floor = 2°**
- roughness: **σ_floor = 10 m**
- local_relief: **σ_floor = 50 m**

**Landing site scoring:**
- Variables: local slope (°) and roughness (m) at the cell.
- Scoring: Gaussian similarity with σ_floor applied (see above).
- **Hard cap (TEAM ASSUMPTION):** cells with slope > **12°** score 0 for topography.
  Basis: Apollo surface operations used slopes ≤ 12° as a practical safe limit.
  No verifiable mission-specific HLS threshold has been confirmed; labeled as a team
  assumption in preset metadata. Must be validated against mission-specific specs.
- Final: geometric mean of slope score and roughness score.

**Permanent base scoring — two parts, equal weight:**
- (a) Buildable ground: local slope scored identically to landing site (same hard cap applies).
- (b) Surrounding relief: local relief within a **12 km neighborhood radius** computed from
  the DEM; scored by Gaussian similarity with σ_floor = 50 m.
  Rationale for 12 km: a base support perimeter of roughly one day's surface traverse.
- Final: geometric mean of (a) and (b).

### 2.2 geology

**Comparison rule:** Categorical.  
**Earth variables:** GLiM global lithological map (PANGAEA), volcanic classes and
evaporite/sedimentary classes; grain size proxy from class label.  
**Moon variables:** Unified Geologic Map of the Moon (USGS, 1:5 M), unit age and class.  
**Mars variables:** USGS Global Geologic Map of Mars (Tanaka et al. 2014), unit age and class.

**Scoring:** Map each GLiM class to a Moon or Mars geologic analog class. Score = 1.0 if
the GLiM class matches the target's primary class; 0.5 for a secondary match; 0.0 otherwise.
Mapping table is stored in `config/characteristics.json` under `class_mapping`.

### 2.3 thermal

**Comparison rule:** Percentile / regime (Earth cannot match absolute lunar or Martian temperatures — see Section 5).  
**Earth variables:** MODIS Land Surface Temperature (MOD11A2, 1 km, 8-day composite):
annual mean (°C), annual range (°C), mean diurnal range (°C).  
**Moon variables:** Diviner Lunar Radiometer temperatures: annual mean, range, diurnal range at the target.  
**Mars variables:** TES thermal data and Mars Climate Database: annual mean, range, diurnal range.

**Scoring:** Rank-transform each of the three variables across all Earth cells to [0, 1].
Score for each variable = 1 − |percentile_earth − percentile_target|.
Final score = geometric mean of the three variable scores.
This normalizes out the absolute temperature gap.

### 2.4 aridity

**Comparison rule:** Requirement (the Moon and Mars require maximum aridity; labeled REQUIREMENT).  
**Earth variables:** TerraClimate annual precipitation (pr, mm/yr) and annual
potential evapotranspiration (pet, mm/yr); aridity index = pr / pet.  
**Moon/Mars:** Requirement — both are maximally arid; no liquid water.

**Scoring:** `score = max(1 − min(pr/pet, 1), 1 − min(pr / 250 mm, 1))`.  
Score = 1 for hyperarid (pr/pet → 0 or pr = 0 mm/yr); score = 0 for humid (pr/pet ≥ 1 and pr ≥ 250 mm/yr).  
This dual formulation ensures cold/polar deserts (such as Devon Island and the Antarctic plateau)
with precipitation under 250 mm/yr correctly score as arid analogs despite low potential evapotranspiration (PET).
Permanent ice sheets are not zeroed out for aridity (their absence of liquid water is analog-relevant).

### 2.5 ice_polar

**Comparison rule:** Categorical + Absolute.  
**Earth variables:** permafrost extent class (IPA Global Permafrost Zonation Index, 0–1),
ice/snow land-cover fraction (MODIS MCD12Q1 or equivalent), latitude.  
**Moon variables:** LOLA polar illumination products (average illumination fraction),
LROC permanently shadowed regions (PSR) atlas, lunar ice detections.  
**Mars variables:** Shallow water-ice maps (SWIM dataset), subsurface ice depth.

**Scoring:**
- Ground-ice score: `score = permafrost_index`.
- Cells that are permanent ice sheet (`ice_cover_fraction >= 0.5`) score `0.5` and receive the tag `ice sheet`,
  because glacier ice is not ice-cemented regolith.
- `permafrost_index` is marked as proxy when derived from latitude zonation pending local IPA datasets.

### 2.6 volcanic_caves

**Comparison rule:** Categorical — proxy, LOW confidence (labeled PROXY in data and UI).  
**Earth variables (proxy):**
  - GLiM basic volcanic class (vb): indicates basaltic lithology.
  - Distance to nearest Smithsonian GVP Holocene shield volcano, fissure vent,
    or volcanic field (lava domes are excluded as they are built by viscous flows and do not produce tubes).
  - Combined into a categorical likelihood:
    - HIGH: GLiM vb class present AND distance ≤ 50 km to qualifying Holocene volcano.
    - MEDIUM: GLiM vb class present OR distance ≤ 100 km.
    - LOW: neither condition met.
  - Scores: HIGH = 1.0, MEDIUM = 0.5, LOW = 0.0.
  - Confidence: always LOW; labeled "proxy" in data and UI.
  - Validation: compare high-likelihood cells against known lava-tube regions from the
    NASA Planetary Pits and Caves Analog Dataset. If dataset is unavailable at preprocessing
    time, mark `UNVERIFIED` and list canonical examples (Iceland, Hawaii, Lanzarote,
    Undara, Kazumura Cave).

**Moon variables:** LROC lunar pit atlas (pit locations, dimensions).  
**Mars variables:** Mars Global Cave Candidate Catalog (MGC³).

### 2.7 surface_optics

**Comparison rule:** Absolute.  
**Earth variables:** MODIS MCD43A3 broadband shortwave albedo (0–1), annual mean.  
**Moon variables:** LROC WAC reflectance (normalized to same wavelength range if possible).  
**Mars variables:** TES bolometric albedo.

**Scoring:** Gaussian similarity to target's mean albedo with sigma floor:
`score = exp( −(albedo_earth − albedo_target)² / (2 × σ_eff²) )`
where `σ_eff = max(σ_target, 0.05)`.
**σ_floor = 0.05** (absolute albedo units, team assumption) prevents near-zero scores
when the target has a very uniform surface. Adjust σ_target per body from actual spread.

### 2.8 illumination

**Comparison rule:** Percentile / regime — similarity to the target's solar-elevation regime.
The analog value of the lunar south pole is a **LOW SUN** regime: low solar elevation,
long shadows, extended day/night cycles. This is not "maximize illumination".

**Earth solar geometry — formulas (computed analytically from latitude φ, no external dataset):**

For each Earth cell centroid latitude φ and each day d of the year (d = 0…364):
```
declination(d)       = 23.44° × sin(360/365 × (d − 81))      [degrees]
max_solar_elevation  = 90° − |φ| + 23.44°                  (capped at 90°; summer solstice)
cos_h0(d)            = −tan(φ) × tan(declination(d))
  if cos_h0 ≥ 1 → polar night (day_fraction = 0)
  if cos_h0 ≤ −1 → midnight sun (day_fraction = 1)
  else → day_fraction = arccos(cos_h0) / π
mean_solar_elevation = time-weighted mean of arcsin(sin(decl)·sin(φ) + cos(decl)·cos(φ)·sin(h0)/h0)
                       over all days above horizon
longest_polar_night_days = maximum consecutive days where the solar center remains below horizon
longest_polar_day_days   = maximum consecutive days of continuous 24-hour daylight
```

**Variables:**
1. `max_solar_elevation` (°): annual maximum solar elevation angle.
   - Reference target anchor: Lunar south pole (~1.5° to 6.0°); Mars equator (~65°).
   - Terrestrial range: 23.44° (Poles) to 90.0° (Equator).
2. `mean_solar_elevation` (°): time-weighted mean solar elevation while above horizon.
3. `longest_polar_night_days` (days): continuous 24-hour darkness (0 days below polar circle |lat| <= 66.56°; 182 days at pole).
4. `longest_polar_day_days` (days): continuous 24-hour daylight / midnight sun (0 days below polar circle; 182 days at pole).

**Key constraint (what Earth cannot reproduce):**
The Moon's obliquity is ~1.54°, so solar elevation at the lunar south pole (−89.9°) stays
between −1.54° and +1.54° all year — the sun never rises more than ~6° above the horizon even
at the most illuminated ridge. On Earth, the annual maximum solar elevation is `90° − |φ| + 23.44°`,
which reaches a **minimum of 23.44°** at the geographic South Pole. No Earth surface location can
replicate the Moon's near-horizontal sun regime. The percentile/regime comparison captures
relative similarity but this fundamental gap must always be reported in `cannot_reproduce`.

**Scoring:** Rank-transform Earth variables across all cells to [0, 1].
Score = 1 − |percentile_earth − percentile_target| for each variable.
Final score = geometric mean of the variable scores.

### 2.9 Bare Surface Precondition (Vegetation Filter)

**Analogs must be bare surfaces:** Planetary analog environments for the Moon and Mars must possess exposed bedrock, regolith, gravel, sand, or permanent ice substrates, devoid of dense terrestrial vegetation. Forest canopies, crop fields, and dense grasslands introduce complex biogenic optical scattering, organic soil layers, moisture retention, and mechanical cushioning completely absent from planetary surfaces. Notably, dense tropical rainforest canopies (such as in Indonesia, New Caledonia, or the Congo Basin) exhibit low broadband albedos (~0.12–0.15) that unconstrained optical matching would otherwise mistake for dark lunar mare basalt or regolith. To prevent these spurious analog identifications, a strict bare-surface precondition is enforced across all candidate screening: cells must have a `barren_sparse_fraction >= 0.5` derived from MODIS MCD12Q1 land cover (combining IGBP Class 16 Barren, Class 15 Snow/Ice, and Class 7 Open Shrublands). Only cells meeting this threshold (or verified reference analog sites preserved for validation) qualify as terrestrial analogs.

---

## 3. Mission type presets

### 3.1 Landing site

**Goal:** safe descent and short surface access.  
**Activities to test:** descent imaging, hazard detection, landing pad, first mobility.  
**Default characteristics and weight rationale:**

| Characteristic | Moon weight | Mars weight | Rationale |
|---|---|---|---|
| topography | 0.35 | 0.40 | Slope/roughness is the primary landing safety constraint |
| surface_optics | 0.20 | 0.25 | Albedo affects imaging; dust cover on Mars adds hazard |
| illumination | 0.25 | — | Low-sun regime critical for Moon south-pole targets |
| thermal | 0.20 | 0.15 | Temperature extremes affect hardware; less dominant than geometry |
| aridity | — | 0.20 | Mars requires hyperarid; replaces illumination in Mars landing preset |

**Mars landing note:** illumination is excluded from the mars-landing preset because
the sol-length day and lack of PSRs make illumination a minor constraint for Martian
landing sites compared to the Moon. Aridity replaces it.
(AGENTS.md default for mars-landing updated accordingly — 2026-11-14 decision.)

### 3.2 Permanent base

**Goal:** long-duration human operations — resources, shelter, thermal endurance.  
**Activities to test:** habitat construction, ISRU water extraction, shelter, power in
extreme light regimes, long-duration crew operations.  
**Default characteristics and weight rationale:**

| Characteristic | Moon weight | Mars weight | Rationale |
|---|---|---|---|
| ice_polar | 0.25 | 0.25 | In-situ water resource: highest priority for both |
| illumination | 0.20 | — | Continuous power via solar; critical at Moon south pole |
| volcanic_caves | 0.15 | 0.20 | Natural shelter from radiation and thermal extremes |
| thermal | 0.15 | 0.15 | Long-duration thermal load; insulation requirements |
| topography | 0.15 | 0.10 | Buildable terrain; surrounding relief for shelter |
| geology | 0.10 | 0.15 | Regolith analog for construction, ISRU feedstock |
| aridity | — | 0.15 | Mars ISRU context: aridity still important for site characterization |

---

## 4. Environment-family tags

Tags are non-exclusive. A site can carry multiple tags. Tags are computed from the
characteristic scores (not the weighted total).

| Tag | Rule |
|---|---|
| `desert` | aridity score > 0.75 |
| `arid` | aridity score > 0.50 (broader; overlaps desert) |
| `polar` | \|latitude\| > 60° |
| `ice sheet` | ice_cover_fraction ≥ 0.50 (permanent glacier ice) |
| `volcanic` | volcanic_caves score > 0 (GLiM vb class present, any proximity) |
| `cave` | volcanic_caves likelihood = HIGH (score = 1.0, lava-tube proxy threshold met) |

---

## 5. Confidence levels

| Level | Criteria |
|---|---|
| High | Data resolution ≤ 1 km; full spatial coverage; rule type Absolute or Requirement |
| Medium | Resolution 1–10 km; minor gaps (< 20 % of land area); rule type Percentile/regime |
| Low | Proxy used; resolution > 10 km; or Categorical with uncertain class mapping |

Each characteristic score carries its confidence level. The cell-level confidence is the
minimum of the characteristic confidences for the selected set.

---

## 6. Known-analog exclusion and blind validation

**Exclusion:** A 50 km radius buffer is applied around every site in:
- USGS Known Terrestrial Analog Sites (doi:10.5066/P9J72921)
- NASA Astrobiology Field Sites registry
- ESA Catalogue of Planetary Analogues
- NASA Planetary Pits and Caves Analog Dataset

Sites inside any buffer are removed from the "new candidates" output list.
They are retained in a separate validation set.

**Blind validation:** the engine runs on the validation set; we report whether each
known analog appears in the top 5 % of the ranked global output for the relevant
body, mission type, and primary characteristic. This is a qualitative sanity check,
not a statistical test.

---

## 7. What Earth cannot reproduce

### Moon
- Gravity: 1/6 g (1.62 m/s²)
- Atmosphere: vacuum (10⁻¹⁰ Pa); no convection, no acoustic hazards from wind
- Radiation: unfiltered solar energetic particles and galactic cosmic rays
- Absolute temperatures: 40 K in PSRs to ~400 K in equatorial noon; Earth cannot match either extreme
- Day/night cycle: 14 Earth days of continuous daylight followed by 14 days of darkness
- Regolith: electrostatic, sharp-edged (no weathering); no terrestrial equivalent

### Mars
- Gravity: 0.38 g (3.72 m/s²)
- Atmosphere: 0.6 kPa, 95 % CO₂; no breathable air, partial pressure too low for liquid water at surface
- UV/radiation: no ozone layer; UV and ionizing radiation at surface
- Global dust storms: planetary-scale events lasting months with severe irradiance loss
- Absolute temperatures: −140 °C (polar night) to +20 °C (equatorial afternoon); range exceeds any Earth surface
- Perchlorates in regolith: no terrestrial surface-level analog

---

## 8. Limitations and assumptions

1. Global screening resolution is 0.25° (~28 km at equator). Sub-grid variability is not captured.
2. Geology proxy (volcanic_caves) uses a categorical likelihood of LOW confidence; lava-tube presence is unverified at this resolution.
3. Thermal scores use annual statistics; seasonal dynamics and sub-daily extremes are not captured.
4. GLiM lithology class mapping to lunar/Martian geologic classes is expert-assigned and carries inherent uncertainty.
5. MODIS-era data vintage: some tiles may reflect land-use change not representative of natural conditions.
6. Topography hard cap (12°) is a default; it should be validated against mission-specific landing system specs.
7. For cells with no MODIS coverage (e.g., polar night), thermal data quality is degraded; flag with Low confidence.
8. The score combination (weighted geometric mean) treats characteristics as independent, which is an approximation.
9. **Polar Desert Aridity Climatology (McMurdo Dry Valleys):** In extreme coastal Antarctic polar deserts such as the McMurdo Dry Valleys, annual water-equivalent precipitation measured on the ground is < 50 mm/yr. However, global 4 km gridded reanalyses (TerraClimate) blend regional coastal precipitation gradients into narrow valley corridors, reporting modeled precipitation around 100–120 mm/yr and placing McMurdo near the 57th percentile globally for aridity. While the dual P/PET and P/250 mm rule correctly flags it as a polar desert analog, global reanalysis precipitation overestimates actual hyperarid hyper-localized Antarctic valley floors.
