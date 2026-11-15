"""
08_illumination.py — Earth illumination preprocessing
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_illumination_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           max_solar_elevation, max_solar_elevation_pct,
           mean_solar_elevation, mean_solar_elevation_pct,
           longest_polar_night_days, longest_polar_night_days_pct,
           longest_polar_day_days, longest_polar_day_days_pct,
           sun_fraction, sun_fraction_pct,
           illumination_confidence, illumination_proxy, illumination_source
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from tqdm import tqdm

OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_illumination_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"

CELL_DEG = 0.25
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Solar geometry
# ---------------------------------------------------------------------------

DAYS = np.arange(365)
# Declination (degrees) for each day: 23.44 × sin(360/365 × (d − 81))
_DECL_DEG = 23.44 * np.sin(np.radians(360.0 / 365.0 * (DAYS - 81.0)))
_DECL_RAD = np.radians(_DECL_DEG)


def compute_illumination(lat_deg: float) -> tuple[float, float, float, float, float]:
    """
    Return:
      max_solar_elevation_deg,
      mean_solar_elevation_deg,
      longest_polar_night_days,
      longest_polar_day_days,
      sun_fraction
    """
    phi = np.radians(lat_deg)
    max_elev = min(90.0, 90.0 - abs(lat_deg) + 23.44)

    tan_phi = np.tan(phi)
    tan_decl = np.tan(_DECL_RAD)
    cos_h0 = -tan_phi * tan_decl

    # Polar night: cos_h0 >= 1.0; Midnight sun: cos_h0 <= -1.0
    is_polar_night = cos_h0 >= 1.0
    is_polar_day = cos_h0 <= -1.0

    day_frac = np.where(
        is_polar_night, 0.0,
        np.where(is_polar_day, 1.0,
                 np.arccos(np.clip(cos_h0, -1.0, 1.0)) / np.pi)
    )
    sun_fraction = float(np.mean(day_frac))

    # Longest continuous run of polar night / polar day
    def max_continuous_run(mask: np.ndarray) -> float:
        if not np.any(mask):
            return 0.0
        # Check wrapped runs around year boundary
        runs = []
        cur = 0
        for val in np.concatenate([mask, mask]):
            if val:
                cur += 1
            else:
                runs.append(cur)
                cur = 0
        runs.append(cur)
        return float(min(365, max(runs)))

    longest_night = max_continuous_run(is_polar_night)
    longest_day = max_continuous_run(is_polar_day)

    # Time-weighted mean solar elevation above horizon
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    sin_decl = np.sin(_DECL_RAD)
    cos_decl = np.cos(_DECL_RAD)

    h0 = np.arccos(np.clip(cos_h0, -1.0, 1.0))
    with np.errstate(invalid="ignore", divide="ignore"):
        sinH0_over_H0 = np.where(h0 > 1e-9, np.sin(h0) / h0, 0.0)
    elev_arg = np.clip(sin_decl * sin_phi + cos_decl * cos_phi * sinH0_over_H0, -1.0, 1.0)
    elev_per_day = np.degrees(np.arcsin(elev_arg))

    total_weight = np.sum(day_frac)
    if total_weight > 0:
        mean_elev = float(np.sum(day_frac * elev_per_day) / total_weight)
    else:
        mean_elev = 0.0

    return max_elev, mean_elev, longest_night, longest_day, sun_fraction


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "lat_center", "lon_center", "land_fraction"]]
    
    print(f"[08_illumination] Computing analytical illumination for {len(land_mask):,} land cells...")
    
    # Cache by unique latitude (only 720 unique latitudes)
    unique_lats = land_mask["lat_center"].unique()
    lat_cache = {}
    for lat in unique_lats:
        lat_cache[lat] = compute_illumination(lat)
        
    records = []
    for lat in land_mask["lat_center"]:
        records.append(lat_cache[lat])
        
    res_df = pd.DataFrame(records, columns=[
        "max_solar_elevation",
        "mean_solar_elevation",
        "longest_polar_night_days",
        "longest_polar_day_days",
        "sun_fraction"
    ])
    
    merged = pd.concat([land_mask.reset_index(drop=True), res_df], axis=1)
    
    # Compute percentile ranks across Earth land cells
    for col in [
        "max_solar_elevation",
        "mean_solar_elevation",
        "longest_polar_night_days",
        "longest_polar_day_days",
        "sun_fraction",
    ]:
        merged[f"{col}_pct"] = merged[col].rank(pct=True).clip(0.0, 1.0)
        
    merged["illumination_confidence"] = "high"
    merged["illumination_proxy"] = False
    merged["illumination_source"] = (
        f"Analytical solar geometry (continuous polar night/day replacement); processed {PROC_DATE}"
    )
    
    cols = [
        "cell_id", "lat_center", "lon_center",
        "max_solar_elevation", "max_solar_elevation_pct",
        "mean_solar_elevation", "mean_solar_elevation_pct",
        "longest_polar_night_days", "longest_polar_night_days_pct",
        "longest_polar_day_days", "longest_polar_day_days_pct",
        "sun_fraction", "sun_fraction_pct",
        "illumination_confidence", "illumination_proxy", "illumination_source"
    ]
    merged = merged[cols]
    merged.to_parquet(OUT_FILE, index=False)
    print(f"[08_illumination] Saved {len(merged):,} land cells -> {OUT_FILE}")
    print(f"  Columns: {list(merged.columns)}")
    print(f"  Polar night cells (>0 days): {(merged['longest_polar_night_days'] > 0).sum():,}")
    print(f"  Polar day cells (>0 days): {(merged['longest_polar_day_days'] > 0).sum():,}")


if __name__ == "__main__":
    main()
