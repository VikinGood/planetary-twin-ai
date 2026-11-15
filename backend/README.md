# Backend — Planetary Twin AI

Space Logistics team, NASA Space Apps Challenge 2026.  
AI use disclosure: this file was generated with AI assistance and reviewed by the team.

---

## Overview

FastAPI backend that scores Earth locations as analogs for Moon and Mars mission sites.
Implements the scoring engine from `docs/METHODOLOGY.md` and exposes the API described in `docs/ARCHITECTURE.md`.

---

## Prerequisites

- Python 3.11+ in `.venv` at repo root
- `data/processed/earth_cells_025deg.parquet` (from `scripts/earth/00_assemble.py`)
- `data/processed/targets.json` (from `scripts/planets/00_assemble_targets.py`)

---

## Install dependencies

```bash
# From repo root (c:\dev\planetary-twin-ai)
.venv\Scripts\python -m pip install -r backend/requirements.txt
```

---

## Start the development server

```bash
# From repo root — uses package import backend.main:app
uvicorn backend.main:app --reload
```

Server starts at **http://127.0.0.1:8000**.  
Interactive docs: **http://127.0.0.1:8000/docs**

> The server starts even if the Earth parquet is missing; endpoints that need data
> return HTTP 503 until the preprocessing pipeline has been run.

---

## Run tests

```bash
# From repo root
.venv\Scripts\python -m pytest backend/tests/ -v
```

Tests in `backend/tests/test_api.py` use mock data fixtures and do **not** require
the real parquet. Tests in `test_scoring.py` test the pure scoring engine with
synthesized `pd.Series` inputs.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/characteristics` | Returns all 8 characteristic definitions from `config/characteristics.json` |
| GET | `/missions` | Returns all 4 mission presets from `config/missions/*.json` |
| GET | `/candidates` | Main scoring endpoint — returns ranked Earth analog cells |
| GET | `/candidates/{cell_id}` | Full SimilarityResult for one cell |
| GET | `/compare` | Landing vs base rankings side by side |
| GET | `/validation` | Known-analog cells with scores (blind validation) |
| POST | `/interpret` | AI interpretation of a SimilarityResult |

### GET /candidates parameters

| Parameter | Default | Description |
|---|---|---|
| `body` | required | `moon` or `mars` |
| `mission_type` | required | `landing` or `base` |
| `target` | (all for body+mission) | Target ID (e.g. `malapert_massif`) |
| `characteristics` | preset defaults | Comma-separated char IDs |
| `weights` | preset defaults | JSON string `{"topography":0.4,"thermal":0.6}` |
| `tags` | (none) | Comma-separated tag filter (AND logic) |
| `exclude_known` | `true` | Exclude known analog sites |
| `limit` | `50` | Max results (max 200) |

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Optional | Enables AI interpretation via Groq LLaMA |
| `GROQ_MODEL` | Optional | Default: `llama-3.3-70b-versatile` |
| `EE_PROJECT` | For preprocessing | Google Earth Engine project ID |

---

## File layout

```
backend/
  __init__.py
  main.py          # FastAPI app — imports all routers
  scoring.py       # Pure scoring engine — no FastAPI imports
  llm_provider.py  # LLMProvider interface + GroqProvider + NoLLMProvider
  data_loader.py   # Loads parquet + targets.json at startup, caches in memory
  routers/
    __init__.py
    characteristics.py
    missions.py
    candidates.py
    compare.py
    validation.py
    interpret.py
  tests/
    __init__.py
    test_scoring.py
    test_api.py
  requirements.txt
  README.md        # This file
```

---

## Static export (for GitHub Pages frontend)

```bash
python scripts/export_static.py
```

Produces `frontend/public/data/{body}_{mission_type}.json` GeoJSON files.
Requires both the Earth parquet and targets.json to be present.
