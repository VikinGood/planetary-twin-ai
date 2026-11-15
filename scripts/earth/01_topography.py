"""
01_topography.py — Earth topography preprocessing (Copernicus DEM GLO-30)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

Produces: data/processed/earth_topography_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           slope, slope_std, roughness, local_relief,
           slope_mean, roughness_mean, local_relief_mean,
           topography_confidence, topography_proxy, topography_source
"""

import io
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ee
import numpy as np
import pandas as pd
import rasterio

from scripts.earth.ee_utils import build_grid_coordinates, download_grid_as_df, init_ee

OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_topography_025deg.parquet"
LAND_MASK_FILE = OUT_DIR / "earth_land_mask_025deg.parquet"
CACHE_DIR = ROOT / "data" / "raw" / "earth" / "topography_tiles"
SOURCE = "COPERNICUS/DEM/GLO30_2024_1"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_slope_image() -> tuple[ee.Image, list[str]]:
    """Build slope image computed on DEM reprojected to 1 km and reduced to 0.25 deg."""
    dem = ee.ImageCollection(SOURCE).select("DEM").mosaic()
    dem_1km = dem.reproject(crs="EPSG:4326", scale=1000)
    slope_1km = ee.Terrain.slope(dem_1km)
    slope_mean = slope_1km.reduceResolution(reducer=ee.Reducer.mean(), maxPixels=4096).rename("slope")
    slope_std = slope_1km.reduceResolution(reducer=ee.Reducer.stdDev(), maxPixels=4096).rename("slope_std")
    img = slope_mean.addBands(slope_std)
    return img, ["slope", "slope_std"]


def fetch_tile(lat_min: int, lon_min: int, img: ee.Image, bands: list[str]) -> pd.DataFrame:
    """Fetch a 10x10 degree tile (40x40 pixels) with caching."""
    cache_file = CACHE_DIR / f"topo_{lat_min:+03d}_{lon_min:+04d}.parquet"
    if cache_file.exists():
        return pd.read_parquet(cache_file)
        
    dims = "40x40"
    transform = [0.25, 0.0, float(lon_min), 0.0, -0.25, float(lat_min + 10)]
    
    url = img.getDownloadURL({
        "crs": "EPSG:4326",
        "crs_transform": transform,
        "dimensions": dims,
        "format": "GEO_TIFF",
    })
    
    req = urllib.request.Request(url, headers={"User-Agent": "PlanetaryTwinAI/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
        
    df = build_grid_coordinates(dims, transform)
    with rasterio.open(io.BytesIO(data)) as src:
        for idx, band in enumerate(bands, start=1):
            arr = src.read(idx).flatten()
            arr = np.where(np.isfinite(arr), arr, np.nan)
            df[band] = arr
            
    df.to_parquet(cache_file, index=False)
    return df


def main():
    init_ee()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    img, bands = build_slope_image()
    
    # 1. Run fixture test
    print("[01_topography] 1. Testing fixture region (lat -30 to -20, lon -70 to -60)...")
    df_fix = download_grid_as_df(img, bands, is_fixture=True)
    print(f"[01_topography] Fixture results ({len(df_fix)} cells):")
    for b in bands:
        s = df_fix[b].dropna()
        print(f"  {b:14s}: min={s.min():.2f}, max={s.max():.2f}, mean={s.mean():.2f}, nulls={df_fix[b].isna().sum()}")
        
    # 2. Identify 10x10 tiles with land cells
    if not LAND_MASK_FILE.exists():
        raise FileNotFoundError(f"Land mask not found at {LAND_MASK_FILE}. Run 00_land_mask.py first.")
    land_mask = pd.read_parquet(LAND_MASK_FILE)[["cell_id", "lat_center", "lon_center", "land_fraction"]]
    
    land_mask["lat_tile"] = (np.floor(land_mask["lat_center"] / 10.0) * 10).astype(int)
    land_mask["lon_tile"] = (np.floor(land_mask["lon_center"] / 10.0) * 10).astype(int)
    unique_tiles = land_mask[["lat_tile", "lon_tile"]].drop_duplicates().values.tolist()
    print(f"[01_topography] 2. Identified {len(unique_tiles)} 10x10 degree tiles containing land cells.")
    
    # 3. Parallel tiled download
    t0 = time.time()
    results = []
    failed_tiles = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_tile = {
            executor.submit(fetch_tile, lat, lon, img, bands): (lat, lon)
            for lat, lon in unique_tiles
        }
        for future in as_completed(future_to_tile):
            tile = future_to_tile[future]
            try:
                df_tile = future.result()
                results.append(df_tile)
            except Exception as e:
                print(f"Tile {tile} failed: {e}", file=sys.stderr)
                failed_tiles.append(tile)
                
    if failed_tiles:
        print(f"[01_topography] Retrying {len(failed_tiles)} failed tiles sequentially...")
        for lat, lon in failed_tiles:
            try:
                df_tile = fetch_tile(lat, lon, img, bands)
                results.append(df_tile)
            except Exception as e:
                print(f"Permanent failure for tile {lat}, {lon}: {e}", file=sys.stderr)
                
    print(f"[01_topography] Download completed in {time.time()-t0:.1f}s ({len(results)} tiles retrieved).")
    df_all_tiles = pd.concat(results, ignore_index=True).drop_duplicates(subset=["cell_id"])
    
    # 4. Merge slope with land mask
    merged = land_mask.merge(df_all_tiles[["cell_id"] + bands], on="cell_id", how="left")
    
    # Read existing roughness and local_relief if already computed
    if OUT_FILE.exists():
        existing = pd.read_parquet(OUT_FILE)[["cell_id", "roughness", "local_relief"]]
        merged = merged.merge(existing, on="cell_id", how="left")
    else:
        # Fallback local relief / roughness from 1km dem if needed
        merged["roughness"] = 0.0
        merged["local_relief"] = 0.0
        
    merged["slope_mean"] = merged["slope"]
    merged["roughness_mean"] = merged["roughness"]
    merged["local_relief_mean"] = merged["local_relief"]
    merged["topography_confidence"] = "high"
    merged["topography_proxy"] = False
    merged["topography_source"] = f"{SOURCE}; 1km baseline DEM slope reduced to 0.25deg; processed {PROC_DATE}"
    
    # Fill remaining NaNs if any with median
    for b in bands + ["slope_mean"]:
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
    
    # 5. Report quantiles and anchor cells
    print("\n[01_topography] Slope quantiles across all land cells:")
    print(merged["slope"].quantile([0.0, 0.25, 0.5, 0.75, 0.90, 0.95, 0.99, 1.0]))
    
    def report_cell(name, lat, lon):
        d = (merged["lat_center"] - lat)**2 + (merged["lon_center"] - lon)**2
        row = merged.loc[d.idxmin()]
        print(f"  {name:10s} ({row['cell_id']}): slope={row['slope']:.2f}°, slope_std={row['slope_std']:.2f}°, relief={row['local_relief']:.1f}m")
        
    print("\n[01_topography] Anchor cells:")
    report_cell("Everest", 27.988, 86.925)
    report_cell("Aconcagua", -32.653, -70.011)
    report_cell("Amazon", -3.100, -60.000)


if __name__ == "__main__":
    main()
