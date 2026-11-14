"""
06_volcanic_caves.py — Earth volcanic terrain / lava-tube proxy
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_volcanic_caves_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           glim_vb, dist_to_volcano_km, volcanic_caves_likelihood, volcanic_caves_score,
           volcanic_caves_confidence, volcanic_caves_proxy, volcanic_caves_source

Inputs (both required):
  1. data/processed/earth_geology_025deg.parquet  (produced by 05_geology.py)
  2. data/raw/earth/gvp/<any .csv file>           (Smithsonian GVP Holocene catalog)

GVP catalog download:
  URL: https://volcano.si.edu/database/search_volcano_excel_select.cfm
  (choose CSV export; free, no account required)
  Place CSV in: data/raw/earth/gvp/

GVP qualifying volcano types (from config/characteristics.json):
  "Shield volcano", "Fissure vent(s)", "Volcanic field", "Lava dome(s)"

Likelihood rules (METHODOLOGY §2.6, labeled PROXY / LOW confidence):
  HIGH   : glim_vb == 1  AND  dist_to_volcano_km ≤ 50
  MEDIUM : glim_vb == 1  OR   dist_to_volcano_km ≤ 100
  LOW    : neither condition met
Scores: HIGH=1.0, MEDIUM=0.5, LOW=0.0

Runtime: ~2–5 min (GeoPandas spatial join).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from tqdm import tqdm

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_volcanic_caves_025deg.parquet"
GEOLOGY_FILE = OUT_DIR / "earth_geology_025deg.parquet"
GVP_DIR = ROOT / "data" / "raw" / "earth" / "gvp"

GVP_DOWNLOAD_URL = "https://volcano.si.edu/database/search_volcano_excel_select.cfm"
GVP_DOWNLOAD_NOTE = (
    "Download the Smithsonian GVP Holocene volcano catalog as CSV from:\n"
    f"  {GVP_DOWNLOAD_URL}\n"
    f"Place the CSV file in: {GVP_DIR}/\n"
    "No account required."
)

# ---------------------------------------------------------------------------
QUALIFYING_TYPES = {"Shield volcano", "Fissure vent(s)", "Volcanic field", "Lava dome(s)"}
HIGH_DIST_KM = 50.0
MEDIUM_DIST_KM = 100.0
LIKELIHOOD_SCORES = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.0}
CELL_DEG = 0.25
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Approximate metres per degree of latitude (used for fast distance filter)
M_PER_DEG = 111_320.0


def find_gvp_file() -> Path | None:
    candidates = sorted(GVP_DIR.glob("*.csv")) + sorted(GVP_DIR.glob("*.CSV"))
    return candidates[0] if candidates else None


def load_gvp(path: Path) -> gpd.GeoDataFrame:
    """Load GVP CSV, filter to qualifying types, return GeoDataFrame (WGS84)."""
    df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")

    # Normalize column names (GVP CSV may vary between downloads)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Try common column name variants
    type_col = next(
        (c for c in df.columns if "type" in c and "volcano" in c), None
    ) or next((c for c in df.columns if "type" in c), None)
    lat_col = next((c for c in df.columns if c in ("latitude", "lat")), None)
    lon_col = next((c for c in df.columns if c in ("longitude", "lon", "long")), None)

    if type_col is None or lat_col is None or lon_col is None:
        raise ValueError(
            f"Could not identify type/lat/lon columns in GVP CSV. "
            f"Columns found: {list(df.columns)}"
        )

    # Filter to qualifying types
    qualifying = df[df[type_col].isin(QUALIFYING_TYPES)].copy()
    qualifying = qualifying.dropna(subset=[lat_col, lon_col])
    qualifying[lat_col] = pd.to_numeric(qualifying[lat_col], errors="coerce")
    qualifying[lon_col] = pd.to_numeric(qualifying[lon_col], errors="coerce")
    qualifying = qualifying.dropna(subset=[lat_col, lon_col])

    geom = [Point(lon, lat) for lon, lat in zip(qualifying[lon_col], qualifying[lat_col])]
    gdf = gpd.GeoDataFrame(qualifying, geometry=geom, crs="EPSG:4326")
    print(f"  Loaded {len(gdf)} qualifying GVP volcanoes (of {len(df)} total)")
    return gdf


def haversine_km(lat1: np.ndarray, lon1: np.ndarray,
                 lat2: float, lon2: float) -> np.ndarray:
    """Vectorised haversine distance in km from arrays (lat1, lon1) to scalar (lat2, lon2)."""
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(a))


def compute_distances(cells_df: pd.DataFrame, volcanoes_gdf: gpd.GeoDataFrame) -> pd.Series:
    """
    For each cell, compute the distance (km) to the nearest qualifying volcano.
    Uses a vectorised approach: for each volcano, compute distance to all cells,
    then take the minimum.
    """
    vol_lats = volcanoes_gdf.geometry.y.values
    vol_lons = volcanoes_gdf.geometry.x.values
    cell_lats = cells_df["lat_center"].values
    cell_lons = cells_df["lon_center"].values

    # Build distance matrix: shape (n_cells, n_volcanoes)
    # Process in chunks to avoid memory explosion for large datasets
    chunk_size = 500
    min_dists = np.full(len(cells_df), np.inf)

    for v_start in tqdm(range(0, len(vol_lats), chunk_size), desc="Distance chunks"):
        v_end = min(v_start + chunk_size, len(vol_lats))
        for vi in range(v_start, v_end):
            d = haversine_km(cell_lats, cell_lons, vol_lats[vi], vol_lons[vi])
            min_dists = np.minimum(min_dists, d)

    return pd.Series(min_dists, index=cells_df.index)


def assign_likelihood(glim_vb: int, dist_km: float) -> str:
    if glim_vb == 1 and dist_km <= HIGH_DIST_KM:
        return "HIGH"
    if glim_vb == 1 or dist_km <= MEDIUM_DIST_KM:
        return "MEDIUM"
    return "LOW"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Check geology input ---
    if not GEOLOGY_FILE.exists():
        print(
            f"ERROR: Geology file not found: {GEOLOGY_FILE}\n"
            "Run 05_geology.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Check GVP input ---
    gvp_path = find_gvp_file()
    if gvp_path is None:
        print(
            f"ERROR: GVP catalog CSV not found in {GVP_DIR}/\n" + GVP_DOWNLOAD_NOTE,
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading geology data from {GEOLOGY_FILE} …")
    geo_df = pd.read_parquet(GEOLOGY_FILE)

    print(f"Loading GVP catalog from {gvp_path} …")
    vol_gdf = load_gvp(gvp_path)

    print("Computing distances to nearest qualifying volcano …")
    min_dists = compute_distances(geo_df, vol_gdf)
    geo_df["dist_to_volcano_km"] = min_dists

    # Assign likelihood and score
    geo_df["volcanic_caves_likelihood"] = [
        assign_likelihood(int(row["glim_vb"]), row["dist_to_volcano_km"])
        for _, row in tqdm(geo_df.iterrows(), total=len(geo_df), desc="Likelihood")
    ]
    geo_df["volcanic_caves_score"] = geo_df["volcanic_caves_likelihood"].map(
        LIKELIHOOD_SCORES
    )

    # Provenance — always LOW confidence and PROXY labeled per methodology
    geo_df["volcanic_caves_confidence"] = "low"
    geo_df["volcanic_caves_proxy"] = True
    geo_df["volcanic_caves_source"] = (
        "PROXY; "
        f"GLiM vb class from {GEOLOGY_FILE.name}; "
        f"GVP Holocene catalog {gvp_path.name} (qualifying types: {sorted(QUALIFYING_TYPES)}); "
        f"HIGH=vb AND dist≤{HIGH_DIST_KM}km; MEDIUM=vb OR dist≤{MEDIUM_DIST_KM}km; "
        f"validation: compare against NASA Pits and Caves Analog Dataset (UNVERIFIED); "
        f"processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "glim_vb", "dist_to_volcano_km",
        "volcanic_caves_likelihood", "volcanic_caves_score",
        "volcanic_caves_confidence", "volcanic_caves_proxy", "volcanic_caves_source",
    ]
    geo_df[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(geo_df):,} land cells -> {OUT_FILE}")


if __name__ == "__main__":
    main()
