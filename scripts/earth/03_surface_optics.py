"""
03_surface_optics.py — Earth surface optics preprocessing (MODIS BRDF/Albedo)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_surface_optics_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           broadband_albedo,
           surface_optics_confidence, surface_optics_proxy, surface_optics_source

Source: MODIS MCD43A3 (500 m, daily)
  - Band: Albedo_WSA_shortwave, scale ×0.001
  - QA filter: BRDF_Albedo_Band_Mandatory_Quality_shortwave == 0 (best quality)
  - Annual mean 2015–2022
  - Aggregated to 0.25° by mean of valid pixels

Runtime: ~15–25 min.
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
OUT_FILE = OUT_DIR / "earth_surface_optics_025deg.parquet"

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
COLLECTION = "MODIS/061/MCD43A3"
YEAR_START = 2015
YEAR_END = 2022
ALBEDO_SCALE = 0.001
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_albedo_image() -> ee.Image:
    """Return annual-mean broadband shortwave albedo (best-quality QA only)."""
    start = f"{YEAR_START}-01-01"
    end = f"{YEAR_END + 1}-01-01"
    col = (
        ee.ImageCollection(COLLECTION)
        .filterDate(start, end)
        .select(["Albedo_WSA_shortwave",
                 "BRDF_Albedo_Band_Mandatory_Quality_shortwave"])
    )

    def apply_qa_and_scale(img):
        qa = img.select("BRDF_Albedo_Band_Mandatory_Quality_shortwave")
        # Keep only pixels where QA == 0 (full BRDF inversion, best quality)
        good = qa.eq(0)
        albedo = img.select("Albedo_WSA_shortwave").multiply(ALBEDO_SCALE)
        return albedo.updateMask(good).rename("albedo")

    masked = col.map(apply_qa_and_scale)
    return masked.mean().rename("broadband_albedo")


def sample_global_grid(image: ee.Image) -> pd.DataFrame:
    lats = np.arange(-89.875, 90.0, CELL_DEG)
    lons = np.arange(-179.875, 180.0, CELL_DEG)

    records = []
    for lat in tqdm(lats, desc="Surface optics rows"):
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
                "broadband_albedo": info.get("broadband_albedo"),
            })
    return pd.DataFrame(records)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building MODIS MCD43A3 albedo image ({YEAR_START}–{YEAR_END}) …")
    albedo_img = build_albedo_image()

    print("Sampling 0.25° global grid …")
    df = sample_global_grid(albedo_img)

    # Drop ocean/no-data cells
    df = df.dropna(subset=["broadband_albedo"])

    # Clamp to [0, 1]
    df["broadband_albedo"] = df["broadband_albedo"].clip(0.0, 1.0)

    # Provenance
    df["cell_id"] = (
        "E_"
        + df["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    # Note: polar-night cells are dropped (null); remaining have best-quality QA
    df["surface_optics_confidence"] = "medium"
    df["surface_optics_proxy"] = False
    df["surface_optics_source"] = (
        f"{COLLECTION}; band Albedo_WSA_shortwave; QA==0 filter; "
        f"scale×{ALBEDO_SCALE}; years {YEAR_START}-{YEAR_END}; "
        f"processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "broadband_albedo",
        "surface_optics_confidence", "surface_optics_proxy", "surface_optics_source",
    ]
    df[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} land cells → {OUT_FILE}")


if __name__ == "__main__":
    main()
