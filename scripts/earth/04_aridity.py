"""
04_aridity.py — Earth aridity preprocessing (TerraClimate pr/pet)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_aridity_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           annual_pr_mm, annual_pet_mm, aridity_index,
           aridity_score,
           aridity_confidence, aridity_proxy, aridity_source

Source: TerraClimate (IDAHO_EPSCOR/TERRACLIMATE)
  - Band pr: precipitation mm/month (no scale factor needed)
  - Band pet: potential evapotranspiration mm/month × 0.1 (multiply raw by 0.1)
  - Annual sum both over 2015–2022 mean year
  - aridity_index = annual_pr / annual_pet (capped at 2.0 to avoid div-by-zero)
  - aridity_score = 1 − min(aridity_index, 1)  [REQUIREMENT type]

Runtime: ~10–20 min.
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
OUT_FILE = OUT_DIR / "earth_aridity_025deg.parquet"

load_dotenv(ROOT / ".env")
EE_PROJECT = os.environ.get("EE_PROJECT", "")
if not EE_PROJECT:
    print("ERROR: EE_PROJECT not set in .env", file=sys.stderr)
    sys.exit(1)
ee.Initialize(project=EE_PROJECT)

# ---------------------------------------------------------------------------
SCALE_4KM = 4000       # TerraClimate native ~4 km; use for reduceRegion
CELL_DEG = 0.25
HALF = CELL_DEG / 2.0
COLLECTION = "IDAHO_EPSCOR/TERRACLIMATE"
YEAR_START = 2015
YEAR_END = 2022
PET_SCALE = 0.1        # raw integer × 0.1 → mm/month
ARIDITY_CAP = 2.0      # cap aridity_index to avoid extreme values in ice cells
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_aridity_image() -> ee.Image:
    """Return a 2-band image: annual_pr and annual_pet in mm/yr (mean year 2015–2022)."""
    start = f"{YEAR_START}-01-01"
    end = f"{YEAR_END + 1}-01-01"
    col = (
        ee.ImageCollection(COLLECTION)
        .filterDate(start, end)
        .select(["pr", "pet"])
    )

    def scale_pet(img):
        pr = img.select("pr")
        pet = img.select("pet").multiply(PET_SCALE)
        return pr.rename("pr").addBands(pet.rename("pet")).copyProperties(
            img, ["system:time_start"]
        )

    scaled = col.map(scale_pet)

    # Sum months per year, then take mean across years
    def annual_sum(year):
        yr = ee.Number(year)
        y_col = scaled.filterDate(
            ee.Date.fromYMD(yr, 1, 1),
            ee.Date.fromYMD(yr.add(1), 1, 1),
        )
        return y_col.sum().set("year", yr)

    years = list(range(YEAR_START, YEAR_END + 1))
    annual_col = ee.ImageCollection(
        [annual_sum(y) for y in years]
    )
    annual_mean_pr = annual_col.select("pr").mean().rename("annual_pr_mm")
    annual_mean_pet = annual_col.select("pet").mean().rename("annual_pet_mm")

    return annual_mean_pr.addBands(annual_mean_pet)


def sample_global_grid(image: ee.Image) -> pd.DataFrame:
    lats = np.arange(-89.875, 90.0, CELL_DEG)
    lons = np.arange(-179.875, 180.0, CELL_DEG)

    records = []
    for lat in tqdm(lats, desc="Aridity rows"):
        for lon in lons:
            region = ee.Geometry.Rectangle(
                [lon - HALF, lat - HALF, lon + HALF, lat + HALF]
            )
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=SCALE_4KM,
                maxPixels=1e6,
                bestEffort=True,
            )
            info = stats.getInfo()
            records.append({
                "lat_center": lat,
                "lon_center": lon,
                "annual_pr_mm": info.get("annual_pr_mm"),
                "annual_pet_mm": info.get("annual_pet_mm"),
            })
    return pd.DataFrame(records)


def compute_aridity_score(pr: float, pet: float) -> tuple[float, float]:
    """Return (aridity_index, aridity_score). pet=0 → index=cap, score=0."""
    if pd.isna(pr) or pd.isna(pet):
        return float("nan"), float("nan")
    if pet <= 0:
        ai = ARIDITY_CAP
    else:
        ai = min(pr / pet, ARIDITY_CAP)
    score = 1.0 - min(ai, 1.0)
    return ai, score


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building TerraClimate aridity image ({YEAR_START}–{YEAR_END}) …")
    aridity_img = build_aridity_image()

    print("Sampling 0.25° global grid …")
    df = sample_global_grid(aridity_img)

    # Drop ocean/no-data cells
    df = df.dropna(subset=["annual_pr_mm", "annual_pet_mm"])

    # Compute aridity index and score
    results = df.apply(
        lambda row: compute_aridity_score(row["annual_pr_mm"], row["annual_pet_mm"]),
        axis=1,
        result_type="expand",
    )
    df["aridity_index"] = results[0]
    df["aridity_score"] = results[1]

    # Provenance
    df["cell_id"] = (
        "E_"
        + df["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    df["aridity_confidence"] = "medium"
    df["aridity_proxy"] = False
    df["aridity_source"] = (
        f"{COLLECTION}; bands pr (mm/month), pet (mm/month×{PET_SCALE}); "
        f"years {YEAR_START}-{YEAR_END}; aridity_index=pr/pet capped at {ARIDITY_CAP}; "
        f"score=1-min(ai,1); REQUIREMENT type; processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "annual_pr_mm", "annual_pet_mm", "aridity_index", "aridity_score",
        "aridity_confidence", "aridity_proxy", "aridity_source",
    ]
    df[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
