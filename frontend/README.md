# Planetary Twin AI Explorer (frontend)

Interactive dashboard to find and characterize new Earth analogs for Moon and Mars
landing sites and permanent bases. React + MapLibre GL JS, built with Vite.
Yarn only (never npm or npx).

## Run

```
cd frontend
yarn install
yarn mock        # writes MOCK data to public/data/ (only until the real export exists)
yarn dev         # http://localhost:5173
yarn test        # unit tests for the client-side ranking
yarn build       # static site in frontend/dist/
```

The real data comes from `python scripts/export_static.py` (repository root), which writes
to `frontend/public/data/` and replaces the MOCK files. The UI shows a MOCK banner while
any loaded file has `"mock": true`.

## What the dashboard does

- Body: Moon or Mars. Mission type: Landing site, Permanent base, or Compare both.
- Reference target per preset (`config/missions/*.json`).
- Characteristics: select one or several; each selected one has a weight slider.
  The ranking combines only the selected ones with a weighted geometric mean
  (`src/lib/scoring.mjs`, same formula as `docs/METHODOLOGY.md`). A zero on a selected
  characteristic drops the cell; a characteristic without data lowers "coverage" instead.
- Top 10 shows distinct places: neighbouring cells closer than 3° are collapsed.
- Filters: environment family from the challenge (desert, polar, volcanic, arid, cave) and
  "Exclude known analogs".
- Compare both: landing and base rankings side by side and on the map; sites in both top
  lists are highlighted.
- Candidate card: score by characteristic with confidence, activities the site can test for
  the chosen mission type, measured values with source, reference target, what Earth cannot
  reproduce, and the AI interpretation in a separate, labeled block.
- Validation badge: share of known analogs found in the top 100 when they are not excluded.

## Data contract (files under `public/data/`)

| File | Content |
| --- | --- |
| `meta.json` | `mock`, `characteristics` (id, name, description, comparison_rule, proxy), `presets` keyed `moon_landing`, `moon_base`, `mars_landing`, `mars_base` (body, mission_type, default_characteristics, default_weights, targets with id, name, lat, lon, description, coordinate_status, value_origin), `cannot_reproduce` (moon, mars), `known_analogs` (name, lat, lon) |
| `{body}_{mission_type}.json` | GeoJSON FeatureCollection from `scripts/export_static.py`. Per feature: `cell_id`, `lat_center`, `lon_center`, `environment_tags`, `is_known_analog`, `scores[characteristic][target_id]` in [0, 1] or null. Optional: `region_hint`, `known_analog_name`, `confidence[characteristic]`, `values[variable] = {value, units, source}` |
| `interpretations/{body}_{mission_type}/{target_id}/{cell_id}.json` | Optional (Phase 4), valid against `contracts/interpretation.schema.json` |

Data source switch: by default the app reads `data/` next to `index.html`. Another base URL
can be given with `?data=https://host/path/` or `VITE_DATA_BASE` at build time.

## Deploy

`.github/workflows/pages.yml` builds this folder and publishes it to GitHub Pages on every
push to `main`. One-time setup: repository Settings → Pages → Source: GitHub Actions.

## Use of AI

Portions of this frontend were generated with AI (Claude) and reviewed by the team.
Map tiles © OpenStreetMap contributors.
