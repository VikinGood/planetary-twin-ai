# Prompt for Antigravity — Export quality fixes before Phase 6

Reviewer (Claude, analyst) audited the real export in `frontend/public/data`. Fix the five
items below in `scripts/export_static.py` (and the Earth scripts only where noted), re-export,
run tests, commit, push, then STOP and write `docs/reviews/handoff-export-fixes.md`.
Follow `.agents/rules/token-budget.md`: never print raw data, logs to `logs/`, show only `tail -30`.

Already done by Claude (do not change): `frontend/src/lib/scoring.mjs` and
`backend/analyst/analyst.py` now treat values below 0.01 as 0.01 (penalized, not dropped)
and the value `-1` as "hard requirement failed" (cell dropped when that characteristic is
selected). Tests updated and passing.

## 1. Vegetation filter (most important)
Problem: Moon landing top candidates are tropical forests (Indonesia, New Caledonia)
because dark vegetation matches lunar albedo ~0.12.
Fix: add `barren_sparse_fraction` per cell from MODIS MCD12Q1 (IGBP classes 16 barren,
15 snow/ice, 7 open shrublands; share of the 0.25° cell, latest year). Export only cells
with `barren_sparse_fraction >= 0.5`. Put the value in `values` with units "fraction",
source "MODIS MCD12Q1", so the card shows it. Document the rule in docs/METHODOLOGY.md
(one paragraph: why analogs must be bare surfaces).

## 2. No zeros from rounding; `-1` only for hard caps
- Do not round scores to 3 decimals before export if that makes them 0; use
  `max(round(s, 3), 0.001)` for any s > 0.
- A categorical mismatch (geology, cave likelihood LOW) must be a low score (0.05–0.2 as
  in METHODOLOGY), not 0.
- Write `-1` only where METHODOLOGY defines a hard cap (landing: slope > 12°). Nowhere else.
- Report in the handoff: for each preset, how many exported cells have a non-null,
  non-negative default-combination score > 0.05, and how many are in Antarctica (lat < -60).

## 3. Real region names
`REGIONS` (line ~80) and `get_region_hint` (line ~131) are copied from the mock and give
wrong names (e.g. "Puna de Atacama" for Santa Fe, "Sahara-Arabian Belt" for Crimea).
Replace with real names: on the exported cells only, reduce against
`FAO/GAUL/2015/level1` in Earth Engine (`ADM1_NAME`, `ADM0_NAME`) → `region_hint =
"ADM1, ADM0"`. Antarctica / ocean / no match → "Antarctica" or "Unnamed area (lat, lon)".
Delete the REGIONS list.

## 4. Real known analogs
Check where `is_known_analog` comes from. If it is the mock KNOWN list, replace it with
`data/reference/known_analogs.csv` (name, lat, lon, body, type, source URL). Use only
well-documented sites, for example: Haughton Crater (Devon Is.), Atacama/Yungay, Dry
Valleys (McMurdo), Mauna Kea/Mauna Loa (HI-SEAS, PISCES), Lanzarote (PANGAEA), Rio Tinto,
Mars Desert Research Station (Utah), Svalbard (AMASE/Bockfjord), Craters of the Moon (ID),
SP Crater/Black Point lava flow (AZ, Desert RATS), Ries crater, Kilauea. Flag a cell when
its center is within 0.5° of a site. Add the CSV to the repo and cite sources in DATA_SOURCES.

## 5. Export selection
Today cells are selected as top-N per single characteristic (moon_landing has only 480).
Also include, for every target, the top 300 cells by the preset's default combination
(same geometric mean, with the 0.01 floor and `-1` drop). Keep the union, deduplicated.
Keep each JSON under ~3 MB.

## Check, commit, stop
- `pytest -q` and `cd frontend && yarn test && yarn build` pass.
- Print per preset: feature count, file size, top 5 cells of the first target with
  region_hint and default score (5 lines each, no raw JSON).
- Commit "Export quality fixes: barren filter, hard-cap sentinel, real regions, known analogs",
  push, write the handoff, STOP. Claude runs Phase 6 validation next.
