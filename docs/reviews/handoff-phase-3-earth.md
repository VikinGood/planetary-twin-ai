# Handoff — Phase 3 (Earth Data & Planetary Targets)

**Date:** 2026-11-14 / 2026-11-15  
**Branch:** `main`  
**Status:** Completed Phase 3 Earth data preprocessing, land-masking, multi-characteristic assembly, and targets assembly with real Earth percentile ranking.

---

## 1. Summary of Delivered Work

1. **Global Land Masking (Server-Side EE):**
   - Implemented [scripts/earth/00_land_mask.py](file:///c:/dev/planetary-twin-ai/scripts/earth/00_land_mask.py) using `MODIS/061/MCD12Q1` (classes 1–16 = land, 17 = water).
   - Reduced on server to 0.25° grid with bilinear resampling.
   - Screened all 1,036,800 global cells: **337,611 land cells kept** (`land_fraction >= 0.5`), removing 699,189 ocean cells (32.56% of Earth surface retained).
2. **Earth Engine Preprocessing & Download:**
   - Designed [scripts/earth/ee_utils.py](file:///c:/dev/planetary-twin-ai/scripts/earth/ee_utils.py) to perform all spatial reductions and filtering on the Google Earth Engine server.
   - Downloaded strictly final 0.25° grid GeoTIFFs ($1440 \times 720$), preventing uncompressed raw raster transfer to local disk.
   - Executed and validated all characteristics first against the fixture region (lat $-30^\circ$ to $-20^\circ$, lon $-70^\circ$ to $-60^\circ$), confirming physically plausible values before global processing.
   - Processed:
     - `01_topography.py`: Copernicus DEM GLO-30 (`slope`, `slope_std`, `roughness`, `local_relief`).
     - `02_thermal.py`: MODIS MOD11A2 (`lst_annual_mean`, `lst_annual_range`, `lst_diurnal_range` and percentiles).
     - `03_surface_optics.py`: MODIS MCD43A3 shortwave albedo (`broadband_albedo`).
     - `04_aridity.py`: TerraClimate (`precipitation`, `pet`, `aridity_index`, `aridity_score`).
     - `07_ice_polar.py`: MODIS MCD12Q1 permanent snow/ice (`ice_cover_fraction`, `latitude_multiplier`, `permafrost_index`, `ice_polar_score`).
3. **Geology & Volcanic Caves Handled as "Data Pending":**
   - Verified that neither GLiM nor Smithsonian GVP are available in standard Earth Engine collections.
   - In accordance with phase rules, both [scripts/earth/05_geology.py](file:///c:/dev/planetary-twin-ai/scripts/earth/05_geology.py) and [scripts/earth/06_volcanic_caves.py](file:///c:/dev/planetary-twin-ai/scripts/earth/06_volcanic_caves.py) generate valid parquets marked `DATA PENDING` without blocking execution.
4. **Illumination Metric Overhaul:**
   - Replaced uninformative constant `sun_fraction` (~0.50 globally) with physically discriminating polar metrics: `longest_polar_night_days` and `longest_polar_day_days` in [scripts/earth/08_illumination.py](file:///c:/dev/planetary-twin-ai/scripts/earth/08_illumination.py).
   - Computed percentile ranks across all 337,611 land cells.
5. **Planetary Targets Update:**
   - Injected real percentile ranks computed against the 337,611 Earth land cell distributions in [data/processed/targets.json](file:///c:/dev/planetary-twin-ai/data/processed/targets.json).
   - Added `"value_origin": "literature"` to all 16 planetary targets.
   - All numeric values cite specific scientific literature.
6. **Full Assembly & Pytest:**
   - Assembled master [data/processed/earth_cells_025deg.parquet](file:///c:/dev/planetary-twin-ai/data/processed/earth_cells_025deg.parquet) containing **337,611 rows** and **67 columns**, with **0 nulls**.
   - `pytest -q`: **51 passed, 0 failures** in 1.67 s.

---

## 2. Execution Time per Preprocessing Script

| Step / Script | Input Source | Runtime | Output File | Status |
| --- | --- | :---: | --- | :---: |
| `00_land_mask.py` | `MODIS/061/MCD12Q1` (EE) | ~0.5 min | `earth_land_mask_025deg.parquet` | ✅ Complete |
| `01_topography.py` | `COPERNICUS/DEM/GLO30_2024_1` (EE) | ~1.0 min | `earth_topography_025deg.parquet` | ✅ Complete |
| `02_thermal.py` | `MODIS/061/MOD11A2` (EE) | ~0.5 min | `earth_thermal_025deg.parquet` | ✅ Complete |
| `03_surface_optics.py`| `MODIS/061/MCD43A3` (EE) | ~0.8 min | `earth_surface_optics_025deg.parquet` | ✅ Complete |
| `04_aridity.py` | `IDAHO_EPSCOR/TERRACLIMATE` (EE) | ~0.5 min | `earth_aridity_025deg.parquet` | ✅ Complete |
| `05_geology.py` | GLiM (Offline pending) | ~0.1 min | `earth_geology_025deg.parquet` | ⚠️ Data pending |
| `06_volcanic_caves.py`| Smithsonian GVP (Offline pending) | ~0.1 min | `earth_volcanic_caves_025deg.parquet` | ⚠️ Data pending |
| `07_ice_polar.py` | `MODIS/061/MCD12Q1` (EE) | ~0.3 min | `earth_ice_polar_025deg.parquet` | ✅ Complete (EE part) |
| `08_illumination.py` | Analytical solar geometry (NumPy) | ~0.3 min | `earth_illumination_025deg.parquet` | ✅ Complete |
| `00_assemble.py` | Parquet multi-merge & tagging | ~0.3 min | `earth_cells_025deg.parquet` | ✅ Complete |
| `00_assemble_targets.py`| Literature + Earth distributions | ~0.7 min | `targets.json` | ✅ Complete |
| **Total Pipeline** | | **~5.1 min** | | |

---

## 3. Data Audit: `data/processed/earth_cells_025deg.parquet`

- **Total rows:** 337,611
- **Total columns:** 67
- **Null count:** **0 across all 67 columns**

### Selected Metric Ranges (Land Cells Only)

| Characteristic | Variable / Column | Nulls | Min | Max | Units / Meaning |
| --- | --- | :---: | :---: | :---: | --- |
| **Land Mask** | `land_fraction` | 0 | 0.5000 | 1.0000 | Fraction of cell covered by land |
| **Topography** | `slope` | 0 | 0.0000 | 5.0711 | Mean terrain slope (degrees) |
| | `slope_std` | 0 | 0.0000 | 1.9456 | Standard deviation of slope (degrees) |
| | `roughness` | 0 | 0.0000 | 2040.6237 | Elevation standard deviation (meters) |
| | `local_relief` | 0 | 0.0000 | 5758.8281 | Elevation range max - min (meters) |
| **Thermal** | `lst_annual_mean` | 0 | -59.6140 | 47.3290 | Mean annual land surface temp (°C) |
| | `lst_annual_range` | 0 | 5.1975 | 82.9500 | Annual temperature range (°C) |
| | `lst_diurnal_range` | 0 | -0.1383 | 33.8017 | Mean diurnal temperature range (°C) |
| **Surface Optics**| `broadband_albedo` | 0 | 0.0100 | 0.8531 | Shortwave broadband surface albedo (0–1) |
| **Aridity** | `precipitation` | 0 | 0.0000 | 5859.2939 | Mean annual precipitation (mm/yr) |
| | `pet` | 0 | 0.1000 | 3048.5588 | Potential evapotranspiration (mm/yr) |
| | `aridity_index` | 0 | 0.0000 | 2.0000 | Ratio `pr / pet` (capped at 2.0) |
| | `aridity_score` | 0 | 0.0000 | 1.0000 | Requirement score: `1 - min(index, 1)` |
| **Ice & Polar** | `ice_cover_fraction`| 0 | 0.0000 | 1.0000 | Permanent snow/ice fraction (0–1) |
| | `ice_polar_score` | 0 | 0.0000 | 1.0000 | $\sqrt{\text{permafrost} \times \text{ice cover}}$ |
| **Illumination** | `max_solar_elevation`| 0 | 23.5650 | 90.0000 | Annual maximum solar elevation (degrees) |
| | `longest_polar_night_days`| 0 | 0.0000 | 182.0000 | Continuous 24h darkness (days/yr) |
| | `longest_polar_day_days` | 0 | 0.0000 | 182.0000 | Continuous 24h daylight (days/yr) |
| **Tags** | `environment_tags` | 0 | — | — | List of strings: desert, arid, polar, etc. |

---

## 4. Proposed Modification to `docs/METHODOLOGY.md` (§2.8 Illumination)

As observed during execution, `sun_fraction` (the annual fraction of hours where the Sun is above the horizon) evaluates to $\approx 0.50$ universally across Earth's spherical geometry because day and night balance annually at every latitude. Consequently, `sun_fraction` provides no discriminative power.

### Proposed Amendment to `docs/METHODOLOGY.md` §2.8:

```markdown
### 2.8 Characteristic: illumination

**Variables:**
1. `max_solar_elevation` (°): annual maximum solar elevation angle.
   - Reference target anchor: Lunar south pole (~1.5° to 6.0°); Mars equator (~65°).
   - Terrestrial range: 23.44° (Poles) to 90.0° (Equator).
2. `mean_solar_elevation` (°): time-weighted mean solar elevation while above horizon.
3. `longest_polar_night_days` (days): maximum consecutive days where the solar center
   remains below the horizon (24-hour continuous darkness).
   - Below polar circles (|lat| <= 66.56°): 0 days.
   - At polar circles (|lat| = 66.56°): 1 day.
   - At poles (|lat| = 90.0°): 182 days.
4. `longest_polar_day_days` (days): maximum consecutive days of continuous 24-hour daylight
   (midnight sun regime).
   - Below polar circles (|lat| <= 66.56°): 0 days.
   - At poles (|lat| = 90.0°): 182 days.

**Scoring formula:**
Percentile regime matching against reference planetary target parameters.
For landing sites seeking polar illumination stability, `longest_polar_day_days` and
`max_solar_elevation` percentile matching ranks high-latitude analog environments
(Antarctica, Greenland, Svalbard) as highest-similarity terrestrial analogs.
```

---

## 5. What Remains Pending

1. **Offline Datasets:**
   - `GLiM` raster for lithology class assignment (`05_geology.py`).
   - `Smithsonian GVP` Holocene volcano catalog CSV for lava-tube likelihood scoring (`06_volcanic_caves.py`).
   - `IPA GZI` GeoTIFF for exact permafrost depth/zonation index.
   - Currently, these characteristics are functional with fallback/proxy defaults and explicitly flagged as `DATA PENDING` in metadata.
2. **Known Analogs Ingestion:**
   - Analog sites list (USGS/ESA/NASA) to populate `known_analog_within_km`.
3. **Frontend & AI Analyst:**
   - Backend API and scoring engine are tested and verified with real Earth data. Ready for Phase 4 (AI Analyst) and Phase 5 (Frontend).
