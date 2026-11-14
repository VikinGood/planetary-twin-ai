# Phase 2 — Datasets, data model and architecture (no implementation)

Mode: Plan. Runs alone. Suggested owner: Guillermo.

## Before you start
Read `AGENTS.md`, `docs/ESTADO.md`, `docs/METHODOLOGY.md` and the files in `config/`.

## How to split the work
Spawn three `general` subagents IN PARALLEL. Each reads `AGENTS.md` and
`docs/METHODOLOGY.md` first and returns a table: characteristic, dataset, provider,
resolution, units, format, access method (Earth Engine ID, URL, account needed), license,
coverage. Anything not verified is marked `UNVERIFIED`.

- **Subagent A — Earth (global coverage required).** Candidates to verify:
  Copernicus DEM GLO-30 (`COPERNICUS/DEM/GLO30`; NASADEM and SRTM stop at 60° N),
  MODIS land surface temperature (`MODIS/061/MOD11A2`), MODIS albedo (`MODIS/061/MCD43A3`),
  TerraClimate (`IDAHO_EPSCOR/TERRACLIMATE`, aridity as pr / pet),
  GLiM global lithological map (PANGAEA, volcanic classes), Smithsonian Global Volcanism
  Program Holocene volcanoes, a permafrost extent map and a snow/ice land-cover layer,
  travel time to cities (Oxford/MAP in Earth Engine), protected areas (WDPA).
  Note: there is no global open catalog of Earth lava tubes; propose a proxy and say so.
- **Subagent B — Moon.** Candidates: LOLA DEM and slope (polar products included), Diviner
  temperatures, LOLA polar illumination maps, LROC permanently shadowed region atlas,
  lunar ice detections, unified geologic map of the Moon (USGS, 1:5M), LROC lunar pit
  locations (shapefile and CSV at data.lroc.im-ldi.com), LROC WAC reflectance, NASA's nine
  candidate south-polar landing regions.
- **Subagent C — Mars and known analogs.** Candidates: MOLA DEM (463 m) and MOLA-HRSC
  blended DEM (200 m), TES albedo, TES thermal inertia, TES dust cover index, Mars Climate
  Database (non-commercial license), USGS global geologic map of Mars (Tanaka et al. 2014),
  Mars Global Cave Candidate Catalog (MGC³), subsurface water ice maps (SWIM),
  USGS Known Terrestrial Analog Sites (doi:10.5066/P9J72921), NASA astrobiology field
  sites, ESA Catalogue of Planetary Analogues, NASA planetary pits and caves analog dataset.

## Deliverables (written by you after the subagents return)
1. `docs/DATASETS.md`: merged table, one row per characteristic per body, plus a
   "gaps and proxies" section.
2. `docs/ARCHITECTURE.md`:
   - Data model with fields, provenance and uncertainty for: Dataset, Layer, Location,
     Measurement, Characteristic, MissionProfile, Target, CharacteristicScore,
     SimilarityResult, Interpretation.
   - Mermaid diagram: offline preprocessing, per-characteristic score tables, engine,
     AI analyst, API, static export, dashboard.
   - Folder structure (`backend/`, `frontend/`, `scripts/`, `data/`, `config/`, `contracts/`).
   - Compute plan: per (body, target), compute the eight characteristic scores for every
     land cell at 0.25°; export only the union of cells that rank in the top 2,000 for any
     characteristic, with all eight scores, so the dashboard can combine any selection on
     the client. Estimate file sizes; GitHub Pages must load them comfortably.
3. `contracts/similarity_result.sample.json`: realistic, labeled MOCK, with body, mission
   type, target, selected characteristics, per-characteristic scores and variables,
   measured values with provenance, reference values, environment tags, confidence,
   "cannot reproduce" list and an empty interpretation slot.
4. `contracts/interpretation.schema.json`: the JSON schema the AI analyst returns.

## Done when
- Each characteristic has a dataset for Earth and for each body that supports it, or a
  documented proxy or gap.
- Phases 3, 4 and 5 can start in parallel using only the contracts.

## Close the phase
Update `docs/ESTADO.md` (contracts, open questions, accounts the team must create), commit
`phase 2: data and architecture`, STOP and report. Remind the user that Phases 3, 4 and 5
can now run in parallel.
