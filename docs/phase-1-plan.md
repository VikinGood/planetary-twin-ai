# Phase 1 — Scientific Methodology Plan

## Overview

Produce the three scientific deliverables that all later phases depend on:
1. `docs/METHODOLOGY.md` — scoring rules, mission types, tags, confidence, limitations
2. `config/characteristics.json` — machine-readable catalog of the 8 characteristics
3. `config/missions/*.json` — 4 mission presets with reference targets, selected characteristics, and default weights

No application code is written in this phase. All files are documentation and configuration.
Phase 2 (data and architecture) cannot start until these files exist and are approved.

**Key constraint from `AGENTS.md`:** combination rule is a weighted geometric mean over the
SELECTED characteristics only, so a characteristic that scores zero drops the site.

---

## Sub-task 1 — docs/METHODOLOGY.md

### Intent
Write the scientific methodology document that justifies every scoring choice. This is the
single reference that Science Reviewer will check and that Phase 3 (backend) will implement.

### Expected Outcomes
- One markdown file, ≤ 3 pages, covering all items in `docs/prompts/01-methodology.md`.
- Every characteristic has a comparison rule (Absolute / Requirement / Percentile or regime /
  Categorical), units on Earth and on each body, and a justification.
- Two mission types are explained with why their default selections and weights differ.
- Environment-family tag rules are explicit and unambiguous.
- Confidence levels are defined (High / Medium / Low) with criteria.
- Known-analog exclusion buffer is stated (distance in km).
- "What Earth cannot reproduce" section per body.
- Limitations and assumptions section.

### Todo List
- [ ] For each of the 8 characteristics, state: comparison rule, Earth variable(s) + units,
      Moon variable(s) + units, Mars variable(s) + units (or N/A with reason).
  - `topography`: Absolute — slope in degrees at resampled 1 km baseline; roughness as
    standard deviation of elevation within a 5×5 cell window.
  - `geology`: Categorical — GLiM lithology class mapped to Moon/Mars geologic class;
    score = 1 if class matches any target class, 0 otherwise; intermediate values for
    partial matches.
  - `thermal`: Percentile/regime — MODIS LST annual range mapped to Diviner (Moon) or
    TES/MCD (Mars) thermal regime; Earth cannot match absolute temperatures (say so).
  - `aridity`: Requirement — pr/pet (TerraClimate) minimized; score = 1 − (pr/pet) capped
    at 1; Moon/Mars are always maximum aridity.
  - `ice_polar`: Categorical + Absolute — permafrost presence, ice fraction, and latitude
    combined; score = 0 if site is in tropics (> 23.5° from pole).
  - `volcanic_caves`: Categorical — GLiM volcanic classes present + Holocene volcano within
    buffer; lava-tube proxy (no global open catalog: use GLiM volcanic + age proxy); score
    is binary + proximity bonus.
  - `surface_optics`: Absolute — MODIS MCD43A3 broadband albedo (0–1); Moon LROC WAC
    reflectance; Mars TES albedo.
  - `illumination`: Percentile/regime — computed from latitude and terrain shading; for
    permanent base: maximize near-continuous illumination (poles); for landing site: maximize
    illumination during the landing window.
- [ ] State the weighted geometric mean formula explicitly:
      `score_total = prod(score_i ^ w_i)` for all selected i, where `sum(w_i) = 1`.
- [ ] Define two mission types with rationale:
  - Landing site: safe descent (slope, roughness, albedo, illumination); short visit;
    activities: descent imaging, hazard detection, landing pad, first mobility.
  - Permanent base: resources (ice), shelter (caves), thermal endurance, long-duration
    illumination, construction-compatible geology; activities listed in `AGENTS.md`.
- [ ] Define 5 environment-family tag rules (mutually non-exclusive):
  - `desert`: aridity score > 0.75
  - `polar`: |latitude| > 60°
  - `volcanic`: volcanic_caves score > 0 (GLiM volcanic class present)
  - `arid`: aridity score > 0.5 (overlaps desert; finer gradation)
  - `cave`: volcanic_caves score for lava-tube proxy > threshold (define threshold)
- [ ] Define confidence levels:
  - High: data resolution ≤ 1 km, full spatial coverage, rule type Absolute or Requirement.
  - Medium: resolution 1–10 km, minor gaps, Percentile/regime.
  - Low: proxy used, >10 km resolution, or Categorical with uncertain class mapping.
- [ ] State known-analog exclusion buffer: 50 km radius around every site in
      USGS Known Terrestrial Analog Sites, NASA astrobiology field sites,
      ESA Catalogue of Planetary Analogues, and NASA pits and caves analog dataset.
- [ ] Write "What Earth cannot reproduce" per body:
  - Moon: gravity (1/6 g), vacuum, unfiltered solar and cosmic radiation, absolute
    temperatures (40 K–400 K), 14-day light/dark cycle.
  - Mars: gravity (0.38 g), 0.6 % CO₂ atmosphere, UV flux without ozone shield,
    global dust storms, absolute temperatures (−140 °C to +20 °C).
- [ ] Write Limitations section: global resolution 0.25°, no sub-grid variability,
      geology proxy uncertainty, lava-tube proxy unverified, thermal data vintage,
      no seasonal dynamics in score (annual mean/range used).

### Relevant Context
- [`AGENTS.md`](AGENTS.md) — characteristic catalog table with Earth side / body side datasets
- [`docs/prompts/01-methodology.md`](docs/prompts/01-methodology.md) — full deliverable spec

### Status
[ ] pending

---

## Sub-task 2 — config/characteristics.json

### Intent
Produce a machine-readable file that Phase 3 (backend) uses to know the id, name,
comparison rule, units, variables, and body support for each characteristic.
The Science Reviewer will check it against `docs/METHODOLOGY.md`.

### Expected Outcomes
- Valid JSON array of 8 objects, one per characteristic.
- Each object has: `id`, `name`, `description`, `comparison_rule`
  (`absolute` | `requirement` | `percentile_regime` | `categorical`),
  `earth_variables` (array of `{name, source, units}`),
  `moon_variables` (array or `null` with `not_applicable_reason`),
  `mars_variables` (array or `null` with `not_applicable_reason`),
  `score_range` (`[0, 1]`),
  `supported_bodies` (array of `"moon"` and/or `"mars"`).

### Todo List
- [ ] Create `config/` directory.
- [ ] Write `config/characteristics.json` with all 8 entries consistent with the
      rules defined in Sub-task 1.
- [ ] Verify JSON is valid (no trailing commas, all strings quoted).

### Relevant Context
- Sub-task 1 output: `docs/METHODOLOGY.md`
- [`AGENTS.md`](AGENTS.md) lines for characteristic catalog (ids are fixed)

### Status
[ ] pending

---

## Sub-task 3 — config/missions/moon-landing.json

### Intent
Encode the Moon landing-site preset: reference targets, default selected characteristics,
and default weights. Phase 3 uses this to initialize the scoring engine.

### Expected Outcomes
- Valid JSON with: `body: "moon"`, `mission_type: "landing"`,
  `reference_targets` (array with `name`, `lat`, `lon`, `description`),
  `default_characteristics` (array of ids from the catalog),
  `default_weights` (object id → weight, summing to 1.0 over the selection).
- Reference targets: NASA's nine candidate south-polar landing regions from AGENTS.md
  (Malapert Massif, Mons Mouton, Haworth, Slater Plain, and others).
- Default selection: `topography`, `surface_optics`, `thermal`, `illumination`
  (as stated in AGENTS.md mission presets).
- Weights: slope/roughness (topography) highest; illumination second.

### Todo List
- [ ] Create `config/missions/` directory.
- [ ] Look up approximate coordinates for the 9 NASA south-polar landing regions;
      mark any unverified coordinate as `UNVERIFIED`.
- [ ] Write `config/missions/moon-landing.json`.
- [ ] Verify weights sum to exactly 1.0 over the selected characteristics.

### Relevant Context
- [`AGENTS.md`](AGENTS.md) — "Reference targets" and "Mission type presets" sections
- Sub-task 2 output: `config/characteristics.json` (use the fixed ids)

### Status
[ ] pending

---

## Sub-task 4 — config/missions/moon-base.json

### Intent
Encode the Moon permanent-base preset.

### Expected Outcomes
- Same schema as moon-landing.json.
- Reference targets: Shackleton–de Gerlache ridge and Marius Hills pit.
- Default selection: `ice_polar`, `volcanic_caves`, `thermal`, `illumination`,
  `geology`, `topography` (from AGENTS.md).
- Weights: ice (ice_polar) and shelter (volcanic_caves) highest.

### Todo List
- [ ] Look up approximate coordinates for Shackleton–de Gerlache ridge and Marius Hills pit;
      mark unverified.
- [ ] Write `config/missions/moon-base.json`.
- [ ] Verify weights sum to 1.0.

### Relevant Context
- Same as Sub-task 3.

### Status
[ ] pending

---

## Sub-task 5 — config/missions/mars-landing.json

### Intent
Encode the Mars landing-site preset.

### Expected Outcomes
- Same schema; `body: "mars"`, `mission_type: "landing"`.
- Reference targets: Jezero crater, Gale crater, Meridiani Planum (from AGENTS.md).
- Default selection and weights analogous to moon-landing but adapted for Mars
  (no illumination cycle issue; dust cover matters more).

### Todo List
- [ ] Look up approximate coordinates for Jezero, Gale, Meridiani Planum; mark unverified.
- [ ] Adjust default weights for Mars context (surface_optics gets higher weight due to dust).
- [ ] Write `config/missions/mars-landing.json`.
- [ ] Verify weights sum to 1.0.

### Relevant Context
- Same as Sub-task 3.

### Status
[ ] pending

---

## Sub-task 6 — config/missions/mars-base.json

### Intent
Encode the Mars permanent-base preset.

### Expected Outcomes
- Same schema; `body: "mars"`, `mission_type: "base"`.
- Reference targets: Arcadia Planitia (shallow ground ice) and an Arsia Mons cave candidate.
- Default selection: `ice_polar`, `volcanic_caves`, `thermal`, `geology`, `topography`
  (illumination less critical on Mars due to longer day and no PSR equivalent).

### Todo List
- [ ] Look up approximate coordinates for Arcadia Planitia and Arsia Mons; mark unverified.
- [ ] Write `config/missions/mars-base.json`.
- [ ] Verify weights sum to 1.0.

### Relevant Context
- Same as Sub-task 3.

### Status
[ ] pending

---

## Plan Validation Checklist

Before switching to Agent mode to implement:

- [ ] Does every characteristic in METHODOLOGY.md have a comparison rule AND units for all
      applicable bodies?
- [ ] Is the weighted geometric mean formula explicitly stated?
- [ ] Are the 5 environment-family tag thresholds defined with numeric cutoffs?
- [ ] Do the 4 mission presets use only ids from `config/characteristics.json`?
- [ ] Do weights in each preset sum to exactly 1.0?
- [ ] Are all UNVERIFIED coordinates flagged?
- [ ] Does METHODOLOGY.md have a "What Earth cannot reproduce" section for both bodies?
- [ ] Is the known-analog exclusion buffer distance stated?

---

## Appendix A — config/characteristics.json (exact content to write)

```json
[
  {
    "id": "topography",
    "name": "Topography",
    "description": "Slope, roughness, and local relief — primary safety and construction constraint.",
    "comparison_rule": "absolute",
    "landing_hard_cap_slope_deg": 12,
    "landing_hard_cap_source": "NASA Human Landing System terrain hazard threshold (Apollo operations ≤12°)",
    "base_neighborhood_radius_km": 12,
    "earth_variables": [
      { "name": "slope", "source": "Copernicus DEM GLO-30, resampled to 1 km", "units": "degrees" },
      { "name": "roughness", "source": "Copernicus DEM GLO-30 — std-dev of elevation in 3×3 km window", "units": "meters" },
      { "name": "local_relief", "source": "Copernicus DEM GLO-30 — elevation range in 12 km neighborhood", "units": "meters" }
    ],
    "moon_variables": [
      { "name": "slope", "source": "LOLA slope products (polar and global)", "units": "degrees" },
      { "name": "roughness", "source": "LOLA DEM — std-dev of elevation in equivalent window", "units": "meters" },
      { "name": "local_relief", "source": "LOLA DEM — elevation range in 12 km neighborhood", "units": "meters" }
    ],
    "mars_variables": [
      { "name": "slope", "source": "MOLA/MOLA-HRSC blended DEM (200 m)", "units": "degrees" },
      { "name": "roughness", "source": "MOLA/MOLA-HRSC — std-dev of elevation", "units": "meters" },
      { "name": "local_relief", "source": "MOLA/MOLA-HRSC — elevation range in 12 km neighborhood", "units": "meters" }
    ],
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "geology",
    "name": "Geology",
    "description": "Lithology and regolith analog — indicates construction material and surface chemistry.",
    "comparison_rule": "categorical",
    "class_mapping_note": "GLiM class → Moon/Mars geologic class; mapping table maintained in preprocessing scripts.",
    "earth_variables": [
      { "name": "lithology_class", "source": "GLiM global lithological map (PANGAEA)", "units": "categorical" }
    ],
    "moon_variables": [
      { "name": "geologic_unit", "source": "Unified Geologic Map of the Moon, USGS 1:5M", "units": "categorical" }
    ],
    "mars_variables": [
      { "name": "geologic_unit", "source": "USGS Global Geologic Map of Mars, Tanaka et al. 2014", "units": "categorical" }
    ],
    "score_range": [0, 1],
    "score_values": { "primary_match": 1.0, "secondary_match": 0.5, "no_match": 0.0 },
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "thermal",
    "name": "Thermal",
    "description": "Temperature extremes and daily range — hardware stress and thermal management.",
    "comparison_rule": "percentile_regime",
    "comparison_rule_note": "Absolute temperatures cannot be reproduced on Earth. Scoring uses percentile rank of annual mean, range, and diurnal range across all Earth cells.",
    "earth_variables": [
      { "name": "lst_annual_mean", "source": "MODIS MOD11A2 (1 km, 8-day composite)", "units": "°C" },
      { "name": "lst_annual_range", "source": "MODIS MOD11A2 — max minus min monthly mean", "units": "°C" },
      { "name": "lst_diurnal_range", "source": "MODIS MOD11A2 — mean of (day LST − night LST)", "units": "°C" }
    ],
    "moon_variables": [
      { "name": "temp_annual_mean", "source": "Diviner Lunar Radiometer — annual mean", "units": "K" },
      { "name": "temp_annual_range", "source": "Diviner — max minus min", "units": "K" },
      { "name": "temp_diurnal_range", "source": "Diviner — mean diurnal amplitude", "units": "K" }
    ],
    "mars_variables": [
      { "name": "temp_annual_mean", "source": "TES thermal data / Mars Climate Database", "units": "K" },
      { "name": "temp_annual_range", "source": "TES / MCD — max minus min", "units": "K" },
      { "name": "temp_diurnal_range", "source": "TES / MCD — mean diurnal amplitude", "units": "K" }
    ],
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "aridity",
    "name": "Aridity",
    "description": "Aridity and liquid-water absence — REQUIREMENT: score rewards proximity to maximum aridity.",
    "comparison_rule": "requirement",
    "comparison_rule_note": "REQUIREMENT. Moon and Mars are maximally arid. Score = 1 − min(pr/pet, 1). Cells with permanent ice cover score 0.",
    "earth_variables": [
      { "name": "precipitation", "source": "TerraClimate (IDAHO_EPSCOR/TERRACLIMATE), annual sum", "units": "mm/yr" },
      { "name": "pet", "source": "TerraClimate, annual potential evapotranspiration", "units": "mm/yr" },
      { "name": "aridity_index", "source": "Computed: pr / pet", "units": "dimensionless" }
    ],
    "moon_variables": null,
    "moon_not_applicable_reason": "Moon is maximally arid by definition; requirement score always = 1 for Moon targets.",
    "mars_variables": null,
    "mars_not_applicable_reason": "Mars is maximally arid by definition; requirement score always = 1 for Mars targets.",
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "ice_polar",
    "name": "Ice and Polar",
    "description": "Ground ice, permafrost, and polar light regime — in-situ water resource and polar environment.",
    "comparison_rule": "categorical_and_absolute",
    "earth_variables": [
      { "name": "permafrost_index", "source": "IPA Global Permafrost Zonation Index (GZI)", "units": "0–1" },
      { "name": "ice_cover_fraction", "source": "MODIS MCD12Q1 ice/snow land-cover fraction", "units": "0–1" },
      { "name": "latitude", "source": "Cell centroid", "units": "degrees" }
    ],
    "latitude_multipliers": {
      "abs_lat_gt_55": 1.0,
      "abs_lat_23p5_to_55": 0.5,
      "abs_lat_lt_23p5": 0.0
    },
    "moon_variables": [
      { "name": "illumination_fraction", "source": "LOLA polar illumination products — average illumination fraction", "units": "0–1" },
      { "name": "psr_coverage", "source": "LROC permanently shadowed region atlas", "units": "fraction" },
      { "name": "ice_detection", "source": "Lunar ice detection maps (combined LCROSS, LEND, Mini-RF)", "units": "binary/confidence" }
    ],
    "mars_variables": [
      { "name": "ice_depth", "source": "SWIM (Subsurface Water Ice Mapping) dataset", "units": "cm depth to ice" },
      { "name": "ice_confidence", "source": "SWIM — confidence class", "units": "categorical" }
    ],
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "volcanic_caves",
    "name": "Volcanic Terrain and Caves",
    "description": "Volcanic terrain and lava-tube proxy — natural shelter from radiation and thermal extremes.",
    "comparison_rule": "categorical",
    "proxy_confidence": "LOW",
    "proxy_label": "PROXY",
    "proxy_note": "No global open catalog of Earth lava tubes exists. Likelihood is estimated from GLiM vb class and distance to qualifying Holocene volcanoes. Validate against NASA Planetary Pits and Caves Analog Dataset.",
    "proxy_likelihood_rules": {
      "HIGH": "GLiM vb class present AND distance ≤ 50 km to qualifying Holocene volcano",
      "MEDIUM": "GLiM vb class present OR distance ≤ 100 km to qualifying Holocene volcano",
      "LOW": "neither condition met"
    },
    "proxy_scores": { "HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.0 },
    "qualifying_volcano_types": ["Shield volcano", "Lava dome(s)", "Fissure vent(s)", "Volcanic field"],
    "earth_variables": [
      { "name": "lithology_class_vb", "source": "GLiM — basic volcanic class (vb)", "units": "categorical" },
      { "name": "distance_to_holocene_volcano", "source": "Smithsonian GVP Holocene volcanoes, filtered by type", "units": "km" }
    ],
    "moon_variables": [
      { "name": "pit_location", "source": "LROC lunar pit atlas (data.lroc.im-ldi.com)", "units": "point geometry" }
    ],
    "mars_variables": [
      { "name": "cave_candidate", "source": "Mars Global Cave Candidate Catalog (MGC³)", "units": "point geometry" }
    ],
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "surface_optics",
    "name": "Surface Optics",
    "description": "Albedo and dust — affects imaging, thermal balance, and surface operations.",
    "comparison_rule": "absolute",
    "scoring_sigma": 0.05,
    "scoring_note": "Gaussian similarity: score = exp(−(albedo_earth − albedo_target)² / (2 × 0.05²)).",
    "earth_variables": [
      { "name": "broadband_albedo", "source": "MODIS MCD43A3 broadband shortwave albedo, annual mean", "units": "0–1" }
    ],
    "moon_variables": [
      { "name": "reflectance", "source": "LROC WAC reflectance (normalized broadband)", "units": "0–1" }
    ],
    "mars_variables": [
      { "name": "albedo", "source": "TES bolometric albedo", "units": "0–1" },
      { "name": "dust_cover_index", "source": "TES dust cover index", "units": "0–1" }
    ],
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  },
  {
    "id": "illumination",
    "name": "Illumination",
    "description": "Solar elevation regime — LOW SUN analog for lunar south pole; latitude-driven for Mars.",
    "comparison_rule": "percentile_regime",
    "comparison_rule_note": "Scores similarity to the target's solar-elevation regime. The lunar south-pole analog is a LOW SUN regime, not 'maximize illumination'.",
    "earth_variables": [
      { "name": "max_solar_elevation", "source": "Computed from latitude (annual maximum solar elevation angle)", "units": "degrees" },
      { "name": "mean_solar_elevation", "source": "Computed from latitude (annual mean above horizon)", "units": "degrees" },
      { "name": "sun_fraction", "source": "Computed from latitude (fraction of year with sun above horizon)", "units": "0–1" }
    ],
    "moon_variables": [
      { "name": "illumination_fraction", "source": "LOLA polar illumination products — average illumination fraction", "units": "0–1" },
      { "name": "solar_elevation_range", "source": "Derived from orbital geometry at target latitude", "units": "degrees" }
    ],
    "mars_variables": [
      { "name": "illumination_fraction", "source": "Computed from Mars orbital parameters and target latitude", "units": "0–1" }
    ],
    "mars_weight_note": "Illumination gets low default weight for Mars (excluded from mars-landing preset); seasonal dust variation is captured by surface_optics.",
    "score_range": [0, 1],
    "supported_bodies": ["moon", "mars"]
  }
]
```

---

## Appendix B — config/missions/moon-landing.json (exact content to write)

Coordinates for NASA's south-polar landing regions are UNVERIFIED — approximate centers.

```json
{
  "body": "moon",
  "mission_type": "landing",
  "reference_targets": [
    { "name": "Malapert Massif", "lat": -85.9, "lon": -3.5, "description": "High peak near south pole; persistent illumination candidate", "coordinate_status": "UNVERIFIED" },
    { "name": "Mons Mouton", "lat": -84.5, "lon": -20.0, "description": "Plateau south of south pole; multiple NASA candidate regions", "coordinate_status": "UNVERIFIED" },
    { "name": "Haworth Crater rim", "lat": -86.9, "lon": -5.6, "description": "PSR access and illumination ridge", "coordinate_status": "UNVERIFIED" },
    { "name": "Slater Plain", "lat": -88.5, "lon": 55.0, "description": "Relatively flat plain near south pole", "coordinate_status": "UNVERIFIED" },
    { "name": "Nobile Crater rim", "lat": -85.2, "lon": 53.5, "description": "Rim of large crater; ice access candidate", "coordinate_status": "UNVERIFIED" },
    { "name": "Faustini Crater rim", "lat": -87.3, "lon": 77.0, "description": "PSR and illuminated rim candidate", "coordinate_status": "UNVERIFIED" },
    { "name": "Shackleton Crater rim", "lat": -89.9, "lon": 0.0, "description": "South pole crater rim; near-continuous illumination", "coordinate_status": "UNVERIFIED" },
    { "name": "Leibnitz Beta Plateau", "lat": -85.0, "lon": -170.0, "description": "High plateau; illumination and terrain candidate", "coordinate_status": "UNVERIFIED" },
    { "name": "Connecting Ridge Extension", "lat": -88.0, "lon": -100.0, "description": "Ridge between Shackleton and de Gerlache", "coordinate_status": "UNVERIFIED" }
  ],
  "default_characteristics": ["topography", "surface_optics", "thermal", "illumination"],
  "default_weights": {
    "topography": 0.35,
    "illumination": 0.25,
    "surface_optics": 0.20,
    "thermal": 0.20
  },
  "topography_hard_cap_slope_deg": 12,
  "topography_neighborhood_radius_km": 12
}
```

---

## Appendix C — config/missions/moon-base.json (exact content to write)

```json
{
  "body": "moon",
  "mission_type": "base",
  "reference_targets": [
    { "name": "Shackleton–de Gerlache Ridge", "lat": -89.5, "lon": -100.0, "description": "High-illumination ridge between Shackleton and de Gerlache craters; PSR access for ice", "coordinate_status": "UNVERIFIED" },
    { "name": "Marius Hills Pit", "lat": 14.1, "lon": -56.3, "description": "Lunar pit — probable lava-tube skylight; natural shelter candidate", "coordinate_status": "UNVERIFIED" }
  ],
  "default_characteristics": ["ice_polar", "illumination", "volcanic_caves", "thermal", "topography", "geology"],
  "default_weights": {
    "ice_polar": 0.25,
    "illumination": 0.20,
    "volcanic_caves": 0.15,
    "thermal": 0.15,
    "topography": 0.15,
    "geology": 0.10
  },
  "topography_hard_cap_slope_deg": 12,
  "topography_neighborhood_radius_km": 12
}
```

---

## Appendix D — config/missions/mars-landing.json (exact content to write)

Note: illumination excluded from mars-landing preset per 2026-11-14 decision; aridity replaces it.

```json
{
  "body": "mars",
  "mission_type": "landing",
  "reference_targets": [
    { "name": "Jezero Crater", "lat": 18.4, "lon": 77.7, "description": "Ancient river delta and lake bed; Mars 2020 Perseverance landing site", "coordinate_status": "UNVERIFIED" },
    { "name": "Gale Crater", "lat": -5.4, "lon": 137.8, "description": "Layered sedimentary mound; Mars Science Laboratory Curiosity site", "coordinate_status": "UNVERIFIED" },
    { "name": "Meridiani Planum", "lat": -1.9, "lon": -5.5, "description": "Hematite-bearing plains; Mars Exploration Rover Opportunity site", "coordinate_status": "UNVERIFIED" }
  ],
  "default_characteristics": ["topography", "surface_optics", "aridity", "thermal"],
  "default_weights": {
    "topography": 0.40,
    "surface_optics": 0.25,
    "aridity": 0.20,
    "thermal": 0.15
  },
  "topography_hard_cap_slope_deg": 12,
  "topography_neighborhood_radius_km": 12,
  "illumination_excluded_reason": "Mars sol-length day and lack of PSR equivalent make illumination a minor constraint for Martian landing sites. Aridity is more discriminating for Mars analog selection."
}
```

---

## Appendix E — config/missions/mars-base.json (exact content to write)

```json
{
  "body": "mars",
  "mission_type": "base",
  "reference_targets": [
    { "name": "Arcadia Planitia", "lat": 46.7, "lon": -172.0, "description": "Shallow ground ice detected by SWIM; best current Mars ISRU water candidate", "coordinate_status": "UNVERIFIED" },
    { "name": "Arsia Mons Cave Candidate", "lat": -8.3, "lon": -120.5, "description": "Candidate lava-tube pit on Arsia Mons flank (MGC³); natural shelter analog", "coordinate_status": "UNVERIFIED" }
  ],
  "default_characteristics": ["ice_polar", "volcanic_caves", "geology", "thermal", "aridity", "topography"],
  "default_weights": {
    "ice_polar": 0.25,
    "volcanic_caves": 0.20,
    "geology": 0.15,
    "thermal": 0.15,
    "aridity": 0.15,
    "topography": 0.10
  },
  "topography_hard_cap_slope_deg": 12,
  "topography_neighborhood_radius_km": 12
}
```
