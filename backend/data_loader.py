"""
data_loader.py — Load and cache Earth cells and targets at startup.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.

Both functions are designed to be called once from FastAPI lifespan and stored on
app.state.  They raise FileNotFoundError with helpful messages if data is missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
PROC_DIR = ROOT / "data" / "processed"
EARTH_PARQUET = PROC_DIR / "earth_cells_025deg.parquet"
TARGETS_JSON = PROC_DIR / "targets.json"
CHARACTERISTICS_JSON = ROOT / "config" / "characteristics.json"
MISSIONS_DIR = ROOT / "config" / "missions"


# ---------------------------------------------------------------------------

def load_earth_cells() -> pd.DataFrame:
    """Read data/processed/earth_cells_025deg.parquet into memory.

    Raises FileNotFoundError with a helpful message if the file is missing.
    Call once at startup; store result in app.state.earth_df.
    """
    if not EARTH_PARQUET.exists():
        raise FileNotFoundError(
            f"Earth cells parquet not found: {EARTH_PARQUET}\n"
            "Run the Earth preprocessing pipeline first:\n"
            "  python scripts/earth/00_assemble.py\n"
            "(Requires scripts 01–08 to have been run on the raw data.)"
        )
    df = pd.read_parquet(EARTH_PARQUET)
    return df


def load_targets() -> dict:
    """Read data/processed/targets.json into memory.

    Raises FileNotFoundError with a helpful message if the file is missing.
    Returns the full JSON dict (schema_version, generated_at, note, targets).
    Call once at startup; store result in app.state.targets.
    """
    if not TARGETS_JSON.exists():
        raise FileNotFoundError(
            f"Targets JSON not found: {TARGETS_JSON}\n"
            "Run the targets assembly script first:\n"
            "  python scripts/planets/00_assemble_targets.py"
        )
    with open(TARGETS_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def load_characteristics() -> list[dict]:
    """Read config/characteristics.json (8 characteristic definitions)."""
    with open(CHARACTERISTICS_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def load_missions() -> list[dict]:
    """Read all four config/missions/*.json presets and return as a list."""
    presets = []
    for path in sorted(MISSIONS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as fh:
            preset = json.load(fh)
            # Ensure a stable 'id' field for the frontend
            preset.setdefault("id", path.stem)
            presets.append(preset)
    return presets
