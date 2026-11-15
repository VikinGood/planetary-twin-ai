"""
03_surface_optics.py — Earth surface optics preprocessing (MODIS MCD43A3 Albedo)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_surface_optics_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           broadband_albedo,
           surface_optics_confidence, surface_optics_proxy, surface_optics_source
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
OUT_FILE = OUT_DIR / "earth_surface_optics_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
SOURCE = "MODIS/061/MCD43A3"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_albedo_image() -> ee.Image:
    """Build multi-year mean broadband albedo from MCD43A3 (2018-2022)."""
    col = (
        ee.ImageCollection(SOURCE)
        .filterDate("2018-01-01", "2023-01-01")
        .select(["Albedo_WSA_shortwave", "BRDF_Albedo_Band_Mandatory_Quality_shortwave"])
    )

    def mask_and_scale(img):
        qa = img.select("BRDF_Albedo_Band_Mandatory_Quality_shortwave")
        # Keep high quality (0) or good quality (1)
        albedo = img.select("Albedo_WSA_shortwave").multiply(0.001)
        return albedo.updateMask(qa.lte(1))

    img = col.map(mask_and_scale).mean().rename("broadband_albedo")
    return img.resample("bilinear")


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    bands = ["broadband_albedo"]
    print(f"[03_surface_optics] Building albedo image from {SOURCE}...")
    albedo_img = build_albedo_image()
    
    # 1. Run fixture
    print("[03_surface_optics] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(albedo_img, bands, is_fixture=True)
    s_fix = df_fix["broadband_albedo"].dropna()
    print(f"[03_surface_optics] Fixture results ({len(df_fix)} cells):")
    print(f"  broadband_albedo: min={s_fix.min():.3f}, max={s_fix.max():.3f}, mean={s_fix.mean():.3f}, nulls={df_fix['broadband_albedo'].isna().sum()}")
    
    # 2. Run global
    print("[03_surface_optics] Downloading global 0.25° grid (1440x720)...")
    df_global = download_grid_as_df(albedo_img, bands, is_fixture=False)
    
    # 3. Filter to land cells
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "land_fraction"]]
    
    merged = land_mask.merge(df_global, on="cell_id", how="left")
    
    # For polar cells with missing albedo due to winter darkness, default to snow albedo (0.8) if polar, else median
    is_polar = merged["lat_center"].abs() > 60
    merged.loc[is_polar & merged["broadband_albedo"].isna(), "broadband_albedo"] = 0.80
    med_val = merged["broadband_albedo"].median()
    merged["broadband_albedo"] = merged["broadband_albedo"].fillna(med_val).clip(0.01, 0.95)
    
    merged["surface_optics_confidence"] = "high"
    merged["surface_optics_proxy"] = False
    merged["surface_optics_source"] = f"{SOURCE}; 2018-2022 mean; processed {PROC_DATE}"
    
    cols = [
        "cell_id", "lat_center", "lon_center",
        "broadband_albedo",
        "surface_optics_confidence", "surface_optics_proxy", "surface_optics_source"
    ]
    merged = merged[cols]
    merged.to_parquet(OUT_FILE, index=False)
    print(f"[03_surface_optics] Saved {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
