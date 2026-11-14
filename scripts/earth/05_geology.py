"""
05_geology.py — Earth geology preprocessing (GLiM lithological map)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_geology_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           glim_class, glim_vb,
           geology_confidence, geology_proxy, geology_source

Source: GLiM — Global Lithological Map (Hartmann & Moosdorf 2012)
  PANGAEA doi:10.1594/PANGAEA.788537
  Place the raster GeoTIFF at: data/raw/earth/glim/glim_wgs84_0point5deg.tif
  (or the full-resolution version; script reads whatever GeoTIFF is present)

  If the file is not present, the script prints download instructions and exits 1.

GLiM class codes (from Hartmann & Moosdorf 2012):
  vb  = basic volcanic (basaltic)   — key class for volcanic_caves proxy
  va  = acid volcanic
  vi  = intermediate volcanic
  pb  = basic plutonic
  pa  = acid plutonic
  pi  = intermediate plutonic
  sc  = carbonate sedimentary
  ss  = siliciclastic sedimentary
  sm  = mixed sedimentary
  su  = unconsolidated sediments
  ev  = evaporites
  py  = pyroclastics
  mt  = metamorphic
  wb  = water bodies
  ice = glaciers / ice
  nd  = no data

Runtime: ~5–15 min (pure local rasterio + GeoPandas).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol
from tqdm import tqdm

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_geology_025deg.parquet"
RAW_DIR = ROOT / "data" / "raw" / "earth" / "glim"

DOWNLOAD_URL = "https://doi.pangaea.de/10.1594/PANGAEA.788537"
DOWNLOAD_NOTE = (
    "Download the GLiM raster (GeoTIFF) from PANGAEA:\n"
    f"  {DOWNLOAD_URL}\n"
    "Look for a file named 'glim_wgs84_0point5deg.tif' or similar.\n"
    f"Place it in: {RAW_DIR}/\n"
    "Free PANGAEA registration may be required."
)

# ---------------------------------------------------------------------------
CELL_DEG = 0.25
HALF = CELL_DEG / 2.0
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# GLiM class integer → string mapping (adjust if the actual raster uses different values)
# The GeoTIFF from PANGAEA encodes classes as integers in the raster band.
# This mapping is based on Hartmann & Moosdorf (2012) Table 1.
GLIM_INT_TO_CLASS = {
    1: "vb",  2: "va",  3: "vi",  4: "pb",  5: "pa",  6: "pi",
    7: "sc",  8: "ss",  9: "sm", 10: "su", 11: "ev", 12: "py",
    13: "mt", 14: "wb", 15: "ice", 0: "nd",
}

VOLCANIC_BASIC_CLASS = "vb"


def find_glim_file() -> Path:
    """Return the first GeoTIFF found in the GLiM raw directory, or raise."""
    candidates = sorted(RAW_DIR.glob("*.tif")) + sorted(RAW_DIR.glob("*.tiff"))
    if not candidates:
        return None
    return candidates[0]


def mode_in_window(data: np.ndarray, nodata) -> int | None:
    """Return the most common value in data, ignoring nodata."""
    flat = data.flatten()
    if nodata is not None:
        flat = flat[flat != nodata]
    if len(flat) == 0:
        return None
    vals, counts = np.unique(flat, return_counts=True)
    return int(vals[np.argmax(counts)])


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    glim_path = find_glim_file()
    if glim_path is None:
        print(
            f"ERROR: GLiM GeoTIFF not found in {RAW_DIR}/\n"
            + DOWNLOAD_NOTE,
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Reading GLiM raster: {glim_path}")
    records = []

    with rasterio.open(glim_path) as src:
        band = src.read(1)
        transform = src.transform
        nodata = src.nodata
        res_x = abs(transform.a)   # pixel width in degrees
        res_y = abs(transform.e)   # pixel height in degrees

        lats = np.arange(-89.875, 90.0, CELL_DEG)
        lons = np.arange(-179.875, 180.0, CELL_DEG)

        for lat in tqdm(lats, desc="Geology rows"):
            for lon in lons:
                # Compute pixel window covering the 0.25° cell
                lat_min = lat - HALF
                lat_max = lat + HALF
                lon_min = lon - HALF
                lon_max = lon + HALF

                # Row/col indices (top-left corner of raster)
                row_min, col_min = rowcol(transform, lon_min, lat_max)
                row_max, col_max = rowcol(transform, lon_max, lat_min)

                # Clamp to raster bounds
                row_min = max(0, row_min)
                col_min = max(0, col_min)
                row_max = min(band.shape[0] - 1, row_max)
                col_max = min(band.shape[1] - 1, col_max)

                if row_min > row_max or col_min > col_max:
                    continue

                window_data = band[row_min: row_max + 1, col_min: col_max + 1]
                modal_int = mode_in_window(window_data, nodata)

                if modal_int is None:
                    continue

                glim_class = GLIM_INT_TO_CLASS.get(modal_int, "nd")
                # Skip water / no-data classes
                if glim_class in ("wb", "nd"):
                    continue

                records.append({
                    "lat_center": lat,
                    "lon_center": lon,
                    "glim_class": glim_class,
                    "glim_vb": int(glim_class == VOLCANIC_BASIC_CLASS),
                })

    df = pd.DataFrame(records)

    # Provenance
    df["cell_id"] = (
        "E_"
        + df["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    df["geology_confidence"] = "medium"
    df["geology_proxy"] = False
    df["geology_source"] = (
        f"GLiM — Hartmann & Moosdorf 2012, PANGAEA doi:10.1594/PANGAEA.788537; "
        f"file={glim_path.name}; mode of 1 km pixels per 0.25° cell; "
        f"processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "glim_class", "glim_vb",
        "geology_confidence", "geology_proxy", "geology_source",
    ]
    df[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
