"""
export_static.py — Export scored Earth cells to GeoJSON and meta.json for the frontend.
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.

Produces:
    frontend/public/data/meta.json
    frontend/public/data/moon_landing.json
    frontend/public/data/moon_base.json
    frontend/public/data/mars_landing.json
    frontend/public/data/mars_base.json
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data_loader import load_earth_cells, load_targets

OUT_DIR = ROOT / "frontend" / "public" / "data"
CONFIG_DIR = ROOT / "config"
CACHE_DIR = ROOT / "data" / "raw" / "earth"
REGION_CACHE_FILE = CACHE_DIR / "region_hints_cache.json"
KNOWN_ANALOGS_CSV = ROOT / "data" / "reference" / "known_analogs.csv"
WARN_SIZE_MB = 5.0
MAX_TARGET_SIZE_MB = 3.0

ALL_CHARS = [
    "topography",
    "geology",
    "thermal",
    "aridity",
    "ice_polar",
    "volcanic_caves",
    "surface_optics",
    "illumination",
]

CANNOT_REPRODUCE = {
    "moon": [
        "Gravity: 1/6 g (1.62 m/s²)",
        "Vacuum: about 10⁻¹⁰ Pa",
        "Unfiltered solar and cosmic radiation",
        "Absolute temperatures from about 40 K to 400 K",
        "14-day day/night cycle",
        "Near-horizon sun all year at the south pole: on Earth the yearly maximum sun elevation is at least 23.4°",
        "Sharp-edged, electrostatically charged regolith",
    ],
    "mars": [
        "Gravity: 0.38 g (3.72 m/s²)",
        "Atmosphere: about 0.6 kPa, 95% CO₂",
        "No ozone layer: full UV and ionizing radiation",
        "Global dust storms",
        "Absolute temperatures from about −140 °C to +20 °C",
        "Perchlorates in the regolith",
    ],
}


def slugify(text: str) -> str:
    s = text.replace("–", " ").replace("—", " ")
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[\s-]+", "_", s)


def normalize_weights(selected: list[str], weights: dict[str, float]) -> dict[str, float]:
    sub = {c: float(weights.get(c, 0.0)) for c in selected}
    tot = sum(sub.values())
    if tot <= 0:
        return {c: 1.0 / len(selected) for c in selected}
    return {c: v / tot for c, v in sub.items()}


# ---------------------------------------------------------------------------
# Region hints resolution via FAO GAUL level1 in Earth Engine
# ---------------------------------------------------------------------------

def load_cached_regions() -> dict[str, str]:
    if REGION_CACHE_FILE.exists():
        try:
            with open(REGION_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cached_regions(cache: dict[str, str]):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGION_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1, ensure_ascii=False)


def resolve_region_hints(cells: list[tuple[str, float, float]]) -> dict[str, str]:
    """Resolve ADM1_NAME, ADM0_NAME for cells using FAO/GAUL/2015/level1."""
    cache = load_cached_regions()
    results = {}
    to_query = []

    for cid, lat, lon in cells:
        # Spot-check Arctic archipelagos: Franz Josef Land is in the high Arctic (80-82N, 42-65E)
        if 79.5 <= lat <= 82.5 and 42.0 <= lon <= 66.0:
            hint = "Franz Josef Land, Russian Federation"
            results[cid] = hint
            cache[cid] = hint
        elif cid in cache:
            results[cid] = cache[cid]
        elif lat < -60.0:
            results[cid] = "Antarctica"
            cache[cid] = "Antarctica"
        else:
            to_query.append((cid, lat, lon))

    if not to_query:
        return results

    print(f"[export_static] Resolving region hints for {len(to_query):,} uncached cells via FAO GAUL...")
    try:
        from scripts.earth.ee_utils import init_ee
        import ee
        init_ee()

        gaul = ee.FeatureCollection("FAO/GAUL/2015/level1").select(["ADM1_NAME", "ADM0_NAME"])
        join = ee.Join.saveFirst(matchKey="adm")
        sf = ee.Filter.intersects(leftField=".geo", rightField=".geo")

        chunk_size = 250
        for i in range(0, len(to_query), chunk_size):
            chunk = to_query[i:i + chunk_size]
            pts = [
                ee.Feature(ee.Geometry.Point([lon, lat]), {"cid": cid, "lat": lat, "lon": lon})
                for cid, lat, lon in chunk
            ]
            pts_fc = ee.FeatureCollection(pts)
            joined = join.apply(pts_fc, gaul, sf)
            stripped = joined.map(lambda f: ee.Feature(None, {
                "cid": f.get("cid"),
                "lat": f.get("lat"),
                "lon": f.get("lon"),
                "adm1": ee.Algorithms.If(f.get("adm"), ee.Feature(f.get("adm")).get("ADM1_NAME"), None),
                "adm0": ee.Algorithms.If(f.get("adm"), ee.Feature(f.get("adm")).get("ADM0_NAME"), None),
            }))
            res = stripped.getInfo()
            for f in res.get("features", []):
                p = f.get("properties", {})
                cid = p.get("cid")
                adm1 = p.get("adm1")
                adm0 = p.get("adm0")
                lat_val = float(p.get("lat", 0.0))
                lon_val = float(p.get("lon", 0.0))

                if 79.5 <= lat_val <= 82.5 and 42.0 <= lon_val <= 66.0:
                    hint = "Franz Josef Land, Russian Federation"
                elif adm1 and adm0:
                    if "Antarctica" in str(adm0) or "Antarctica" in str(adm1):
                        hint = "Antarctica"
                    elif adm1 == "Administrative unit not available":
                        hint = str(adm0)
                    else:
                        hint = f"{adm1}, {adm0}"
                elif adm0:
                    hint = str(adm0)
                else:
                    hint = f"Unnamed area ({lat_val:.2f}, {lon_val:.2f})"

                results[cid] = hint
                cache[cid] = hint

        save_cached_regions(cache)
    except Exception as e:
        print(f"[export_static] Warning: EE GAUL resolution failed ({e}). Using geographic fallback.", file=sys.stderr)
        for cid, lat, lon in to_query:
            if 79.5 <= lat <= 82.5 and 42.0 <= lon <= 66.0:
                hint = "Franz Josef Land, Russian Federation"
            elif lat < -60.0:
                hint = "Antarctica"
            else:
                hint = f"Unnamed area ({lat:.2f}, {lon:.2f})"
            results[cid] = hint
            cache[cid] = hint
        save_cached_regions(cache)

    return results


# ---------------------------------------------------------------------------
# Vectorized Scorers
# ---------------------------------------------------------------------------

def _ref_val(d: dict, key: str, default: float) -> float:
    entry = d.get(key, {})
    if isinstance(entry, dict):
        v = entry.get("value", default)
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default
    try:
        return float(entry) if entry is not None else default
    except (TypeError, ValueError):
        return default


def _ref_pct(d: dict, key: str, default: float) -> float:
    entry = d.get(key, {})
    if isinstance(entry, dict):
        v = entry.get("percentile_estimate", default)
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default
    try:
        return float(entry) if entry is not None else default
    except (TypeError, ValueError):
        return default


def score_topography_vec(earth_df: pd.DataFrame, target: dict, mission_type: str) -> np.ndarray:
    topo = target.get("reference_values", {}).get("topography", {})
    slope = earth_df["slope"].values
    
    if mission_type == "landing":
        mu_slope = _ref_val(topo, "slope", 4.0)
        mu_rough = _ref_val(topo, "roughness", 10.0)
        roughness = earth_df["roughness"].values
        
        slope_score = np.exp(-((slope - mu_slope) ** 2) / (2 * 2.0 ** 2))
        rough_score = np.exp(-((roughness - mu_rough) ** 2) / (2 * 10.0 ** 2))
        
        # Hard cap: slope > 12.0 deg -> score = -1.0
        score = np.where(slope > 12.0, -1.0, np.sqrt(slope_score * rough_score))
        return score
    else:
        # Base
        mu_slope = _ref_val(topo, "slope", 4.0)
        mu_relief = _ref_val(topo, "local_relief", 500.0)
        local_relief = earth_df["local_relief"].values
        
        slope_score = np.exp(-((slope - mu_slope) ** 2) / (2 * 2.0 ** 2))
        relief_score = np.exp(-((local_relief - mu_relief) ** 2) / (2 * 50.0 ** 2))
        
        # Hard cap: slope > 12.0 deg -> score = -1.0 (same hard cap applies per METHODOLOGY §2.1)
        score = np.where(slope > 12.0, -1.0, np.sqrt(slope_score * relief_score))
        return score


def score_thermal_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    th = target.get("reference_values", {}).get("thermal", {})
    t_mean_pct = _ref_pct(th, "temp_annual_mean", 0.0)
    t_range_pct = _ref_pct(th, "temp_annual_range", 0.0)
    t_diurnal_pct = _ref_pct(th, "temp_diurnal_range", 0.0)
    
    s_mean = np.clip(1.0 - np.abs(earth_df["lst_annual_mean_pct"].values - t_mean_pct), 0.0, 1.0)
    s_range = np.clip(1.0 - np.abs(earth_df["lst_annual_range_pct"].values - t_range_pct), 0.0, 1.0)
    s_diurnal = np.clip(1.0 - np.abs(earth_df["lst_diurnal_range_pct"].values - t_diurnal_pct), 0.0, 1.0)
    
    score = (s_mean * s_range * s_diurnal) ** (1.0 / 3.0)
    return score


def score_surface_optics_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    opt = target.get("reference_values", {}).get("surface_optics", {})
    mu_albedo = _ref_val(opt, "albedo", _ref_val(opt, "reflectance", 0.12))
    sigma_albedo = _ref_val(opt, "albedo_sigma", 0.03)
    sigma_eff = max(sigma_albedo, 0.05)
    
    albedo = earth_df["broadband_albedo"].values
    score = np.exp(-((albedo - mu_albedo) ** 2) / (2 * sigma_eff ** 2))
    return score


def score_illumination_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    ill = target.get("reference_values", {}).get("illumination", {})
    t_elev_pct = _ref_pct(ill, "solar_elevation_range", 0.0)
    t_night_pct = _ref_pct(ill, "illumination_fraction", 0.5)
    
    s_elev = np.clip(1.0 - np.abs(earth_df["max_solar_elevation_pct"].values - t_elev_pct), 0.0, 1.0)
    s_night = np.clip(1.0 - np.abs(earth_df["longest_polar_night_days_pct"].values - t_night_pct), 0.0, 1.0)
    
    score = np.sqrt(s_elev * s_night)
    return score


def score_geology_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    geo = target.get("reference_values", {}).get("geology", {})
    unit = geo.get("geologic_unit", {})
    if isinstance(unit, dict):
        class_desc = unit.get("class_description", "").lower()
    else:
        class_desc = str(unit).lower()
        
    classes = earth_df["lithology_class"].values
    scores = np.full(len(earth_df), np.nan, dtype=object)
    
    from backend.scoring import _GEOLOGY_PRIMARY, _GEOLOGY_SECONDARY
    
    for i, c in enumerate(classes):
        if c is None or (isinstance(c, float) and np.isnan(c)) or c == "unclassified":
            scores[i] = None
        else:
            c_str = str(c)
            p_kw = _GEOLOGY_PRIMARY.get(c_str, [])
            s_kw = _GEOLOGY_SECONDARY.get(c_str, [])
            if any(kw in class_desc for kw in p_kw):
                scores[i] = 1.0
            elif any(kw in class_desc for kw in s_kw):
                scores[i] = 0.5
            else:
                scores[i] = 0.1  # Categorical mismatch: low score (0.05-0.2), not 0
                
    return scores


def score_volcanic_caves_vec(earth_df: pd.DataFrame) -> np.ndarray:
    likelihoods = earth_df["volcanic_caves_likelihood"].values
    scores = np.full(len(earth_df), np.nan, dtype=object)
    
    for i, lh in enumerate(likelihoods):
        if lh is None or (isinstance(lh, float) and np.isnan(lh)):
            scores[i] = None
        elif lh == "HIGH":
            scores[i] = 1.0
        elif lh == "MEDIUM":
            scores[i] = 0.5
        elif lh == "LOW":
            scores[i] = 0.1  # Categorical mismatch: low score (0.05-0.2), not 0
        else:
            scores[i] = None
            
    return scores


def format_score(val) -> float | None:
    """Format exported score: -1.0 for hard-fail, max(round(s, 3), 0.001) for positive, None for missing."""
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isneginf(val))):
        return None
    val_f = float(val)
    if val_f < 0:
        return -1.0
    return max(round(val_f, 3), 0.001)


# ---------------------------------------------------------------------------
# Export Logic
# ---------------------------------------------------------------------------

def export_meta(targets_data: dict, known_df: pd.DataFrame):
    missions_files = {
        "moon_landing": "moon-landing.json",
        "moon_base": "moon-base.json",
        "mars_landing": "mars-landing.json",
        "mars_base": "mars-base.json",
    }
    
    with open(CONFIG_DIR / "characteristics.json", encoding="utf-8") as f:
        chars_raw = json.load(f)
        
    chars_list = [
        {
            "id": c["id"],
            "name": c["name"],
            "description": c["description"],
            "comparison_rule": c["comparison_rule"],
            "proxy": c.get("proxy_label") == "PROXY",
        }
        for c in chars_raw
    ]
    
    presets = {}
    for preset_key, m_file in missions_files.items():
        with open(CONFIG_DIR / "missions" / m_file, encoding="utf-8") as f:
            m = json.load(f)
            
        presets[preset_key] = {
            "body": m["body"],
            "mission_type": m["mission_type"],
            "default_characteristics": m["default_characteristics"],
            "default_weights": m["default_weights"],
            "targets": [
                {
                    "id": slugify(t["name"]),
                    "name": t["name"],
                    "lat": t["lat"],
                    "lon": t["lon"],
                    "description": t["description"],
                    "coordinate_status": t["coordinate_status"],
                    "value_origin": "literature",
                }
                for t in m["reference_targets"]
            ],
        }
        
    known_list = [
        {
            "name": r["name"],
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "body": r["body"],
            "type": r["type"],
            "source_url": r["source_url"],
        }
        for _, r in known_df.iterrows()
    ]
    
    meta = {
        "mock": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Production static export generated from processed NASA Earth Engine DEM, MODIS, and TerraClimate datasets.",
        "characteristics": chars_list,
        "presets": presets,
        "cannot_reproduce": CANNOT_REPRODUCE,
        "known_analogs": known_list,
    }
    
    meta_path = OUT_DIR / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(f"[export_static] Wrote {meta_path} (mock: false)")


def process_preset(
    earth_df: pd.DataFrame,
    targets_data: dict,
    preset_key: str,
    top_n_per_char: int = 50,
    top_n_default: int = 300,
) -> tuple[dict, list[tuple[str, float, float]]]:
    parts = preset_key.split("_")
    body, mission_type = parts[0], parts[1]
    
    with open(CONFIG_DIR / "missions" / f"{body}-{mission_type}.json", encoding="utf-8") as f:
        preset_cfg = json.load(f)
    def_chars = preset_cfg["default_characteristics"]
    def_weights = normalize_weights(def_chars, preset_cfg["default_weights"])
    
    targets_dict = targets_data.get("targets", {})
    relevant_targets = [
        t for t in targets_dict.values()
        if t.get("body") == body and t.get("mission_type") == mission_type
    ]
    
    if not relevant_targets:
        return {"type": "FeatureCollection", "features": []}, []
        
    print(f"[export_static] Processing {preset_key} ({len(relevant_targets)} targets)...")
    
    # Precompute target-independent scores on earth_df
    aridity_arr = earth_df["aridity_score"].values.astype(float)
    ice_polar_arr = earth_df["ice_polar_score"].values.astype(float)
    volcanic_caves_arr = score_volcanic_caves_vec(earth_df)
    
    # Store scores: char_id -> target_id -> array
    scores = {c: {} for c in ALL_CHARS}
    for tgt in relevant_targets:
        tid = tgt["id"]
        scores["aridity"][tid] = aridity_arr
        scores["ice_polar"][tid] = ice_polar_arr
        scores["volcanic_caves"][tid] = volcanic_caves_arr
        scores["topography"][tid] = score_topography_vec(earth_df, tgt, mission_type)
        scores["thermal"][tid] = score_thermal_vec(earth_df, tgt)
        scores["surface_optics"][tid] = score_surface_optics_vec(earth_df, tgt)
        scores["illumination"][tid] = score_illumination_vec(earth_df, tgt)
        scores["geology"][tid] = score_geology_vec(earth_df, tgt)
        
    # Selection of candidate cells
    # Eligible universe: barren_sparse_fraction >= 0.5 OR is_known_analog
    eligible_indices = np.where(earth_df["eligible_barren"].values)[0]
    print(f"  Eligible candidate cells (barren >= 0.5 or known analog): {len(eligible_indices):,}")
    
    top_indices = set()
    
    # 1. Top cells by default combination for every target
    for tgt in relevant_targets:
        tid = tgt["id"]
        hard_fail = np.zeros(len(eligible_indices), dtype=bool)
        log_sum = np.zeros(len(eligible_indices), dtype=float)
        used_weight = np.zeros(len(eligible_indices), dtype=float)
        
        for c in def_chars:
            w_c = def_weights[c]
            s_all = scores[c][tid]
            s_sub = s_all[eligible_indices]
            
            # None or NaN check
            is_valid = np.array([x is not None and not (isinstance(x, float) and np.isnan(x)) for x in s_sub])
            # If s < 0 -> hard fail
            is_neg = np.array([x is not None and isinstance(x, (int, float)) and x < 0 for x in s_sub])
            hard_fail |= is_neg
            
            # Align with dashboard scoring.mjs: missing data (null) is skipped and lowers coverage,
            # not floored to 0.01. Valid positive scores are floored to 0.01 and re-normalized by used_weight.
            valid_pos = is_valid & ~is_neg
            pos_vals = np.where(valid_pos, s_sub.astype(float), 1.0)
            floored_vals = np.clip(pos_vals, 0.01, 1.0)
            
            log_sum += np.where(valid_pos, w_c * np.log(floored_vals), 0.0)
            used_weight += np.where(valid_pos, w_c, 0.0)
            
        with np.errstate(divide="ignore", invalid="ignore"):
            norm_log_sum = np.where(used_weight > 0, log_sum / used_weight, 0.0)
            comb_scores = np.where(hard_fail | (used_weight == 0), -1.0, np.exp(norm_log_sum))
        valid_comb_mask = comb_scores > 0
        
        if np.any(valid_comb_mask):
            k = min(top_n_default, int(valid_comb_mask.sum()))
            comb_for_sort = np.where(valid_comb_mask, comb_scores, -1.0)
            part_idx = np.argpartition(comb_for_sort, -k)[-k:]
            top_indices.update(eligible_indices[part_idx].tolist())
            
    # 2. Top cells per individual characteristic for every target
    for char_id in ALL_CHARS:
        for tgt in relevant_targets:
            tid = tgt["id"]
            arr = scores[char_id][tid][eligible_indices]
            valid_mask = np.array([x is not None and not (isinstance(x, float) and np.isnan(x)) and float(x) > 0 for x in arr])
            if not np.any(valid_mask):
                continue
            num_vals = np.where(valid_mask, arr.astype(float), -1.0)
            k = min(top_n_per_char, int(valid_mask.sum()))
            part_idx = np.argpartition(num_vals, -k)[-k:]
            top_indices.update(eligible_indices[part_idx].tolist())
            
    # 3. Always include known analog cells
    known_indices = np.where(earth_df["is_known_analog"].values)[0]
    top_indices.update(known_indices.tolist())
    
    selected_indices = sorted(top_indices)
    print(f"  Selected {len(selected_indices):,} unique candidate cells.")
    
    coords_for_regions = [
        (str(earth_df.iloc[idx]["cell_id"]), float(earth_df.iloc[idx]["lat_center"]), float(earth_df.iloc[idx]["lon_center"]))
        for idx in selected_indices
    ]
    
    return {
        "preset_key": preset_key,
        "selected_indices": selected_indices,
        "scores": scores,
        "relevant_targets": relevant_targets,
        "def_chars": def_chars,
        "def_weights": def_weights,
    }, coords_for_regions


def build_geojson(
    earth_df: pd.DataFrame,
    preset_pack: dict,
    region_hints: dict[str, str],
) -> tuple[dict, dict]:
    selected_indices = preset_pack["selected_indices"]
    scores = preset_pack["scores"]
    relevant_targets = preset_pack["relevant_targets"]
    def_chars = preset_pack["def_chars"]
    def_weights = preset_pack["def_weights"]
    
    features = []
    first_target_id = relevant_targets[0]["id"]
    
    n_positive_comb = 0
    n_antarctica = 0
    
    for idx in selected_indices:
        row = earth_df.iloc[idx]
        lat = float(row["lat_center"])
        lon = float(row["lon_center"])
        cell_id = str(row["cell_id"])
        is_known = bool(row["is_known_analog"])
        known_name = row["known_analog_name"] if is_known else None
        region_hint = region_hints.get(cell_id, f"Unnamed area ({lat:.2f}, {lon:.2f})")
        
        if lat < -60.0:
            n_antarctica += 1
            
        # Build score dict for this cell
        cell_scores = {c: {} for c in ALL_CHARS}
        for c in ALL_CHARS:
            for tid in scores[c]:
                val = scores[c][tid][idx]
                cell_scores[c][tid] = format_score(val)
                
        # Compute default combination score for the first target
        hard_fail = False
        log_sum = 0.0
        used_weight = 0.0
        for c in def_chars:
            s = cell_scores[c].get(first_target_id)
            if s is None:
                continue
            if s < 0:
                hard_fail = True
                break
            w_c = def_weights[c]
            used_weight += w_c
            log_sum += w_c * math.log(max(0.01, min(1.0, s)))
        if hard_fail or used_weight == 0:
            def_score_first_tgt = -1.0
        else:
            def_score_first_tgt = round(math.exp(log_sum / used_weight), 3)
        if def_score_first_tgt > 0.05:
            n_positive_comb += 1
            
        values = {
            "barren_sparse_fraction": {
                "value": round(float(row["barren_sparse_fraction"]), 2),
                "units": "fraction",
                "source": "MODIS MCD12Q1",
            },
            "slope_mean_deg": {
                "value": round(float(row["slope"]), 1),
                "units": "degrees",
                "source": "Copernicus DEM GLO-30 (1km baseline)",
            },
            "roughness_m": {
                "value": round(float(row["roughness"]), 1),
                "units": "meters",
                "source": "Copernicus DEM GLO-30",
            },
            "broadband_albedo": {
                "value": round(float(row["broadband_albedo"]), 3),
                "units": "0-1",
                "source": "MODIS MCD43A3",
            },
            "aridity_index": {
                "value": round(float(row["aridity_index"]), 3),
                "units": "P/PET",
                "source": "TerraClimate",
            },
            "precipitation_mm": {
                "value": round(float(row["precipitation"]), 1),
                "units": "mm/yr",
                "source": "TerraClimate",
            },
            "lst_annual_mean_c": {
                "value": round(float(row["lst_annual_mean"]), 1),
                "units": "°C",
                "source": "MODIS MOD11A2",
            },
            "ice_cover_fraction": {
                "value": round(float(row["ice_cover_fraction"]), 2),
                "units": "0-1",
                "source": "MODIS MCD12Q1",
            },
            "longest_polar_night_days": {
                "value": int(round(float(row["longest_polar_night_days"]))),
                "units": "days",
                "source": "Analytical solar geometry",
            },
            "lithology_class": {
                "value": row["lithology_class"] if pd.notna(row["lithology_class"]) else None,
                "units": "class",
                "source": "GLiM 0.5deg (PANGAEA)",
            },
            "volcanic_caves_likelihood": {
                "value": row["volcanic_caves_likelihood"] if pd.notna(row["volcanic_caves_likelihood"]) else None,
                "units": "likelihood",
                "source": "Smithsonian GVP Holocene catalog",
            },
        }
        
        confidence = {
            "topography": str(row.get("topography_confidence", "high")),
            "thermal": str(row.get("thermal_confidence", "high")),
            "surface_optics": str(row.get("surface_optics_confidence", "high")),
            "aridity": str(row.get("aridity_confidence", "high")),
            "ice_polar": str(row.get("ice_polar_confidence", "medium")),
            "volcanic_caves": str(row.get("volcanic_caves_confidence", "low")),
            "geology": str(row.get("geology_confidence", "high")),
            "illumination": str(row.get("illumination_confidence", "high")),
        }
        
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "cell_id": cell_id,
                "lat_center": lat,
                "lon_center": lon,
                "region_hint": region_hint,
                "land_fraction": round(float(row["land_fraction"]), 2),
                "is_known_analog": is_known,
                "known_analog_name": known_name,
                "environment_tags": row["environment_tags"].tolist() if isinstance(row["environment_tags"], np.ndarray) else list(row["environment_tags"]),
                "scores": cell_scores,
                "confidence": confidence,
                "values": values,
            },
        }
        features.append((def_score_first_tgt, feature))
        
    features.sort(key=lambda x: x[0], reverse=True)
    top_5 = [
        {
            "cell_id": f["properties"]["cell_id"],
            "lat": f["properties"]["lat_center"],
            "lon": f["properties"]["lon_center"],
            "region_hint": f["properties"]["region_hint"],
            "default_score": score,
        }
        for score, f in features[:5]
    ]
    
    fc = {"type": "FeatureCollection", "features": [f for _, f in features]}
    
    stats = {
        "n_features": len(features),
        "n_positive_comb": n_positive_comb,
        "n_antarctica": n_antarctica,
        "first_target_id": first_target_id,
        "top_5": top_5,
    }
    return fc, stats


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("[export_static] Loading Earth cells parquet...")
    earth_df = load_earth_cells()
    print(f"  Loaded {len(earth_df):,} land cells.")
    
    print(f"[export_static] Loading known analogs from {KNOWN_ANALOGS_CSV}...")
    known_df = pd.read_csv(KNOWN_ANALOGS_CSV)
    print(f"  Loaded {len(known_df)} known analog sites.")
    
    is_known_mask = np.zeros(len(earth_df), dtype=bool)
    known_name_arr = np.full(len(earth_df), None, dtype=object)
    
    for _, r in known_df.iterrows():
        d = np.hypot(earth_df["lat_center"].values - r["lat"], earth_df["lon_center"].values - r["lon"])
        match = d <= 0.5
        is_known_mask |= match
        for idx in np.where(match)[0]:
            if known_name_arr[idx] is None:
                known_name_arr[idx] = r["name"]
                
    earth_df["is_known_analog"] = is_known_mask
    earth_df["known_analog_name"] = known_name_arr
    print(f"  Flagged {is_known_mask.sum():,} cells within 0.5° of a known analog site.")
    
    eligible_mask = (earth_df["barren_sparse_fraction"].values >= 0.5) | is_known_mask
    earth_df["eligible_barren"] = eligible_mask
    print(f"  Eligible screening pool: {eligible_mask.sum():,} cells (barren >= 0.5 or known analog).")
    
    print("[export_static] Loading reference targets...")
    targets_data = load_targets()
    
    # 1. Export meta.json
    export_meta(targets_data, known_df)
    
    # 2. Select candidates for each preset
    presets_to_process = ["moon_landing", "moon_base", "mars_landing", "mars_base"]
    packs = {}
    all_coords_to_resolve = []
    
    for p_key in presets_to_process:
        pack, coords = process_preset(
            earth_df,
            targets_data,
            p_key,
            top_n_per_char=50,
            top_n_default=300,
        )
        packs[p_key] = pack
        all_coords_to_resolve.extend(coords)
        
    unique_cells_dict = {}
    for cid, lat, lon in all_coords_to_resolve:
        unique_cells_dict[cid] = (cid, lat, lon)
    unique_cells = list(unique_cells_dict.values())
    print(f"[export_static] Resolving region hints for {len(unique_cells):,} unique exported cells...")
    region_hints = resolve_region_hints(unique_cells)
    print(f"[export_static] Resolved region hints for {len(region_hints):,} cells.")
    
    # 3. Build GeoJSON for each preset and report stats
    report_data = {}
    for p_key in presets_to_process:
        fc, stats = build_geojson(earth_df, packs[p_key], region_hints)
        out_file = OUT_DIR / f"{p_key}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(fc, f, separators=(",", ":"), ensure_ascii=False)
            
        size_mb = out_file.stat().st_size / (1024 * 1024)
        stats["size_mb"] = size_mb
        report_data[p_key] = stats
        
        print(f"\n[export_static] Preset: {p_key}")
        print(f"  Feature count: {stats['n_features']:,}")
        print(f"  File size: {size_mb:.2f} MB")
        print(f"  Non-null, non-negative default combination score > 0.05: {stats['n_positive_comb']:,}")
        print(f"  Cells in Antarctica (lat < -60): {stats['n_antarctica']:,}")
        print(f"  Top 5 cells for target '{stats['first_target_id']}':")
        for rank, c in enumerate(stats["top_5"], 1):
            print(f"    {rank}. {c['cell_id']} ({c['lat']:+.3f}, {c['lon']:+.3f}) | {c['region_hint']} | default score = {c['default_score']:.3f}")
            
        if size_mb > WARN_SIZE_MB:
            print(f"  WARNING: File size {size_mb:.2f} MB exceeds {WARN_SIZE_MB} MB limit!", file=sys.stderr)
            
    print("\n[export_static] All static exports completed successfully.")


if __name__ == "__main__":
    main()
