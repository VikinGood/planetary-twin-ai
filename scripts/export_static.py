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
WARN_SIZE_MB = 5.0

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

KNOWN_ANALOGS = [
    ("Atacama Desert core", -24.1, -70.0),
    ("Haughton Crater, Devon Island", 75.4, -89.7),
    ("Death Valley", 36.5, -117.1),
    ("McMurdo Dry Valleys", -77.5, 162.0),
    ("Svalbard", 79.0, 16.0),
    ("Rio Tinto", 37.7, -6.6),
    ("Craters of the Moon, Idaho", 43.4, -113.5),
    ("Lanzarote", 29.0, -13.6),
    ("Mauna Kea, Hawaii", 19.8, -155.5),
    ("Iceland central highlands", 64.9, -17.5),
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

REGIONS = [
    ("Puna de Atacama", -25.0, -67.5),
    ("Payunia volcanic field", -36.4, -69.2),
    ("Patagonian basalt plateaus", -47.0, -70.5),
    ("Altiplano salt flats", -20.3, -67.6),
    ("Namib Desert", -24.5, 15.3),
    ("Sahara, Tibesti", 20.8, 18.0),
    ("Sahara, Hoggar", 23.3, 5.6),
    ("Arabian Harrat Khaybar", 25.8, 39.9),
    ("Rub al Khali", 20.5, 50.0),
    ("Afar depression", 13.0, 41.0),
    ("Gobi Desert", 43.0, 104.0),
    ("Taklamakan Desert", 39.0, 83.0),
    ("Qaidam Basin", 37.5, 93.0),
    ("Tibetan Plateau, Changtang", 34.5, 85.0),
    ("Lut Desert", 30.0, 58.5),
    ("Great Victoria Desert", -28.5, 128.0),
    ("Pilbara", -22.0, 118.0),
    ("Kalahari", -23.5, 22.0),
    ("Mojave volcanic fields", 34.9, -116.0),
    ("Snake River Plain", 43.4, -113.5),
    ("Sonoran, Pinacate", 31.8, -113.5),
    ("Columbia Plateau", 47.0, -119.5),
    ("Canadian Arctic Archipelago", 76.0, -95.0),
    ("Greenland ice-free margin", 70.0, -51.0),
    ("Ellesmere Island", 80.0, -80.0),
    ("Taymyr Peninsula", 75.0, 100.0),
    ("Kamchatka lava fields", 55.8, 160.3),
    ("Yakutia permafrost plains", 66.0, 125.0),
    ("Antarctic Peninsula ice-free", -63.5, -57.0),
    ("Transantarctic nunataks", -84.0, -170.0),
    ("Ethiopian Highlands lava", 11.5, 39.5),
    ("Deccan Traps", 19.0, 75.0),
    ("Siberian Traps", 66.0, 95.0),
    ("Mongolian volcanic plateau", 47.5, 99.0),
    ("Sinai Peninsula", 29.0, 33.8),
    ("Danakil salt plain", 14.2, 40.3),
    ("Karakum Desert", 39.5, 60.0),
    ("Thar Desert", 27.0, 71.0),
    ("Chihuahuan basalt fields", 31.5, -107.2),
    ("Andean altiplano volcanoes", -22.5, -68.0),
]


def slugify(text: str) -> str:
    s = text.replace("–", " ").replace("—", " ")
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[\s-]+", "_", s)


def get_region_hint(lat: float, lon: float) -> str:
    # Nearest landmark region within 8 degrees
    min_dist_sq = float("inf")
    best_name = ""
    for name, r_lat, r_lon in REGIONS:
        d_sq = (lat - r_lat) ** 2 + (lon - r_lon) ** 2
        if d_sq < min_dist_sq:
            min_dist_sq = d_sq
            best_name = name
    if min_dist_sq <= 64.0:  # ~8 degrees
        return best_name
    # Fallback to broad geographic zone
    if lat > 60:
        return "High Northern Latitude"
    if lat < -60:
        return "Antarctic Region"
    if -20 < lat < 20 and -30 < lon < 50:
        return "Equatorial Africa"
    if 15 < lat < 45 and -15 < lon < 60:
        return "Sahara-Arabian Belt"
    if 25 < lat < 50 and 60 < lon < 120:
        return "Central Asian Basin"
    if -40 < lat < -10 and 110 < lon < 155:
        return "Australian Interior"
    if -55 < lat < 10 and -80 < lon < -35:
        return "South America"
    if 15 < lat < 60 and -130 < lon < -60:
        return "North American Interior"
    return "Continental Interior"


def find_known_analog(lat: float, lon: float) -> tuple[bool, str | None]:
    for name, a_lat, a_lon in KNOWN_ANALOGS:
        if abs(lat - a_lat) <= 1.0 and abs(lon - a_lon) <= 1.0:
            return True, name
    return False, None


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
        
        # Hard cap: slope > 12.0 deg -> score = 0
        score = np.where(slope > 12.0, 0.0, np.sqrt(slope_score * rough_score))
        return np.clip(score, 0.0, 1.0)
    else:
        # Base
        mu_slope = _ref_val(topo, "slope", 4.0)
        mu_relief = _ref_val(topo, "local_relief", 500.0)
        local_relief = earth_df["local_relief"].values
        
        slope_score = np.exp(-((slope - mu_slope) ** 2) / (2 * 2.0 ** 2))
        relief_score = np.exp(-((local_relief - mu_relief) ** 2) / (2 * 50.0 ** 2))
        
        score = np.where(slope > 12.0, 0.0, np.sqrt(slope_score * relief_score))
        return np.clip(score, 0.0, 1.0)


def score_thermal_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    th = target.get("reference_values", {}).get("thermal", {})
    t_mean_pct = _ref_pct(th, "temp_annual_mean", 0.0)
    t_range_pct = _ref_pct(th, "temp_annual_range", 0.0)
    t_diurnal_pct = _ref_pct(th, "temp_diurnal_range", 0.0)
    
    s_mean = np.clip(1.0 - np.abs(earth_df["lst_annual_mean_pct"].values - t_mean_pct), 0.0, 1.0)
    s_range = np.clip(1.0 - np.abs(earth_df["lst_annual_range_pct"].values - t_range_pct), 0.0, 1.0)
    s_diurnal = np.clip(1.0 - np.abs(earth_df["lst_diurnal_range_pct"].values - t_diurnal_pct), 0.0, 1.0)
    
    score = (s_mean * s_range * s_diurnal) ** (1.0 / 3.0)
    return np.clip(score, 0.0, 1.0)


def score_surface_optics_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    opt = target.get("reference_values", {}).get("surface_optics", {})
    mu_albedo = _ref_val(opt, "albedo", _ref_val(opt, "reflectance", 0.12))
    sigma_albedo = _ref_val(opt, "albedo_sigma", 0.03)
    sigma_eff = max(sigma_albedo, 0.05)
    
    albedo = earth_df["broadband_albedo"].values
    score = np.exp(-((albedo - mu_albedo) ** 2) / (2 * sigma_eff ** 2))
    return np.clip(score, 0.0, 1.0)


def score_illumination_vec(earth_df: pd.DataFrame, target: dict) -> np.ndarray:
    ill = target.get("reference_values", {}).get("illumination", {})
    t_elev_pct = _ref_pct(ill, "solar_elevation_range", 0.0)
    t_night_pct = _ref_pct(ill, "illumination_fraction", 0.5)
    
    s_elev = np.clip(1.0 - np.abs(earth_df["max_solar_elevation_pct"].values - t_elev_pct), 0.0, 1.0)
    s_night = np.clip(1.0 - np.abs(earth_df["longest_polar_night_days_pct"].values - t_night_pct), 0.0, 1.0)
    
    score = np.sqrt(s_elev * s_night)
    return np.clip(score, 0.0, 1.0)


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
                scores[i] = 0.0
                
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
            scores[i] = 0.0
        else:
            scores[i] = None
            
    return scores


# ---------------------------------------------------------------------------
# Export Logic
# ---------------------------------------------------------------------------

def export_meta(targets_data: dict):
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
        
    meta = {
        "mock": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Production static export generated from processed NASA Earth Engine DEM, MODIS, and TerraClimate datasets.",
        "characteristics": chars_list,
        "presets": presets,
        "cannot_reproduce": CANNOT_REPRODUCE,
        "known_analogs": [{"name": name, "lat": lat, "lon": lon} for name, lat, lon in KNOWN_ANALOGS],
    }
    
    meta_path = OUT_DIR / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(f"[export_static] Wrote {meta_path} (mock: false)")


def process_preset(
    earth_df: pd.DataFrame,
    targets_data: dict,
    preset_key: str,
    top_n_per_target: int = 400,
) -> dict:
    parts = preset_key.split("_")
    body, mission_type = parts[0], parts[1]
    
    targets_dict = targets_data.get("targets", {})
    relevant_targets = [
        t for t in targets_dict.values()
        if t.get("body") == body and t.get("mission_type") == mission_type
    ]
    
    if not relevant_targets:
        return {"type": "FeatureCollection", "features": []}
        
    print(f"[export_static] Processing {preset_key} ({len(relevant_targets)} targets)...")
    
    n_cells = len(earth_df)
    
    # Precompute target-independent scores
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
        
    # Select top candidate cells
    top_indices = set()
    for char_id in ALL_CHARS:
        for tid, arr in scores[char_id].items():
            valid_mask = np.array([x is not None and not np.isnan(x) for x in arr])
            if not np.any(valid_mask):
                continue
            numeric_vals = np.where(valid_mask, arr.astype(float), -1.0)
            k = min(top_n_per_target, len(numeric_vals))
            idx_part = np.argpartition(numeric_vals, -k)[-k:]
            top_indices.update(idx_part.tolist())
            
    # Always include known analog cells
    known_mask = earth_df["known_analog_within_km"].values >= 0
    known_indices = np.where(known_mask)[0]
    top_indices.update(known_indices.tolist())
    
    selected_indices = sorted(top_indices)
    print(f"  Selected {len(selected_indices):,} unique candidate cells.")
    
    features = []
    for idx in selected_indices:
        row = earth_df.iloc[idx]
        lat = float(row["lat_center"])
        lon = float(row["lon_center"])
        cell_id = str(row["cell_id"])
        
        is_known, known_name = find_known_analog(lat, lon)
        region_hint = get_region_hint(lat, lon)
        
        # Build score dict for this cell
        cell_scores = {c: {} for c in ALL_CHARS}
        for c in ALL_CHARS:
            for tid in scores[c]:
                val = scores[c][tid][idx]
                cell_scores[c][tid] = round(float(val), 3) if val is not None else None
                
        # Main measured values with units and source
        values = {
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
        features.append(feature)
        
    return {"type": "FeatureCollection", "features": features}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("[export_static] Loading Earth cells parquet...")
    earth_df = load_earth_cells()
    print(f"  Loaded {len(earth_df):,} land cells.")
    
    print("[export_static] Loading reference targets...")
    targets_data = load_targets()
    
    # 1. Export meta.json
    export_meta(targets_data)
    
    # 2. Export four presets
    # Top-N per target: 300 for moon_landing (9 targets -> ~1800 cells), 600 for others (2-3 targets -> ~1500 cells)
    # This keeps file sizes strictly between 1.5 MB and 3.5 MB, well below the 5 MB limit.
    preset_configs = [
        ("moon_landing", 60),
        ("moon_base", 120),
        ("mars_landing", 120),
        ("mars_base", 150),
    ]
    
    for preset_key, top_n in preset_configs:
        collection = process_preset(earth_df, targets_data, preset_key, top_n_per_target=top_n)
        out_file = OUT_DIR / f"{preset_key}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(collection, f, separators=(",", ":"), ensure_ascii=False)
            
        size_mb = out_file.stat().st_size / (1024 * 1024)
        n_feats = len(collection["features"])
        print(f"[export_static] Wrote {n_feats:,} features -> {out_file.name} ({size_mb:.2f} MB)")
        if size_mb > WARN_SIZE_MB:
            print(f"  WARNING: File size {size_mb:.2f} MB exceeds {WARN_SIZE_MB} MB limit!", file=sys.stderr)
            
    print("[export_static] All exports completed successfully.")


if __name__ == "__main__":
    main()
