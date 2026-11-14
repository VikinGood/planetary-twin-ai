"""
07_ice_polar.py — Earth ice/polar preprocessing (MODIS MCD12Q1 + IPA GZI permafrost)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_ice_polar_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           ice_cover_fraction, permafrost_index, latitude_multiplier, ice_polar_score,
           ice_polar_confidence, ice_polar_proxy, ice_polar_source

Sources:
  EE: MODIS/061/MCD12Q1 — LC_Type1 annual land cover, class 15 = permanent snow/ice
      (annual mode 2015–2022, aggregate to 0.25° as ice_cover_fraction)
  Local: IPA Global Permafrost Zonation Index (GZI) GeoTIFF
         PANGAEA doi:10.1594/PANGAEA.783900
         Place in: data/raw/earth/ipa_gzi/

  If IPA GZI file is missing, the script exits 1 with download instructions.

Scoring (METHODOLOGY §2.5):
  permafrost_score   = permafrost_index × latitude_multiplier
  ice_polar_score    = geometric_mean(permafrost_score, ice_cover_fraction)
                     = sqrt(permafrost_score × ice_cover_fraction)
  latitude_multiplier: |lat|>55→1.0; 23.5–55→0.5; <23.5→0.0

Runtime: ~15–25 min (EE part) + ~5 min (rasterio part).
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import ee
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_ice_polar_025deg.parquet"
IPA_DIR = ROOT / "data" / "raw" / "earth" / "ipa_gzi"

IPA_DOWNLOAD_URL = "https://doi.pangaea.de/10.1594/PANGAEA.783900"
IPA_DOWNLOAD_NOTE = (
    "Download the IPA Global Permafrost Zonation Index (GZI) GeoTIFF from PANGAEA:\n"
    f"  {IPA_DOWNLOAD_URL}\n"
    f"Place it in: {IPA_DIR}/\n"
    "Free PANGAEA registration may be required."
)

load_dotenv(ROOT / ".env")
EE_PROJECT = os.environ.get("EE_PROJECT", "")
if not EE_PROJECT:
    print("ERROR: EE_PROJECT not set in .env", file=sys.stderr)
    sys.exit(1)
ee.Initialize(project=EE_PROJECT)

# ---------------------------------------------------------------------------
SCALE_500M = 500
CELL_DEG = 0.25
HALF = CELL_DEG / 2.0
MODIS_LC_COLLECTION = "MODIS/061/MCD12Q1"
YEAR_START = 2015
YEAR_END = 2022
SNOW_ICE_CLASS = 15    # IGBP class 15 = permanent snow/ice
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Part 1: MODIS ice cover fraction via EE
# ---------------------------------------------------------------------------

def build_ice_cover_image() -> ee.Image:
    """
    Annual mode of LC_Type1 (2015–2022), then binary class-15 mask.
    Returns a single-band image: ice_cover_fraction (0–1 at 0.25° after reduceRegion).
    """
    start = f"{YEAR_START}-01-01"
    end = f"{YEAR_END + 1}-01-01"
    col = (
        ee.ImageCollection(MODIS_LC_COLLECTION)
        .filterDate(start, end)
        .select("LC_Type1")
    )
    # Mode of annual land-cover class over the study period
    modal_lc = col.mode().rename("lc_mode")
    # Binary: 1 where permanent snow/ice
    ice_binary = modal_lc.eq(SNOW_ICE_CLASS).rename("ice_cover_fraction")
    return ice_binary.toFloat()


def sample_ice_cover(image: ee.Image) -> pd.DataFrame:
    lats = np.arange(-89.875, 90.0, CELL_DEG)
    lons = np.arange(-179.875, 180.0, CELL_DEG)

    records = []
    for lat in tqdm(lats, desc="Ice cover rows (EE)"):
        for lon in lons:
            region = ee.Geometry.Rectangle(
                [lon - HALF, lat - HALF, lon + HALF, lat + HALF]
            )
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=SCALE_500M,
                maxPixels=1e6,
                bestEffort=True,
            )
            info = stats.getInfo()
            records.append({
                "lat_center": lat,
                "lon_center": lon,
                "ice_cover_fraction": info.get("ice_cover_fraction"),
            })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Part 2: IPA GZI permafrost index via rasterio (local file)
# ---------------------------------------------------------------------------

def find_ipa_file() -> Path | None:
    candidates = sorted(IPA_DIR.glob("*.tif")) + sorted(IPA_DIR.glob("*.tiff"))
    return candidates[0] if candidates else None


def sample_permafrost_index(ipa_path: Path, cell_df: pd.DataFrame) -> pd.Series:
    """Read IPA GZI raster and aggregate to 0.25° by mean."""
    values = []
    with rasterio.open(ipa_path) as src:
        band = src.read(1).astype(float)
        transform = src.transform
        nodata = src.nodata
        if nodata is not None:
            band[band == nodata] = np.nan

        for _, row in tqdm(cell_df.iterrows(), total=len(cell_df),
                           desc="Permafrost index (rasterio)"):
            lat = row["lat_center"]
            lon = row["lon_center"]
            lat_min, lat_max = lat - HALF, lat + HALF
            lon_min, lon_max = lon - HALF, lon + HALF

            r_min, c_min = rowcol(transform, lon_min, lat_max)
            r_max, c_max = rowcol(transform, lon_max, lat_min)
            r_min = max(0, r_min)
            c_min = max(0, c_min)
            r_max = min(band.shape[0] - 1, r_max)
            c_max = min(band.shape[1] - 1, c_max)

            if r_min > r_max or c_min > c_max:
                values.append(np.nan)
                continue

            window = band[r_min: r_max + 1, c_min: c_max + 1]
            valid = window[~np.isnan(window)]
            values.append(float(np.mean(valid)) if len(valid) > 0 else np.nan)

    return pd.Series(values, index=cell_df.index)


# ---------------------------------------------------------------------------
# Latitude multiplier (METHODOLOGY §2.5)
# ---------------------------------------------------------------------------

def latitude_multiplier(lat: float) -> float:
    abs_lat = abs(lat)
    if abs_lat > 55.0:
        return 1.0
    if abs_lat >= 23.5:
        return 0.5
    return 0.0


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def compute_ice_polar_score(permafrost_idx: float, lat_mult: float,
                             ice_frac: float) -> float:
    """geometric_mean(permafrost_idx × lat_mult, ice_frac)."""
    if any(pd.isna(v) for v in [permafrost_idx, ice_frac]):
        return float("nan")
    p_score = float(np.clip(permafrost_idx, 0.0, 1.0)) * lat_mult
    i_score = float(np.clip(ice_frac, 0.0, 1.0))
    return float(np.sqrt(max(p_score, 0.0) * max(i_score, 0.0)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check IPA GZI before doing any EE work
    ipa_path = find_ipa_file()
    if ipa_path is None:
        print(
            f"ERROR: IPA GZI GeoTIFF not found in {IPA_DIR}/\n" + IPA_DOWNLOAD_NOTE,
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Building MODIS MCD12Q1 ice cover image ({YEAR_START}–{YEAR_END}) …")
    ice_img = build_ice_cover_image()

    print("Sampling ice cover on 0.25° global grid (EE) …")
    df_ice = sample_ice_cover(ice_img)

    # Keep all cells (ocean will have null; land mask applied in assembly)
    df_ice["ice_cover_fraction"] = df_ice["ice_cover_fraction"].fillna(0.0)

    print(f"Reading permafrost index from {ipa_path} …")
    df_ice["permafrost_index"] = sample_permafrost_index(ipa_path, df_ice)

    # Fill ocean/no-data permafrost with 0
    df_ice["permafrost_index"] = df_ice["permafrost_index"].fillna(0.0)

    # Latitude multiplier
    df_ice["latitude_multiplier"] = df_ice["lat_center"].map(latitude_multiplier)

    # Score
    df_ice["ice_polar_score"] = [
        compute_ice_polar_score(row["permafrost_index"],
                                row["latitude_multiplier"],
                                row["ice_cover_fraction"])
        for _, row in df_ice.iterrows()
    ]

    # Provenance
    df_ice["cell_id"] = (
        "E_"
        + df_ice["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df_ice["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    df_ice["ice_polar_confidence"] = "medium"
    df_ice["ice_polar_proxy"] = False
    df_ice["ice_polar_source"] = (
        f"MODIS MCD12Q1 LC_Type1 class 15, mode {YEAR_START}-{YEAR_END}; "
        f"IPA GZI {ipa_path.name}, PANGAEA doi:10.1594/PANGAEA.783900; "
        f"score=sqrt(permafrost×lat_mult, ice_frac); processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "ice_cover_fraction", "permafrost_index", "latitude_multiplier",
        "ice_polar_score",
        "ice_polar_confidence", "ice_polar_proxy", "ice_polar_source",
    ]
    df_ice[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df_ice):,} cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
