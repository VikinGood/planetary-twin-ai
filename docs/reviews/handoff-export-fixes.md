# Handoff — Export Quality Fixes (Pre-Phase 6 Validation)

**Date:** 2026-11-15  
**Branch:** `main`  
**Status:** Completed all 5 export quality fixes from `docs/prompts/fix-export-quality.md`. Re-exported static GeoJSON files and `meta.json`. Pytest (65 tests) and frontend tests (10 tests) all pass. Production build verified.

---

## 1. Summary of Changes Implemented

1. **Bare Surface / Vegetation Filter (§2.9 & `export_static.py`):**
   - Ingested MODIS MCD12Q1 latest populated land cover (combining IGBP Class 16 Barren, Class 15 Snow/Ice, and Class 7 Open Shrublands) to generate `earth_barren_025deg.parquet`.
   - Filtered candidate screening pool to only cells with `barren_sparse_fraction >= 0.5` (or verified known analog sites preserved for validation).
   - Completely eliminated false-positive tropical rainforest candidates (Indonesia, New Caledonia, Congo) matching dark lunar albedo.
   - Documented the rationale in `docs/METHODOLOGY.md` (§2.9).
   - Added `barren_sparse_fraction` to the `values` dictionary in all exported GeoJSON features.

2. **Hard-Cap Sentinels and Non-Zero Scoring Floors:**
   - Scores below `0.01` are now floored to `0.01` (heavily penalized, not dropped) in `scoring.mjs` and `analyst.py`.
   - Hard requirement failures (landing slope > 12°) strictly emit `-1.0`, triggering candidate drop when topography is selected.
   - Formatted all positive continuous scores with `max(round(s, 3), 0.001)` so rounding never creates false zeroes.
   - Categorical mismatches in geology and volcanic caves now score `0.10` (within the 0.05–0.20 range) rather than zero.

3. **Real Administrative Region Hints:**
   - Deleted the obsolete static/mock `REGIONS` array in `export_static.py`.
   - Queried Earth Engine `FAO/GAUL/2015/level1` (`ADM1_NAME`, `ADM0_NAME`) for all unique exported cells, returning real province and country names (e.g. `Canarias, Spain`, `Nenetskiy Okrug, Russian Federation`, `New South Wales, Australia`, `Nunavut, Canada`).
   - Cells with `lat < -60` are consistently labeled `"Antarctica"`.
   - Unmatched/ocean margin points fall back to `"Unnamed area (lat, lon)"`.
   - Cached resolved names to `data/raw/earth/region_hints_cache.json`.

4. **Real Known Terrestrial Analogs (`data/reference/known_analogs.csv`):**
   - Created `data/reference/known_analogs.csv` containing 12 canonical NASA/ESA/USGS planetary analog sites (Haughton Crater, Atacama/Yungay, McMurdo Dry Valleys, HI-SEAS Mauna Kea/Loa, Lanzarote PANGAEA, Rio Tinto, MDRS Utah, Svalbard AMASE, Craters of the Moon, SP Crater Desert RATS, Ries Crater, Kilauea).
   - Documented full citations and URLs in `docs/DATA_SOURCES.md`.
   - Flagged candidate cells within 0.5° Euclidean distance of any site.
   - Exported the complete catalog to `frontend/public/data/meta.json`.

5. **Multi-Target Default Combination Selection:**
   - For every target, selected the top 300 cells ranked by the preset's weighted geometric mean default combination.
   - Selected top 50 cells per individual characteristic per target.
   - Retained all known analog cells for blind validation.
   - Kept deduplicated union per preset strictly under 3.0 MB.

---

## 2. Per-Preset Export Metrics

| Preset | Target Count | Total Features | File Size | Default Score > 0.05 | Antarctica (`lat < -60`) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **moon_landing** | 9 | 758 | **2.26 MB** | 713 | 339 | ✅ Real (< 3.0 MB) |
| **moon_base** | 2 | 1,335 | **2.58 MB** | 1,270 | 398 | ✅ Real (< 3.0 MB) |
| **mars_landing** | 3 | 1,087 | **2.14 MB** | 739 | 273 | ✅ Real (< 3.0 MB) |
| **mars_base** | 2 | 1,180 | **2.25 MB** | 1,129 | 542 | ✅ Real (< 3.0 MB) |

---

## 3. Top 5 Candidates for the First Target of Each Preset

### 1. Moon Landing — Target: `peak_near_cabeus_b`
1. `E_+69.125_+48.875` (+69.125, +48.875) | **Nenetskiy Okrug, Russian Federation** | default score = **0.603**
2. `E_+69.125_+49.125` (+69.125, +49.125) | **Nenetskiy Okrug, Russian Federation** | default score = **0.592**
3. `E_+69.125_+49.375` (+69.125, +49.375) | **Nenetskiy Okrug, Russian Federation** | default score = **0.575**
4. `E_+80.625_+46.875` (+80.625, +46.875) | **Nenetskiy Okrug, Russian Federation** | default score = **0.543**
5. `E_+28.375_-14.125` (+28.375, -14.125) | **Canarias, Spain** | default score = **0.528**

### 2. Moon Base — Target: `shackleton_de_gerlache_ridge`
1. `E_-73.125_+168.625` (-73.125, +168.625) | **Antarctica** | default score = **0.668**
2. `E_-75.875_-116.375` (-75.875, -116.375) | **Antarctica** | default score = **0.635**
3. `E_-75.875_-115.625` (-75.875, -115.625) | **Antarctica** | default score = **0.634**
4. `E_-75.875_-115.375` (-75.875, -115.375) | **Antarctica** | default score = **0.630**
5. `E_-75.875_-115.125` (-75.875, -115.125) | **Antarctica** | default score = **0.629**

### 3. Mars Landing — Target: `jezero_crater`
1. `E_-34.125_+143.375` (-34.125, +143.375) | **New South Wales, Australia** | default score = **0.728**
2. `E_-34.125_+143.625` (-34.125, +143.625) | **New South Wales, Australia** | default score = **0.721**
3. `E_-33.875_+143.125` (-33.875, +143.125) | **New South Wales, Australia** | default score = **0.685**
4. `E_-25.625_+125.375` (-25.625, +125.375) | **Western Australia, Australia** | default score = **0.682**
5. `E_-25.375_+125.375` (-25.375, +125.375) | **Western Australia, Australia** | default score = **0.669**

### 4. Mars Base — Target: `arcadia_planitia`
1. `E_+65.125_-114.875` (+65.125, -114.875) | **Northwest Territories / Territoires du Nord-Ouest, Canada** | default score = **0.578**
2. `E_+65.375_-114.875` (+65.375, -114.875) | **Northwest Territories / Territoires du Nord-Ouest, Canada** | default score = **0.578**
3. `E_+65.125_-114.625` (+65.125, -114.625) | **Northwest Territories / Territoires du Nord-Ouest, Canada** | default score = **0.569**
4. `E_+65.375_-114.625` (+65.375, -114.625) | **Northwest Territories / Territoires du Nord-Ouest, Canada** | default score = **0.567**
5. `E_+65.875_-113.125` (+65.875, -113.125) | **Nunavut, Canada** | default score = **0.521**

---

## 4. Verification & Test Suite

- **Python tests:** `.venv\Scripts\python -m pytest -q` → **65 passed, 0 failures** in 2.87 s.
- **Frontend test suite:** `yarn test` (`node --test src/lib/*.test.mjs`) → **10 passed, 0 failures** in 0.23 s.
- **Frontend build:** `yarn build` (`vite build`) → **Production build succeeded** in 2.94 s.
- **Data integrity:** All 4 preset files are strictly under 3.0 MB. No false zeroes. Hard-cap sentinels correctly drop unviable slope terrain. Bare-surface filter completely cleans out tropical vegetation.

Ready for Claude to execute Phase 6 (Validation).
