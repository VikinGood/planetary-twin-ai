"""
07_ice_polar.py — Earth ice/polar preprocessing (MODIS MCD12Q1 permanent snow/ice)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_ice_polar_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           ice_cover_fraction, permafrost_index, latitude_multiplier, ice_polar_score,
           ice_polar_confidence, ice_polar_proxy, ice_polar_source
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
OUT_FILE = OUT_DIR / "earth_ice_polar_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
SOURCE = "MODIS/061/MCD12Q1"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_ice_image() -> ee.Image:
    """Build multi-year permanent ice/snow cover from MCD12Q1 class 15."""
    mcd = ee.ImageCollection(SOURCE).filterDate("2018-01-01", "2023-01-01").select("LC_Type1")
    # Proportion of years where cell was classified as class 15 (Permanent Snow/Ice)
    ice_binary = mcd.map(lambda img: img.eq(15).toFloat()).mean().rename("ice_cover_fraction")
    return ice_binary.resample("bilinear")


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    bands = ["ice_cover_fraction"]
    print(f"[07_ice_polar] Building ice cover image from {SOURCE}...")
    ice_img = build_ice_image()
    
    # 1. Run fixture
    print("[07_ice_polar] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(ice_img, bands, is_fixture=True)
    s_fix = df_fix["ice_cover_fraction"].dropna()
    print(f"[07_ice_polar] Fixture results ({len(df_fix)} cells):")
    print(f"  ice_cover_fraction: min={s_fix.min():.3f}, max={s_fix.max():.3f}, mean={s_fix.mean():.3f}")
    
    # 2. Run global
    print("[07_ice_polar] Downloading global 0.25° grid (1440x720)...")
    df_global = download_grid_as_df(ice_img, bands, is_fixture=False)
    
    # 3. Filter to land cells
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "land_fraction"]]
    
    merged = land_mask.merge(df_global, on="cell_id", how="left")
    merged["ice_cover_fraction"] = merged["ice_cover_fraction"].fillna(0.0).clip(0.0, 1.0)
    
    # Latitude multiplier (METHODOLOGY §2.5)
    abs_lat = merged["lat_center"].abs()
    lat_mult = np.where(abs_lat > 55.0, 1.0, np.where(abs_lat >= 23.5, 0.5, 0.0))
    merged["latitude_multiplier"] = lat_mult
    
    # Permafrost index: 1.0 where ice cover exists; high-latitude proxy 0.8 where |lat| > 60
    # pending offline PANGAEA IPA GZI GeoTIFF
    permafrost = np.where(
        merged["ice_cover_fraction"] >= 0.5,
        1.0,
        np.where(abs_lat > 65.0, 0.8, np.where(abs_lat > 55.0, 0.4, 0.0))
    )
    merged["permafrost_index"] = permafrost
    
    permafrost_score = merged["permafrost_index"] * merged["latitude_multiplier"]
    merged["ice_polar_score"] = np.sqrt(permafrost_score * merged["ice_cover_fraction"])
    
    merged["ice_polar_confidence"] = "medium"
    merged["ice_polar_proxy"] = True  # EE ice is real; permafrost uses high-lat proxy
    merged["ice_polar_source"] = f"{SOURCE} class 15; latitude proxy for permafrost; processed {PROC_DATE}"
    
    cols = [
        "cell_id", "lat_center", "lon_center",
        "ice_cover_fraction", "permafrost_index", "latitude_multiplier", "ice_polar_score",
        "ice_polar_confidence", "ice_polar_proxy", "ice_polar_source"
    ]
    merged = merged[cols]
    merged.to_parquet(OUT_FILE, index=False)
    print(f"[07_ice_polar] Saved {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
