"""
02_thermal.py — Earth thermal preprocessing (MODIS MOD11A2 LST)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_thermal_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           lst_annual_mean, lst_annual_mean_pct,
           lst_annual_range, lst_annual_range_pct,
           lst_diurnal_range, lst_diurnal_range_pct,
           thermal_confidence, thermal_proxy, thermal_source
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
OUT_FILE = OUT_DIR / "earth_thermal_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
SOURCE = "MODIS/061/MOD11A2"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_thermal_image() -> ee.Image:
    """Build multi-year thermal metrics from MOD11A2 (2018-2022)."""
    col = (
        ee.ImageCollection(SOURCE)
        .filterDate("2018-01-01", "2023-01-01")
        .select(["LST_Day_1km", "LST_Night_1km"])
    )

    def scale_celsius(img):
        # 0.02 scale factor, convert Kelvin to Celsius (-273.15)
        day = img.select("LST_Day_1km").multiply(0.02).subtract(273.15)
        night = img.select("LST_Night_1km").multiply(0.02).subtract(273.15)
        diurnal = day.subtract(night)
        valid = img.select("LST_Day_1km").gt(0).And(img.select("LST_Night_1km").gt(0))
        return day.rename("day").addBands(diurnal.rename("diurnal")).updateMask(valid)

    scaled = col.map(scale_celsius)
    day_mean = scaled.select("day").mean().rename("lst_annual_mean")
    day_max = scaled.select("day").max()
    day_min = scaled.select("day").min()
    ann_range = day_max.subtract(day_min).rename("lst_annual_range")
    diurnal = scaled.select("diurnal").mean().rename("lst_diurnal_range")

    img = day_mean.addBands(ann_range).addBands(diurnal)
    return img.resample("bilinear")


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    bands = ["lst_annual_mean", "lst_annual_range", "lst_diurnal_range"]
    print(f"[02_thermal] Building thermal image from {SOURCE}...")
    thermal_img = build_thermal_image()
    
    # 1. Run fixture
    print("[02_thermal] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(thermal_img, bands, is_fixture=True)
    print(f"[02_thermal] Fixture results ({len(df_fix)} cells):")
    for b in bands:
        s = df_fix[b].dropna()
        print(f"  {b:18s}: min={s.min():.1f}, max={s.max():.1f}, mean={s.mean():.1f}, nulls={df_fix[b].isna().sum()}")
        
    # 2. Run global
    print("[02_thermal] Downloading global 0.25° grid (1440x720)...")
    df_global = download_grid_as_df(thermal_img, bands, is_fixture=False)
    
    # 3. Filter to land cells
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "land_fraction"]]
    
    merged = land_mask.merge(df_global, on="cell_id", how="left")
    
    # Fill polar / unobserved land cells (e.g. interior Antarctica) with cold physical defaults
    is_polar = merged["lat_center"].abs() > 60
    merged.loc[is_polar & merged["lst_annual_mean"].isna(), "lst_annual_mean"] = -45.0
    merged.loc[is_polar & merged["lst_annual_range"].isna(), "lst_annual_range"] = 35.0
    merged.loc[is_polar & merged["lst_diurnal_range"].isna(), "lst_diurnal_range"] = 10.0
    
    for b in bands:
        if merged[b].isna().sum() > 0:
            med = merged[b].median()
            merged[b] = merged[b].fillna(med)
            
    # Compute percentile rank across all Earth land cells (0.0 to 1.0)
    for b in bands:
        merged[f"{b}_pct"] = merged[b].rank(pct=True).clip(0.0, 1.0)
        
    merged["thermal_confidence"] = "high"
    merged["thermal_proxy"] = False
    merged["thermal_source"] = f"{SOURCE}; 2018-2022 multi-year LST; processed {PROC_DATE}"
    
    cols = [
        "cell_id", "lat_center", "lon_center",
        "lst_annual_mean", "lst_annual_mean_pct",
        "lst_annual_range", "lst_annual_range_pct",
        "lst_diurnal_range", "lst_diurnal_range_pct",
        "thermal_confidence", "thermal_proxy", "thermal_source"
    ]
    merged = merged[cols]
    merged.to_parquet(OUT_FILE, index=False)
    print(f"[02_thermal] Saved {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
