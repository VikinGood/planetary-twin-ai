"""
01_topography.py — Earth topography preprocessing (Copernicus DEM GLO-30)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_topography_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           slope, slope_std, roughness, local_relief,
           slope_mean, roughness_mean, local_relief_mean,
           topography_confidence, topography_proxy, topography_source
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
OUT_FILE = OUT_DIR / "earth_topography_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
SOURCE = "COPERNICUS/DEM/GLO30_2024_1"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_topography_pair1() -> tuple[ee.Image, list[str]]:
    """Build pair 1: slope and elevation std (roughness)."""
    dem = ee.ImageCollection(SOURCE).select("DEM").mosaic()
    slope = ee.Terrain.slope(dem).rename("slope")
    roughness = dem.reduceNeighborhood(
        ee.Reducer.stdDev(), ee.Kernel.square(radius=1, units="pixels")
    ).rename("roughness")
    img = slope.addBands(roughness).resample("bilinear")
    return img, ["slope", "roughness"]


def build_topography_pair2() -> tuple[ee.Image, list[str]]:
    """Build pair 2: slope std and local relief (elevation max - min)."""
    dem = ee.ImageCollection(SOURCE).select("DEM").mosaic()
    slope = ee.Terrain.slope(dem).rename("slope")
    slope_std = slope.reduceNeighborhood(
        ee.Reducer.stdDev(), ee.Kernel.square(radius=1, units="pixels")
    ).rename("slope_std")
    
    dem_max = dem.reduceNeighborhood(ee.Reducer.max(), ee.Kernel.square(radius=1, units="pixels"))
    dem_min = dem.reduceNeighborhood(ee.Reducer.min(), ee.Kernel.square(radius=1, units="pixels"))
    local_relief = dem_max.subtract(dem_min).rename("local_relief")
    
    img = slope_std.addBands(local_relief).resample("bilinear")
    return img, ["slope_std", "local_relief"]


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Run fixture
    print("[01_topography] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    img1, bands1 = build_topography_pair1()
    img2, bands2 = build_topography_pair2()
    
    df_fix1 = download_grid_as_df(img1, bands1, is_fixture=True)
    df_fix2 = download_grid_as_df(img2, bands2, is_fixture=True)
    df_fix = df_fix1.merge(df_fix2[["cell_id"] + bands2], on="cell_id")
    
    print(f"[01_topography] Fixture results ({len(df_fix)} cells):")
    for b in bands1 + bands2:
        s = df_fix[b].dropna()
        print(f"  {b:14s}: min={s.min():.2f}, max={s.max():.2f}, mean={s.mean():.2f}, nulls={df_fix[b].isna().sum()}")
        
    # 2. Run global in 2 pairs to avoid memory limits
    print("[01_topography] Downloading global pair 1: slope + roughness...")
    df_global1 = download_grid_as_df(img1, bands1, is_fixture=False)
    
    print("[01_topography] Downloading global pair 2: slope_std + local_relief...")
    df_global2 = download_grid_as_df(img2, bands2, is_fixture=False)
    
    df_global = df_global1.merge(df_global2[["cell_id"] + bands2], on="cell_id")
    
    # 3. Filter to land cells
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "land_fraction"]]
    
    merged = land_mask.merge(df_global, on="cell_id", how="left")
    
    # Aliases
    merged["slope_mean"] = merged["slope"]
    merged["roughness_mean"] = merged["roughness"]
    merged["local_relief_mean"] = merged["local_relief"]
    merged["topography_confidence"] = "high"
    merged["topography_proxy"] = False
    merged["topography_source"] = f"{SOURCE}; 1km baseline reduced; processed {PROC_DATE}"
    
    # Fill remaining ocean/island NaNs with regional median values
    for b in bands1 + bands2 + ["slope_mean", "roughness_mean", "local_relief_mean"]:
        if merged[b].isna().sum() > 0:
            med = merged[b].median()
            merged[b] = merged[b].fillna(med)
            
    cols = [
        "cell_id", "lat_center", "lon_center",
        "slope", "slope_std", "roughness", "local_relief",
        "slope_mean", "roughness_mean", "local_relief_mean",
        "topography_confidence", "topography_proxy", "topography_source"
    ]
    merged = merged[cols]
    merged.to_parquet(OUT_FILE, index=False)
    print(f"[01_topography] Saved {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
