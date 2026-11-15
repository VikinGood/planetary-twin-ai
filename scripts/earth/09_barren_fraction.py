"""
09_barren_fraction.py — Earth barren/sparse land-cover fraction preprocessing
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Uses MODIS MCD12Q1 (latest populated year) IGBP land cover classes:
  - Class 16: Barren (>60% non-vegetated)
  - Class 15: Permanent Snow/Ice
  - Class 7: Open shrublands (woody perennials 1-2m, 10-60% cover)

Produces: data/processed/earth_barren_025deg.parquet
  Columns: cell_id, lat_center, lon_center, barren_sparse_fraction, barren_source
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ee
import numpy as np
import pandas as pd

from scripts.earth.ee_utils import download_grid_as_df, init_ee

OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_barren_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
SOURCE = "MODIS/061/MCD12Q1"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_barren_image() -> ee.Image:
    """Build barren/sparse fraction from MCD12Q1 classes 16, 15, 7."""
    coll = ee.ImageCollection(SOURCE).filterDate("2023-01-01", "2024-01-01")
    lc = coll.first().select("LC_Type1")
    # Classes 16 (barren), 15 (snow/ice), 7 (open shrublands)
    barren = lc.eq(16).Or(lc.eq(15)).Or(lc.eq(7)).toFloat().rename("barren_sparse_fraction")
    return barren.resample("bilinear")


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    bands = ["barren_sparse_fraction"]
    print(f"[09_barren_fraction] Building barren/sparse image from {SOURCE}...")
    barren_img = build_barren_image()
    
    # 1. Run fixture
    print("[09_barren_fraction] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(barren_img, bands, is_fixture=True)
    print(
        f"[09_barren_fraction] Fixture: {len(df_fix)} cells "
        f"(min={df_fix['barren_sparse_fraction'].min():.3f}, "
        f"max={df_fix['barren_sparse_fraction'].max():.3f}, "
        f"mean={df_fix['barren_sparse_fraction'].mean():.3f})"
    )
    
    # 2. Run global
    print("[09_barren_fraction] Downloading server-reduced global 0.25° grid (1440x720)...")
    df_global = download_grid_as_df(barren_img, bands, is_fixture=False)
    
    # Filter to land cells if mask exists
    if LAND_MASK_FILE.exists():
        land_mask = pd.read_parquet(LAND_MASK_FILE)
        land_cells = set(land_mask[land_mask["land_fraction"] >= 0.5]["cell_id"])
        df_global = df_global[df_global["cell_id"].isin(land_cells)].copy()
        print(f"[09_barren_fraction] Filtered to {len(df_global):,} land cells (land_fraction >= 0.5).")
    
    df_global["barren_sparse_fraction"] = df_global["barren_sparse_fraction"].clip(0.0, 1.0).round(4)
    df_global["barren_source"] = SOURCE
    
    df_global.to_parquet(OUT_FILE, index=False)
    print(f"[09_barren_fraction] Wrote {len(df_global):,} cells to {OUT_FILE}")
    print(
        f"  barren_sparse_fraction summary: "
        f"min={df_global['barren_sparse_fraction'].min():.3f}, "
        f"max={df_global['barren_sparse_fraction'].max():.3f}, "
        f"mean={df_global['barren_sparse_fraction'].mean():.3f}, "
        f"share >= 0.5 = {(df_global['barren_sparse_fraction'] >= 0.5).mean():.1%}"
    )


if __name__ == "__main__":
    main()
