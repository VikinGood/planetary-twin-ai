"""
export_static.py — Export scored Earth cells to GeoJSON for the frontend.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.

Produces:
    frontend/public/data/moon_landing.json
    frontend/public/data/moon_base.json
    frontend/public/data/mars_landing.json
    frontend/public/data/mars_base.json

Each file is a GeoJSON FeatureCollection. Each Feature is a 0.25° Earth cell
that ranks in the top 2,000 for ANY characteristic × ANY target for that
(body, mission_type) combination. All 8 characteristic scores are stored for
all targets so the frontend can re-rank instantly.

Usage:
    python scripts/export_static.py

Requirements:
    - data/processed/earth_cells_025deg.parquet  (from scripts/earth/00_assemble.py)
    - data/processed/targets.json               (from scripts/planets/00_assemble_targets.py)
    - .venv with backend package installed (or run from repo root with PYTHONPATH set)

Runtime: ~10–60 s depending on number of cells and targets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # ensure backend/ is importable

from backend.data_loader import load_earth_cells, load_missions, load_targets
from backend.scoring import (
    aridity_score,
    geology_score,
    ice_polar_score,
    illumination_score,
    surface_optics_score,
    thermal_score,
    topography_score,
    volcanic_caves_score,
)

OUT_DIR = ROOT / "frontend" / "public" / "data"
TOP_N = 2000
WARN_SIZE_MB = 5.0

ALL_CHARS = [
    "topography",
    "geology",
    "thermal",
    "aridity",
    "ice_polar",
    "volcanic_caves",
    "surface_optics",
    "illumination",
]

CANNOT_REPRODUCE_MOON = [
    "Gravity: 1/6 g (1.62 m/s²)",
    "Vacuum: ~10⁻¹⁰ Pa",
    "Radiation: unfiltered solar energetic particles and galactic cosmic rays",
    "Absolute temperatures: 40 K to ~400 K",
    "14-day day/night cycle",
    "Near-horizon sun regime (lunar south pole) — no Earth equivalent",
    "Electrostatic sharp-edged regolith",
]
CANNOT_REPRODUCE_MARS = [
    "Gravity: 0.38 g (3.72 m/s²)",
    "Atmosphere: 0.6 kPa, 95 % CO₂",
    "No ozone layer — full UV and ionizing radiation",
    "Global dust storms",
    "Absolute temperatures: −140 °C to +20 °C",
    "Perchlorates in regolith",
]

# ---------------------------------------------------------------------------


def score_one_char(row: pd.Series, char_id: str, target: dict, mission_type: str) -> float:
    """Return the [0, 1] score for one characteristic for one row against one target."""
    ref = target.get("reference_values", {})
    dispatch = {
        "topography": lambda: topography_score(row, ref, mission_type)[0],
        "geology": lambda: geology_score(row, ref)[0],
        "thermal": lambda: thermal_score(row, ref)[0],
        "aridity": lambda: aridity_score(row)[0],
        "ice_polar": lambda: ice_polar_score(row, ref)[0],
        "volcanic_caves": lambda: volcanic_caves_score(row)[0],
        "surface_optics": lambda: surface_optics_score(row, ref)[0],
        "illumination": lambda: illumination_score(row, ref)[0],
    }
    fn = dispatch.get(char_id)
    return fn() if fn else 0.0


def process_body_mission(
    earth_df: pd.DataFrame,
    targets_data: dict,
    body: str,
    mission_type: str,
) -> dict:
    """Score all cells for one (body, mission_type); return a GeoJSON FeatureCollection."""
    targets_dict = targets_data.get("targets", {})

    # Targets for this combination
    relevant_targets = [
        t for t in targets_dict.values()
        if t.get("body") == body and t.get("mission_type") == mission_type
    ]

    if not relevant_targets:
        print(f"  WARNING: No targets for {body}/{mission_type} — skipping.")
        return {"type": "FeatureCollection", "features": []}

    print(f"  {len(relevant_targets)} targets: {[t['id'] for t in relevant_targets]}")

    # Score each cell × each char × each target
    n_cells = len(earth_df)
    n_targets = len(relevant_targets)
    n_chars = len(ALL_CHARS)
    print(f"  Scoring {n_cells:,} cells × {n_chars} chars × {n_targets} targets …")

    # scores[char][target_id] = numpy array of shape (n_cells,)
    scores: dict[str, dict[str, np.ndarray]] = {c: {} for c in ALL_CHARS}

    for tgt in relevant_targets:
        tid = tgt["id"]
        for char_id in ALL_CHARS:
            char_scores_arr = np.zeros(n_cells, dtype=np.float32)
            for idx, (_, row) in enumerate(earth_df.iterrows()):
                char_scores_arr[idx] = score_one_char(row, char_id, tgt, mission_type)
            scores[char_id][tid] = char_scores_arr
            print(f"    [{body}/{mission_type}] {char_id} vs {tid}: done")

    # Union of top-2000 cells for ANY char × ANY target
    top_indices: set[int] = set()
    for char_id in ALL_CHARS:
        for tid, arr in scores[char_id].items():
            if len(arr) == 0:
                continue
            # Get top-N indices
            top_n = min(TOP_N, len(arr))
            top_idx = np.argpartition(arr, -top_n)[-top_n:]
            top_indices.update(top_idx.tolist())

    print(f"  Union of top-{TOP_N} cells: {len(top_indices):,} unique cells selected.")

    # Build GeoJSON features for selected cells
    features = []
    for idx in sorted(top_indices):
        row = earth_df.iloc[idx]
        lat = float(row.get("lat_center", 0.0))
        lon = float(row.get("lon_center", 0.0))
        cell_id = str(row.get("cell_id", f"E_{lat:+.3f}_{lon:+.3f}"))

        # Properties: all char scores for all targets
        props: dict = {
            "cell_id": cell_id,
            "lat_center": lat,
            "lon_center": lon,
            "land_fraction": float(row.get("land_fraction", 1.0)),
            "is_known_analog": _is_known_analog(row),
        }

        # Environment tags
        props["environment_tags"] = _compute_env_tags(row)

        # Scores by char × target
        props["scores"] = {}
        for char_id in ALL_CHARS:
            props["scores"][char_id] = {}
            for tid, arr in scores[char_id].items():
                props["scores"][char_id][tid] = round(float(arr[idx]), 4)

        # Per-target rank (rank within this char's top list)
        props["ranks"] = {}
        for tgt in relevant_targets:
            tid = tgt["id"]
            # Rank by topography score as a quick proxy; frontend computes final rank
            topo_scores = scores.get("topography", {}).get(tid, np.zeros(n_cells))
            cell_score = topo_scores[idx]
            # We don't compute full rank here (expensive); set -1 as placeholder
            props["ranks"][tid] = -1

        # Cannot-reproduce
        props["cannot_reproduce"] = (
            CANNOT_REPRODUCE_MOON if body == "moon" else CANNOT_REPRODUCE_MARS
        )

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def _is_known_analog(row: pd.Series) -> bool:
    try:
        d = float(row.get("known_analog_within_km", -1))
        return 0 <= d <= 50.0
    except (TypeError, ValueError):
        return False


def _compute_env_tags(row: pd.Series) -> list[str]:
    tags = []
    lat = _safe_float(row, "lat_center")
    if lat is not None and abs(lat) > 60:
        tags.append("polar")
    aridity_idx = _safe_float(row, "aridity_index")
    if aridity_idx is not None:
        s = max(0.0, 1.0 - min(aridity_idx, 1.0))
        if s > 0.75:
            tags.append("desert")
        if s > 0.50:
            tags.append("arid")
    glim_vb = row.get("glim_vb")
    if glim_vb is not None:
        try:
            if int(float(glim_vb)) == 1:
                tags.append("volcanic")
        except (ValueError, TypeError):
            pass
    likelihood = row.get("volcanic_caves_likelihood")
    if likelihood is not None and str(likelihood).upper() == "HIGH":
        tags.append("cave")
    return tags


def _safe_float(row: pd.Series, key: str):
    v = row.get(key)
    if v is None:
        return None
    try:
        f = float(v)
        return None if f != f else f  # NaN check
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Loading Earth cells …")
    try:
        earth_df = load_earth_cells()
        print(f"  {len(earth_df):,} cells loaded.")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Loading targets …")
    try:
        targets_data = load_targets()
        n = len(targets_data.get("targets", {}))
        print(f"  {n} targets loaded.")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    combinations = [
        ("moon", "landing"),
        ("moon", "base"),
        ("mars", "landing"),
        ("mars", "base"),
    ]

    for body, mission_type in combinations:
        print(f"\n--- {body}/{mission_type} ---")
        collection = process_body_mission(earth_df, targets_data, body, mission_type)

        out_path = OUT_DIR / f"{body}_{mission_type}.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(collection, fh, separators=(",", ":"), ensure_ascii=False)

        size_mb = out_path.stat().st_size / 1024 / 1024
        n_features = len(collection["features"])
        print(f"  Wrote {n_features:,} features → {out_path}  ({size_mb:.2f} MB)")

        if size_mb > WARN_SIZE_MB:
            print(
                f"  WARNING: {out_path.name} is {size_mb:.2f} MB > {WARN_SIZE_MB} MB limit. "
                "Consider splitting by target or using tiled GeoJSON for GitHub Pages."
            )

    print("\nDone.")


if __name__ == "__main__":
    main()
