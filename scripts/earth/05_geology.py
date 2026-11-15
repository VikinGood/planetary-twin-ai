"""
05_geology.py — Earth geology preprocessing (GLiM 0.5 deg raster)
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
RAW_GLIM_FILE = ROOT / "data" / "raw" / "earth" / "glim" / "glim_wgs84_0point5deg.txt.asc"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

GLIM_INT_TO_CLASS = {
    1: "su",  # Unconsolidated sediments
    2: "vb",  # Basic volcanic rocks
    3: "ss",  # Siliciclastic sedimentary rocks
    4: "pb",  # Basic plutonic rocks
    5: "sm",  # Mixed sedimentary rocks
    6: "sc",  # Carbonate sedimentary rocks
    7: "va",  # Acid volcanic rocks
    8: "mt",  # Metamorphic rocks
    9: "pa",  # Acid plutonic rocks
    10: "vi", # Intermediate volcanic rocks
    11: "wb", # Water bodies
    12: "py", # Pyroclastics
    13: "pi", # Intermediate plutonic rocks
    14: "ev", # Evaporites
    15: "nd", # No data
    16: "ig", # Ice and glaciers
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "lat_center", "lon_center"]]
    
    if not RAW_GLIM_FILE.exists():
        print(f"[05_geology] WARNING: GLiM raw raster not found at {RAW_GLIM_FILE}.")
        print("[05_geology] Writing NULL for geology columns as requested by analyst notes.")
        df = land_mask.copy()
        df["lithology_class"] = None
        df["glim_vb"] = None
        df["geology_confidence"] = "low"
        df["geology_proxy"] = True
        df["geology_source"] = "DATA PENDING: GLiM 0.5deg raster missing"
        df.to_parquet(OUT_FILE, index=False)
        return
        
    print(f"[05_geology] Loading GLiM 0.5 deg ASC grid from {RAW_GLIM_FILE}...")
    glim_grid = np.loadtxt(RAW_GLIM_FILE, skiprows=6, dtype=int)
    
    # Map lat/lon to row/col
    # Row 0 = lat +90, Row 359 = lat -90
    # Col 0 = lon -180, Col 719 = lon +180
    lats = land_mask["lat_center"].values
    lons = land_mask["lon_center"].values
    
    rows = np.clip(np.floor((90.0 - lats) / 0.5).astype(int), 0, 359)
    cols = np.clip(np.floor((lons + 180.0) / 0.5).astype(int), 0, 719)
    
    values = glim_grid[rows, cols]
    
    lithology_classes = [GLIM_INT_TO_CLASS.get(val, None) if val > 0 and val != 15 else None for val in values]
    glim_vbs = [1 if cls == "vb" else (0 if cls is not None else None) for cls in lithology_classes]
    
    df = land_mask.copy()
    df["lithology_class"] = lithology_classes
    df["glim_vb"] = glim_vbs
    df["geology_confidence"] = ["high" if cls is not None else "low" for cls in lithology_classes]
    df["geology_proxy"] = False
    df["geology_source"] = f"GLiM 0.5deg raster (Hartmann & Moosdorf 2012, PANGAEA); processed {PROC_DATE}"
    
    df.to_parquet(OUT_FILE, index=False)
    print(f"[05_geology] Saved {len(df):,} land cells -> {OUT_FILE}")
    valid_count = df["lithology_class"].notna().sum()
    vb_count = (df["glim_vb"] == 1).sum()
    print(f"  Valid lithology cells: {valid_count:,} ({valid_count/len(df)*100:.1f}%)")
    print(f"  Basic volcanic (vb) cells: {vb_count:,} ({vb_count/len(df)*100:.2f}%)")


if __name__ == "__main__":
    main()
