# Architecture — Planetary Twin AI

Space Logistics team, NASA Space Apps Challenge 2026.
AI use disclosure: this document was drafted with AI assistance and reviewed by the team.

---

## 1. Data model

### 1.1 Dataset

A source dataset used as input for one or more characteristics.

| field | type | description |
|---|---|---|
| `id` | string | Stable identifier (e.g. `copernicus_dem_glo30`) |
| `name` | string | Human-readable name |
| `provider` | string | Originating organization |
| `access` | string | Earth Engine ID or download URL |
| `resolution_m` | number | Native pixel size in meters |
| `units` | string | Physical units |
| `license` | string | License or terms of use |
| `vintage_start` | string ISO 8601 | Earliest data date |
| `vintage_end` | string ISO 8601 | Latest data date (or "ongoing") |
| `global_coverage` | boolean | True if full land surface is covered |
| `polar_gap` | boolean | True if data are missing at high latitudes |
| `account_needed` | string | Account type required, or "none" |

### 1.2 Layer

A processed, single-variable raster derived from one Dataset at the working resolution (0.25°).

| field | type | description |
|---|---|---|
| `id` | string | Stable identifier (e.g. `lst_annual_range`) |
| `dataset_id` | string | FK → Dataset |
| `characteristic_id` | string | FK → Characteristic |
| `body` | enum | `earth` / `moon` / `mars` |
| `variable_name` | string | Variable name from `config/characteristics.json` |
| `units` | string | Units after processing |
| `processing_script` | string | Relative path to the script that produced this layer |
| `produced_at` | string ISO 8601 | Timestamp of last preprocessing run |
| `cell_count_valid` | integer | Number of land cells with valid data |
| `confidence_default` | enum | `high` / `medium` / `low` |
| `proxy` | boolean | True if this layer is a proxy (not a direct measurement) |
| `proxy_label` | string | Label shown in UI if proxy = true |

### 1.3 Location

A 0.25° grid cell on Earth.

| field | type | description |
|---|---|---|
| `cell_id` | string | H3 index (resolution 3) or `{lat}_{lon}` key |
| `lat_center` | number | Cell centroid latitude (°) |
| `lon_center` | number | Cell centroid longitude (°) |
| `land_fraction` | number | Fraction of cell that is land (0–1) |
| `environment_tags` | string[] | Environment-family tags: desert, arid, polar, volcanic, cave |

### 1.4 Measurement

A processed value for one Layer at one Location.

| field | type | description |
|---|---|---|
| `cell_id` | string | FK → Location |
| `layer_id` | string | FK → Layer |
| `value` | number | Processed value in Layer units |
| `confidence` | enum | `high` / `medium` / `low` |
| `data_gap` | boolean | True if value was gap-filled or extrapolated |

### 1.5 Characteristic

Defined in `config/characteristics.json`. Reproduced here for data-model completeness.
Key fields: `id`, `comparison_rule`, `supported_bodies`, `proxy_confidence` (if proxy).

### 1.6 MissionProfile

One of the four presets in `config/missions/`. Fields: `body`, `mission_type`,
`reference_targets`, `default_characteristics`, `default_weights`.

### 1.7 Target

One reference location on Moon or Mars.

| field | type | description |
|---|---|---|
| `id` | string | Stable identifier |
| `mission_profile_id` | string | FK → MissionProfile |
| `name` | string | Human-readable name |
| `lat` | number | Latitude on the target body |
| `lon` | number | Longitude on the target body |
| `coordinate_status` | string | `verified` or `UNVERIFIED` |
| `reference_values` | object | `{layer_id: value}` — target-body measurements used as reference |

### 1.8 CharacteristicScore

The score [0, 1] for one characteristic for one Earth cell against one target.

| field | type | description |
|---|---|---|
| `cell_id` | string | FK → Location |
| `target_id` | string | FK → Target |
| `characteristic_id` | string | FK → Characteristic |
| `score` | number | Similarity score 0–1 |
| `variables` | object | `{variable_name: {earth_value, reference_value, units}}` |
| `confidence` | enum | `high` / `medium` / `low` |
| `proxy` | boolean | True if characteristic is a proxy |

### 1.9 SimilarityResult

A ranked output for one Earth cell, one mission profile, and a chosen weight set.
Stored as a row in the exported Parquet / JSON file loaded by the dashboard.

| field | type | description |
|---|---|---|
| `cell_id` | string | FK → Location |
| `body` | string | `moon` / `mars` |
| `mission_type` | string | `landing` / `base` |
| `target_id` | string | FK → Target |
| `selected_characteristics` | string[] | IDs of selected characteristics |
| `weights` | object | `{characteristic_id: weight}` |
| `characteristic_scores` | CharacteristicScore[] | One per selected characteristic |
| `total_score` | number | Weighted geometric mean 0–1 |
| `environment_tags` | string[] | Computed from characteristic scores |
| `confidence` | enum | Minimum of characteristic confidences |
| `cannot_reproduce` | string[] | List of conditions Earth cannot match (from METHODOLOGY §7) |
| `interpretation` | Interpretation | AI analyst output slot; null until filled |
| `is_known_analog` | boolean | True if cell is within 50 km of a catalog site |
| `rank` | integer | Rank within the current selection/weight combination |

### 1.10 Interpretation

The AI analyst's structured output. Stored separately from scoring results.

| field | type | description |
|---|---|---|
| `cell_id` | string | FK → Location |
| `target_id` | string | FK → Target |
| `model` | string | LLM model identifier |
| `generated_at` | string ISO 8601 | Timestamp |
| `analog_summary` | string | ≤ 100 words: what this site analogs |
| `non_analog_summary` | string | ≤ 100 words: what it does NOT analog |
| `testable_activities` | string[] | Activities that can be tested here |
| `confidence_note` | string | Explicit note on data limitations |
| `ai_disclosure` | string | Standard AI-use disclosure string |

---

## 2. System architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  OFFLINE PREPROCESSING  (scripts/ — runs once; output to data/)      │
│                                                                      │
│  Earth Engine scripts         Local Rasterio/GeoPandas scripts       │
│  ├── slope, roughness, relief  ├── GLiM geology (not in EE)         │
│  ├── MODIS LST annual stats    ├── IPA GZI permafrost (not in EE)   │
│  ├── MODIS albedo annual mean  └── GVP Holocene distance raster     │
│  ├── TerraClimate aridity idx                                        │
│  └── MCD12Q1 ice fraction       Moon / Mars data download scripts   │
│                                 ├── LOLA DEM → slope, roughness      │
│                                 ├── Diviner GDR → thermal stats      │
│                                 ├── LOLA illumination fraction        │
│                                 ├── MOLA/HRSC DEM → slope, roughness │
│                                 └── TES albedo / thermal inertia     │
└───────────────────────────┬──────────────────────────────────────────┘
                            │  per-characteristic score rasters
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  SCORING ENGINE  (scripts/score.py)                                  │
│                                                                      │
│  For each (body, target):                                            │
│  ├── compute CharacteristicScore for all 8 chars × all land cells   │
│  ├── compute environment_tags per cell                               │
│  ├── apply 50 km exclusion buffer (is_known_analog flag)            │
│  └── export top-2000 union cells with all 8 scores                  │
│       → data/processed/{body}_{target_id}_scores.parquet            │
└───────────────────────────┬──────────────────────────────────────────┘
                            │  Parquet files (pre-scored, all 8 chars)
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STATIC EXPORT  (scripts/export_json.py)                             │
│                                                                      │
│  Convert Parquet to compact JSON (GeoJSON FeatureCollection)         │
│  → frontend/public/data/{body}_{mission_type}.json                  │
└───────────────────────────┬──────────────────────────────────────────┘
                            │  Compact JSON (served from GitHub Pages)
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND  (backend/)                                         │
│                                                                      │
│  GET /api/score?body=&mission=&chars=&weights=                       │
│  ├── loads pre-scored JSON                                           │
│  ├── applies user weights → weighted geometric mean (client-side    │
│  │   capable; backend for server-side validation and AI trigger)    │
│  └── returns SimilarityResult[]                                      │
│                                                                      │
│  POST /api/interpret  (body: SimilarityResult)                       │
│  └── LLMProvider → Interpretation                                    │
└───────────────────────────┬──────────────────────────────────────────┘
                            │  SimilarityResult[] / Interpretation
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  REACT DASHBOARD  (frontend/)                                        │
│                                                                      │
│  MapLibre GL JS map — OpenStreetMap tiles + scored cells             │
│  ├── body selector (Moon / Mars)                                     │
│  ├── mission type selector (landing / base / compare both)           │
│  ├── multi-select characteristics + weight sliders                   │
│  ├── weighted geometric mean computed on client → instant re-rank    │
│  ├── candidate card: scores, environment tags, cannot-reproduce,    │
│  │   confidence, AI interpretation (lazy-loaded)                    │
│  └── "Compare both" view: side-by-side rank tables                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Folder structure

```
planetary-twin-ai/
├── AGENTS.md                       # Project rules (read by every task)
├── config/
│   ├── characteristics.json        # 8 characteristic definitions
│   └── missions/
│       ├── moon-landing.json
│       ├── moon-base.json
│       ├── mars-landing.json
│       └── mars-base.json
├── contracts/
│   ├── similarity_result.sample.json   # MOCK — interface contract
│   └── interpretation.schema.json      # JSON Schema for AI output
├── data/
│   ├── raw/                        # Downloaded source files (gitignored)
│   │   ├── earth/
│   │   ├── moon/
│   │   └── mars/
│   ├── processed/                  # Per-characteristic score rasters + exports
│   │   ├── earth/                  # Layer GeoTIFFs at 0.25°
│   │   ├── moon/                   # Target reference values
│   │   └── mars/
│   └── analogs/                    # Known-analog catalog CSVs (gitignored)
├── scripts/
│   ├── ee/                         # Earth Engine Python scripts
│   ├── preprocess/                 # Rasterio/GeoPandas scripts (GLiM, GZI, GVP)
│   ├── score.py                    # Scoring engine — produces Parquet
│   └── export_json.py              # Parquet → compact JSON for frontend
├── backend/
│   ├── main.py                     # FastAPI app
│   ├── scoring.py                  # Weighted geometric mean, rank, tags
│   ├── llm_provider.py             # LLMProvider interface + GroqProvider + NoLLMProvider
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── data/                   # Pre-scored JSON files (served statically)
│   ├── src/
│   │   ├── components/
│   │   └── App.tsx
│   ├── package.json
│   └── yarn.lock
├── docs/
│   ├── ESTADO.md                   # Single source of truth for phase status
│   ├── METHODOLOGY.md              # Phase 1 deliverable
│   ├── DATASETS.md                 # Phase 2 deliverable
│   ├── ARCHITECTURE.md             # This file
│   └── prompts/                    # Phase instruction files
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 4. Compute plan and file-size estimate

### 4.1 Working grid

- Resolution: 0.25° (~28 km at equator)
- Total land cells: approximately 56,000 (global land area ~148 M km² ÷ 784 km² per cell)
- Per (body, target): one score row per land cell = ~56,000 rows

### 4.2 Score computation

For each of the N configured targets across two bodies:
- Moon: up to 11 targets (9 south-polar landing + 2 base)
- Mars: up to 5 targets (3 landing + 2 base)
- Total target count: 16

For each target, compute all 8 characteristic scores × 56,000 cells.
Write output to `data/processed/{body}_{target_id}_scores.parquet`.
Each Parquet file: 56,000 rows × ~20 columns (8 scores + 8 confidence flags + lat/lon +
metadata) ≈ **~5–8 MB per target** (compressed Parquet). Total: ~16 × 7 MB ≈ **~110 MB** preprocessed.

### 4.3 Static export for dashboard

Export **only the union of cells that rank in the top 2,000 for any characteristic across
all targets** for a given (body, mission_type) combination. This union typically covers
3,000–6,000 unique cells (cells can rank in top 2,000 for multiple targets/characteristics).

Each exported cell carries all 8 characteristic scores for all targets of that (body, mission_type)
pair, so the client can re-rank instantly for any user selection.

Estimated JSON file sizes (minified GeoJSON):
- ~5,000 cells × (geometry + 8 scores × 11 targets + tags + metadata) ≈ **~2–4 MB per file**
- 4 files total (moon-landing, moon-base, mars-landing, mars-base): **~10–15 MB total**

GitHub Pages has a soft limit of ~1 GB repository size; individual files load comfortably
under 10 MB on a modern connection. Files will be gzip-compressed in transit.
If any file exceeds 5 MB after compression, split by target or use a tiled approach.

### 4.4 Client-side combination

The dashboard loads one JSON file per (body, mission_type) selection.
When the user adjusts characteristics or weights, the browser recomputes:
`total_score = product(score_i ^ w_i)` in JavaScript — instant re-rank, no API call.
The API is called only when the user requests an AI interpretation of a specific cell.
