"""
scoring.py — Pure scoring engine for Planetary Twin AI.

No FastAPI imports. Import and test this module independently.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.

All formulas implement METHODOLOGY.md exactly:
  §2.1 topography  — gaussian + hard cap + base relief
  §2.2 geology     — categorical 1.0 / 0.5 / 0.0
  §2.3 thermal     — percentile regime, 3 variables
  §2.4 aridity     — requirement: 1 − min(pr/pet, 1)
  §2.5 ice_polar   — geometric_mean(permafrost × lat_mult, ice_cover)
  §2.6 volcanic_caves — categorical HIGH/MEDIUM/LOW
  §2.7 surface_optics — gaussian, sigma_floor=0.05
  §2.8 illumination   — percentile regime, 3 variables
Combination: weighted geometric mean (§1).
Environment tags: §4.
Cannot-reproduce: §7.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Sigma floors (config/characteristics.json §gaussian_sigma_floors)
# ---------------------------------------------------------------------------
SIGMA_FLOOR_SLOPE = 2.0       # degrees
SIGMA_FLOOR_ROUGHNESS = 10.0  # meters
SIGMA_FLOOR_RELIEF = 50.0     # meters
SIGMA_FLOOR_ALBEDO = 0.05     # albedo units

HARD_CAP_SLOPE_DEG = 12.0     # §2.1 landing hard cap

# ---------------------------------------------------------------------------
# cannot_reproduce constants (METHODOLOGY §7)
# ---------------------------------------------------------------------------
CANNOT_REPRODUCE_MOON = [
    "Gravity: 1/6 g (1.62 m/s²) — no terrestrial equivalent",
    "Atmosphere: vacuum (~10⁻¹⁰ Pa); no convection, no acoustic hazards from wind",
    "Radiation: unfiltered solar energetic particles and galactic cosmic rays",
    "Absolute temperatures: 40 K in permanently shadowed regions to ~400 K at "
    "equatorial noon — far outside any Earth surface range",
    "14-Earth-day continuous daylight / 14-Earth-day darkness cycle — no terrestrial analog",
    "Solar elevation regime: lunar obliquity ~1.54° means the sun never rises above ~6° "
    "at the south pole all year. Earth's annual maximum solar elevation cannot drop below "
    "~23.4° (South Pole at summer solstice). No Earth cell can replicate the near-horizon "
    "sun regime of the lunar south pole.",
    "Regolith: electrostatic, sharp-edged (no weathering) — no terrestrial surface-level equivalent",
]

CANNOT_REPRODUCE_MARS = [
    "Gravity: 0.38 g (3.72 m/s²) — no terrestrial equivalent",
    "Atmosphere: 0.6 kPa, 95 % CO₂; no breathable air, partial pressure too low for "
    "liquid water at surface",
    "UV/radiation: no ozone layer; UV and ionizing radiation at surface",
    "Global dust storms: planetary-scale events lasting months with severe irradiance loss",
    "Absolute temperatures: −140 °C (polar night) to +20 °C (equatorial afternoon); "
    "range exceeds any Earth surface",
    "Perchlorates in regolith: no terrestrial surface-level analog",
]

# ---------------------------------------------------------------------------
# Geology primary/secondary class mappings
# GLiM class → Moon/Mars analog match quality
# Keys are GLiM class codes; value: list of target geologic unit keywords that
# constitute a primary (1.0) or secondary (0.5) match.
# ---------------------------------------------------------------------------
# Broad mapping based on METHODOLOGY §2.2 and config/characteristics.json
_GEOLOGY_PRIMARY: dict[str, list[str]] = {
    "vb": ["basalt", "basaltic", "mare", "volcanic", "volcanic_highland", "lava"],
    "va": ["andesite", "volcanic"],
    "vi": ["volcanic"],
    "ss": ["sedimentary", "sandstone", "clastic", "lacustrine", "fluvial", "delta"],
    "sm": ["mudstone", "shale", "clay", "sedimentary"],
    "sc": ["carbonate", "limestone"],
    "su": ["unconsolidated", "regolith", "eolian", "dune"],
    "py": ["pyroclastic", "volcanic", "ash"],
    "mt": ["metamorphic"],
    "pa": ["anorthosite", "highland", "breccia", "noritic"],
    "pb": ["breccia", "highland", "ejecta"],
}
_GEOLOGY_SECONDARY: dict[str, list[str]] = {
    "vb": ["highland", "breccia", "regolith"],
    "va": ["basalt", "basaltic", "highland"],
    "ss": ["eolian", "volcanic"],
    "su": ["sedimentary", "basaltic"],
    "pa": ["basaltic", "volcanic"],
}


# ---------------------------------------------------------------------------
# 1. gaussian_score
# ---------------------------------------------------------------------------

def gaussian_score(x: float, mu: float, sigma_target: float, sigma_floor: float) -> float:
    """Gaussian similarity score per METHODOLOGY §2.1.

    sigma_eff = max(sigma_target, sigma_floor)
    return exp(-(x - mu)^2 / (2 * sigma_eff^2))
    """
    sigma_eff = max(sigma_target, sigma_floor)
    return math.exp(-((x - mu) ** 2) / (2 * sigma_eff ** 2))


# ---------------------------------------------------------------------------
# 2. topography_score
# ---------------------------------------------------------------------------

def topography_score(
    earth_row: pd.Series,
    target_ref: dict,
    mission_type: str,
) -> tuple[float, str, dict]:
    """Score topography per METHODOLOGY §2.1.

    Returns (score, confidence, detail_dict).
    detail_dict keys: slope_score, roughness_score, hard_cap_applied, variables.
    """
    topo = target_ref.get("topography", {})

    # --- slope ---
    earth_slope = _get_float(earth_row, "slope", 0.0)
    mu_slope = _get_ref_value(topo, "slope", 4.0)
    # sigma_target derived from published range; use 2.0 as a default if unavailable
    sigma_slope = 2.0

    # Hard cap
    hard_cap_applied = False
    if earth_slope > HARD_CAP_SLOPE_DEG:
        hard_cap_applied = True
        return (
            0.0,
            "low",
            {
                "slope_score": 0.0,
                "roughness_score": 0.0,
                "hard_cap_applied": True,
                "hard_cap_slope_deg": HARD_CAP_SLOPE_DEG,
                "hard_cap_label": "TEAM ASSUMPTION",
                "variables": {
                    "slope": {
                        "earth_value": earth_slope,
                        "reference_mean": mu_slope,
                        "sigma_floor": SIGMA_FLOOR_SLOPE,
                        "sigma_eff": max(sigma_slope, SIGMA_FLOOR_SLOPE),
                        "score": 0.0,
                        "units": "degrees",
                    }
                },
            },
        )

    slope_score = gaussian_score(earth_slope, mu_slope, sigma_slope, SIGMA_FLOOR_SLOPE)

    # --- roughness ---
    earth_rough = _get_float(earth_row, "roughness", 20.0)
    mu_rough = _get_ref_value(topo, "roughness", 20.0)
    sigma_rough = 8.0  # representative spread; floors kick in at 10

    roughness_score = gaussian_score(earth_rough, mu_rough, sigma_rough, SIGMA_FLOOR_ROUGHNESS)

    if mission_type == "landing":
        # Final: geometric mean of slope and roughness
        score = math.sqrt(slope_score * roughness_score)
        confidence = "high"
        detail = {
            "slope_score": round(slope_score, 4),
            "roughness_score": round(roughness_score, 4),
            "hard_cap_applied": False,
            "hard_cap_slope_deg": HARD_CAP_SLOPE_DEG,
            "hard_cap_label": "TEAM ASSUMPTION",
            "variables": {
                "slope": {
                    "earth_value": earth_slope,
                    "reference_mean": mu_slope,
                    "sigma_target": sigma_slope,
                    "sigma_floor": SIGMA_FLOOR_SLOPE,
                    "sigma_eff": max(sigma_slope, SIGMA_FLOOR_SLOPE),
                    "score": round(slope_score, 4),
                    "units": "degrees",
                },
                "roughness": {
                    "earth_value": earth_rough,
                    "reference_mean": mu_rough,
                    "sigma_target": sigma_rough,
                    "sigma_floor": SIGMA_FLOOR_ROUGHNESS,
                    "sigma_eff": max(sigma_rough, SIGMA_FLOOR_ROUGHNESS),
                    "score": round(roughness_score, 4),
                    "units": "meters",
                },
            },
        }
    else:
        # Base: (a) buildable ground = same as landing; (b) surrounding relief
        buildable_score = math.sqrt(slope_score * roughness_score)

        earth_relief = _get_float(earth_row, "local_relief", 500.0)
        mu_relief = _get_ref_value(topo, "local_relief", 500.0)
        sigma_relief = 200.0

        relief_score = gaussian_score(earth_relief, mu_relief, sigma_relief, SIGMA_FLOOR_RELIEF)

        score = math.sqrt(buildable_score * relief_score)
        confidence = "medium"
        detail = {
            "buildable_score": round(buildable_score, 4),
            "relief_score": round(relief_score, 4),
            "slope_score": round(slope_score, 4),
            "roughness_score": round(roughness_score, 4),
            "hard_cap_applied": False,
            "hard_cap_slope_deg": HARD_CAP_SLOPE_DEG,
            "hard_cap_label": "TEAM ASSUMPTION",
            "variables": {
                "slope": {
                    "earth_value": earth_slope,
                    "reference_mean": mu_slope,
                    "sigma_target": sigma_slope,
                    "sigma_floor": SIGMA_FLOOR_SLOPE,
                    "sigma_eff": max(sigma_slope, SIGMA_FLOOR_SLOPE),
                    "score": round(slope_score, 4),
                    "units": "degrees",
                },
                "roughness": {
                    "earth_value": earth_rough,
                    "reference_mean": mu_rough,
                    "sigma_target": sigma_rough,
                    "sigma_floor": SIGMA_FLOOR_ROUGHNESS,
                    "sigma_eff": max(sigma_rough, SIGMA_FLOOR_ROUGHNESS),
                    "score": round(roughness_score, 4),
                    "units": "meters",
                },
                "local_relief": {
                    "earth_value": earth_relief,
                    "reference_mean": mu_relief,
                    "sigma_target": sigma_relief,
                    "sigma_floor": SIGMA_FLOOR_RELIEF,
                    "sigma_eff": max(sigma_relief, SIGMA_FLOOR_RELIEF),
                    "score": round(relief_score, 4),
                    "units": "meters",
                },
            },
        }

    return (round(score, 4), confidence, detail)


# ---------------------------------------------------------------------------
# 3. thermal_score
# ---------------------------------------------------------------------------

def thermal_score(
    earth_row: pd.Series,
    target_ref: dict,
) -> tuple[float, str, dict]:
    """Score thermal per METHODOLOGY §2.3: percentile regime, 3 variables."""
    thermal = target_ref.get("thermal", {})

    var_map = [
        ("lst_annual_mean", "temp_annual_mean"),
        ("lst_annual_range", "temp_annual_range"),
        ("lst_diurnal_range", "temp_diurnal_range"),
    ]

    scores = []
    variables = {}
    for earth_col, ref_key in var_map:
        pct_earth = _get_float(earth_row, f"{earth_col}_pct", None)
        ref_entry = thermal.get(ref_key, {})
        if isinstance(ref_entry, dict):
            pct_target = ref_entry.get("percentile_estimate")
        else:
            pct_target = None

        if pct_earth is None or pct_target is None:
            # Missing data — use 0.5 as neutral (mid-range)
            var_score = 0.5
        else:
            var_score = max(0.0, 1.0 - abs(float(pct_earth) - float(pct_target)))

        scores.append(var_score)
        earth_val = _get_float(earth_row, earth_col, None)
        variables[earth_col] = {
            "earth_value": earth_val,
            "earth_percentile": pct_earth,
            "reference_percentile": pct_target,
            "score": round(var_score, 4),
            "score_formula": (
                f"1 - |{pct_earth} - {pct_target}|" if pct_earth is not None else "neutral=0.5"
            ),
        }

    final_score = _geometric_mean_list(scores)
    return (round(final_score, 4), "medium", {"variables": variables})


# ---------------------------------------------------------------------------
# 4. surface_optics_score
# ---------------------------------------------------------------------------

def surface_optics_score(
    earth_row: pd.Series,
    target_ref: dict,
) -> tuple[float, str, dict]:
    """Score surface optics per METHODOLOGY §2.7: gaussian on broadband_albedo."""
    optics = target_ref.get("surface_optics", {})

    earth_albedo = _get_float(earth_row, "broadband_albedo", None)

    # Target albedo — may be stored as 'reflectance' (Moon) or 'albedo' (Mars)
    ref_entry = optics.get("reflectance") or optics.get("albedo") or {}
    if isinstance(ref_entry, dict):
        mu_albedo = ref_entry.get("value", 0.11)
    else:
        mu_albedo = 0.11

    sigma_target = 0.03  # typical spread
    if earth_albedo is None:
        return (0.5, "low", {"note": "broadband_albedo missing — neutral score"})

    score = gaussian_score(earth_albedo, mu_albedo, sigma_target, SIGMA_FLOOR_ALBEDO)
    sigma_eff = max(sigma_target, SIGMA_FLOOR_ALBEDO)

    return (
        round(score, 4),
        "medium",
        {
            "variables": {
                "broadband_albedo": {
                    "earth_value": earth_albedo,
                    "reference_mean": mu_albedo,
                    "sigma_target": sigma_target,
                    "sigma_floor": SIGMA_FLOOR_ALBEDO,
                    "sigma_eff": sigma_eff,
                    "score": round(score, 4),
                    "score_formula": (
                        f"exp(-({earth_albedo}-{mu_albedo})^2 / "
                        f"(2*{sigma_eff}^2))"
                    ),
                    "units": "0–1",
                }
            }
        },
    )


# ---------------------------------------------------------------------------
# 5. aridity_score
# ---------------------------------------------------------------------------

def aridity_score(earth_row: pd.Series) -> tuple[float, str, dict]:
    """Score aridity per METHODOLOGY §2.4: REQUIREMENT, no target reference needed.

    score = max(1 - min(P/PET, 1), 1 - min(P / 250 mm, 1))
    so polar deserts with under 250 mm/yr score as arid.
    Permanent ice is not penalized (liquid water absence rule updated).
    """
    pr = _get_float(earth_row, "precipitation", None)
    if pr is None:
        pr = _get_float(earth_row, "annual_pr_mm", None)
    pet = _get_float(earth_row, "pet", None)
    if pet is None:
        pet = _get_float(earth_row, "annual_pet_mm", None)

    aridity_index = _get_float(earth_row, "aridity_index", None)
    if aridity_index is None:
        if pr is not None and pet is not None and pet > 0:
            aridity_index = pr / pet
        else:
            aridity_index = 0.5  # neutral if data missing

    p_pet_term = max(0.0, 1.0 - min(aridity_index, 1.0))
    if pr is not None:
        pr_250_term = max(0.0, 1.0 - min(pr / 250.0, 1.0))
    else:
        pr_250_term = 0.0

    score = max(p_pet_term, pr_250_term)
    return (
        round(score, 4),
        "high",
        {
            "aridity_index": round(aridity_index, 4),
            "precipitation": pr,
            "score_formula": f"max(1 - min(P/PET, 1), 1 - min(P/250, 1)) = {score:.4f}",
            "note": "REQUIREMENT — Moon and Mars are maximally arid",
        },
    )


# ---------------------------------------------------------------------------
# 6. ice_polar_score
# ---------------------------------------------------------------------------

def ice_polar_score(
    earth_row: pd.Series,
    target_ref: dict,  # kept for API consistency; not used in computation
) -> tuple[float, str, dict]:
    """Score ice/polar per METHODOLOGY §2.5.

    ground-ice score = permafrost_index;
    permanent ice sheet (ice_cover_fraction >= 0.5) scores 0.5 (glacier ice is not ice-cemented regolith).
    """
    permafrost = _get_float(earth_row, "permafrost_index", 0.0)
    ice_cover = _get_float(earth_row, "ice_cover_fraction", 0.0)

    if permafrost is None:
        permafrost = 0.0
    if ice_cover is None:
        ice_cover = 0.0

    if ice_cover >= 0.5:
        score = 0.5
        note = "Permanent ice sheet (score 0.5; glacier ice is not ice-cemented regolith)"
    else:
        score = float(permafrost)
        note = "Ground-ice score from permafrost index"

    score = max(0.0, min(1.0, score))

    return (
        round(score, 4),
        "medium",
        {
            "permafrost_index": permafrost,
            "ice_cover_fraction": ice_cover,
            "score_formula": "0.5 if ice_cover >= 0.5 else permafrost_index",
            "note": note,
        },
    )


# ---------------------------------------------------------------------------
# 7. volcanic_caves_score
# ---------------------------------------------------------------------------

def volcanic_caves_score(earth_row: pd.Series) -> tuple[float, str, dict]:
    """Score volcanic caves per METHODOLOGY §2.6.

    Uses precomputed likelihood column (HIGH/MEDIUM/LOW).
    Confidence always 'low' (PROXY).
    """
    likelihood = earth_row.get("volcanic_caves_likelihood", None)
    if pd.isna(likelihood) if likelihood is not None else True:
        likelihood = "LOW"

    score_map = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.0}
    score = score_map.get(str(likelihood).upper(), 0.0)

    return (
        round(score, 4),
        "low",
        {
            "likelihood": likelihood,
            "proxy": True,
            "proxy_label": "PROXY",
            "note": "Lava-tube likelihood estimated from GLiM vb class + GVP Holocene volcano distance",
        },
    )


# ---------------------------------------------------------------------------
# 8. geology_score
# ---------------------------------------------------------------------------

def geology_score(
    earth_row: pd.Series,
    target_ref: dict,
) -> tuple[float, str, dict]:
    """Score geology per METHODOLOGY §2.2: categorical 1.0/0.5/0.0."""
    geo = target_ref.get("geology", {})
    geologic_unit = geo.get("geologic_unit", {})
    if isinstance(geologic_unit, dict):
        class_desc = geologic_unit.get("class_description", "").lower()
    else:
        class_desc = str(geologic_unit).lower()

    earth_class = _get_str(earth_row, "lithology_class", "")

    # Determine score from mapping
    primary_keywords = _GEOLOGY_PRIMARY.get(earth_class, [])
    secondary_keywords = _GEOLOGY_SECONDARY.get(earth_class, [])

    score = 0.0
    match_type = "none"

    if any(kw in class_desc for kw in primary_keywords):
        score = 1.0
        match_type = "primary"
    elif any(kw in class_desc for kw in secondary_keywords):
        score = 0.5
        match_type = "secondary"

    return (
        round(score, 4),
        "low",
        {
            "earth_lithology_class": earth_class,
            "target_class_description": class_desc[:120],
            "match_type": match_type,
            "score": score,
        },
    )


# ---------------------------------------------------------------------------
# 9. illumination_score
# ---------------------------------------------------------------------------

def illumination_score(
    earth_row: pd.Series,
    target_ref: dict,
) -> tuple[float, str, dict]:
    """Score illumination per METHODOLOGY §2.8: percentile regime, 3 variables."""
    illum = target_ref.get("illumination", {})

    # Variable mapping:
    # earth max_solar_elevation ↔ target solar_elevation_range
    # earth sun_fraction        ↔ target illumination_fraction
    # earth mean_solar_elevation has no direct target equivalent; use solar_elevation_range pct

    var_defs = [
        ("max_solar_elevation", "solar_elevation_range"),
        ("mean_solar_elevation", "solar_elevation_range"),  # proxy
        ("sun_fraction", "illumination_fraction"),
    ]

    scores = []
    variables = {}

    for earth_col, ref_key in var_defs:
        pct_earth = _get_float(earth_row, f"{earth_col}_pct", None)
        ref_entry = illum.get(ref_key, {})
        if isinstance(ref_entry, dict):
            pct_target = ref_entry.get("percentile_estimate")
        else:
            pct_target = None

        if pct_earth is None or pct_target is None:
            var_score = 0.5
        else:
            var_score = max(0.0, 1.0 - abs(float(pct_earth) - float(pct_target)))

        scores.append(var_score)
        earth_val = _get_float(earth_row, earth_col, None)
        variables[earth_col] = {
            "earth_value": earth_val,
            "earth_percentile": pct_earth,
            "reference_percentile": pct_target,
            "score": round(var_score, 4),
            "score_formula": (
                f"1 - |{pct_earth} - {pct_target}|" if pct_earth is not None else "neutral=0.5"
            ),
        }

    final_score = _geometric_mean_list(scores)
    return (round(final_score, 4), "high", {"variables": variables})


# ---------------------------------------------------------------------------
# 10. weighted_geometric_mean
# ---------------------------------------------------------------------------

def weighted_geometric_mean(
    scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Weighted geometric mean over selected characteristics.

    product(score_i ^ w_i) for selected i only.
    Weights are renormalized to sum to 1 over the selection.
    If any score is 0, the total is 0.
    """
    selected = {k: v for k, v in scores.items() if k in weights}
    if not selected:
        return 0.0

    total_w = sum(weights[k] for k in selected)
    if total_w <= 0:
        return 0.0

    result = 1.0
    for char_id, score in selected.items():
        w = weights[char_id] / total_w  # renormalized
        if score <= 0.0:
            return 0.0
        result *= score ** w

    return round(result, 6)


# ---------------------------------------------------------------------------
# 11. score_cell
# ---------------------------------------------------------------------------

def score_cell(
    earth_row: pd.Series,
    target: dict,
    selected_chars: list[str],
    weights: dict[str, float],
    mission_type: str,
) -> dict:
    """Score one Earth cell against one target.

    Returns a dict matching the SimilarityResult contract.
    """
    body = target.get("body", "moon")
    target_id = target.get("id", "unknown")
    ref = target.get("reference_values", {})

    char_scores: dict[str, float] = {}
    char_entries: list[dict] = []

    # Dispatch each selected characteristic
    _scorers = {
        "topography": lambda: topography_score(earth_row, ref, mission_type),
        "thermal": lambda: thermal_score(earth_row, ref),
        "surface_optics": lambda: surface_optics_score(earth_row, ref),
        "aridity": lambda: aridity_score(earth_row),
        "ice_polar": lambda: ice_polar_score(earth_row, ref),
        "volcanic_caves": lambda: volcanic_caves_score(earth_row),
        "geology": lambda: geology_score(earth_row, ref),
        "illumination": lambda: illumination_score(earth_row, ref),
    }

    for char_id in selected_chars:
        scorer = _scorers.get(char_id)
        if scorer is None:
            continue
        score, confidence, detail = scorer()
        char_scores[char_id] = score

        entry: dict[str, Any] = {
            "characteristic_id": char_id,
            "score": score,
            "confidence": confidence,
        }
        if char_id == "volcanic_caves":
            entry["proxy"] = True
        else:
            entry["proxy"] = False
        entry.update(detail)
        char_entries.append(entry)

    # Total score
    total = weighted_geometric_mean(char_scores, weights)

    # Environment tags (from individual scores, computed for all 8)
    env_tags = compute_environment_tags(earth_row, char_scores)

    # Confidence = minimum of all selected characteristic confidences
    confidence_order = {"high": 2, "medium": 1, "low": 0}
    min_conf = "high"
    for entry in char_entries:
        c = entry.get("confidence", "low")
        if confidence_order.get(c, 0) < confidence_order.get(min_conf, 2):
            min_conf = c

    # Cannot-reproduce list from target (verbatim) or fallback to body constant
    cannot_reproduce = target.get("cannot_reproduce") or (
        CANNOT_REPRODUCE_MOON if body == "moon" else CANNOT_REPRODUCE_MARS
    )

    # Cell metadata
    cell_id = str(earth_row.get("cell_id", f"{earth_row.get('lat_center', 0)}_{earth_row.get('lon_center', 0)}"))
    lat = float(earth_row.get("lat_center", 0.0))
    lon = float(earth_row.get("lon_center", 0.0))

    is_known = _is_known_analog(earth_row)

    return {
        "cell_id": cell_id,
        "lat_center": lat,
        "lon_center": lon,
        "body": body,
        "mission_type": mission_type,
        "target": {
            "id": target_id,
            "name": target.get("name", target_id),
            "lat": target.get("lat"),
            "lon": target.get("lon"),
            "coordinate_status": target.get("coordinate_status", "UNVERIFIED"),
        },
        "selected_characteristics": selected_chars,
        "weights": {k: weights[k] for k in selected_chars if k in weights},
        "characteristic_scores": char_entries,
        "characteristic_summary_scores": char_scores,
        "total_score": total,
        "environment_tags": env_tags,
        "confidence": min_conf,
        "is_known_analog": is_known,
        "rank": None,  # filled by score_all
        "cannot_reproduce": cannot_reproduce,
        "interpretation": None,
    }


# ---------------------------------------------------------------------------
# 12. score_all
# ---------------------------------------------------------------------------

def score_all(
    earth_df: pd.DataFrame,
    target: dict,
    selected_chars: list[str],
    weights: dict[str, float],
    mission_type: str,
    exclude_known: bool = True,
) -> list[dict]:
    """Score all Earth cells against one target.

    Returns list of SimilarityResult dicts, sorted by total_score desc,
    with rank assigned.  Known analogs are filtered if exclude_known=True.
    """
    results = []
    for _, row in earth_df.iterrows():
        result = score_cell(row, target, selected_chars, weights, mission_type)
        is_known = result.get("is_known_analog", False)
        if exclude_known and is_known:
            continue
        results.append(result)

    # Sort descending by total_score
    results.sort(key=lambda r: r["total_score"], reverse=True)

    # Assign rank (1-based)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    return results


# ---------------------------------------------------------------------------
# Environment tags (METHODOLOGY §4)
# ---------------------------------------------------------------------------

def compute_environment_tags(earth_row: pd.Series, char_scores: dict[str, float]) -> list[str]:
    """Compute environment-family tags from characteristic scores and cell attributes."""
    tags: list[str] = []

    # desert / arid
    aridity = char_scores.get("aridity")
    if aridity is None:
        # Compute from row directly
        aridity_idx = _get_float(earth_row, "aridity_index", None)
        if aridity_idx is not None:
            aridity = max(0.0, 1.0 - min(aridity_idx, 1.0))

    if aridity is not None:
        if aridity > 0.75:
            tags.append("desert")
        if aridity > 0.50:
            tags.append("arid")

    # polar
    lat = _get_float(earth_row, "lat_center", 0.0)
    if lat is not None and abs(lat) > 60.0:
        tags.append("polar")

    # ice sheet
    ice_cover = _get_float(earth_row, "ice_cover_fraction", None)
    if ice_cover is not None and ice_cover >= 0.5:
        tags.append("ice sheet")

    # volcanic (GLiM vb class)
    glim_vb = earth_row.get("glim_vb", None)
    if glim_vb is not None and not _is_nan(glim_vb) and int(float(glim_vb)) == 1:
        tags.append("volcanic")

    # cave (HIGH volcanic_caves likelihood)
    likelihood = earth_row.get("volcanic_caves_likelihood", None)
    if likelihood is not None and not _is_nan(likelihood) and str(likelihood).upper() == "HIGH":
        tags.append("cave")

    return tags


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_float(row: pd.Series, key: str, default=None):
    val = row.get(key, default)
    if val is None:
        return default
    if _is_nan(val):
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _get_str(row: pd.Series, key: str, default: str = "") -> str:
    val = row.get(key, default)
    if val is None or _is_nan(val):
        return default
    return str(val)


def _is_nan(val) -> bool:
    try:
        return math.isnan(float(val))
    except (TypeError, ValueError):
        return False


def _get_ref_value(ref_char: dict, var_name: str, default: float) -> float:
    entry = ref_char.get(var_name, {})
    if isinstance(entry, dict):
        return entry.get("value", default)
    return default


def _geometric_mean_list(values: list[float]) -> float:
    if not values:
        return 0.0
    product = 1.0
    for v in values:
        if v <= 0.0:
            return 0.0
        product *= v
    return product ** (1.0 / len(values))


def _is_known_analog(row: pd.Series) -> bool:
    """Return True if the cell is within 50 km of a known analog site.

    Uses known_analog_within_km column; -1.0 means not yet computed (Phase 3c placeholder).
    """
    dist = _get_float(row, "known_analog_within_km", -1.0)
    if dist is None or dist < 0:
        return False  # placeholder — treat as not known until populated
    return dist <= 50.0
