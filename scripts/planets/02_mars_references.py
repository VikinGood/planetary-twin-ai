"""
02_mars_references.py — Mars reference target literature values
Planetary Twin AI, Space Logistics team, NASA Space Apps Challenge 2026.

AI use disclosure: this script was generated with AI assistance and reviewed by the team.

Produces: data/processed/mars_targets_raw.json

All values are from published literature. EVERY entry is marked UNVERIFIED and must be
validated by the team against primary PDS data before Phase 6.

Sources used:
  Golombek et al. 2003 — Mars Exploration Rover landing site selection (topography).
                         doi:10.1029/2003JE002074
  Golombek et al. 2012 — MSL Curiosity landing site topography statistics.
                         doi:10.1029/2012JE004116
  Golombek et al. 2020 — Mars 2020 Perseverance landing site (Jezero).
                         doi:10.1029/2020EA001152
  Christensen et al. 2001 — TES bolometric albedo (surface_optics).
                         doi:10.1029/2000JE001374
  Smith et al. 2001 — MOLA global topography (MEGDR).
                         doi:10.1029/2000JE001364
  Morgan et al. 2021 — Shallow water ice on Mars (SWIM dataset, Arcadia Planitia).
                         doi:10.1029/2020GL088143  (see also swim.psi.edu)
  Tanaka et al. 2014 — USGS Global Geologic Map of Mars.
                         https://astropedia.astrogeology.usgs.gov/download/Mars/Geology/
                         Mars_Global_Geologic_Map_Tanaka2014
  Wyrick et al. 2004 / Cushing et al. 2007 — Martian cave candidate system (Arsia Mons).
                         Wyrick: doi:10.1029/2004JE002277
                         Cushing: doi:10.1029/2007GL030894
  Forget et al. 2006 — MCD thermal statistics.
                         doi:10.1016/j.pss.2005.11.013
  Haberle et al. 2001 — Mars surface temperature compilation.
                         doi:10.1029/2001JE001505
  Ruff & Christensen 2002 — TES dust cover index.
                         doi:10.1029/2001JE001583
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "mars_targets_raw.json"
PROC_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# cannot_reproduce list for Mars (METHODOLOGY §7)
# ---------------------------------------------------------------------------
MARS_CANNOT_REPRODUCE = [
    "Gravity: 0.38 g (3.72 m/s²) — no terrestrial equivalent",
    "Atmosphere: 0.6 kPa, 95% CO₂; no breathable air; partial pressure too low for "
    "liquid water at the surface",
    "UV and ionizing radiation: no ozone layer; UV and ionizing radiation at surface "
    "exceeds any habitable Earth surface",
    "Global dust storms: planetary-scale events lasting months with severe irradiance loss "
    "— no terrestrial equivalent at planetary scale",
    "Absolute temperatures: −140 °C (polar night) to +20 °C (equatorial afternoon); "
    "annual and diurnal range exceeds any Earth surface location",
    "Perchlorates in regolith: no terrestrial surface-level analog",
    "Dust: fine-grained (<10 µm) globally mobile dust; settling behavior fundamentally "
    "different from Earth owing to low gravity and thin atmosphere",
]

# ---------------------------------------------------------------------------
# Helper: null placeholder
# ---------------------------------------------------------------------------

def null_val(notes: str) -> dict:
    return {"value": None, "source": "not found", "confidence": "low", "notes": notes}


# ---------------------------------------------------------------------------
# Target definitions
# ---------------------------------------------------------------------------

def build_mars_targets() -> dict:
    targets = {}

    # =========================================================================
    # MARS-LANDING: Jezero Crater
    # =========================================================================
    # Golombek et al. 2020: Jezero slope ~0.5–2° at 1 km scale; local relief moderate.
    # TES albedo (Christensen 2001): Jezero ~0.14–0.17.
    # MCD/TES annual mean ~−10 to −5°C; range ~90–110 K; diurnal ~40–60 K.

    targets["jezero_crater"] = {
        "id": "jezero_crater",
        "name": "Jezero Crater",
        "body": "mars",
        "mission_type": "landing",
        "lat": 18.4,
        "lon": 77.7,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "Mars 2020 landing ellipse center — Golombek et al. 2020; "
                             "widely cited in literature. Approximate.",
        "cannot_reproduce": MARS_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 1.0,
                    "units": "degrees",
                    "source": "MOLA MEGDR Jezero crater floor — Golombek et al. 2020 "
                              "(doi:10.1029/2020EA001152): slope 0.5–2° at 1 km scale; "
                              "midpoint used. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of published range (0.5–2°).",
                },
                "roughness": {
                    "value": 8.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Jezero floor roughness; Golombek et al. 2020 "
                              "reports rock abundance and roughness within acceptable range; "
                              "rough estimate 5–15 m. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. No direct 1 km roughness value found in cited "
                             "literature; range 5–15 m from MOLA global statistics for "
                             "low-slope terrains.",
                },
                "local_relief": {
                    "value": 300.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Jezero crater is ~45 km diameter with ~600 m "
                              "rim; floor local relief within 12 km ~100–600 m; midpoint "
                              "used. Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Rim-to-floor relief significant at 12 km scale.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 263.0,
                    "units": "K",
                    "source": "Mars Climate Database v6.1 / TES — Jezero at 18.4°N, 77.7°E: "
                              "annual mean surface temperature ~255–270 K. Forget et al. 2006; "
                              "Haberle et al. 2001 (doi:10.1029/2001JE001505). UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. MCD 5°×5° grid value; local variation not captured.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 100.0,
                    "units": "K",
                    "source": "TES / MCD — Jezero annual surface temperature range "
                              "~80–120 K (summer–winter variation at 18°N). "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 50.0,
                    "units": "K",
                    "source": "TES Thermal Inertia / MCD — equatorial Mars diurnal range "
                              "~40–70 K depending on season and dust loading. "
                              "Haberle et al. 2001. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "surface_optics": {
                "albedo": {
                    "value": 0.155,
                    "units": "0–1 (bolometric albedo)",
                    "source": "TES bolometric albedo mosaic — Christensen et al. 2001 "
                              "(doi:10.1029/2000JE001374): Jezero region ~0.14–0.17; "
                              "midpoint used. UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. TES pixel scale ~3–8 km (PDS label unconfirmed — "
                             "DATASETS.md §3).",
                },
                "dust_cover_index": {
                    "value": 0.94,
                    "units": "0–1 (DCI — higher = less dust)",
                    "source": "TES DCI — Ruff & Christensen 2002 "
                              "(doi:10.1029/2001JE001583): Jezero region relatively "
                              "low dust cover (DCI ~0.93–0.96). UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; "
                         "no liquid water on Mars surface",
            },
            "geology": {
                "geologic_unit": {
                    "class_description": "Noachian/Hesperian transitional — lacustrine delta "
                                        "and fluvial deposits within Jezero crater (unit eHt / "
                                        "NHli in Tanaka 2014). Ancient lake sediments and basaltic "
                                        "basement.",
                    "source": "Tanaka et al. 2014 USGS Global Geologic Map of Mars. "
                              "https://astropedia.astrogeology.usgs.gov/download/Mars/Geology/"
                              "Mars_Global_Geologic_Map_Tanaka2014. UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED. Unit assignment from published figure; GIS query "
                             "needed for exact unit at target coordinates.",
                }
            },
        },
    }

    # =========================================================================
    # MARS-LANDING: Gale Crater
    # =========================================================================
    # Golombek et al. 2012: Gale slope ~1–3° at 1 km; central mound (Aeolis Mons) relief.
    # TES albedo: ~0.17–0.20 (slightly dustier than Jezero).
    # MCD: equatorial night temperatures lower than Jezero (southward tilt of crater).

    targets["gale_crater"] = {
        "id": "gale_crater",
        "name": "Gale Crater",
        "body": "mars",
        "mission_type": "landing",
        "lat": -5.4,
        "lon": 137.8,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "MSL Curiosity landing site — Golombek et al. 2012 / "
                             "published landing ellipse center. Approximate.",
        "cannot_reproduce": MARS_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 1.5,
                    "units": "degrees",
                    "source": "MOLA MEGDR Gale crater floor — Golombek et al. 2012 "
                              "(doi:10.1029/2012JE004116): 1–3° at 1 km; midpoint 1.5°. "
                              "UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "roughness": {
                    "value": 10.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Gale floor roughness; similar to Jezero. "
                              "Rough estimate 6–15 m. Golombek et al. 2012. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "local_relief": {
                    "value": 2000.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Gale crater has central mound (Aeolis Mons) "
                              "~5 km tall; local relief within 12 km near landing site "
                              "~1000–4000 m. Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Very wide range; depends on proximity to Aeolis Mons.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 260.0,
                    "units": "K",
                    "source": "MCD / TES — Gale at -5.4°S, 137.8°E: annual mean ~250–270 K. "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 100.0,
                    "units": "K",
                    "source": "TES / MCD — near-equatorial Mars annual range ~80–120 K. "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 55.0,
                    "units": "K",
                    "source": "TES / MCD — near-equatorial diurnal range ~40–70 K. "
                              "Haberle et al. 2001. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "surface_optics": {
                "albedo": {
                    "value": 0.185,
                    "units": "0–1 (bolometric albedo)",
                    "source": "TES bolometric albedo — Christensen et al. 2001: Gale / "
                              "Aeolis region ~0.17–0.20. Midpoint used. UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "dust_cover_index": {
                    "value": 0.93,
                    "units": "0–1 (DCI)",
                    "source": "TES DCI — Ruff & Christensen 2002: Aeolis region moderate "
                              "dust coverage ~0.91–0.95. UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; no liquid water",
            },
            "geology": {
                "geologic_unit": {
                    "class_description": "Hesperian-age layered sedimentary and aeolian "
                                        "deposits within Gale crater and Aeolis Mons (unit Hve / "
                                        "AHi in Tanaka 2014). Sulfate-bearing strata.",
                    "source": "Tanaka et al. 2014 USGS Global Geologic Map of Mars. UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
        },
    }

    # =========================================================================
    # MARS-LANDING: Meridiani Planum
    # =========================================================================
    # Golombek et al. 2003: very flat terrain; slope <1° over km scale.
    # TES albedo: ~0.12–0.15 (dark hematite-bearing plains).
    # MCD: near-equatorial thermal regime.

    targets["meridiani_planum"] = {
        "id": "meridiani_planum",
        "name": "Meridiani Planum",
        "body": "mars",
        "mission_type": "landing",
        "lat": -1.9,
        "lon": -5.5,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "MER Opportunity landing site — Golombek et al. 2003 / "
                             "widely cited. Approximate.",
        "cannot_reproduce": MARS_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 0.5,
                    "units": "degrees",
                    "source": "MOLA MEGDR — Golombek et al. 2003 "
                              "(doi:10.1029/2003JE002074): Meridiani slope 0.2–1° at 1 km; "
                              "midpoint 0.5°. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Very flat terrain.",
                },
                "roughness": {
                    "value": 6.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Meridiani Planum among flattest landing sites "
                              "on Mars; roughness ~3–10 m. Golombek et al. 2003. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "local_relief": {
                    "value": 100.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Meridiani Planum: flat plains with small craters; "
                              "local relief within 12 km ~50–200 m. Smith et al. 2001. "
                              "UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Flattest reference target; very low relief.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 263.0,
                    "units": "K",
                    "source": "TES / MCD — Meridiani at -1.9°S: annual mean ~255–270 K. "
                              "Forget et al. 2006; Haberle et al. 2001. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 95.0,
                    "units": "K",
                    "source": "TES / MCD — near-equatorial annual range ~80–110 K. "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 50.0,
                    "units": "K",
                    "source": "TES / MCD — equatorial diurnal ~40–60 K. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "surface_optics": {
                "albedo": {
                    "value": 0.13,
                    "units": "0–1 (bolometric albedo)",
                    "source": "TES bolometric albedo — Christensen et al. 2001: Meridiani "
                              "dark hematite-bearing plains ~0.12–0.15; midpoint 0.13. "
                              "UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Hematite-rich surface gives lower albedo than "
                             "typical Mars dust.",
                },
                "dust_cover_index": {
                    "value": 0.95,
                    "units": "0–1 (DCI)",
                    "source": "TES DCI — Ruff & Christensen 2002: Meridiani relatively "
                              "clean (DCI ~0.94–0.97). UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; no liquid water",
            },
            "geology": {
                "geologic_unit": {
                    "class_description": "Hesperian-age plains with hematite-bearing "
                                        "sedimentary/aeolian lag (unit Hvl in Tanaka 2014). "
                                        "Sulfate-cemented sandstone (Burns Formation) overlying "
                                        "basaltic basement.",
                    "source": "Tanaka et al. 2014 USGS Global Geologic Map of Mars. UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
        },
    }

    # =========================================================================
    # MARS-BASE: Arcadia Planitia
    # =========================================================================
    # Morgan et al. 2021: SWIM v3 ice depth ~10–30 cm at ~47°N; confidence class 4–5.
    # Topography: northern plains; slope 1–3° at 1 km (Smith et al. 2001).
    # TES albedo: ~0.22–0.28 (dustier northern plains).

    targets["arcadia_planitia"] = {
        "id": "arcadia_planitia",
        "name": "Arcadia Planitia",
        "body": "mars",
        "mission_type": "base",
        "lat": 46.7,
        "lon": -172.0,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "Representative center of SWIM high-confidence ice region in "
                             "Arcadia Planitia — Morgan et al. 2021 / swim.psi.edu. "
                             "GIS verification needed.",
        "cannot_reproduce": MARS_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 1.5,
                    "units": "degrees",
                    "source": "MOLA MEGDR — Arcadia Planitia northern plains; "
                              "typical slope 1–3° at 1 km. Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "roughness": {
                    "value": 15.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — smooth northern plains; roughness ~8–25 m. "
                              "Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "local_relief": {
                    "value": 200.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Arcadia Planitia is a relatively smooth "
                              "northern plain; local relief within 12 km ~50–400 m. "
                              "Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 218.0,
                    "units": "K",
                    "source": "TES / MCD — Arcadia Planitia at 46.7°N; "
                              "annual mean ~200–235 K. Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Cold northern mid-latitude site.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 110.0,
                    "units": "K",
                    "source": "TES / MCD — mid-latitude Mars annual range ~80–140 K. "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 45.0,
                    "units": "K",
                    "source": "TES / MCD — mid-latitude diurnal ~30–60 K. "
                              "Haberle et al. 2001. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "surface_optics": {
                "albedo": {
                    "value": 0.25,
                    "units": "0–1 (bolometric albedo)",
                    "source": "TES bolometric albedo — Christensen et al. 2001: "
                              "Arcadia Planitia northern plains ~0.22–0.28; midpoint 0.25. "
                              "UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Dusty northern plains; moderate albedo.",
                },
                "dust_cover_index": {
                    "value": 0.90,
                    "units": "0–1 (DCI)",
                    "source": "TES DCI — Ruff & Christensen 2002: Arcadia higher dust "
                              "cover than equatorial sites (DCI ~0.87–0.93). UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; no liquid water",
            },
            "geology": {
                "geologic_unit": {
                    "class_description": "Amazonian-age plains unit — smooth volcanic/periglacial "
                                        "plains with ice-rich substrate (unit AHv / Avf in "
                                        "Tanaka 2014). Arcadia Formation — mantled plains "
                                        "with patterned ground.",
                    "source": "Tanaka et al. 2014 USGS Global Geologic Map of Mars. UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
            "ice_polar": {
                "ice_depth": {
                    "value": 20.0,
                    "units": "cm depth to top of ice table",
                    "source": "SWIM v3 — Morgan et al. 2021 "
                              "(doi:10.1029/2020GL088143): Arcadia Planitia ice depth "
                              "~10–30 cm in high-confidence regions; midpoint 20 cm. "
                              "UNVERIFIED at swim.psi.edu.",
                    "resolution_m": 7000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. SWIM v3 resolution ~7 km. High confidence (class 4–5) "
                             "reported for Arcadia Planitia. Exact depth varies spatially.",
                },
                "ice_confidence": {
                    "value": "class_4",
                    "units": "categorical (SWIM confidence class 1–5)",
                    "source": "SWIM v3 — Morgan et al. 2021: Arcadia Planitia high-confidence "
                              "region; SWIM class 4–5. UNVERIFIED.",
                    "resolution_m": 7000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "volcanic_caves": null_val(
                "No MGC³ cave candidate reported in Arcadia Planitia plains region. "
                "volcanic_caves characteristic not applicable for this target."
            ),
        },
    }

    # =========================================================================
    # MARS-BASE: Arsia Mons Cave Candidate
    # =========================================================================
    # Wyrick et al. 2004; Cushing et al. 2007 — pit/cave candidate on Arsia Mons flank.
    # MOLA: Arsia Mons edifice slope 2–5° on flanks at 1 km.
    # TES albedo: ~0.15–0.22 (volcanic terrain, some dust).
    # Coordinates approximate from MGC³ or Cushing et al. 2007 figure.

    targets["arsia_mons_cave_candidate"] = {
        "id": "arsia_mons_cave_candidate",
        "name": "Arsia Mons Cave Candidate",
        "body": "mars",
        "mission_type": "base",
        "lat": -8.3,
        "lon": -120.5,
        "coordinate_status": "UNVERIFIED",
        "coordinate_source": "Approximate — Arsia Mons flank cave candidate; coordinates "
                             "estimated from Cushing et al. 2007 (doi:10.1029/2007GL030894) "
                             "figures. MGC³ doi:10.5066/P9VXZEF5 field schema unconfirmed. "
                             "GIS verification required.",
        "cannot_reproduce": MARS_CANNOT_REPRODUCE,
        "reference_values": {
            "topography": {
                "slope": {
                    "value": 3.5,
                    "units": "degrees",
                    "source": "MOLA MEGDR — Arsia Mons flank at ~8°S: flanks slope 2–5° "
                              "at 1 km scale. Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Midpoint of published flank range (2–5°).",
                },
                "roughness": {
                    "value": 20.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Arsia Mons lava flows; roughness higher than "
                              "plains ~10–35 m. Smith et al. 2001. UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "local_relief": {
                    "value": 1500.0,
                    "units": "meters",
                    "source": "MOLA MEGDR — Arsia Mons is ~20 km tall; flank local relief "
                              "within 12 km ~500–3000 m; midpoint 1500 m. Smith et al. 2001. "
                              "UNVERIFIED.",
                    "resolution_m": 1000,
                    "confidence": "low",
                    "notes": "UNVERIFIED. Very wide range on a shield volcano flank.",
                },
            },
            "thermal": {
                "temp_annual_mean": {
                    "value": 230.0,
                    "units": "K",
                    "source": "TES / MCD — Arsia Mons at -8.3°S, elevated altitude; "
                              "annual mean ~215–245 K (cooler than plains due to altitude). "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_annual_range": {
                    "value": 100.0,
                    "units": "K",
                    "source": "TES / MCD — equatorial-to-subtropical annual range ~80–120 K. "
                              "Forget et al. 2006. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
                "temp_diurnal_range": {
                    "value": 50.0,
                    "units": "K",
                    "source": "TES / MCD — equatorial diurnal range ~40–60 K. UNVERIFIED.",
                    "resolution_m": 50000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                    "percentile_estimate": None,
                    "basis": "APPROXIMATE — to be computed by assemble script.",
                },
            },
            "surface_optics": {
                "albedo": {
                    "value": 0.18,
                    "units": "0–1 (bolometric albedo)",
                    "source": "TES bolometric albedo — Christensen et al. 2001: "
                              "Arsia Mons volcanic region ~0.15–0.22; midpoint 0.18. "
                              "UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
                "dust_cover_index": {
                    "value": 0.93,
                    "units": "0–1 (DCI)",
                    "source": "TES DCI — Ruff & Christensen 2002: Tharsis volcanic region "
                              "moderate dust cover ~0.90–0.95. UNVERIFIED.",
                    "resolution_m": 8000,
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                },
            },
            "aridity": {
                "score": 1.0,
                "basis": "REQUIREMENT — maximally arid by definition; no liquid water",
            },
            "geology": {
                "geologic_unit": {
                    "class_description": "Amazonian-age volcanic shield deposits — Arsia Mons "
                                        "flank lava flows (unit Avf / Ael in Tanaka 2014). "
                                        "Shield volcano basalt with possible lava tubes.",
                    "source": "Tanaka et al. 2014 USGS Global Geologic Map of Mars. UNVERIFIED.",
                    "confidence": "low",
                    "notes": "UNVERIFIED.",
                }
            },
            "ice_polar": null_val(
                "Arsia Mons at -8.3°S: equatorial location. SWIM dataset does not cover "
                "equatorial latitudes (< 30°). No ground ice expected at this latitude. "
                "ice_polar characteristic not applicable."
            ),
            "volcanic_caves": {
                "cave_candidate": {
                    "value": "confirmed_candidate",
                    "units": "categorical (confirmed_candidate/possible/not_detected)",
                    "diameter_m": 150.0,
                    "depth_m": None,
                    "source": "Mars Global Cave Candidate Catalog (MGC³) — USGS/PSI; "
                              "doi:10.5066/P9VXZEF5. Arsia Mons pit skylight candidates "
                              "reported by Cushing et al. 2007 "
                              "(doi:10.1029/2007GL030894) and Wyrick et al. 2004 "
                              "(doi:10.1029/2004JE002277). Diameter ~100–250 m from "
                              "THEMIS imaging. UNVERIFIED — MGC³ field schema unconfirmed.",
                    "resolution_m": 100,
                    "confidence": "low",
                    "notes": "UNVERIFIED. MGC³ catalog schema not confirmed (DATASETS.md §3). "
                             "Diameter is an estimate from THEMIS figures; depth not measured. "
                             "Lava-tube extent beneath surface is unknown.",
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

    print("Building Mars reference target values from literature …")
    targets = build_mars_targets()
    print(f"  Built {len(targets)} Mars targets.")

    output = {
        "schema_version": "1.0",
        "body": "mars",
        "generated_at": PROC_DATE,
        "note": "UNVERIFIED — all values from published literature. Must be validated "
                "against primary PDS/MCD data before Phase 6.",
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
