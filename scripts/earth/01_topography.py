"""
01_topography.py — Earth topography preprocessing
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_topography_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           slope_mean, roughness_mean, local_relief_mean,
           topography_confidence, topography_proxy, topography_source

Source: Copernicus DEM GLO-30 (EE asset COPERNICUS/DEM/GLO30_2024_1)
  - Resampled to 1 km on EE
  - slope (°), roughness (std-dev in 3×3 km window), local_relief (range in 12 km radius)
  - Aggregated to 0.25° by mean of valid 1 km pixels per cell

Runtime: ~10–20 min depending on EE quota.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import ee
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_topography_025deg.parquet"

# ---------------------------------------------------------------------------
# EE initialisation
# ---------------------------------------------------------------------------
load_dotenv(ROOT / ".env")
EE_PROJECT = os.environ.get("EE_PROJECT", "")
if not EE_PROJECT:
    print("ERROR: EE_PROJECT not set in .env", file=sys.stderr)
    sys.exit(1)
ee.Initialize(project=EE_PROJECT)

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
SCALE_1KM = 1000        # metres — common 1 km baseline
CELL_DEG = 0.25         # target grid spacing
HALF = CELL_DEG / 2.0
SOURCE = "COPERNICUS/DEM/GLO30_2024_1"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# EE computation helpers
# ---------------------------------------------------------------------------

def build_topography_image() -> ee.Image:
    """Return a 3-band EE image: slope_deg, roughness_m, local_relief_m at ~1 km."""
    dem = ee.ImageCollection(SOURCE).select("DEM").mosaic()

    # Resample DEM to 1 km (bilinear)
    dem_1km = dem.resample("bilinear").reproject(crs="EPSG:4326", scale=SCALE_1KM)

    # Slope (°)
    slope = ee.Terrain.slope(dem_1km)

    # Roughness: std-dev of elevation in 3×3 km (3 pixel) window
    kernel_3px = ee.Kernel.square(radius=1, units="pixels")
    roughness = dem_1km.reduceNeighborhood(
        reducer=ee.Reducer.stdDev(), kernel=kernel_3px
    ).rename("roughness")

    # Local relief: elevation range in 12 km radius (~12 pixel radius at 1 km)
    kernel_12km = ee.Kernel.circle(radius=12, units="pixels")
    local_relief = dem_1km.reduceNeighborhood(
        reducer=ee.Reducer.minMax(), kernel=kernel_12km
    )
    local_relief = local_relief.select("DEM_max").subtract(
        local_relief.select("DEM_min")
    ).rename("local_relief")

    return slope.rename("slope").addBands(roughness).addBands(local_relief)


def sample_global_grid(image: ee.Image) -> pd.DataFrame:
    """Sample image at every 0.25° cell centroid using EE reduceRegion in tiles."""
    lats = np.arange(-89.875, 90.0, CELL_DEG)
    lons = np.arange(-179.875, 180.0, CELL_DEG)

    records = []
    total_tiles = len(range(0, len(lats), 20))
    for i, lat_start_idx in enumerate(tqdm(range(0, len(lats), 20),
                                           desc="Topography tiles", total=total_tiles)):
        lat_chunk = lats[lat_start_idx: lat_start_idx + 20]
        for lat in lat_chunk:
            for lon in lons:
                point = ee.Geometry.Point([float(lon), float(lat)])
                val = image.sample(region=point, scale=SCALE_1KM,
                                   numPixels=1, geometries=False).first()
                # EE sampling: use reduceRegion on small rectangle for reliability
                region = ee.Geometry.Rectangle(
                    [lon - HALF, lat - HALF, lon + HALF, lat + HALF]
                )
                stats = image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=region,
                    scale=SCALE_1KM,
                    maxPixels=1e6,
                    bestEffort=True,
                )
                info = stats.getInfo()
                records.append({
                    "lat_center": lat,
                    "lon_center": lon,
                    "slope_mean": info.get("slope"),
                    "roughness_mean": info.get("roughness"),
                    "local_relief_mean": info.get("local_relief"),
                })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building topography image on EE (source: {SOURCE}) …")
    topo_img = build_topography_image()

    print("Sampling 0.25° global grid (this takes ~10–20 min) …")
    df = sample_global_grid(topo_img)

    # Drop ocean cells (all three variables null)
    df = df.dropna(subset=["slope_mean", "roughness_mean", "local_relief_mean"])

    # Add provenance columns
    df["cell_id"] = (
        "E_"
        + df["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    df["topography_confidence"] = "high"
    df["topography_proxy"] = False
    df["topography_source"] = f"{SOURCE}; processed {PROC_DATE}; resolution_m=1000"

    df = df[["cell_id", "lat_center", "lon_center",
             "slope_mean", "roughness_mean", "local_relief_mean",
             "topography_confidence", "topography_proxy", "topography_source"]]

    df.to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
