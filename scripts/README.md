# scripts/README.md — Earth Preprocessing Scripts

Planetary Twin AI — Space Logistics team, NASA Space Apps Challenge 2026.

This directory contains the Earth-side preprocessing scripts that produce
`data/processed/earth_cells_025deg.parquet` — the global 0.25° land-cell table
used by the backend scoring engine.

---

## Prerequisites

### 1. Python virtual environment

All scripts run inside `.venv` (project root). The venv is **already created**.
Install dependencies once:

```bash
# From the project root
.venv\Scripts\pip install -r backend\requirements.txt   # Windows
# or
.venv/bin/pip install -r backend/requirements.txt       # macOS/Linux
```

### 2. Google Earth Engine (EE) authentication

Scripts 01–04 and 07 (EE-based) require a GEE account and authentication.
Authenticate once per machine:

```bash
.venv\Scripts\earthengine authenticate
```

Set the EE project ID in `.env` (copy from `.env.example` if needed):

```
EE_PROJECT=your-earth-engine-cloud-project-id
```

The project used by this team is `space-logistics-ee`.

### 3. Raw data files (manual download required)

Three datasets are NOT in Google Earth Engine and must be downloaded manually.
Scripts will **exit with code 1** and print the download URL if a file is missing.

| Dataset | Download URL | Place in |
|---------|-------------|----------|
| GLiM lithological map (GeoTIFF) | https://doi.pangaea.de/10.1594/PANGAEA.788537 | `data/raw/earth/glim/` |
| Smithsonian GVP Holocene catalog (CSV) | https://volcano.si.edu/database/search_volcano_excel_select.cfm | `data/raw/earth/gvp/` |
| IPA Global Permafrost Zonation Index GeoTIFF | https://doi.pangaea.de/10.1594/PANGAEA.783900 | `data/raw/earth/ipa_gzi/` |

**PANGAEA note:** Direct download works without an account for most datasets.
Free registration (pangaea.de) is sufficient if a login is required.

**GVP note:** On the GVP download page, choose "Export to Excel/CSV" and
filter to Holocene volcanoes. No account required.

---

## Run order

Run scripts in numerical order. Scripts 01–08 are independent and can run in parallel
if you have multiple EE quota allocations; otherwise run sequentially.

```bash
# From the project root (activate venv first)
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate
```

### Step 1 — Topography (Copernicus DEM GLO-30, EE)
```bash
python scripts/earth/01_topography.py
```
Output: `data/processed/earth_topography_025deg.parquet`
Approximate runtime: **10–20 min** (EE rate-limited)

### Step 2 — Thermal (MODIS MOD11A2, EE)
```bash
python scripts/earth/02_thermal.py
```
Output: `data/processed/earth_thermal_025deg.parquet`
Approximate runtime: **15–30 min**

### Step 3 — Surface optics (MODIS MCD43A3, EE)
```bash
python scripts/earth/03_surface_optics.py
```
Output: `data/processed/earth_surface_optics_025deg.parquet`
Approximate runtime: **15–25 min**

### Step 4 — Aridity (TerraClimate, EE)
```bash
python scripts/earth/04_aridity.py
```
Output: `data/processed/earth_aridity_025deg.parquet`
Approximate runtime: **10–20 min**

### Step 5 — Geology (GLiM, local rasterio)
**Requires:** `data/raw/earth/glim/*.tif`
```bash
python scripts/earth/05_geology.py
```
Output: `data/processed/earth_geology_025deg.parquet`
Approximate runtime: **5–15 min**

### Step 6 — Volcanic caves proxy (GLiM + GVP, local GeoPandas)
**Requires:** Step 5 output AND `data/raw/earth/gvp/*.csv`
```bash
python scripts/earth/06_volcanic_caves.py
```
Output: `data/processed/earth_volcanic_caves_025deg.parquet`
Approximate runtime: **2–5 min**

### Step 7 — Ice / polar (MODIS MCD12Q1 EE + IPA GZI local)
**Requires:** `data/raw/earth/ipa_gzi/*.tif`
```bash
python scripts/earth/07_ice_polar.py
```
Output: `data/processed/earth_ice_polar_025deg.parquet`
Approximate runtime: **15–30 min** (EE part)

### Step 8 — Illumination (pure latitude computation, no external data)
```bash
python scripts/earth/08_illumination.py
```
Output: `data/processed/earth_illumination_025deg.parquet`
Approximate runtime: **< 1 min**
Unit tests run automatically before output is written.

### Step 0 — Assemble master table
**Requires:** one or more of the above outputs. Run after all available steps complete.
```bash
python scripts/earth/00_assemble.py
```
Output: `data/processed/earth_cells_025deg.parquet`
Approximate runtime: **< 2 min**

If some raw data files have not been downloaded yet, the assembly runs with the
available characteristics and prints which ones are missing. Re-run after downloading
the missing raw files.

---

## Expected outputs

| File | Rows (approx.) | Notes |
|------|---------------|-------|
| `earth_topography_025deg.parquet` | ~56,000 | Land cells at 0.25° |
| `earth_thermal_025deg.parquet` | ~56,000 | Polar-night cells may be absent |
| `earth_surface_optics_025deg.parquet` | ~56,000 | Polar-night cells may be absent |
| `earth_aridity_025deg.parquet` | ~56,000 | |
| `earth_geology_025deg.parquet` | ~56,000 | Excludes water body / no-data GLiM cells |
| `earth_volcanic_caves_025deg.parquet` | ~56,000 | PROXY / LOW confidence |
| `earth_ice_polar_025deg.parquet` | ~1,440,000 (all grid) | Ice scores are 0 for most cells |
| `earth_illumination_025deg.parquet` | ~1,440,000 (all grid) | All lat/lon, land mask applied in assembly |
| **`earth_cells_025deg.parquet`** | **~56,000** | **Master output — used by backend** |

---

## Known missing / placeholder values

- `land_fraction` = 1.0 for all cells (placeholder; full fractional land mask is Phase 3b).
- `known_analog_within_km` = -1.0 for all cells (populated in Phase 3c when analog
  catalogs are downloaded and the exclusion buffer is applied).

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `EE_PROJECT not set in .env` | `.env` file missing or incomplete | Copy `.env.example` to `.env` and fill in `EE_PROJECT` |
| `earthengine.ee.EEException` | Not authenticated | Run `earthengine authenticate` |
| `GLiM GeoTIFF not found` | Raw file not downloaded | Download from PANGAEA (see §3 above) |
| `GVP catalog CSV not found` | Raw file not downloaded | Download from volcano.si.edu |
| `IPA GZI GeoTIFF not found` | Raw file not downloaded | Download from PANGAEA (see §3 above) |
| `No per-characteristic parquet files found` | 00_assemble.py run before any data exists | Run steps 01–08 first |

---

## Planet reference targets (`scripts/planets/`)

These scripts build `data/processed/targets.json` — the reference value table for all 16
planetary targets (9 moon-landing, 2 moon-base, 3 mars-landing, 2 mars-base).
They use **hardcoded literature values only** — no live API calls, no EE, no raw data
downloads required.

### No prerequisites beyond the venv

All three scripts run with the base `.venv` (only `numpy` required; already installed).

### Step P1 — Moon reference values (literature)

```bash
python scripts/planets/01_moon_references.py
```

Output: `data/processed/moon_targets_raw.json`
Approximate runtime: **< 1 s**

### Step P2 — Mars reference values (literature)

```bash
python scripts/planets/02_mars_references.py
```

Output: `data/processed/mars_targets_raw.json`
Approximate runtime: **< 1 s**

### Step P0 — Assemble targets.json

**Requires:** P1 and P2 outputs.

```bash
python scripts/planets/00_assemble_targets.py
```

Output: `data/processed/targets.json`
Approximate runtime: **< 10 s**

If `data/processed/earth_cells_025deg.parquet` exists and contains illumination columns,
illumination percentile estimates are computed from the real Earth distribution.
If thermal columns are not yet present, those percentile estimates fall back to hardcoded
APPROXIMATE values labeled in the output. Re-run after completing the Earth pipeline.

### Expected output summary

| File | Targets | Notes |
|------|---------|-------|
| `moon_targets_raw.json` | 11 (9 landing + 2 base) | All values UNVERIFIED; from literature |
| `mars_targets_raw.json` | 5 (3 landing + 2 base) | All values UNVERIFIED; from literature |
| `targets.json` | 16 total | Merged; percentile estimates injected |

All values are marked `UNVERIFIED` and must be validated against primary PDS/LROC/MCD
data before Phase 6.
