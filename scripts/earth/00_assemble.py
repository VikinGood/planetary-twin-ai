"""
00_assemble.py — Assemble all per-characteristic outputs into the master Earth cell table
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_cells_025deg.parquet

Inputs (all must exist in data/processed/):
  earth_topography_025deg.parquet     (from 01_topography.py)
  earth_thermal_025deg.parquet        (from 02_thermal.py)
  earth_surface_optics_025deg.parquet (from 03_surface_optics.py)
  earth_aridity_025deg.parquet        (from 04_aridity.py)
  earth_geology_025deg.parquet        (from 05_geology.py)
  earth_volcanic_caves_025deg.parquet (from 06_volcanic_caves.py)
  earth_ice_polar_025deg.parquet      (from 07_ice_polar.py)
  earth_illumination_025deg.parquet   (from 08_illumination.py)

Output schema: one row per 0.25° global land cell.
  Core:        cell_id, lat_center, lon_center, land_fraction
  Per-char:    <char>_confidence, <char>_proxy, <char>_source (and all data columns)
  Tags:        environment_tags  (list: desert, arid, polar, volcanic, cave)
  Placeholder: known_analog_within_km = -1.0  (populated in Phase 3c)

Land mask: a cell is included if it appears in ANY per-characteristic output file
           (i.e., non-ocean land determined by EE/rasterio dropping ocean pixels).
           land_fraction is set to 1.0 (a detailed fractional land mask is a Phase 3b
           enhancement; this placeholder is noted in source metadata).

Environment-family tag rules (METHODOLOGY §4):
  desert   : aridity_score > 0.75
  arid     : aridity_score > 0.50
  polar    : |lat| > 60°
  volcanic : glim_vb == 1 (GLiM basic volcanic class present)
  cave     : volcanic_caves_likelihood == 'HIGH'

Runtime: < 2 min (pure pandas merge).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
PROC_DIR = ROOT / "data" / "processed"
OUT_FILE = PROC_DIR / "earth_cells_025deg.parquet"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Input files
# ---------------------------------------------------------------------------
INPUT_FILES = {
    "topography":      PROC_DIR / "earth_topography_025deg.parquet",
    "thermal":         PROC_DIR / "earth_thermal_025deg.parquet",
    "surface_optics":  PROC_DIR / "earth_surface_optics_025deg.parquet",
    "aridity":         PROC_DIR / "earth_aridity_025deg.parquet",
    "geology":         PROC_DIR / "earth_geology_025deg.parquet",
    "volcanic_caves":  PROC_DIR / "earth_volcanic_caves_025deg.parquet",
    "ice_polar":       PROC_DIR / "earth_ice_polar_025deg.parquet",
    "illumination":    PROC_DIR / "earth_illumination_025deg.parquet",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def merge_key(df: pd.DataFrame) -> pd.DataFrame:
    """Round lat/lon to 3 decimal places to ensure consistent merge keys."""
    df = df.copy()
    df["lat_center"] = df["lat_center"].round(3)
    df["lon_center"] = df["lon_center"].round(3)
    return df


def load_or_warn(name: str, path: Path) -> pd.DataFrame | None:
    """Load a parquet file, or print a warning and return None."""
    if not path.exists():
        print(f"  WARNING: {name} file not found: {path.name} — column will be missing.")
        return None
    df = pd.read_parquet(path)
    df = merge_key(df)
    # Drop the char-specific cell_id (we'll regenerate the master one)
    df = df.drop(columns=["cell_id"], errors="ignore")
    print(f"  Loaded {len(df):,} cells from {path.name}")
    return df


# ---------------------------------------------------------------------------
# Environment tags
# ---------------------------------------------------------------------------

def build_env_tags(row: pd.Series) -> list[str]:
    tags = []

    # desert / arid (from aridity score)
    aridity_score = row.get("aridity_score", np.nan)
    if not pd.isna(aridity_score):
        if aridity_score > 0.75:
            tags.append("desert")
        if aridity_score > 0.50:
            tags.append("arid")

    # polar
    if abs(row["lat_center"]) > 60.0:
        tags.append("polar")

    # volcanic (GLiM basic volcanic class present)
    glim_vb = row.get("glim_vb", np.nan)
    if not pd.isna(glim_vb) and int(glim_vb) == 1:
        tags.append("volcanic")

    # cave (high volcanic-caves likelihood = lava-tube proxy threshold met)
    likelihood = row.get("volcanic_caves_likelihood", None)
    if likelihood == "HIGH":
        tags.append("cave")

    return tags


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    # --- Check which inputs exist ---
    missing = [n for n, p in INPUT_FILES.items() if not p.exists()]
    present = [n for n, p in INPUT_FILES.items() if p.exists()]

    if not present:
        print(
            "ERROR: No per-characteristic parquet files found in data/processed/.\n"
            "Run scripts 01–08 first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if missing:
        print(
            f"WARNING: {len(missing)} characteristic(s) missing: {missing}\n"
            "Assembly will proceed with available files; missing columns will be NaN."
        )

    # --- Load all available files ---
    print("Loading per-characteristic files …")
    frames: dict[str, pd.DataFrame] = {}
    for name, path in INPUT_FILES.items():
        df = load_or_warn(name, path)
        if df is not None:
            frames[name] = df

    if not frames:
        print("ERROR: No data to assemble.", file=sys.stderr)
        sys.exit(1)

    # --- Build master cell list from union of all lat/lon pairs ---
    print("Building master cell index …")
    all_cells = pd.concat(
        [df[["lat_center", "lon_center"]] for df in frames.values()],
        ignore_index=True,
    ).drop_duplicates()
    all_cells = all_cells.sort_values(["lat_center", "lon_center"]).reset_index(drop=True)
    print(f"  {len(all_cells):,} unique cells in union.")

    # --- Merge all characteristics ---
    merged = all_cells.copy()
    for name, df in tqdm(frames.items(), desc="Merging characteristics"):
        # Drop duplicate lat/lon rows in source (keep first)
        df = df.drop_duplicates(subset=["lat_center", "lon_center"], keep="first")
        merged = merged.merge(df, on=["lat_center", "lon_center"], how="left")

    # --- Add master provenance columns ---
    merged["cell_id"] = (
        "E_"
        + merged["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + merged["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    # land_fraction placeholder (see docstring — full fractional mask is Phase 3b)
    merged["land_fraction"] = 1.0

    # --- Environment tags ---
    print("Computing environment tags …")
    merged["environment_tags"] = [
        build_env_tags(row) for _, row in tqdm(merged.iterrows(), total=len(merged))
    ]

    # --- Known-analog placeholder ---
    # Real values populated in Phase 3c when analog catalogs are downloaded.
    # -1.0 means "not yet computed".
    merged["known_analog_within_km"] = -1.0

    # --- Column ordering ---
    core_cols = ["cell_id", "lat_center", "lon_center", "land_fraction"]
    tag_cols = ["environment_tags", "known_analog_within_km"]
    # All remaining data columns
    meta_cols = [c for c in merged.columns if c not in core_cols + tag_cols]
    final_cols = core_cols + meta_cols + tag_cols

    # Only include columns that exist
    final_cols = [c for c in final_cols if c in merged.columns]
    merged = merged[final_cols]

    # --- Write output ---
    merged.to_parquet(OUT_FILE, index=False)
    print(f"\nWrote {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")

    if missing:
        print(
            f"\nNOTE: {len(missing)} characteristic(s) are missing (exit-1 cases): {missing}\n"
            "Re-run the corresponding scripts once raw data files are downloaded, "
            "then re-run 00_assemble.py."
        )


if __name__ == "__main__":
    main()
