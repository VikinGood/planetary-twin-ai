"""
00_assemble_targets.py — Assemble Moon and Mars reference targets into targets.json
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/targets.json

Inputs:
  data/processed/moon_targets_raw.json   (from scripts/planets/01_moon_references.py)
  data/processed/mars_targets_raw.json   (from scripts/planets/02_mars_references.py)
  data/processed/earth_cells_025deg.parquet  (optional — from scripts/earth/ pipeline)

Behaviour with/without earth parquet:
  - If earth_cells_025deg.parquet exists AND contains thermal/illumination columns,
    percentile_estimate values are computed by ranking each target's reference value
    against the global Earth distribution.
  - If the parquet is absent or missing the required columns, percentile_estimate fields
    are populated with APPROXIMATE hardcoded values labeled "APPROXIMATE" and the script
    exits successfully (code 0).

Percentile conventions:
  - Thermal: percentile rank of target's annual temperature range among all Earth cells.
    Higher percentile = more extreme temperature range = higher Earth cell similarity
    score for a "high range" target.
  - Illumination: percentile rank of target's sun_fraction among all Earth cells.
    Low sun_fraction at south pole → low percentile → Earth cells with midnight-sun
    will rank highly for similarity.

Output schema: see contracts/similarity_result.sample.json and task description.

Runtime: < 10 s (pure JSON / pandas merge).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
PROC_DIR = ROOT / "data" / "processed"
MOON_RAW = PROC_DIR / "moon_targets_raw.json"
MARS_RAW = PROC_DIR / "mars_targets_raw.json"
EARTH_PARQUET = PROC_DIR / "earth_cells_025deg.parquet"
OUT_FILE = PROC_DIR / "targets.json"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Hardcoded APPROXIMATE percentile estimates (used when parquet is absent)
# Basis: published statistics and expert judgment — labeled APPROXIMATE throughout.
#
# Thermal percentile = where the target's annual temp range falls in the
# global Earth distribution (percentile 0 = coldest/smallest range, 1 = highest).
# Moon south-pole (small diurnal range, cold): ~0.02 annual mean, ~0.70 annual range.
# Moon equatorial (Marius Hills, huge range): off the top of Earth distribution → ~0.99.
# Mars equatorial (~100 K range): above Earth max → ~0.99.
# Mars mid-latitude (~110 K range): ~0.99.
#
# Illumination percentile = where the target's sun_fraction falls in Earth distribution.
# South pole (sun_fraction ~0.80 from LOLA, but sun regime very different):
#   Earth sun_fraction at poles ~0.50 (circumpolar half-year); 0.80 outside Earth range.
#   Map to ~0.98 (very high Earth sun_fraction required to approach).
# Marius Hills (equatorial, 0.50): ~0.50.
# ---------------------------------------------------------------------------

# Format: target_id -> {variable_name -> approximate_percentile}
APPROXIMATE_PERCENTILES = {
    # Moon south-polar landing targets — shared thermal regime
    "_moon_sp_landing_thermal": {
        "temp_annual_mean": 0.03,     # very cold (~150 K) → bottom of Earth distribution
        "temp_annual_range": 0.72,    # ~80 K annual range → upper-middle of Earth dist.
        "temp_diurnal_range": 0.45,   # ~30 K diurnal → mid Earth distribution
    },
    "_moon_sp_base_thermal": {
        "temp_annual_mean": 0.03,
        "temp_annual_range": 0.60,
        "temp_diurnal_range": 0.30,
    },
    "marius_hills_pit_thermal": {
        "temp_annual_mean": 0.70,     # ~240 K → warm for Earth distribution
        "temp_annual_range": 0.99,    # ~200 K → exceeds Earth max → 0.99
        "temp_diurnal_range": 0.99,   # ~250 K diurnal → far exceeds Earth
    },
    # Moon illumination percentiles
    "_moon_sp_illumination": {
        "illumination_fraction": 0.98,   # 0.80–0.86 → near top of Earth sun_fraction
        "solar_elevation_range": 0.00,   # ~3° → absolute bottom of Earth distribution
    },
    "marius_hills_pit_illumination": {
        "illumination_fraction": 0.50,   # equatorial half-year/half-year
        "solar_elevation_range": 0.85,   # ~76° → high elevation (near-equatorial)
    },
    # Mars equatorial landing targets — shared thermal regime
    "_mars_eq_landing_thermal": {
        "temp_annual_mean": 0.45,    # ~260 K → mid-low Earth distribution
        "temp_annual_range": 0.98,   # ~100 K → exceeds Earth range → near top
        "temp_diurnal_range": 0.95,  # ~50 K diurnal → upper Earth distribution
    },
    # Mars base targets
    "arcadia_planitia_thermal": {
        "temp_annual_mean": 0.05,    # ~218 K → very cold, bottom of Earth distribution
        "temp_annual_range": 0.99,   # ~110 K → exceeds Earth max
        "temp_diurnal_range": 0.90,  # ~45 K diurnal
    },
    "arsia_mons_cave_candidate_thermal": {
        "temp_annual_mean": 0.25,    # ~230 K → cold end of Earth distribution
        "temp_annual_range": 0.98,   # ~100 K → near-top
        "temp_diurnal_range": 0.95,  # ~50 K
    },
}


# ---------------------------------------------------------------------------
# Try loading Earth parquet for percentile computation
# ---------------------------------------------------------------------------

def load_earth_percentile_data() -> dict | None:
    """
    Load Earth cells parquet and extract percentile distributions for thermal
    and illumination variables.  Returns a dict of variable -> sorted numpy array,
    or None if the parquet is not available or lacks required columns.
    """
    if not EARTH_PARQUET.exists():
        print(
            f"  NOTE: {EARTH_PARQUET.name} not found — using APPROXIMATE percentile estimates."
        )
        return None

    try:
        import pandas as pd
        df = pd.read_parquet(EARTH_PARQUET)
    except Exception as exc:
        print(f"  WARNING: Could not read {EARTH_PARQUET.name}: {exc} — using APPROXIMATE.")
        return None

    # Columns we want for percentile ranking
    wanted = {
        "lst_annual_mean",
        "lst_annual_range",
        "lst_diurnal_range",
        "max_solar_elevation",
        "mean_solar_elevation",
        "sun_fraction",
    }
    available = wanted & set(df.columns)
    if not available:
        print(
            "  NOTE: earth_cells_025deg.parquet exists but contains none of the required "
            "thermal/illumination columns — using APPROXIMATE percentile estimates.\n"
            f"  Available columns: {list(df.columns)}"
        )
        return None

    print(f"  Found Earth parquet with {len(df):,} cells. "
          f"Available percentile columns: {sorted(available)}")

    result = {}
    for col in available:
        vals = df[col].dropna().values
        result[col] = np.sort(vals)

    missing = wanted - available
    if missing:
        print(f"  NOTE: columns not yet in parquet (will use APPROXIMATE): {sorted(missing)}")
    return result


def percentile_rank(value: float, distribution: np.ndarray) -> float:
    """Return the percentile rank (0–1) of `value` in `distribution`."""
    n = len(distribution)
    if n == 0:
        return None
    rank = int(np.searchsorted(distribution, value, side="right"))
    return round(rank / n, 4)


# ---------------------------------------------------------------------------
# Inject percentile_estimate into target reference_values
# ---------------------------------------------------------------------------

def _inject_thermal_percentiles(
    thermal: dict,
    target_id: str,
    earth_data: dict | None,
    approx_key: str,
) -> dict:
    """
    Given a thermal reference_values dict, fill in percentile_estimate fields.
    Uses real Earth distribution if available; otherwise APPROXIMATE hardcoded values.
    """
    var_map = {
        "temp_annual_mean":    "lst_annual_mean",
        "temp_annual_range":   "lst_annual_range",
        "temp_diurnal_range":  "lst_diurnal_range",
    }
    approx = APPROXIMATE_PERCENTILES.get(approx_key, {})

    for rv_key, earth_col in var_map.items():
        if rv_key not in thermal:
            continue
        entry = thermal[rv_key]
        if not isinstance(entry, dict):
            continue

        if earth_data and earth_col in earth_data:
            val = entry.get("value")
            # Moon temps are in K; Earth LST is in °C — convert K → °C for Moon/Mars
            # Earth parquet uses °C (from MODIS), so convert target K → °C before ranking.
            if val is not None and entry.get("units", "").startswith("K"):
                val_for_rank = val - 273.15
            else:
                val_for_rank = val

            if val_for_rank is not None:
                p = percentile_rank(val_for_rank, earth_data[earth_col])
                entry["percentile_estimate"] = p
                entry["basis"] = (
                    f"Computed from earth_cells_025deg.parquet ({len(earth_data[earth_col]):,} "
                    f"cells); target value {val} → {val_for_rank:.1f} °C → "
                    f"percentile rank {p:.4f}."
                )
        else:
            # Use hardcoded approximate
            p = approx.get(rv_key)
            entry["percentile_estimate"] = p
            entry["basis"] = (
                f"APPROXIMATE — Earth parquet not available or missing column {earth_col!r}. "
                f"Approximate percentile {p} based on literature comparison to Earth "
                "temperature distribution. Recompute when earth_cells_025deg.parquet "
                "includes thermal columns."
            )

    return thermal


def _inject_illumination_percentiles(
    illumination: dict,
    target_id: str,
    earth_data: dict | None,
    approx_key: str,
) -> dict:
    """
    Given an illumination reference_values dict, fill in percentile_estimate fields.
    """
    var_map = {
        "illumination_fraction": "sun_fraction",
        "solar_elevation_range": "max_solar_elevation",
    }
    approx = APPROXIMATE_PERCENTILES.get(approx_key, {})

    for rv_key, earth_col in var_map.items():
        if rv_key not in illumination:
            continue
        entry = illumination[rv_key]
        if not isinstance(entry, dict):
            continue

        if earth_data and earth_col in earth_data:
            val = entry.get("value")
            if val is not None:
                p = percentile_rank(val, earth_data[earth_col])
                entry["percentile_estimate"] = p
                entry["basis"] = (
                    f"Computed from earth_cells_025deg.parquet ({len(earth_data[earth_col]):,} "
                    f"cells); target value {val} → percentile rank {p:.4f}."
                )
        else:
            p = approx.get(rv_key)
            entry["percentile_estimate"] = p
            entry["basis"] = (
                f"APPROXIMATE — Earth parquet not available or missing column {earth_col!r}. "
                f"Approximate percentile {p} based on comparison to Earth illumination "
                "distribution. Recompute when earth_cells_025deg.parquet includes "
                "illumination columns."
            )

    # Also update the top-level percentile_estimate / basis for the illumination block
    illumination["percentile_estimate"] = None
    illumination["basis"] = (
        "See per-variable percentile_estimate fields above. "
        "Scoring uses per-variable rank comparison (METHODOLOGY §2.8)."
    )
    return illumination


def inject_percentiles(targets: dict, earth_data: dict | None) -> dict:
    """
    Walk all targets and fill in percentile_estimate for thermal and illumination.
    """
    # Determine approx_key per target
    for tid, t in targets.items():
        body = t["body"]
        rv = t.get("reference_values", {})

        if body == "moon":
            if t["mission_type"] == "landing":
                th_key = "_moon_sp_landing_thermal"
                il_key = "_moon_sp_illumination"
                if tid == "marius_hills_pit":
                    th_key = "marius_hills_pit_thermal"
                    il_key = "marius_hills_pit_illumination"
            else:  # base
                if tid == "marius_hills_pit":
                    th_key = "marius_hills_pit_thermal"
                    il_key = "marius_hills_pit_illumination"
                else:
                    th_key = "_moon_sp_base_thermal"
                    il_key = "_moon_sp_illumination"
        else:  # mars
            if tid == "arcadia_planitia":
                th_key = "arcadia_planitia_thermal"
                il_key = "_mars_eq_landing_thermal"
            elif tid == "arsia_mons_cave_candidate":
                th_key = "arsia_mons_cave_candidate_thermal"
                il_key = "_mars_eq_landing_thermal"
            else:  # Jezero, Gale, Meridiani
                th_key = "_mars_eq_landing_thermal"
                il_key = "_mars_eq_landing_thermal"

        if "thermal" in rv:
            rv["thermal"] = _inject_thermal_percentiles(
                rv["thermal"], tid, earth_data, th_key
            )

        if "illumination" in rv:
            rv["illumination"] = _inject_illumination_percentiles(
                rv["illumination"], tid, earth_data, il_key
            )

    return targets


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    # --- Check raw input files ---
    errors = []
    for path in (MOON_RAW, MARS_RAW):
        if not path.exists():
            errors.append(
                f"Missing: {path.name} — run the corresponding reference script first."
            )
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Load raw targets ---
    print("Loading raw target files …")
    with open(MOON_RAW, encoding="utf-8") as fh:
        moon_data = json.load(fh)
    with open(MARS_RAW, encoding="utf-8") as fh:
        mars_data = json.load(fh)

    all_targets: dict = {}
    all_targets.update(moon_data["targets"])
    all_targets.update(mars_data["targets"])
    for tid, t in all_targets.items():
        t["value_origin"] = "literature"
    print(f"  Loaded {len(all_targets)} targets total.")

    # --- Optionally load Earth percentile distributions ---
    print("Checking for Earth parquet …")
    earth_data = load_earth_percentile_data()

    # --- Inject percentile estimates ---
    print("Injecting percentile estimates …")
    all_targets = inject_percentiles(all_targets, earth_data)

    # --- Compose final output ---
    output = {
        "schema_version": "1.0",
        "generated_at": PROC_DATE,
        "note": (
            "UNVERIFIED — all planetary reference values from published literature. "
            "Percentile estimates labeled APPROXIMATE when Earth parquet is absent or "
            "incomplete. Validate all values against primary PDS/LROC/MCD data before "
            "Phase 6."
        ),
        "targets": all_targets,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(all_targets)} targets -> {OUT_FILE}")
    for tid, t in all_targets.items():
        chars = list(t.get("reference_values", {}).keys())
        print(f"  [{t['body']:4s} {t['mission_type']:7s}] {tid}: {chars}")

    if earth_data is None:
        print(
            "\nNOTE: Run scripts/earth/08_illumination.py and the full Earth pipeline, "
            "then re-run this script to replace APPROXIMATE percentile estimates with "
            "computed values."
        )


if __name__ == "__main__":
    main()
