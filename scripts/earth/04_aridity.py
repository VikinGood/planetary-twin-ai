"""
04_aridity.py — Earth aridity preprocessing (TerraClimate pr/pet)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_aridity_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           annual_pr_mm, annual_pet_mm, precipitation, pet,
           aridity_index, aridity_score,
           aridity_confidence, aridity_proxy, aridity_source
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
OUT_FILE = OUT_DIR / "earth_aridity_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
SOURCE = "IDAHO_EPSCOR/TERRACLIMATE"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_aridity_image() -> ee.Image:
    """Build multi-year annual mean precipitation and PET from TerraClimate (2015-2022)."""
    col = (
        ee.ImageCollection(SOURCE)
        .filterDate("2015-01-01", "2023-01-01")
        .select(["pr", "pet"])
    )
    # 8 years of monthly data: sum divided by 8 gives mean annual total (mm/yr)
    # pet raw integer is in units of 0.1 mm/month, so multiply by 0.1
    annual_pr = col.select("pr").sum().divide(8.0).rename("annual_pr_mm")
    annual_pet = col.select("pet").sum().multiply(0.1).divide(8.0).rename("annual_pet_mm")
    
    img = annual_pr.addBands(annual_pet)
    return img.resample("bilinear")


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    bands = ["annual_pr_mm", "annual_pet_mm"]
    print(f"[04_aridity] Building aridity image from {SOURCE}...")
    aridity_img = build_aridity_image()
    
    # 1. Run fixture
    print("[04_aridity] Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(aridity_img, bands, is_fixture=True)
    print(f"[04_aridity] Fixture results ({len(df_fix)} cells):")
    for b in bands:
        s = df_fix[b].dropna()
        print(f"  {b:14s}: min={s.min():.2f}, max={s.max():.2f}, mean={s.mean():.2f}, nulls={df_fix[b].isna().sum()}")
        
    # 2. Run global
    print("[04_aridity] Downloading global 0.25° grid (1440x720)...")
    df_global = download_grid_as_df(aridity_img, bands, is_fixture=False)
    
    # 3. Filter to land cells
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "land_fraction"]]
    
    merged = land_mask.merge(df_global, on="cell_id", how="left")
    
    # Compatibility aliases
    merged["precipitation"] = merged["annual_pr_mm"]
    merged["pet"] = merged["annual_pet_mm"]
    
    # Fill Antarctica / polar voids where PET is 0 or unmeasured:
    # In polar ice sheets, PR is low (~50mm), PET is near 0.
    merged["annual_pr_mm"] = merged["annual_pr_mm"].fillna(50.0).clip(lower=0.0)
    merged["precipitation"] = merged["annual_pr_mm"]
    merged["annual_pet_mm"] = merged["annual_pet_mm"].fillna(10.0).clip(lower=0.1)
    merged["pet"] = merged["annual_pet_mm"]
    
    # Compute aridity_index = pr / pet (capped at 2.0 per methodology §2.4)
    merged["aridity_index"] = (merged["precipitation"] / merged["pet"]).clip(0.0, 2.0)
    
    # Requirement scoring formula: max(1 - min(P/PET, 1), 1 - min(P / 250 mm, 1))
    # so polar deserts with under 250 mm/yr score as arid
    p_pet_term = 1.0 - (merged["precipitation"] / merged["pet"]).clip(0.0, 1.0)
    pr_250_term = 1.0 - (merged["precipitation"] / 250.0).clip(0.0, 1.0)
    merged["aridity_score"] = np.maximum(p_pet_term, pr_250_term)
    
    merged["aridity_confidence"] = "high"
    merged["aridity_proxy"] = False
    merged["aridity_source"] = f"{SOURCE}; 2015-2022 mean; processed {PROC_DATE}"
    
    cols = [
        "cell_id", "lat_center", "lon_center",
        "annual_pr_mm", "annual_pet_mm", "precipitation", "pet",
        "aridity_index", "aridity_score",
        "aridity_confidence", "aridity_proxy", "aridity_source"
    ]
    merged = merged[cols]
    merged.to_parquet(OUT_FILE, index=False)
    print(f"[04_aridity] Saved {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
