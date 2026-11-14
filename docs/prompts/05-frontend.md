# Phase 5 — Explorer dashboard (frontend)

Mode: Agent. Runs in parallel with Phases 3 and 4. Suggested owner: Susana.
Writes only in `frontend/`. YARN only, never npm or npx. All UI text in English.
Works against `contracts/similarity_result.sample.json` until the static export exists.

## Before you start
Read `AGENTS.md`, `docs/ESTADO.md`, the files in `contracts/` and `config/`.

## Deliverables
A minimal React + MapLibre dashboard:
- **Controls:**
  - Body toggle: Moon / Mars.
  - Mission type toggle: Landing site / Permanent base / Compare both.
  - Reference target selector (from the preset of the chosen body and mission type).
  - Characteristic chips, multi-select (one or several at once), preselected by the
    mission type preset; a weight slider for each selected chip.
  - Environment-family filter: desert, polar, volcanic, arid, cave.
  - "Exclude known analogs" switch.
- **Ranking:** combines the selected characteristics on the client with the weighted
  geometric mean from the exported per-characteristic scores, so every change re-ranks
  instantly.
- **World map:** OpenStreetMap tiles (attribution visible), top-10 candidates colored by
  score; known analogs shown as a separate layer.
- **Compare both:** landing and base rankings side by side (or as two map layers), with
  the sites that rank high in both highlighted.
- **Candidate card (characterization):**
  - overall score and per-characteristic breakdown,
  - measured values with source, resolution, units and timestamp,
  - reference target values side by side,
  - environment tags,
  - confidence,
  - "What Earth cannot reproduce" box,
  - activities this site can test for the chosen mission type,
  - AI interpretation in a separate block labeled "AI interpretation".
- Validation badge: share of known analogs the engine recovers for the current preset.
- Data source switch: reads `public/data/` by default (static mode); API URL optional.
- `yarn build` output deployable to GitHub Pages; steps in `frontend/README.md`.

## Done when
- `yarn build` succeeds and the built site works from a static server.
- Switching body, mission type or any characteristic changes the ranking visibly.
- Nothing labeled MOCK remains visible once real data is exported.

## Close the phase
Update `docs/ESTADO.md`, commit `phase 5: explorer dashboard`, STOP and report.
