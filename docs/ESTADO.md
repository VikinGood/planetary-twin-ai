# Project state (single source of truth)

Every task reads this file first and updates it last. Keep entries short. English only.

## Phases

| Phase | File | Mode | Status | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 Setup | 00-kickoff-orchestrator.md | Space Apps Orchestrator | approved | Guillermo | |
| 1 Methodology | 01-methodology.md | Plan | approved | | |
| 2 Data and architecture | 02-data-architecture.md | Plan | approved | | |
| 3 Backend core | 03-backend.md | Agent | approved | | Earth pipeline (1km slope, aridity, ice_polar, GLiM, GVP), targets, scoring engine, API complete |
| 4 AI analyst | 04-ai-analyst.md | Agent | approved | | Pre-generated AI interpretations cached for top 3 per target via Groq with deterministic checker |
| 5 Explorer dashboard | 05-frontend.md | Agent | approved | | Static export <3MB, Vite build & Yarn tests passing, no MOCK banner, validation badge integrated |
| 6 Validation | 06-validation.md | Science Reviewer + Agent | approved | Claude | Blind validation against 337k cells & 12 known analogs, stability +-20%, contrast tests passed |
| 7 Submission package | 07-submission.md | Agent | pending | | |

Status values: pending, in progress, review, approved, blocked.

## Decisions (append, newest last)

- 2026-11-15 (Project Title & Branding):
  - Updated dashboard title to "Celestial Analog Finder - Planetary Twin AI" in `frontend/src/App.jsx` and `frontend/index.html`.
  - Added docs/*.mp3 to `.gitignore` alongside docs/*.mp4 to protect audio/video assets from repo commits.
  - Updated README.md and docs/SUBMISSION.md with tagline "Discover Earth. Prepare for other worlds."
  - Deployed to GitHub Pages and verified live in browser.

- 2026-11-15 (AI Analyst caching):
  - Pre-generated and cached AI interpretations for top 3 candidates per target using Groq (`openai/gpt-oss-120b`).
  - Strict schema and deterministic number checker enforced; 47 interpretations cached in `frontend/public/data/interpretations/`.
  - Pushed to `main` and deployed to GitHub Pages via Actions.

- 2026-11-15 (GitHub Pages deployment & CI):
  - Updated `.github/workflows/pages.yml` to `node-version: 22` to satisfy dependencies.
  - GitHub Actions build and deployment succeeded.
  - Live deployment verified at `https://vikingood.github.io/planetary-twin-ai/`: interactive map rendered with numbered pins and top 10 analog ranking table fully populated.

- 2026-11-15 (Phase 6 validation & open items resolution):
  - Verified and updated all 12 `source_url` entries in `data/reference/known_analogs.csv` to active HTTP 200 URLs.
  - Spot-checked Franz Josef Land coordinates (`E_+80.625_+46.875`), correctly labeled `Franz Josef Land, Russian Federation`.
  - Aligned `process_preset` candidate selection with `scoring.mjs` and `analyst.py`: missing characteristic scores are skipped (not floored to 0.01) and weights re-normalized over available data.
  - Added limitation on coarse 4 km precipitation reanalysis overestimating coastal/valley polar desert rainfall (McMurdo Dry Valleys) in `docs/METHODOLOGY.md` §8.
  - Re-exported static datasets and re-ran `scripts/validate_phase6.py` (`validation.json` updated).
  - Pytest (65 tests) and frontend test suite (11 tests) pass; production build verified.

- 2026-11-15 (Export quality fixes pre-validation):
  - Bare surface / vegetation filter: MODIS MCD12Q1 (IGBP classes 16, 15, 7) ingested (`earth_barren_025deg.parquet`).
    Only cells with `barren_sparse_fraction >= 0.5` (or known analog sites) are screened, completely removing
    tropical rainforest false-positives from Moon landing rankings.
  - Scoring floor & hard-cap sentinels: scores below 0.01 floored to 0.01 in `scoring.mjs` and `analyst.py`.
    Hard caps (slope > 12°) strictly emit `-1.0` (dropping cell when selected). No rounding zeroes (`max(round(s, 3), 0.001)`).
    Categorical mismatches in geology and volcanic caves score 0.10.
  - Real administrative names from Earth Engine `FAO/GAUL/2015/level1` (`ADM1_NAME`, `ADM0_NAME`) replacing
    mock REGIONS list. Polar cells labeled "Antarctica". Cached in `data/raw/earth/region_hints_cache.json`.
  - Canonical known analogs catalog `data/reference/known_analogs.csv` (12 sites) created, flagged within 0.5°,
    and documented in `docs/DATA_SOURCES.md`.
  - Multi-target export selection: top 300 cells by default combination per target plus top 50 per characteristic,
    deduplicated union per preset strictly under 2.6 MB (`moon_landing`: 2.26 MB, `moon_base`: 2.58 MB,
    `mars_landing`: 2.14 MB, `mars_base`: 2.25 MB).
  - 65 pytest tests and 10 frontend tests passing; production build verified.

- 2026-11-15 (Phase 3 fixes and Phase 5 static export):
  - Slope recalculated on Copernicus DEM GLO-30 reprojected to 1 km baseline before reducing
    mean and std to the 0.25° grid across 386 10°×10° land tiles with local caching. Global max
    slope rose from 5.07° to 25.77°; Everest 18.54° (relief 4318.9 m), Aconcagua 15.81° (relief 3567.7 m),
    Amazon 0.82° (relief 86.5 m).
  - Ground ice score updated to `ground_ice_score = permafrost_index`. Permanent ice sheets
    (`ice_cover_fraction >= 0.5`) capped at score 0.5 and tagged `"ice sheet"`. Devon Island awarded
    full permafrost index (0.80).
  - Aridity updated to dual rule `aridity_score = max(1 - min(P/PET, 1), 1 - min(P / 250 mm, 1))`.
    Zeroing for permanent ice removed. Polar deserts (Antarctic plateau 0.71, Devon Island 0.18)
    properly scored as arid analogs.
  - Volcano qualifying types: removed `"Lava dome(s)"`, retaining only low-viscosity basaltic systems.
  - Real GLiM 0.5° lithology (PANGAEA) ingested: 332,998 valid cells (98.6% coverage), 9,490 basic volcanic (`vb`).
  - Smithsonian GVP Holocene volcano catalog (1,215 volcanoes, 303 qualifying) ingested: 754 HIGH
    and 14,184 MEDIUM likelihood lava-tube cells identified globally.
  - All 64 scoring and API unit tests passing (1.61 s).
  - Static export `scripts/export_static.py` vectorized with NumPy across 337,611 cells. Generates
    `meta.json` (`"mock": false`), and all 4 preset GeoJSONs (`moon_landing.json`: 1.37 MB / 480 feats;
    `moon_base.json`: 2.81 MB / 1,529 feats; `mars_landing.json`: 2.60 MB / 1,397 feats;
    `mars_base.json`: 2.96 MB / 1,632 feats), all strictly under 3.0 MB.
  - Frontend production build verified (`yarn build` in 3.61 s; `yarn test` 9/9 passing; no MOCK banner).
  - GitHub Pages deploy workflow added (`.github/workflows/pages.yml`).

- 2026-11-15 (Phase 3 Earth data & targets):
  - Land mask computed from MODIS MCD12Q1 (classes 1–16 = land, 17 = water) with bilinear resampling;
    337,611 land cells kept (`land_fraction >= 0.5`), filtering out 699,189 ocean cells (32.56% of Earth surface).
  - Preprocessing pipeline executed on Google Earth Engine with server-side spatial reductions:
    topography (Copernicus DEM GLO-30), thermal (MODIS MOD11A2), surface optics (MODIS MCD43A3),
    aridity (TerraClimate), ice & polar (MODIS MCD12Q1).
  - Illumination overhauled: `sun_fraction` (~0.50 globally) replaced with continuous polar night and day
    days per year (`longest_polar_night_days`, `longest_polar_day_days`), non-zero only above polar circles.
  - GLiM lithology and Smithsonian GVP Holocene volcano catalog marked `DATA PENDING` without blocking execution.
  - Planetary targets (`targets.json`) updated with `"value_origin": "literature"` and percentiles computed
    against the 337,611 Earth land cell distributions.
  - Full master dataset `data/processed/earth_cells_025deg.parquet` written with 337,611 rows, 67 columns,
    and 0 nulls. All 51 unit and API integration tests passing (1.67 s).

- 2026-11-14: Scope follows the official challenge text in AGENTS.md: Moon and Mars;
  landing site and permanent base; multi-select characteristics; whole-planet Earth search;
  environment-family tags (desert, polar, volcanic, arid, cave). All outputs in English.
  This replaces the earlier "Mars only, rover mobility" scope.
- 2026-11-14: General scoring principle: analog score = similarity to reference target.
  Only REQUIREMENT characteristics (aridity) are exceptions (labeled as such).
  Combination: weighted geometric mean over selected characteristics only (zero score eliminates site).
- 2026-11-14: Topography — landing: slope/roughness similarity + 12° hard cap (NASA HLS threshold).
  Base: adds surrounding relief within 12 km neighborhood radius.
- 2026-11-14: Lava-tube proxy = GLiM vb class + distance to qualifying Smithsonian GVP
  Holocene volcano (shield, lava field, fissure vent, volcanic field); HIGH/MEDIUM/LOW
  categorical output; always LOW confidence; labeled PROXY in data and UI.
- 2026-11-14: Illumination = LOW SUN regime similarity (not "maximize illumination").
  Scored as percentile/regime match on solar elevation statistics.
- 2026-11-14: Mission preset weights defined (summing to 1):
  moon-landing: topography 0.35, illumination 0.25, surface_optics 0.20, thermal 0.20.
  moon-base: ice_polar 0.25, illumination 0.20, volcanic_caves 0.15, thermal 0.15, topography 0.15, geology 0.10.
  mars-landing: topography 0.40, surface_optics 0.25, aridity 0.20, thermal 0.15 (illumination replaced by aridity).
  mars-base: ice_polar 0.25, volcanic_caves 0.20, geology 0.15, thermal 0.15, aridity 0.15, topography 0.10.
- 2026-11-14: mars-landing preset excludes illumination; aridity replaces it.
  AGENTS.md default characteristic list for mars-landing updated accordingly.
- 2026-11-14 (Phase 2 review fixes):
  - Moon landing targets corrected to NASA release 24-136 (Oct 28 2024): Peak near Cabeus B,
    Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2,
    de Gerlache Rim 2, Slater Plain. Previous list (Faustini, Shackleton rim, Leibnitz Beta,
    Connecting Ridge Extension) was from 2022 Artemis III shortlist — removed.
  - Common 1 km slope baseline: slope/roughness/relief computed from each body's native DEM
    resampled to 1 km for all three bodies (Copernicus GLO-30 for Earth, LOLA LDEM for Moon,
    MOLA MEGDR 463 m for Mars). LOLA slope products and MOLA-HRSC blended DEM not used for
    scoring; retained as reference in DATASETS.md.
  - Gaussian sigma floor added: σ_eff = max(σ_target, σ_floor). Floors: slope 2°,
    roughness 10 m, local_relief 50 m, albedo 0.05. All labeled TEAM ASSUMPTION.
  - Hard cap (12° slope) relabeled TEAM ASSUMPTION throughout all presets and METHODOLOGY.md.
  - PANGAEA (GLiM, IPA GZI): confirm free download without registration before preprocessing;
    if account required, free registration suffices (no commercial account needed).
  - MOLA-HRSC blended DEM: retained in DATASETS.md as reference-only; not needed for scoring.
- 2026-11-15 (Phase 3c):
  - Scoring engine (backend/scoring.py): 12 pure functions implementing METHODOLOGY.md §2 exactly.
  - FastAPI backend (backend/main.py + 6 routers): /characteristics, /missions, /candidates,
    /candidates/{cell_id}, /compare, /validation, /interpret.
  - LLM integration (backend/llm_provider.py): LLMProvider, NoLLMProvider, GroqProvider.
  - data_loader.py: load_earth_cells() + load_targets() + load_characteristics() + load_missions().
  - Unit tests: 51 tests, 0 failures (pytest backend/tests/ in 1.81 s).
  - scripts/export_static.py: produces frontend/public/data/{body}_{mission_type}.json GeoJSON.
  - backend/README.md: exact server start command documented (uvicorn backend.main:app --reload).
  - known_analog_within_km placeholder still -1.0 (Phase 3c populates real values when analog
    catalog CSVs are downloaded; scoring._is_known_analog() treats -1.0 as not-known).
- 2026-11-14 (Phase 3a):
  - GLiM integer-to-class mapping: assumes standard Hartmann & Moosdorf 2012 encoding
    (1=vb, 2=va, … 15=ice). Adjust GLIM_INT_TO_CLASS dict in 05_geology.py if the PANGAEA
    raster uses a different encoding (read the .tif metadata on first download).
  - 00_assemble.py uses union of all per-characteristic lat/lon grids; land_fraction=1.0
    placeholder (Phase 3b to add a proper fractional land mask).
  - known_analog_within_km=-1.0 placeholder throughout; Phase 3c populates real values.
  - GVP qualifying types from config/characteristics.json: "Shield volcano", "Fissure vent(s)",
    "Volcanic field", "Lava dome(s)". Note: AGENTS.md listed "Lava dome(s)" but
    characteristics.json also lists it — no conflict.

## Contracts (files other phases depend on)

- `config/characteristics.json`: ✅ produced in Phase 1.
- `config/missions/*.json` (four presets: moon-landing, moon-base, mars-landing, mars-base): ✅ produced in Phase 1.
- `contracts/similarity_result.sample.json`: ✅ produced in Phase 2.
- `contracts/interpretation.schema.json`: ✅ produced in Phase 2.
- `docs/DATASETS.md`: ✅ produced in Phase 2.
- `docs/ARCHITECTURE.md`: ✅ produced in Phase 2.
- `backend/requirements.txt`: ✅ produced in Phase 3a (deps installed in .venv).
- `scripts/earth/01_topography.py` through `scripts/earth/08_illumination.py`: ✅ Phase 3a.
- `scripts/earth/00_assemble.py`: ✅ Phase 3a.
- `scripts/README.md`: ✅ Phase 3a.
- `backend/__init__.py`, `backend/scoring.py`: ✅ Phase 3c.
- `backend/data_loader.py`: ✅ Phase 3c.
- `backend/llm_provider.py`: ✅ Phase 3c.
- `backend/main.py`: ✅ Phase 3c.
- `backend/routers/` (6 routers): ✅ Phase 3c.
- `backend/tests/test_scoring.py`: ✅ Phase 3c & 3 fixes (64 unit & scoring tests passing).
- `backend/tests/test_api.py`: ✅ Phase 3c (15 API tests).
- `scripts/export_static.py`: ✅ Phase 3c & 5 (vectorized NumPy export, files under 3 MB).
- `backend/README.md`: ✅ Phase 3c.
- `data/processed/earth_cells_025deg.parquet`: ✅ complete (337,611 land cells, 67 columns, all 8 characteristics, 0 nulls).
- `scripts/planets/01_moon_references.py`: ✅ Phase 3b — 11 Moon targets (9 landing + 2 base); literature values, all UNVERIFIED.
- `scripts/planets/02_mars_references.py`: ✅ Phase 3b — 5 Mars targets (3 landing + 2 base); literature values, all UNVERIFIED.
- `scripts/planets/00_assemble_targets.py`: ✅ Phase 3b — merges both; computes percentiles against 337,611 Earth cells.
- `data/processed/moon_targets_raw.json`: ✅ produced.
- `data/processed/mars_targets_raw.json`: ✅ produced.
- `data/processed/targets.json`: ✅ produced — 16 targets with empirical Earth percentiles.
- `frontend/public/data/` (`meta.json` + 4 presets): ✅ Phase 5 static exports (< 3 MB each, mock: false).
- `.github/workflows/pages.yml`: ✅ Phase 5 GitHub Pages deployment workflow.
- `docs/reviews/handoff-phase-3-fixes.md`: ✅ Phase 3 fixes and Phase 5 export handoff.

## Open questions for the team

- **Moon target coordinates (UNVERIFIED):** targets corrected to NASA release 24-136. Approximate coordinates from USGS Gazetteer and release map image. Ramiro (GIS) must verify against NASA's official region maps before Phase 6.
- **Mars target coordinates (UNVERIFIED):** Jezero, Gale, Meridiani well-known; Arcadia Planitia center and Arsia Mons pit coordinates need GIS verification before Phase 6.
- **LOLA illumination sub-product URL:** PDS volume path for Mazarico et al. 2011 illumination maps needs confirmation before Moon preprocessing begins.
- **TES pixel scale:** PDS label must be read to confirm exact resolution of TES bolometric albedo, thermal inertia, and DCI mosaics (stated ~3–8 km in literature).
- ~~MOLA–HRSC blended DEM completeness~~ — resolved: MOLA MEGDR is the scoring DEM; HRSC blended is reference-only, completeness no longer a blocker.
- **MGC³ field schema:** download from ScienceBase doi:10.5066/P9VXZEF5 to confirm candidate count and field names.
- **NASA Planetary Pits and Caves Analog Dataset URL:** locate exact ScienceBase URL before Phase 3; needed for volcanic_caves proxy validation.
- **NASA Astrobiology Field Sites bulk download:** confirm if machine-readable CSV/GeoJSON export is available; if not, manually curate.
- **WAC broadband cross-calibration:** LROC WAC mosaic is single-band (604 nm); cross-calibration to MODIS broadband shortwave albedo is unconfirmed. Apply percentile/regime fallback if no calibration factor found.

## Accounts the team must create before preprocessing

- Google Earth Engine (all members who run scripts): https://earthengine.google.com — free non-commercial registration.
- PANGAEA (to download GLiM and IPA GZI): https://pangaea.de — try direct download first (some datasets are openly accessible without login); free registration is sufficient if required.
- Mars Climate Database (for high-res MCD runs, optional): https://www-mars.lmd.jussieu.fr/mars/access.html — free registration.
- NASA Earthdata (for MODIS direct download, optional — not needed if using EE): https://urs.earthdata.nasa.gov

## Known issues

-
