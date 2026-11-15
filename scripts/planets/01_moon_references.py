"""
01_moon_references.py — Moon reference target literature values
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/moon_targets_raw.json

All values are from published literature. EVERY entry is marked UNVERIFIED and must be
validated by the team against primary PDS/LROC data before Phase 6.

Sources used:
  Paige et al. 2010  — Diviner lunar radiometer south-pole thermal maps.
                       doi:10.1126/science.1187726
  Hayne et al. 2015  — Diviner thermal observations of permanent shadow.
                       doi:10.1016/j.icarus.2015.02.011
  Mazarico et al. 2011 — LOLA illumination fraction south-polar regions.
                       doi:10.1029/2010JE003739
  Noda et al. 2008   — Illumination conditions near lunar poles from Kaguya LIDAR.
                       doi:10.1029/2008GL034887
  Wagner & Robinson 2015 — LROC NAC-derived lunar pit morphology (Marius Hills Pit).
                       doi:10.1016/j.icarus.2015.09.001
  Speyerer & Robinson 2013 — Persistently illuminated regions at the lunar poles.
                       doi:10.1016/j.icarus.2012.10.010
  USGS Unified Geologic Map of the Moon v2 — Fortezzo et al. 2020.
                       https://astrogeology.usgs.gov/search/map/Moon/Geology/
                       Unified_Geologic_Map_of_the_Moon_GIS_v2
  NASA release 24-136, Oct 28 2024 — Artemis south-polar candidate regions.
  LROC WAC south-polar mosaic — Scholten et al. 2012 (mean reflectance ~0.10–0.13).
                       doi:10.1029/2011JE003926
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "moon_targets_raw.json"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# cannot_reproduce list for the Moon (METHODOLOGY §7)
# ---------------------------------------------------------------------------
MOON_CANNOT_REPRODUCE = [
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
    "Regolith: electrostatic, sharp-edged (no weathering) — no terrestrial surface-level "
    "equivalent",
]

# ---------------------------------------------------------------------------
# Helper: build a null placeholder when literature value is not available
# ---------------------------------------------------------------------------

def null_val(notes: str) -> dict:
    return {"value": None, "source": "not found", "confidence": "low", "notes": notes}


# ---------------------------------------------------------------------------
# Individual target definitions
# All numeric values are midpoints or typical values from the literature ranges
# cited in the module docstring.  Confidence is always "low" because:
#   (a) values come from published statistics, not from direct PDS download
#   (b) exact coordinates are UNVERIFIED (see config/missions/moon-landing.json)
# ---------------------------------------------------------------------------

def south_pole_landing_target(
    target_id: str,
    name: str,
    lat: float,
    lon: float,
    coordinate_source: str,
    illumination_fraction: float | None = None,
    illumination_notes: str = "",
    slope_notes: str = "",
    roughness_notes: str = "",
) -> dict:
    """
    Build a reference-value object for a south-polar landing site.
    All characteristic values are drawn from south-polar statistics shared across
    the nine Artemis candidates (Paige et al. 2010, Mazarico et al. 2011,
    Scholten et al. 2012).  Site-specific overrides can be passed as arguments.
    """
    illum_frac = illumination_fraction if illumination_fraction is not None else 0.80

    return {
        "id": target_id,
        "name": name,
        "body": "moon",
        "mission_type": "landing",
        "lat": lat,
        "lon": lon,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": coordinate_source,
        "cannot_reproduce": MOON_CANNOT_REPRODUCE,
        "reference_values": {
            # --- topography ---
            # Literature: south-polar highland terrain; slopes 2–8° typical at 1 km
            # scale (Noda et al. 2008; Mazarico et al. 2011 supplementary).
            "topography": {
                "slope": {
                    "value": 4.0,
                    "units": "degrees",
                    "source": "LOLA LDEM south-polar statistics — typical range 2–8° "
                              "at 1 km scale; midpoint used. Noda et al. 2008; "
                              "Mazarico et al. 2011. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of published south-polar 1 km range (2–8°). "
                             + slope_notes,
                },
                "roughness": {
                    "value": 20.0,
                    "units": "meters",
                    "source": "LOLA LDEM south-polar roughness statistics — typical range "
                              "10–30 m (std-dev of elevation in 3×3 km window). "
                              "Paige et al. 2010 supplementary. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of published south-polar 1 km roughness "
                             "range (10–30 m). " + roughness_notes,
                },
                "local_relief": {
                    "value": 500.0,
                    "units": "meters",
                    "source": "LOLA LDEM south-polar relief — south-polar highland terrain "
                              "shows 200–1500 m within 12 km radius; midpoint used. "
                              "USGS Unified Geologic Map; Mazarico et al. 2011. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Wide range; midpoint 500 m used as placeholder. "
                             "High local relief near crater rims and massifs.",
                },
            },
            # --- thermal ---
            # Paige et al. 2010 (Science): south-polar PSR temperatures 40–100 K;
            # illuminated ridge temperatures 100–200 K annual mean; diurnal range near
            # ridges is small due to near-continuous illumination.
            "thermal": {
                "temp_annual_mean": {
                    "value": 150.0,
                    "units": "K",
                    "source": "Diviner DLRE south-polar thermal maps — illuminated ridge "
                              "annual mean ~100–220 K; midpoint ~150 K. "
                              "Paige et al. 2010 (doi:10.1126/science.1187726). UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Wide range across south-polar sites.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — no Earth parquet available; "
                             "to be computed by 00_assemble_targets.py once "
                             "earth_cells_025deg.parquet contains thermal columns.",
                },
                "temp_annual_range": {
                    "value": 80.0,
                    "units": "K",
                    "source": "Diviner DLRE — illuminated south-polar ridges: annual range "
                              "~50–120 K; PSRs near 0 K range (nearly isothermal). "
                              "Paige et al. 2010; Hayne et al. 2015 "
                              "(doi:10.1016/j.icarus.2015.02.011). UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of illuminated-ridge range.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 30.0,
                    "units": "K",
                    "source": "Diviner DLRE — south-polar illuminated ridges: near-continuous "
                              "illumination suppresses diurnal range to ~20–50 K. "
                              "Paige et al. 2010. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of published range.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            # --- illumination ---
            # Mazarico et al. 2011 (JGR): illumination fractions for persistent-light
            # ridges range 0.75–0.86; Speyerer & Robinson 2013 extend analysis.
            "illumination": {
                "illumination_fraction": {
                    "value": illum_frac,
                    "units": "0–1",
                    "source": "LOLA polar illumination maps — Mazarico et al. 2011 "
                              "(doi:10.1029/2010JE003739); Speyerer & Robinson 2013 "
                              "(doi:10.1016/j.icarus.2012.10.010). UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. " + illumination_notes,
                },
                "solar_elevation_range": {
                    "value": 3.0,
                    "units": "degrees",
                    "source": "Lunar orbital geometry: obliquity 1.54°; maximum solar "
                              "elevation at lunar south pole ~1.5–6°. Literature: Noda et al. "
                              "2008 (doi:10.1029/2008GL034887). UNVERIFIED.",
                    "resolution_m": None,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of ~1.5–6° range; obliquity ~1.54° sets hard "
                             "geometric limit.",
                },
                "percentile_estimate": None,
                "basis": "APPROXIMATE — to be computed by assemble script.",
            },
            # --- surface_optics ---
            # Scholten et al. 2012 (JGR): south-polar mean reflectance from LROC WAC
            # 604 nm ~0.10–0.13; highland regolith darker than equatorial maria average.
            "surface_optics": {
                "reflectance": {
                    "value": 0.115,
                    "units": "0–1 (604 nm normalized reflectance)",
                    "source": "LROC WAC south-polar mosaic — Scholten et al. 2012 "
                              "(doi:10.1029/2011JE003926) south-polar mean ~0.10–0.13; "
                              "midpoint used. UNVERIFIED. Note: single-band 604 nm — "
                              "cross-calibration to broadband albedo UNVERIFIED.",
                    "resolution_m": 100,
                    "confidence": "low",
                    "notes": "UNVERIFIED. WAC single-band (604 nm); broadband cross-calibration "
                             "unconfirmed (DATASETS.md §2 note). Apply percentile/regime fallback "
                             "if no calibration factor found.",
                }
            },
            # --- aridity ---
            # REQUIREMENT: Moon is maximally arid by definition (METHODOLOGY §2.4)
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; "
                         "no liquid water on lunar surface",
            },
            # --- geology ---
            # USGS Unified Geologic Map of the Moon v2 (Fortezzo et al. 2020):
            # south-polar region is Nectarian-age highland breccia/ejecta (unit Nplh / NpHb).
            "geology": {
                "geologic_unit": {
                    "class_description": "Nectarian-age pre-Nectarian highland breccia and "
                                        "ejecta (units Nplh / NpHb) — ancient heavily cratered "
                                        "highland terrain; anorthositic/noritic regolith.",
                    "source": "USGS Unified Geologic Map of the Moon v2 — Fortezzo et al. 2020. "
                              "https://astrogeology.usgs.gov/search/map/Moon/Geology/"
                              "Unified_Geologic_Map_of_the_Moon_GIS_v2. UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED. Unit assignment based on south-polar region general "
                             "geology; exact unit at each target coordinate must be read from "
                             "GIS file.",
                }
            },
            # --- ice_polar ---
            # LEND hydrogen signal near lunar south pole (Mitrofanov et al. 2010);
            # PSR coverage near ridges varies; landing sites prefer illuminated ridges
            # adjacent to PSRs rather than inside them.
            "ice_polar": {
                "illumination_fraction": {
                    "value": illum_frac,
                    "units": "0–1",
                    "source": "LOLA illumination fraction — same as illumination characteristic. "
                              "Mazarico et al. 2011. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Landing sites on illuminated ridges; PSR access within "
                             "walking distance but PSR not at landing coordinates.",
                },
                "psr_coverage": {
                    "value": 0.1,
                    "units": "0–1 fraction within 5 km radius",
                    "source": "LROC PSR Atlas — south-polar region PSR coverage near ridges "
                              "varies 5–30% within 5 km; low estimate used for illuminated "
                              "ridge landing sites. Hayne et al. 2015. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Coarse estimate; exact value requires GIS query of "
                             "PSR Atlas at target coordinates.",
                },
                "ice_detection": {
                    "value": "possible",
                    "units": "categorical (confirmed/possible/not_detected)",
                    "source": "LEND neutron suppression south-polar map — hydrogen signal "
                              "detected in broad south-polar region >80°S at 10 km scale. "
                              "Mitrofanov et al. 2010 (doi:10.1126/science.1185696). "
                              "UNVERIFIED at target scale.",
                    "resolution_m": 10000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. 10 km LEND resolution cannot confirm ice at "
                             "individual landing site coordinates.",
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# Target definitions — 9 moon-landing + 2 moon-base
# ---------------------------------------------------------------------------

def build_moon_targets() -> dict:
    targets = {}

    # ---- Moon-landing targets (9 Artemis south-polar candidates) ----
    # Individual illumination fractions from Mazarico et al. 2011 / Speyerer & Robinson 2013
    # where site-specific values are cited; otherwise group default 0.80.

    targets["peak_near_cabeus_b"] = south_pole_landing_target(
        target_id="peak_near_cabeus_b",
        name="Peak near Cabeus B",
        lat=-84.9, lon=-47.0,
        coordinate_source="Approximate — informal name from NASA release 24-136 map; "
                          "no USGS Gazetteer entry for this peak",
        illumination_fraction=0.75,
        illumination_notes="Rough estimate from release map context; Cabeus region has "
                           "moderate illumination. Mazarico et al. 2011. UNVERIFIED.",
    )

    targets["haworth"] = south_pole_landing_target(
        target_id="haworth",
        name="Haworth",
        lat=-87.5, lon=-4.5,
        coordinate_source="USGS Gazetteer — Haworth crater center approximate; "
                          "crater rim coordinates differ from center",
        illumination_fraction=0.76,
        illumination_notes="Haworth crater rim area; moderate persistent illumination. "
                           "Mazarico et al. 2011. UNVERIFIED.",
    )

    targets["malapert_massif"] = south_pole_landing_target(
        target_id="malapert_massif",
        name="Malapert Massif",
        lat=-85.9, lon=-2.0,
        coordinate_source="USGS Gazetteer — Malapert crater center ~-84.9°, -2.9°; "
                          "Massif refers to ridge N of the crater, approximate offset applied",
        illumination_fraction=0.86,
        illumination_notes="One of the most persistently illuminated south-polar ridges. "
                           "Mazarico et al. 2011 reports ~0.86 for best ridges near -86°S. "
                           "Speyerer & Robinson 2013. UNVERIFIED.",
        slope_notes="Massif terrain may have steeper local slopes; use with caution.",
    )

    targets["mons_mouton_plateau"] = south_pole_landing_target(
        target_id="mons_mouton_plateau",
        name="Mons Mouton Plateau",
        lat=-84.1, lon=-15.6,
        coordinate_source="USGS Gazetteer — Mons Mouton center approximately -84.1°, -15.6°",
        illumination_fraction=0.82,
        illumination_notes="Mons Mouton plateau — elevated flat terrain with high illumination. "
                           "Mazarico et al. 2011. UNVERIFIED.",
        slope_notes="Plateau surface likely lower slope than massif ridges.",
        roughness_notes="Plateau expected to be relatively smooth; range 10–20 m likely.",
    )

    targets["mons_mouton"] = south_pole_landing_target(
        target_id="mons_mouton",
        name="Mons Mouton",
        lat=-84.1, lon=-15.6,
        coordinate_source="USGS Gazetteer — Mons Mouton center approximately -84.1°, -15.6°",
        illumination_fraction=0.83,
        illumination_notes="Mons Mouton summit area; slightly higher illumination than plateau. "
                           "Mazarico et al. 2011. UNVERIFIED.",
    )

    targets["nobile_rim_1"] = south_pole_landing_target(
        target_id="nobile_rim_1",
        name="Nobile Rim 1",
        lat=-85.2, lon=53.5,
        coordinate_source="USGS Gazetteer — Nobile crater center ~-85.2°, 53.5°; "
                          "rim candidate offset from center",
        illumination_fraction=0.78,
        illumination_notes="Nobile crater rim — good but not exceptional illumination. "
                           "Mazarico et al. 2011. UNVERIFIED.",
    )

    targets["nobile_rim_2"] = south_pole_landing_target(
        target_id="nobile_rim_2",
        name="Nobile Rim 2",
        lat=-84.8, lon=57.0,
        coordinate_source="Approximate — second rim position from NASA release 24-136 map; "
                          "not separately named in USGS Gazetteer",
        illumination_fraction=0.77,
        illumination_notes="Second Nobile rim candidate; similar illumination to Rim 1. "
                           "Mazarico et al. 2011. UNVERIFIED.",
    )

    targets["de_gerlache_rim_2"] = south_pole_landing_target(
        target_id="de_gerlache_rim_2",
        name="de Gerlache Rim 2",
        lat=-88.5, lon=-88.0,
        coordinate_source="USGS Gazetteer — de Gerlache crater center ~-88.5°, -88.0°",
        illumination_fraction=0.84,
        illumination_notes="de Gerlache rim — high persistent illumination; "
                           "near Shackleton-de Gerlache ridge system. "
                           "Mazarico et al. 2011; Speyerer & Robinson 2013. UNVERIFIED.",
    )

    targets["slater_plain"] = south_pole_landing_target(
        target_id="slater_plain",
        name="Slater Plain",
        lat=-88.3, lon=140.0,
        coordinate_source="Approximate — informal name from NASA release 24-136 map; "
                          "no USGS Gazetteer entry",
        illumination_fraction=0.75,
        illumination_notes="Slater Plain — relatively flat south-polar terrain; "
                           "lower illumination fraction than ridges. "
                           "Mazarico et al. 2011. UNVERIFIED.",
        slope_notes="Plain terrain expected lower slopes (1–4°); midpoint 4° may be high.",
        roughness_notes="Plain terrain expected lower roughness (10–20 m).",
    )

    # ---- Moon-base targets ----

    targets["shackleton_de_gerlache_ridge"] = {
        "id": "shackleton_de_gerlache_ridge",
        "name": "Shackleton–de Gerlache Ridge",
        "body": "moon",
        "mission_type": "base",
        "lat": -89.5,
        "lon": -100.0,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "Approximate — USGS Gazetteer Shackleton crater center ~-89.9°, 0°; "
                             "ridge between Shackleton and de Gerlache is off-center; "
                             "coordinate is a rough mid-ridge estimate",
        "cannot_reproduce": MOON_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 5.0,
                    "units": "degrees",
                    "source": "LOLA LDEM — Shackleton-de Gerlache connecting ridge; "
                              "ridge flanks typical 3–8°. Mazarico et al. 2011. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Ridge terrain; slopes higher than flat plateau.",
                },
                "roughness": {
                    "value": 25.0,
                    "units": "meters",
                    "source": "LOLA LDEM south-polar roughness statistics — ridges tend "
                              "higher roughness than plateaus; range 15–35 m. "
                              "Paige et al. 2010. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "local_relief": {
                    "value": 1200.0,
                    "units": "meters",
                    "source": "LOLA LDEM — ridge between two large craters; local relief "
                              "within 12 km likely 800–2000 m. Mazarico et al. 2011. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Very wide range; crater-to-ridge relief dominant.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 170.0,
                    "units": "K",
                    "source": "Diviner DLRE — illuminated ridge near Shackleton annual mean "
                              "~130–220 K; midpoint ~170 K. Paige et al. 2010. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 60.0,
                    "units": "K",
                    "source": "Diviner — near-continuous illumination suppresses annual range. "
                              "Range ~40–100 K for illuminated ridges. Paige et al. 2010. "
                              "UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 20.0,
                    "units": "K",
                    "source": "Diviner — near-continuous illumination reduces diurnal range "
                              "to ~10–30 K on best-illuminated ridges. Paige et al. 2010. "
                              "UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "illumination": {
                "illumination_fraction": {
                    "value": 0.85,
                    "units": "0–1",
                    "source": "LOLA illumination maps — Shackleton-de Gerlache ridge is "
                              "among the best illuminated south-polar regions (~0.80–0.90). "
                              "Mazarico et al. 2011; Speyerer & Robinson 2013. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "solar_elevation_range": {
                    "value": 3.0,
                    "units": "degrees",
                    "source": "Lunar orbital geometry at ~-89.5°: obliquity 1.54° limits "
                              "max solar elevation. Noda et al. 2008. UNVERIFIED.",
                    "resolution_m": None,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "percentile_estimate": None,
                "basis": "APPROXIMATE — to be computed by assemble script.",
            },
            "surface_optics": {
                "reflectance": {
                    "value": 0.115,
                    "units": "0–1 (604 nm)",
                    "source": "LROC WAC south-polar mosaic — Scholten et al. 2012. "
                              "South-polar highland mean ~0.10–0.13. UNVERIFIED.",
                    "resolution_m": 100,
                    "confidence": "low",
                    "notes": "UNVERIFIED. WAC single-band 604 nm; broadband cross-calibration "
                             "unconfirmed.",
                }
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; no liquid water",
            },
            "ice_polar": {
                "illumination_fraction": {
                    "value": 0.85,
                    "units": "0–1",
                    "source": "LOLA illumination fraction. Mazarico et al. 2011. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "psr_coverage": {
                    "value": 0.30,
                    "units": "0–1 fraction within 5 km radius",
                    "source": "LROC PSR Atlas — Shackleton interior is a PSR; ridge overlooks "
                              "PSR access. Estimated ~20–50% PSR within 5 km radius. "
                              "Hayne et al. 2015. UNVERIFIED.",
                    "resolution_m": 240,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Access to PSR ice is key base rationale.",
                },
                "ice_detection": {
                    "value": "possible",
                    "units": "categorical",
                    "source": "LEND hydrogen signal; Shackleton PSR interior may contain "
                              "ice. Mitrofanov et al. 2010. UNVERIFIED.",
                    "resolution_m": 10000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. 10 km LEND resolution.",
                },
            },
            "geology": {
                "geologic_unit": {
                    "class_description": "Nectarian-age highland breccia/ejecta near Shackleton "
                                        "and de Gerlache craters; anorthositic regolith typical "
                                        "of south-polar highlands.",
                    "source": "USGS Unified Geologic Map of the Moon v2 — Fortezzo et al. 2020. "
                              "UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
            "volcanic_caves": null_val(
                "No lunar pit reported near Shackleton-de Gerlache ridge in LROC Lunar Pit "
                "Atlas. Volcanic_caves characteristic not applicable for this target."
            ),
        },
    }

    targets["marius_hills_pit"] = {
        "id": "marius_hills_pit",
        "name": "Marius Hills Pit",
        "body": "moon",
        "mission_type": "base",
        "lat": 14.1,
        "lon": -56.3,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "Wagner & Robinson 2015 (doi:10.1016/j.icarus.2015.09.001); "
                             "LROC NAC image M137929856LE",
        "cannot_reproduce": MOON_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 2.0,
                    "units": "degrees",
                    "source": "LOLA LDEM Marius Hills region — mare basalt plains; "
                              "regional slope typically 1–3°. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Surrounding terrain is flat mare basalt; "
                             "pit rim may have higher local slope.",
                },
                "roughness": {
                    "value": 12.0,
                    "units": "meters",
                    "source": "LOLA LDEM Marius Hills mare basalt — typical roughness "
                              "10–15 m in mare terrain. Paige et al. 2010 supplementary. "
                              "UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "local_relief": {
                    "value": 200.0,
                    "units": "meters",
                    "source": "LOLA LDEM Marius Hills — mare basalt plains with low regional "
                              "relief; volcanic domes in region. 100–400 m within 12 km. "
                              "UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 240.0,
                    "units": "K",
                    "source": "Diviner DLRE global equatorial/mid-latitude — equatorial "
                              "annual mean ~220–260 K. Paige et al. 2010. UNVERIFIED.",
                    "resolution_m": 15000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 200.0,
                    "units": "K",
                    "source": "Diviner DLRE — equatorial diurnal/annual range ~150–280 K "
                              "for mare terrain at 14°N. Paige et al. 2010. UNVERIFIED.",
                    "resolution_m": 15000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 250.0,
                    "units": "K",
                    "source": "Diviner — equatorial mare: very large diurnal range due to "
                              "14-day day/night cycle; ~100–300 K typical. Paige et al. 2010. "
                              "UNVERIFIED.",
                    "resolution_m": 15000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Extreme diurnal range is a key cannot_reproduce item.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "illumination": {
                "illumination_fraction": {
                    "value": 0.50,
                    "units": "0–1",
                    "source": "Equatorial location (~14°N): half-year sun / half-year dark "
                              "per 29.5-day lunar cycle. Computed from orbital geometry. "
                              "UNVERIFIED.",
                    "resolution_m": None,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Equatorial illumination fraction ~0.50 "
                             "(14-day day, 14-day night).",
                },
                "solar_elevation_range": {
                    "value": 76.0,
                    "units": "degrees",
                    "source": "Lunar geometry at 14°N: max elevation ~90°−14°+1.54° ≈ 77.5°; "
                              "moon's obliquity is 1.54°. Noda et al. 2008. UNVERIFIED.",
                    "resolution_m": None,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "percentile_estimate": None,
                "basis": "APPROXIMATE — to be computed by assemble script.",
            },
            "surface_optics": {
                "reflectance": {
                    "value": 0.095,
                    "units": "0–1 (604 nm)",
                    "source": "LROC WAC global mosaic — Marius Hills mare basalt; "
                              "mare reflectance typically 0.08–0.12 at 604 nm. "
                              "Scholten et al. 2012. UNVERIFIED.",
                    "resolution_m": 100,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; no liquid water",
            },
            "ice_polar": null_val(
                "Marius Hills Pit is at 14°N — no ground ice expected at equatorial "
                "latitude. LEND and SWIM do not indicate ice at this location. "
                "ice_polar characteristic not applicable."
            ),
            "geology": {
                "geologic_unit": {
                    "class_description": "Imbrian-age mare basalt (unit Im) — volcanic flood "
                                        "basalt plains in Marius Hills region; associated with "
                                        "volcanic domes and pit skylights.",
                    "source": "USGS Unified Geologic Map of the Moon v2 — Fortezzo et al. 2020. "
                              "UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
            "volcanic_caves": {
                "pit_location": {
                    "value": "confirmed pit",
                    "units": "categorical (confirmed/candidate/not_detected)",
                    "diameter_m": 65.0,
                    "depth_m": 35.0,
                    "source": "LROC NAC imagery — Wagner & Robinson 2015 "
                              "(doi:10.1016/j.icarus.2015.09.001); "
                              "LROC Lunar Pit Atlas. UNVERIFIED at PDS archive.",
                    "resolution_m": 2,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Pit dimensions from Wagner & Robinson 2015 Table 1 "
                             "(approximate: diameter ~65 m, depth ~35 m — values from "
                             "published figure; exact values in PDS NAC product). "
                             "Interpreted as probable lava-tube skylight based on floor "
                             "morphology and location in Marius Hills volcanic complex.",
                }
            },
        },
    }

    return targets


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Building Moon reference target values from literature …")
    targets = build_moon_targets()
    print(f"  Built {len(targets)} Moon targets.")

    output = {
        "schema_version": "1.0",
        "body": "moon",
        "generated_at": PROC_DATE,
        "note": "UNVERIFIED — all values from published literature. Must be validated "
                "against primary PDS/LROC data before Phase 6.",
        "targets": targets,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"Wrote -> {OUT_FILE}")
    for tid, t in targets.items():
        chars = list(t["reference_values"].keys())
        print(f"  {tid}: {len(chars)} characteristics: {chars}")


if __name__ == "__main__":
    main()
