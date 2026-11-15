"""
06_volcanic_caves.py — Earth volcanic caves preprocessing (Smithsonian GVP Holocene volcanoes)
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
GEOLOGY_FILE = OUT_DIR / "earth_geology_025deg.parquet"
RAW_GVP_FILE = ROOT / "data" / "raw" / "earth" / "gvp" / "volcanoes.csv"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Qualifying volcano types for lava tube formation (METHODOLOGY §2.6; Lava domes removed)
QUALIFYING_TYPES = [
    "Shield",
    "Shield(s)",
    "Shield(pyroclastic)",
    "Volcanic field",
    "Fissure vent(s)",
    "Fissure vent"
]


def to_cartesian(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Convert lat/lon degrees to 3D Cartesian coordinates on unit sphere."""
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)
    return np.column_stack([x, y, z])


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "lat_center", "lon_center"]]
    
    if not RAW_GVP_FILE.exists():
        print(f"[06_volcanic_caves] WARNING: GVP raw catalog not found at {RAW_GVP_FILE}.")
        print("[06_volcanic_caves] Writing NULL for volcanic_caves columns as requested by analyst notes.")
        df = land_mask.copy()
        df["volcanic_caves_likelihood"] = None
        df["volcanic_caves_confidence"] = "low"
        df["volcanic_caves_proxy"] = True
        df["volcanic_caves_source"] = "DATA PENDING: Smithsonian GVP volcano catalog missing"
        df.to_parquet(OUT_FILE, index=False)
        return
        
    print(f"[06_volcanic_caves] Loading Smithsonian GVP catalog from {RAW_GVP_FILE}...")
    v_df = pd.read_csv(RAW_GVP_FILE)
    
    # Filter to qualifying types
    v_qual = v_df[v_df["type"].isin(QUALIFYING_TYPES)].dropna(subset=["lat", "lon"]).copy()
    print(f"[06_volcanic_caves] Filtered to {len(v_qual)} qualifying basaltic volcanoes (types: {QUALIFYING_TYPES}).")
    
    # Compute distances using 3D dot product on unit sphere
    cell_xyz = to_cartesian(land_mask["lat_center"].values, land_mask["lon_center"].values)
    volc_xyz = to_cartesian(v_qual["lat"].values, v_qual["lon"].values)
    
    print("[06_volcanic_caves] Computing nearest qualifying volcano distance for 337,611 land cells...")
    # (N, 3) @ (3, M) = (N, M)
    cos_sim = cell_xyz @ volc_xyz.T
    max_cos = np.max(cos_sim, axis=1)
    min_dist_km = 6371.0 * np.arccos(np.clip(max_cos, -1.0, 1.0))
    
    # Read glim_vb from geology file if available
    glim_vb = np.zeros(len(land_mask), dtype=int)
    if GEOLOGY_FILE.exists():
        geo = pd.read_parquet(GEOLOGY_FILE)[["cell_id", "glim_vb"]]
        m_geo = land_mask[["cell_id"]].merge(geo, on="cell_id", how="left")
        glim_vb = m_geo["glim_vb"].fillna(0).astype(int).values
        
    # Likelihood rules (METHODOLOGY §2.6):
    # HIGH: glim_vb == 1 AND dist <= 50 km
    # MEDIUM: glim_vb == 1 OR dist <= 100 km
    # LOW: neither
    is_vb = (glim_vb == 1)
    is_d50 = (min_dist_km <= 50.0)
    is_d100 = (min_dist_km <= 100.0)
    
    likelihood = np.where(
        is_vb & is_d50,
        "HIGH",
        np.where(is_vb | is_d100, "MEDIUM", "LOW")
    )
    
    df = land_mask.copy()
    df["volcanic_caves_likelihood"] = likelihood
    df["volcanic_caves_confidence"] = "low"
    df["volcanic_caves_proxy"] = True
    df["volcanic_caves_source"] = (
        f"Smithsonian GVP Holocene catalog ({len(v_qual)} volcanoes) + GLiM 0.5deg basic volcanic; "
        f"processed {PROC_DATE}"
    )
    
    df.to_parquet(OUT_FILE, index=False)
    print(f"[06_volcanic_caves] Saved {len(df):,} land cells -> {OUT_FILE}")
    print("  Likelihood breakdown:")
    print(df["volcanic_caves_likelihood"].value_counts())


if __name__ == "__main__":
    main()
