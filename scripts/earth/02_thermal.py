"""
02_thermal.py — Earth thermal preprocessing (MODIS LST)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_thermal_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           lst_annual_mean, lst_annual_range, lst_diurnal_range,
           thermal_low_confidence_flag,
           thermal_confidence, thermal_proxy, thermal_source

Source: MODIS MOD11A2 (8-day composite, 1 km)
  - Bands: LST_Day_1km, LST_Night_1km
  - Scale factor: ×0.02, then −273.15 to convert to °C
  - Annual stats: multi-year mean 2015–2022
  - Cells with < 8 valid annual observations flagged as low_confidence

Runtime: ~15–30 min.
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
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_thermal_025deg.parquet"

load_dotenv(ROOT / ".env")
EE_PROJECT = os.environ.get("EE_PROJECT", "")
if not EE_PROJECT:
    print("ERROR: EE_PROJECT not set in .env", file=sys.stderr)
    sys.exit(1)
ee.Initialize(project=EE_PROJECT)

# ---------------------------------------------------------------------------
SCALE_1KM = 1000
CELL_DEG = 0.25
HALF = CELL_DEG / 2.0
COLLECTION = "MODIS/061/MOD11A2"
YEAR_START = 2015
YEAR_END = 2022        # inclusive
LST_SCALE = 0.02
LST_OFFSET = -273.15
MIN_ANNUAL_OBS = 8     # flag cells with fewer valid composites
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_thermal_image() -> ee.Image:
    """
    Build a 4-band image (annual mean stats) over the 2015–2022 period.
    Returns bands: lst_annual_mean, lst_annual_range, lst_diurnal_range, obs_count
    """
    start = f"{YEAR_START}-01-01"
    end = f"{YEAR_END + 1}-01-01"
    col = (
        ee.ImageCollection(COLLECTION)
        .filterDate(start, end)
        .select(["LST_Day_1km", "LST_Night_1km"])
    )

    def scale_to_celsius(img):
        day = img.select("LST_Day_1km").multiply(LST_SCALE).add(LST_OFFSET)
        night = img.select("LST_Night_1km").multiply(LST_SCALE).add(LST_OFFSET)
        diurnal = day.subtract(night)
        # Mask fill values (== 0 before scaling means unobserved)
        valid_mask = img.select("LST_Day_1km").gt(0).And(
            img.select("LST_Night_1km").gt(0)
        )
        return (
            day.rename("day")
            .addBands(night.rename("night"))
            .addBands(diurnal.rename("diurnal"))
            .updateMask(valid_mask)
            .copyProperties(img, ["system:time_start"])
        )

    scaled = col.map(scale_to_celsius)

    # Annual statistics
    day_mean = scaled.select("day").mean().rename("lst_annual_mean")
    # Range: difference between the annual max and min of the per-composite mean
    day_max = scaled.select("day").max()
    day_min = scaled.select("day").min()
    annual_range = day_max.subtract(day_min).rename("lst_annual_range")
    # Diurnal range: mean of (day−night) across all 8-day composites
    diurnal_mean = scaled.select("diurnal").mean().rename("lst_diurnal_range")
    # Observation count (number of valid composites)
    obs_count = scaled.select("day").count().rename("obs_count")

    return day_mean.addBands(annual_range).addBands(diurnal_mean).addBands(obs_count)


def sample_global_grid(image: ee.Image) -> pd.DataFrame:
    lats = np.arange(-89.875, 90.0, CELL_DEG)
    lons = np.arange(-179.875, 180.0, CELL_DEG)

    records = []
    for lat in tqdm(lats, desc="Thermal rows"):
        for lon in lons:
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
                "lst_annual_mean": info.get("lst_annual_mean"),
                "lst_annual_range": info.get("lst_annual_range"),
                "lst_diurnal_range": info.get("lst_diurnal_range"),
                "obs_count": info.get("obs_count"),
            })
    return pd.DataFrame(records)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building MODIS LST image ({YEAR_START}–{YEAR_END}) …")
    thermal_img = build_thermal_image()

    print("Sampling 0.25° global grid …")
    df = sample_global_grid(thermal_img)

    # Drop ocean/no-data cells
    df = df.dropna(subset=["lst_annual_mean", "lst_annual_range", "lst_diurnal_range"])

    # Low-confidence flag: < MIN_ANNUAL_OBS valid composites
    df["thermal_low_confidence_flag"] = (
        df["obs_count"].fillna(0) < MIN_ANNUAL_OBS
    )

    # Provenance
    df["cell_id"] = (
        "E_"
        + df["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    df["thermal_confidence"] = df["thermal_low_confidence_flag"].map(
        {True: "low", False: "medium"}
    )
    df["thermal_proxy"] = False
    df["thermal_source"] = (
        f"{COLLECTION}; bands LST_Day_1km LST_Night_1km; "
        f"years {YEAR_START}-{YEAR_END}; scale×{LST_SCALE} offset {LST_OFFSET}°C; "
        f"processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "lst_annual_mean", "lst_annual_range", "lst_diurnal_range",
        "thermal_low_confidence_flag",
        "thermal_confidence", "thermal_proxy", "thermal_source",
    ]
    df[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
