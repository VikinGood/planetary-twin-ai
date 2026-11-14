# Phase 3 — Backend core: preprocessing, scoring engine and API

Mode: Agent. Runs in parallel with Phases 4 and 5. Suggested owner: Guillermo.
Writes only in `backend/`, `data/` and `scripts/`.

## Before you start
Read `AGENTS.md`, `docs/ESTADO.md`, `docs/METHODOLOGY.md`, `docs/DATASETS.md`,
`docs/ARCHITECTURE.md` and the files in `contracts/` and `config/`.

## How to split the work
Three subtasks. 3a and 3b can run in parallel; 3c starts when 3a delivers the first table.
- **3a — Earth preprocessing.** Scripts in `scripts/earth/` (prefer Google Earth Engine)
  that write `data/processed/earth_cells_025deg.parquet`: every land cell with the raw
  variables of all eight characteristics, provenance columns, environment tags and
  `known_analog_within_km`. Document exact commands in `scripts/README.md`.
- **3b — Moon and Mars references.** Scripts in `scripts/planets/` that write
  `data/processed/targets.json`: every target of the four presets with the same variables,
  with provenance.
- **3c — Engine and API** in `backend/`:
  - `.venv` setup, pinned `requirements.txt`, exact commands in `backend/README.md`.
  - Per-characteristic scores for every (body, target); weighted geometric mean over the
    selected characteristics; confidence; "cannot reproduce" list per body.
  - Endpoints:
    - `GET /characteristics`
    - `GET /missions` (the four presets)
    - `GET /candidates?body=moon|mars&mission_type=landing|base&target=<id>
      &characteristics=topography,thermal&weights=<json>&tags=volcanic,polar
      &exclude_known=true&limit=10`
    - `GET /candidates/{id}?body=&target=`
    - `GET /compare?body=&target=&characteristics=`: landing vs base rankings and the
      sites that rank high in both.
    - `GET /validation?body=&mission_type=`
  - `scripts/export_static.py`: writes, per (body, target), the pruned cell table with all
    eight scores plus presets and validation to `frontend/public/data/`.
  - Unit tests for normalization, each comparison rule and the geometric mean.
- If a dataset is blocked, stop and report; never fake values.

## Done when
- `pytest` passes.
- For each of the four presets, `GET /candidates` returns 10 results traceable to inputs,
  and the results change when characteristics are added or removed.
- The static export exists, matches the contract and stays under the size limit agreed in
  Phase 2.

## Close the phase
Update `docs/ESTADO.md`, commit `phase 3: backend core`, STOP and report.
