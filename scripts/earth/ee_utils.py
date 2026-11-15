"""
ee_utils.py — Helper utilities for server-side Earth Engine reductions and grid downloads.
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.
"""

from __future__ import annotations

import io
import os
import urllib.request
from pathlib import Path
from typing import Sequence

import ee
import numpy as np
import pandas as pd
import rasterio
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

CELL_DEG = 0.25
GLOBAL_DIMS = "1440x720"
GLOBAL_TRANSFORM = [0.25, 0.0, -180.0, 0.0, -0.25, 90.0]

# Fixture: lat -30 to -20 (10 deg = 40 cells), lon -70 to -60 (10 deg = 40 cells)
FIXTURE_DIMS = "40x40"
FIXTURE_TRANSFORM = [0.25, 0.0, -70.0, 0.0, -0.25, -20.0]


def init_ee():
    """Initialize Earth Engine with project from .env."""
    proj = os.environ.get("EE_PROJECT", "")
    if not proj:
        raise RuntimeError("EE_PROJECT not found in .env")
    ee.Initialize(project=proj)


def build_grid_coordinates(dimensions: str, crs_transform: Sequence[float]) -> pd.DataFrame:
    """Compute center lat/lon for each pixel in the raster defined by transform and dimensions."""
    cols, rows = map(int, dimensions.split("x"))
    x_res, _, x_min, _, y_res, y_max = crs_transform  # y_res is negative
    
    # Pixel centers
    lons = x_min + (np.arange(cols) + 0.5) * x_res
    lats = y_max + (np.arange(rows) + 0.5) * y_res
    
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    flat_lats = np.round(lat_grid.flatten(), 3)
    flat_lons = np.round(lon_grid.flatten(), 3)
    
    cell_ids = [f"E_{lat:+.3f}_{lon:+.3f}" for lat, lon in zip(flat_lats, flat_lons)]
    
    return pd.DataFrame({
        "cell_id": cell_ids,
        "lat_center": flat_lats,
        "lon_center": flat_lons,
    })


def download_grid_as_df(
    image: ee.Image,
    band_names: list[str],
    is_fixture: bool = False,
) -> pd.DataFrame:
    """Download server-reduced image via getDownloadURL as GeoTIFF and return DataFrame."""
    dims = FIXTURE_DIMS if is_fixture else GLOBAL_DIMS
    transform = FIXTURE_TRANSFORM if is_fixture else GLOBAL_TRANSFORM
    
    url = image.getDownloadURL({
        "crs": "EPSG:4326",
        "crs_transform": transform,
        "dimensions": dims,
        "format": "GEO_TIFF",
    })
    
    req = urllib.request.Request(url, headers={"User-Agent": "PlanetaryTwinAI/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="replace")
        print(f"EE Download Error: {err.code} {err.reason}\nBody: {err_msg}", file=sys.stderr)
        raise
        
    df = build_grid_coordinates(dims, transform)
    
    with rasterio.open(io.BytesIO(data)) as src:
        for idx, band_name in enumerate(band_names, start=1):
            arr = src.read(idx).flatten()
            # Replace NaNs / Infs / nodata
            arr = np.where(np.isfinite(arr), arr, np.nan)
            df[band_name] = arr
            
    return df
