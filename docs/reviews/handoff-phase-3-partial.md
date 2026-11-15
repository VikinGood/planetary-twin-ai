# Handoff — Phase 3 (Partial / Stocktaking)

**Date:** 2026-11-14 / 2026-11-15  
**Branch:** `main`  
**Latest commit:** `ec72983` (`phase 3b/3c: targets, scoring engine, API (from previous agent)`)  
**Status:** Phase 3b/3c code committed and pushed; Phase 3a Earth pipeline partially assembled (illumination only, real Earth Engine and raw data pipelines pending).

---

## 1. Earth Cells Parquet Audit (`data/processed/earth_cells_025deg.parquet`)

### Overview
- **Row count:** 1,036,800 rows (720 latitude bands $\times$ 1,440 longitude bands at 0.25° resolution).
- **Ocean cells included:** **YES**. The file contains the entire global planetary grid ($[-89.875^\circ, +89.875^\circ] \times [-179.875^\circ, +179.875^\circ]$). Land masking has not been applied yet; `land_fraction` is currently set to placeholder `1.0` everywhere.
- **Column count:** 12 columns.

### Column Summary, Null Counts, and Value Ranges

| Column | Data Type | Null Count | Min | Max | Notes / Sample |
| --- | --- | :---: | :---: | :---: | --- |
| `cell_id` | string | 0 | — | — | e.g. `E_-89.875_-179.875` |
| `lat_center` | float64 | 0 | -89.875 | +89.875 | 0.25° grid center |
| `lon_center` | float64 | 0 | -179.875 | +179.875 | 0.25° grid center |
| `land_fraction` | float64 | 0 | 1.0 | 1.0 | Placeholder (oceans included) |
| `max_solar_elevation` | float64 | 0 | 23.565° | 90.000° | Analytically derived from latitude |
| `mean_solar_elevation` | float64 | 0 | 14.922° | 37.620° | Analytically derived from latitude |
| `sun_fraction` | float64 | 0 | ~0.500 | ~0.500 | Analytically derived (~0.50 everywhere on Earth annually) |
| `illumination_confidence` | string | 0 | — | — | Fixed: `high` |
| `illumination_proxy` | bool | 0 | False | False | Fixed: `False` |
| `illumination_source` | string | 0 | — | — | `Computed analytically from latitude (METHODOLOGY §2.8)...` |
| `environment_tags` | object (list) | 0 | — | — | Contains `['polar']` for $\|lat\| > 60^\circ$, `[]` elsewhere |
| `known_analog_within_km` | float64 | 0 | -1.0 | -1.0 | Placeholder (`-1.0` indicates uncomputed / no catalog ingested) |

> [!NOTE]
> The remaining 7 characteristics (`topography`, `thermal`, `surface_optics`, `aridity`, `geology`, `volcanic_caves`, `ice_polar`) are completely missing from `earth_cells_025deg.parquet` because only `08_illumination.py` has run.

---

## 2. Execution Audit of `scripts/earth/`

### Script Status Summary

| Script | Characteristic | Depends on EE? | Status | Evidence |
| --- | --- | :---: | :---: | --- |
| `00_assemble.py` | Assembler | No | **HAS RUN** (partial) | `earth_cells_025deg.parquet` exists, containing only illumination and metadata columns. |
| `01_topography.py` | Topography | Yes (Copernicus DEM) | **NOT RUN** | `earth_topography_025deg.parquet` does not exist in `data/processed/`. |
| `02_thermal.py` | Thermal | Yes (MODIS LST) | **NOT RUN** | `earth_thermal_025deg.parquet` does not exist in `data/processed/`. |
| `03_surface_optics.py` | Surface Optics | Yes (MODIS MCD43A3) | **NOT RUN** | `earth_surface_optics_025deg.parquet` does not exist in `data/processed/`. |
| `04_aridity.py` | Aridity | Yes (TerraClimate pr/pet) | **NOT RUN** | `earth_aridity_025deg.parquet` does not exist in `data/processed/`. |
| `05_geology.py` | Geology | No (Local GLiM raster) | **NOT RUN** | `earth_geology_025deg.parquet` does not exist; `data/raw/earth/glim/` is empty. |
| `06_volcanic_caves.py`| Volcanic Caves | No (Local GVP CSV) | **NOT RUN** | `earth_volcanic_caves_025deg.parquet` does not exist; `data/raw/earth/gvp/` is empty. |
| `07_ice_polar.py` | Ice & Polar | Yes (MODIS Snow + IPA GZI) | **NOT RUN** | `earth_ice_polar_025deg.parquet` does not exist; `data/raw/earth/ipa_gzi/` is empty. |
| `08_illumination.py` | Illumination | No (NumPy analytical) | **HAS RUN** | `earth_illumination_025deg.parquet` exists (5.0 MB, 1,036,800 rows). |

### Key Evidence
1. **Absence of per-characteristic parquet files:** Only `earth_illumination_025deg.parquet` is present in `data/processed/`.
2. **Empty raw data directories:** `data/raw/earth/glim/`, `data/raw/earth/gvp/`, and `data/raw/earth/ipa_gzi/` exist as empty folders.
3. **No Earth Engine reduction exports:** No script in `scripts/earth/` has executed against Google Earth Engine yet.

---

## 3. Planetary Targets Audit (`data/processed/targets.json`)

`data/processed/targets.json` contains **16 targets** (11 Moon, 5 Mars).

### Origin of Target Values
- **Extraction method:** All values were **TYPED FROM PUBLISHED LITERATURE**, not extracted from raw Moon or Mars raster/vector datasets directly.
- **Verification status:** Every single target has `"coordinate_status": "UNVERIFIED"` and every numeric parameter is flagged as `UNVERIFIED`.
- **Illumination percentiles:** Computed against the real 1,036,800 Earth cell distribution using `earth_cells_025deg.parquet`.
- **Thermal percentiles:** Marked `APPROXIMATE` (estimated from literature ranges) because Earth thermal raster data has not been processed yet.

### Target Catalog Details

| Target ID | Name | Body | Mission Type | Literature Sources Cited |
| --- | --- | :---: | :---: | --- |
| `peak_near_cabeus_b` | Peak near Cabeus B | Moon | Landing | LOLA (Noda 2008, Mazarico 2011, Paige 2010), Diviner (Paige 2010, Hayne 2015), LROC WAC (Scholten 2012), USGS Geologic Map (Fortezzo 2020), LEND (Mitrofanov 2010). |
| `haworth` | Haworth | Moon | Landing | LOLA (Noda 2008, Mazarico 2011), Diviner (Paige 2010, Hayne 2015), LROC WAC, USGS Geologic Map, LEND. |
| `malapert_massif` | Malapert Massif | Moon | Landing | LOLA (Mazarico 2011, Noda 2008), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `mons_mouton_plateau` | Mons Mouton Plateau | Moon | Landing | LOLA (Mazarico 2011), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `mons_mouton` | Mons Mouton | Moon | Landing | LOLA (Mazarico 2011), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `nobile_rim_1` | Nobile Rim 1 | Moon | Landing | LOLA (Mazarico 2011), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `nobile_rim_2` | Nobile Rim 2 | Moon | Landing | LOLA (Mazarico 2011), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `de_gerlache_rim_2` | de Gerlache Rim 2 | Moon | Landing | LOLA (Mazarico 2011), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `slater_plain` | Slater Plain | Moon | Landing | LOLA (Mazarico 2011), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `shackleton_de_gerlache_ridge` | Shackleton–de Gerlache Connecting Ridge | Moon | Base | LOLA (Mazarico 2011, Speyerer & Robinson 2013), Diviner (Paige 2010), LROC WAC, USGS Geologic Map, LEND. |
| `marius_hills_pit` | Marius Hills Pit | Moon | Base | LROC NAC DEM (Wagner & Robinson 2014), Diviner DLRE, LROC WAC, USGS Geologic Map, Haruyama et al. 2009 pit catalog. |
| `jezero_crater` | Jezero Crater | Mars | Landing | MOLA MEGDR (Smith 2001, Grotzinger 2012), TES / MCD (Forget 2006, Haberle 2001), TES Albedo (Christensen 2001, Ruff 2002), USGS Global Geologic Map (Tanaka 2014). |
| `gale_crater` | Gale Crater | Mars | Landing | MOLA MEGDR (Smith 2001, Golombek 2012), TES / MCD (Forget 2006), TES Albedo, USGS Global Geologic Map (Tanaka 2014). |
| `meridiani_planum` | Meridiani Planum | Mars | Landing | MOLA MEGDR (Smith 2001, Golombek 2003), TES / MCD (Forget 2006), TES Albedo, USGS Global Geologic Map (Tanaka 2014). |
| `arcadia_planitia` | Arcadia Planitia | Mars | Base | MOLA MEGDR (Smith 2001), TES / MCD (Forget 2006), TES Albedo, USGS Global Geologic Map (Tanaka 2014), Subsurface Water Ice Mapping (SWIM v3, Morgan 2021). |
| `arsia_mons_cave_candidate` | Arsia Mons Cave Candidate | Mars | Base | MOLA MEGDR (Smith 2001), TES / MCD (Forget 2006), TES Albedo, USGS Global Geologic Map, Mars Global Cave Candidate Catalog (MGC³, Cushing 2007, Wyrick 2004). |

---

## 4. Test Results and Environmental Findings

### Test Results
- **Command:** `.venv\Scripts\python -m pytest -q`
- **Result:** `51 passed, 1 warning in 1.96s` (1 warning: `StarletteDeprecationWarning` regarding `httpx` in `starlette.testclient`).
- **Breakdown:**
  - `backend/tests/test_scoring.py`: 36 unit tests passed. Covers Gaussian scoring, hard slope cutoff (>12° gives 0), aridity scoring, weighted geometric mean, illumination percentiles, and multi-characteristic cell scoring.
  - `backend/tests/test_api.py`: 15 integration tests passed. Covers `/characteristics`, `/missions`, and `/candidates` endpoints.

### Environmental Finding: Windows Sandbox vs. Loopback Sockets
- When tests are run in **Standard Sandbox Mode**, `test_scoring.py` runs in 1.35 seconds, but `test_api.py` hangs indefinitely.
- **Root cause:** `FastAPI`'s `TestClient` uses `anyio.from_thread.start_blocking_portal()`, which under Windows triggers `asyncio.proactor_events._make_self_pipe` $\to$ `_fallback_socketpair` $\to$ `socket.accept()`. The Standard Sandbox boundary isolates network loopback sockets, blocking socketpair handshake.
- **Resolution:** Commands executing `TestClient` or async socket-based test runners require unsandboxed execution (`BypassSandbox: true`).

---

## 5. Open Doubts and Next Steps

1. **Earth Engine Pipeline (Phase 3a completion):**
   - Has the team authenticated Earth Engine via `earthengine authenticate` and set `EE_PROJECT` in `.env`?
   - Steps `01_topography.py`, `02_thermal.py`, `03_surface_optics.py`, `04_aridity.py`, and `07_ice_polar.py` must run to produce real Earth raster metrics.
2. **Offline Raw Data Ingestion:**
   - GLiM shapefile/raster must be placed into `data/raw/earth/glim/` for `05_geology.py`.
   - GVP Holocene volcano catalog CSV must be placed into `data/raw/earth/gvp/` for `06_volcanic_caves.py`.
   - IPA Ground Ice permafrost GeoTIFF must be placed into `data/raw/earth/ipa_gzi/` for `07_ice_polar.py`.
3. **Ocean Masking:**
   - Global grid currently contains all 1,036,800 marine and terrestrial cells. Applying landmasking will reduce grid size to ~250,000–300,000 cells, drastically speeding up queries and GeoJSON export.
4. **Known Analogs Ingestion:**
   - `known_analog_within_km` is currently hardcoded to `-1.0`. Candidate analogs (USGS, ESA, NASA) must be ingested to enable blind validation and analog proximity calculations.
5. **Phase 4 (AI Analyst) & Phase 5 (Frontend):**
   - The FastAPI backend, scoring engine, preset missions, and literature targets are in place and ready for client consumption.
