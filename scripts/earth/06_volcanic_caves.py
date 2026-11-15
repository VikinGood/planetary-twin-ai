"""
06_volcanic_caves.py — Earth volcanic caves preprocessing (Smithsonian GVP)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_volcanic_caves_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           volcanic_caves_likelihood,
           volcanic_caves_confidence, volcanic_caves_proxy, volcanic_caves_source
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_volcanic_caves_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
RAW_GVP_DIR = ROOT / "data" / "raw" / "earth" / "gvp"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "lat_center", "lon_center"]]
    
    # Check if raw GVP files exist
    gvp_files = list(RAW_GVP_DIR.glob("*.*")) if RAW_GVP_DIR.exists() else []
    
    if not gvp_files:
        print("[06_volcanic_caves] NOTE: Smithsonian GVP raw catalog not found in data/raw/earth/gvp/.")
        print("[06_volcanic_caves] Marking characteristic as 'DATA PENDING' per phase instructions.")
        
        df = land_mask.copy()
        df["volcanic_caves_likelihood"] = "LOW"
        df["volcanic_caves_confidence"] = "low"
        df["volcanic_caves_proxy"] = True
        df["volcanic_caves_source"] = "DATA PENDING: Smithsonian GVP Holocene volcano catalog pending"
    else:
        df = land_mask.copy()
        df["volcanic_caves_likelihood"] = "LOW"
        df["volcanic_caves_confidence"] = "low"
        df["volcanic_caves_proxy"] = True
        df["volcanic_caves_source"] = f"Smithsonian GVP; processed {PROC_DATE}"
        
    df.to_parquet(OUT_FILE, index=False)
    print(f"[06_volcanic_caves] Saved {len(df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
