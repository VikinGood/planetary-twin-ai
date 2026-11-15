"""
00_land_mask.py — Earth land/water mask preprocessing (MODIS MCD12Q1 land fraction)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_land_mask_025deg.parquet
  Columns: cell_id, lat_center, lon_center, land_fraction
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
OUT_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"


def build_land_fraction_image() -> ee.Image:
    """Build land fraction image where land classes (1-16) = 1.0, water (17) = 0.0."""
    mcd = ee.ImageCollection("MODIS/061/MCD12Q1").filterDate("2020-01-01", "2021-01-01").first()
    lc = mcd.select("LC_Type1")
    # Land is classes 1..16; 17 is water
    land_binary = lc.gte(1).And(lc.lte(16)).toFloat().rename("land_fraction")
    return land_binary.resample("bilinear")


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("[00_land_mask] Building land fraction image...")
    land_img = build_land_fraction_image()
    
    # 1. Run fixture
    print("[00_land_mask] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(land_img, ["land_fraction"], is_fixture=True)
    fix_land = (df_fix["land_fraction"] >= 0.5).sum()
    print(f"[00_land_mask] Fixture: {len(df_fix)} cells total, {fix_land} land cells (min={df_fix['land_fraction'].min():.3f}, max={df_fix['land_fraction'].max():.3f})")
    
    # 2. Run global
    print("[00_land_mask] Downloading server-reduced global 0.25° grid (1440x720)...")
    df_global = download_grid_as_df(land_img, ["land_fraction"], is_fixture=False)
    
    # Fill any NaNs with 0.0 (open ocean)
    df_global["land_fraction"] = df_global["land_fraction"].fillna(0.0).clip(0.0, 1.0)
    
    # Filter cells with land_fraction >= 0.5
    land_cells = df_global[df_global["land_fraction"] >= 0.5].copy()
    
    land_cells.to_parquet(OUT_FILE, index=False)
    print(f"[00_land_mask] Saved {len(land_cells):,} land cells (land_fraction >= 0.5) to {OUT_FILE}")
    print(f"[00_land_mask] Filtered out {len(df_global) - len(land_cells):,} ocean cells ({len(land_cells)/len(df_global)*100:.2f}% of Earth is land).")


if __name__ == "__main__":
    main()
