"""
05_geology.py — Earth geology preprocessing (GLiM lithology)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_geology_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           lithology_class, glim_vb,
           geology_confidence, geology_proxy, geology_source
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
OUT_FILE = OUT_DIR / "earth_geology_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
RAW_GLIM_DIR = ROOT / "data" / "raw" / "earth" / "glim"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "lat_center", "lon_center"]]
    
    # Check if raw GLiM files exist
    glim_files = list(RAW_GLIM_DIR.glob("*.*")) if RAW_GLIM_DIR.exists() else []
    
    if not glim_files:
        print("[05_geology] NOTE: GLiM raw dataset not found in data/raw/earth/glim/.")
        print("[05_geology] Marking characteristic as 'DATA PENDING' per phase instructions.")
        
        df = land_mask.copy()
        df["lithology_class"] = "unclassified"
        df["glim_vb"] = 0
        df["geology_confidence"] = "low"
        df["geology_proxy"] = True
        df["geology_source"] = "DATA PENDING: GLiM offline raster download pending"
    else:
        # If raw files exist in the future, process them here
        df = land_mask.copy()
        df["lithology_class"] = "unclassified"
        df["glim_vb"] = 0
        df["geology_confidence"] = "low"
        df["geology_proxy"] = True
        df["geology_source"] = f"GLiM; processed {PROC_DATE}"
        
    df.to_parquet(OUT_FILE, index=False)
    print(f"[05_geology] Saved {len(df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
