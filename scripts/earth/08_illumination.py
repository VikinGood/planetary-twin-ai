"""
08_illumination.py — Earth illumination preprocessing (pure latitude computation)
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/earth_illumination_025deg.parquet
  Columns: cell_id, lat_center, lon_center,
           max_solar_elevation, mean_solar_elevation, sun_fraction,
           illumination_confidence, illumination_proxy, illumination_source

No external dataset — computed analytically from latitude.
Formulas: METHODOLOGY §2.8.

Unit test anchors (run with: python 08_illumination.py -- asserts embedded):
  φ=0°:       max_elev=90.00°, sun_fraction≈0.500
  φ=−62.875°: max_elev=50.56°, sun_fraction≈0.500
  φ=−90°:     max_elev=23.44°, sun_fraction≈0.500 (circumpolar half-year)

Runtime: < 1 min (vectorised NumPy).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "earth_illumination_025deg.parquet"

CELL_DEG = 0.25
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Solar geometry (METHODOLOGY §2.8)
# ---------------------------------------------------------------------------

DAYS = np.arange(365)          # d = 0 … 364
# Declination (degrees) for each day: 23.44 × sin(360/365 × (d − 81))
_DECL_DEG = 23.44 * np.sin(np.radians(360.0 / 365.0 * (DAYS - 81.0)))
_DECL_RAD = np.radians(_DECL_DEG)


def compute_illumination(lat_deg: float) -> tuple[float, float, float]:
    """
    Return (max_solar_elevation_deg, mean_solar_elevation_deg, sun_fraction)
    for a given latitude in degrees.

    Formulas: METHODOLOGY §2.8
    """
    phi = np.radians(lat_deg)

    # max_solar_elevation: annual maximum (at summer solstice), capped at 90°
    max_elev = min(90.0, 90.0 - abs(lat_deg) + 23.44)

    # --- day_fraction and mean_solar_elevation per day ---
    # cos_h0(d) = −tan(φ) × tan(declination(d))
    tan_phi = np.tan(phi)
    tan_decl = np.tan(_DECL_RAD)
    cos_h0 = -tan_phi * tan_decl  # shape (365,)

    # Polar night: cos_h0 >= 1  → day_fraction = 0
    # Midnight sun: cos_h0 <= -1 → day_fraction = 1
    # Normal: day_fraction = arccos(cos_h0) / π
    day_frac = np.where(
        cos_h0 >= 1.0, 0.0,
        np.where(cos_h0 <= -1.0, 1.0,
                 np.arccos(np.clip(cos_h0, -1.0, 1.0)) / np.pi)
    )

    sun_fraction = float(np.mean(day_frac))

    # mean_solar_elevation above horizon (time-weighted mean)
    # E(d) = arcsin(sin(δ)·sin(φ) + cos(δ)·cos(φ)·sin(h0)/h0)
    # where h0 = arccos(cos_h0) (half-day angle in radians)
    # For polar night or midnight sun, handle separately.
    # For normal days (0 < day_frac < 1):
    #   h0 = arccos(cos_h0)
    #   mean elevation = arcsin(sin(δ)sin(φ) + cos(δ)cos(φ)·(2/π)·sin(h0)/h0·(π/2))
    # The METHODOLOGY formula simplifies to:
    #   mean_elev_above_horizon = arcsin(sin(δ)·sin(φ) + cos(δ)·cos(φ)·sin(h0)/h0)
    # (using the analytical time-average of cos(hour_angle) over [−h0, h0])

    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    sin_decl = np.sin(_DECL_RAD)
    cos_decl = np.cos(_DECL_RAD)

    # h0 in radians (half-day angle); only defined for days above horizon
    h0 = np.arccos(np.clip(cos_h0, -1.0, 1.0))  # 0 at polar night, π at midnight sun

    # For days with no sun (day_frac == 0): contribution = 0
    # For days with full sun (day_frac == 1, h0 = π):
    #   sin(h0)/h0 = sin(π)/π = 0 — so the formula still applies (reduces to arcsin of sin(δ)sin(φ))
    with np.errstate(invalid="ignore", divide="ignore"):
        sinH0_over_H0 = np.where(h0 > 1e-9, np.sin(h0) / h0, 0.0)
    elev_arg = np.clip(sin_decl * sin_phi + cos_decl * cos_phi * sinH0_over_H0, -1.0, 1.0)
    elev_per_day = np.degrees(np.arcsin(elev_arg))  # degrees, per day

    # Time-weighted mean: weight by day_frac (days above horizon contribute proportionally)
    total_weight = np.sum(day_frac)
    if total_weight > 0:
        mean_elev = float(np.sum(day_frac * elev_per_day) / total_weight)
    else:
        mean_elev = 0.0

    return max_elev, mean_elev, sun_fraction


# ---------------------------------------------------------------------------
# Unit tests (METHODOLOGY §2.8 anchors)
# ---------------------------------------------------------------------------

def run_unit_tests():
    """Run unit test asserts for illumination computation. Raises AssertionError on failure."""
    tol = 0.01  # tolerance for sun_fraction
    tol_elev = 0.1  # tolerance for solar elevation (degrees)

    # φ = 0° (equator)
    max_e, mean_e, sf = compute_illumination(0.0)
    assert abs(max_e - 90.00) < tol_elev, f"φ=0° max_elev expected 90.00, got {max_e:.4f}"
    assert abs(sf - 0.500) < tol, f"φ=0° sun_fraction expected 0.500, got {sf:.4f}"

    # φ = -62.875°
    max_e, mean_e, sf = compute_illumination(-62.875)
    expected_max = min(90.0, 90.0 - 62.875 + 23.44)   # = 50.565
    assert abs(max_e - expected_max) < tol_elev, (
        f"φ=-62.875° max_elev expected {expected_max:.2f}, got {max_e:.4f}"
    )
    assert abs(sf - 0.500) < tol, f"φ=-62.875° sun_fraction expected ≈0.500, got {sf:.4f}"

    # φ = -90° (South Pole)
    max_e, mean_e, sf = compute_illumination(-90.0)
    assert abs(max_e - 23.44) < tol_elev, f"φ=-90° max_elev expected 23.44, got {max_e:.4f}"
    # At the South Pole: sun is above horizon during austral summer (roughly half the year)
    assert abs(sf - 0.500) < tol, f"φ=-90° sun_fraction expected ≈0.500, got {sf:.4f}"

    print("All illumination unit tests passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Run unit tests before producing any output
    run_unit_tests()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    lats = np.arange(-89.875, 90.0, CELL_DEG)
    lons = np.arange(-179.875, 180.0, CELL_DEG)

    # Compute per-latitude (illumination is latitude-only)
    lat_cache: dict[float, tuple[float, float, float]] = {}
    for lat in tqdm(lats, desc="Computing illumination per latitude"):
        lat_cache[lat] = compute_illumination(float(lat))

    records = []
    for lat in lats:
        max_e, mean_e, sf = lat_cache[lat]
        for lon in lons:
            records.append({
                "lat_center": lat,
                "lon_center": lon,
                "max_solar_elevation": max_e,
                "mean_solar_elevation": mean_e,
                "sun_fraction": sf,
            })

    df = pd.DataFrame(records)

    # Provenance
    df["cell_id"] = (
        "E_"
        + df["lat_center"].map(lambda x: f"{x:+.3f}")
        + "_"
        + df["lon_center"].map(lambda x: f"{x:+.3f}")
    )
    df["illumination_confidence"] = "high"
    df["illumination_proxy"] = False
    df["illumination_source"] = (
        "Computed analytically from latitude (METHODOLOGY §2.8); "
        "no external dataset; declination=23.44°×sin(360/365×(d-81)); "
        f"processed {PROC_DATE}"
    )

    out_cols = [
        "cell_id", "lat_center", "lon_center",
        "max_solar_elevation", "mean_solar_elevation", "sun_fraction",
        "illumination_confidence", "illumination_proxy", "illumination_source",
    ]
    df[out_cols].to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} global cells (all latitudes) -> {OUT_FILE}")


if __name__ == "__main__":
    main()
