# Handoff — Phase 5 (Explorer dashboard)

Built by Claude (analyst role) while Antigravity runs the Earth data pipeline.
Status: dashboard complete against MOCK data; waiting for the real export.

## What was built

- `frontend/`: React 18 + MapLibre GL 4 + Vite 5, Yarn only. See `frontend/README.md`.
- Controls: Moon / Mars; Landing site / Permanent base / Compare both; reference target;
  multi-select characteristic chips with a weight slider each; environment family filter
  (desert, polar, volcanic, arid, cave); "Exclude known analogs".
- Ranking on the client (`frontend/src/lib/scoring.mjs`): weighted geometric mean over the
  selected characteristics, weights normalized over the selection; a zero drops the cell;
  a null (no data) lowers coverage instead of counting as zero. Top 10 keeps distinct places
  (cells closer than 3 degrees are collapsed).
- Compare both: both rankings side by side and on the map, overlap highlighted.
- Candidate card: score by characteristic with confidence, activities the site can test,
  measured values with source, reference target, what Earth cannot reproduce, AI
  interpretation block (separate and labeled; "not available" when the file is missing).
- Validation badge: known analogs recovered in the top 100.
- `frontend/scripts/make-mock-data.mjs`: MOCK data built from the real presets in `config/`;
  the UI shows a MOCK banner while any file has `"mock": true`.
- `.github/workflows/pages.yml`: builds and deploys `frontend/` to GitHub Pages on push to
  main (enable Settings → Pages → Source: GitHub Actions once).

## Checks run

- `yarn test`: 9 passed (formula matches the sample contract, zero drops, null coverage,
  re-ranking on selection change, filters, overlap, recall, distinct places).
- `yarn build`: OK (JS 966 kB, 271 kB gzipped).
- Headless Chrome on the built site: all four presets load, compare view renders both
  layers, removing "Ice and Polar" from mars-base changes the top candidate, no page errors.

## Required changes in `scripts/export_static.py` (for Antigravity)

1. **Vectorize.** The current loop calls the scoring functions row by row with `iterrows()`
   for every cell, characteristic and target: about 1 million cells x 8 x up to 9 targets.
   That will not finish in time. Filter to land cells first, then compute each
   characteristic as NumPy array operations over all cells at once.
2. **Null, not zero, for missing data.** Characteristics whose data is pending (geology,
   volcanic_caves until GLiM and GVP arrive) must be exported as `null`. A `0` makes the
   geometric mean drop every cell when that characteristic is selected.
3. **Write `meta.json`** with the contract in `frontend/README.md`. Target ids in `presets`
   must be exactly the keys used in `scores`.
4. **Per-feature fields to add:** `values` (main measured variables with units and source),
   `confidence` per characteristic, and if possible `region_hint` (a readable place name,
   for example the admin-1 region from an Earth Engine boundaries dataset).
5. **Remove** `ranks` (all -1) and the per-feature `cannot_reproduce` (now in `meta.json`).
6. **Size:** keep each file under 5 MB. Round scores to 3 decimals; if `moon_landing`
   (9 targets) is too large, lower TOP_N for that preset.
7. **Interpretations** (Phase 4) go to
   `frontend/public/data/interpretations/{body}_{mission_type}/{target_id}/{cell_id}.json`.

## Open doubts

- Mock scores are synthetic and only exercise the interface; no conclusion should be drawn
  from them.
- The OpenStreetMap tile server is fine for a demo; for heavy public traffic use another
  tile provider.
