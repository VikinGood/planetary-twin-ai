# Project state (single source of truth)

Every task reads this file first and updates it last. Keep entries short. English only.

## Phases

| Phase | File | Mode | Status | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 Setup | 00-kickoff-orchestrator.md | Space Apps Orchestrator | approved | Guillermo | |
| 1 Methodology | 01-methodology.md | Plan | approved | | |
| 2 Data and architecture | 02-data-architecture.md | Plan | approved | | |
| 3 Backend core | 03-backend.md | Agent | in progress | | subtask 3a done; 3b done; 3c done |
| 4 AI analyst | 04-ai-analyst.md | Agent | pending | | parallel with 3 and 5 |
| 5 Explorer dashboard | 05-frontend.md | Agent | pending | | parallel with 3 and 4 |
| 6 Validation | 06-validation.md | Science Reviewer + Agent | pending | | |
| 7 Submission package | 07-submission.md | Agent | pending | | |

Status values: pending, in progress, review, approved, blocked.

## Decisions (append, newest last)

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
- `backend/tests/test_scoring.py` (36 unit tests): ✅ Phase 3c.
- `backend/tests/test_api.py` (15 API tests): ✅ Phase 3c.
- `scripts/export_static.py`: ✅ Phase 3c.
- `backend/README.md`: ✅ Phase 3c.
- `data/processed/earth_illumination_025deg.parquet`: ✅ produced (pure computation, 1,036,800 cells).
- `data/processed/earth_cells_025deg.parquet`: ✅ partial (illumination only; 7 chars pending raw data).
- `scripts/planets/01_moon_references.py`: ✅ Phase 3b — 11 Moon targets (9 landing + 2 base); literature values, all UNVERIFIED.
- `scripts/planets/02_mars_references.py`: ✅ Phase 3b — 5 Mars targets (3 landing + 2 base); literature values, all UNVERIFIED.
- `scripts/planets/00_assemble_targets.py`: ✅ Phase 3b — merges both; computes illumination percentiles from Earth parquet (real); thermal percentiles APPROXIMATE (Earth parquet lacks thermal columns yet).
- `data/processed/moon_targets_raw.json`: ✅ produced.
- `data/processed/mars_targets_raw.json`: ✅ produced.
- `data/processed/targets.json`: ✅ produced — 16 targets; illumination percentiles computed from 1,036,800 Earth cells; thermal percentiles labeled APPROXIMATE until Earth thermal pipeline runs.

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
