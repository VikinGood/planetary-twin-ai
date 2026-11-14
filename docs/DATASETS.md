# Datasets — Planetary Twin AI

Space Logistics team, NASA Space Apps Challenge 2026.
AI use disclosure: this document was compiled with AI assistance from verified source metadata.
Anything not independently confirmed is marked UNVERIFIED.

---

## 1. Earth datasets

All Earth datasets target global land coverage at ≥ 0.25° working resolution.
Datasets not natively hosted in Google Earth Engine (GEE) must be downloaded and either
uploaded as user EE assets or processed locally with Rasterio/GeoPandas.

| characteristic | dataset_name | provider | earth_engine_id or URL | resolution | units | format | license | global_coverage | account_needed |
|---|---|---|---|---|---|---|---|---|---|
| `topography` | Copernicus DEM GLO-30 | ESA / Copernicus | `COPERNICUS/DEM/GLO30` | 30 m (1 arc-sec) | m elevation | GeoTIFF / EE ImageCollection | ESA Open Access (non-commercial) | ✅ Poles included | GEE account |
| `thermal` | MODIS MOD11A2 — Land Surface Temperature | NASA LPDAAC | `MODIS/061/MOD11A2` | 1 km, 8-day composite | K → °C | EE ImageCollection | NASA Open Data | ⚠️ Polar-night gaps > ~70° | GEE account |
| `surface_optics` | MODIS MCD43A3 — BRDF/Albedo | NASA LPDAAC | `MODIS/061/MCD43A3` | 500 m, daily | reflectance 0–1 (×0.001 scale) | EE ImageCollection | NASA Open Data | ⚠️ Polar-night gaps | GEE account |
| `aridity` | TerraClimate | Univ. Idaho / REACCH | `IDAHO_EPSCOR/TERRACLIMATE` | ~4 km (~1/24°), monthly | pr mm/month; pet mm/month×0.1 | EE ImageCollection | CC0 / Public Domain | ✅ Full global land | GEE account |
| `geology` | GLiM — Global Lithological Map | Hartmann & Moosdorf 2012, PANGAEA | doi:10.1594/PANGAEA.788537 | ~1 km raster | categorical (16 classes) | Shapefile + GeoTIFF | CC BY 3.0 | ✅ Full global land | PANGAEA free registration |
| `volcanic_caves` (lithology) | GLiM — basic volcanic class `vb` | Hartmann & Moosdorf 2012, PANGAEA | doi:10.1594/PANGAEA.788537 | ~1 km | binary categorical | GeoTIFF | CC BY 3.0 | ✅ Full global land | PANGAEA free registration |
| `volcanic_caves` (recency) | Smithsonian GVP — Holocene volcano catalog | Smithsonian Institution | https://volcano.si.edu/gvp_votw.cfm | Point (~1,400 volcanoes) | km (distance computed) | CSV / Excel / KMZ | CC BY 4.0 | ✅ Global | No account |
| `ice_polar` (permafrost) | IPA Global Permafrost Zonation Index (GZI) | Gruber 2012, PANGAEA / ETH Zürich | doi:10.1594/PANGAEA.783900 | ~1 km (30 arc-sec) | 0–1 continuous index | GeoTIFF | CC BY 3.0 | ✅ Full global land | No account |
| `ice_polar` (ice cover, primary) | MODIS MCD12Q1 — Land Cover Type | NASA LPDAAC | `MODIS/061/MCD12Q1` | 500 m, annual | IGBP class (class 15 = snow/ice) | EE ImageCollection | NASA Open Data | ✅ Global annual | GEE account |
| `ice_polar` (ice cover, secondary) | ESA WorldCover 2021 | ESA / Vito | `ESA/WorldCover/v200` | 10 m | categorical (class 70 = snow/ice) | EE ImageCollection | CC BY 4.0 | ✅ Global | GEE account |
| `illumination` | Computed from latitude | — derived — | n/a — computed analytically | 0.25° working grid | degrees / fraction | Computed raster | n/a | ✅ Full global | None |
| `logistics` (travel time filter) | Accessibility to Cities 2015 | Oxford / MAP | `Oxford/MAP/accessibility_to_cities_2015_v1_0` | ~1 km | minutes | EE Image | CC BY 3.0 | ✅ Global land | GEE account |
| `logistics` (protected areas filter) | WDPA — World Database of Protected Areas | UNEP-WCMC / IUCN | `WCMC/WDPA/current/polygons` | Vector polygons | categorical | EE FeatureCollection | WDPA Terms (non-commercial OK) | ✅ Global | GEE account |

### Notes on Earth datasets

- **Copernicus DEM GLO-30:** preferred over NASADEM/SRTM because it covers both poles. Slope (°), roughness (std-dev in 3×3 km window), and local relief (range in 12 km radius) all derived during preprocessing.
- **TerraClimate `pet` scale factor:** raw integer values in EE must be multiplied by 0.1 to get mm/month.
- **MODIS polar-night gap:** MOD11A2 and MCD43A3 lack valid retrievals at ≳ ±70° during winter. Cells with insufficient annual valid observations must be flagged **Low confidence** (METHODOLOGY §5 and §8-7).
- **GLiM and IPA GZI:** not in EE; download from PANGAEA and upload as user EE assets, or process locally with Rasterio.
- **GVP Holocene catalog:** not in EE; download as CSV, filter to qualifying volcano types (`Shield volcano`, `Fissure vent(s)`, `Volcanic field`, `Lava dome(s)`), compute distance raster in GeoPandas.
- **MCD12Q1 as primary ice layer:** extract IGBP class 15 as binary mask; aggregate to 0.25° as ice fraction. ESA WorldCover v200 (single epoch 2021, class 70) used as cross-check only.

---

## 2. Moon datasets

All Moon datasets must be downloaded from PDS or LROC nodes and preprocessed offline.
No Moon dataset is natively hosted in Google Earth Engine.

| characteristic | dataset_name | provider | url_or_access | resolution | units | format | license | coverage |
|---|---|---|---|---|---|---|---|---|
| `topography` **(scoring DEM)** | LOLA LDEM global DEM (LDEM_16) — resampled to 1 km for scoring | NASA PDS Geosciences Node | https://pds-geosciences.wustl.edu/missions/lro/lola.htm | ~118 m/px equatorial (16 ppd); resampled to 1 km for slope/roughness/relief | m elevation (IAU r=1737.4 km) | PDS IMG/LBL + GeoTIFF (LROC WMS) | NASA public domain | Global; polar stereo DEMs to ±90° |
| `topography` **(reference only — not used for scoring)** | SLDEM2015 (LOLA + Kaguya LALT fusion) | NASA PDS / JAXA | https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/sldem2015/ | ~59 m/px (512 ppd) for ±60° | degrees (slope); m (roughness) | GeoTIFF / PDS IMG | NASA/JAXA public domain | ±60° lat only |
| `thermal` | Diviner DLRE GDR — temperature products | NASA PDS Geosciences Node | https://pds-geosciences.wustl.edu/missions/lro/diviner.htm | 0.5°/px (~15 km) global; 128 ppd (~237 m) polar composites | K | PDS binary/LBL; GeoTIFF via PDS4 | NASA public domain | Global; continuous polar coverage |
| `illumination` | LOLA polar illumination maps (Mazarico et al. 2011) | NASA PDS Geosciences Node | https://pds-geosciences.wustl.edu/missions/lro/lola.htm (LOLA ancillary / illumination sub-product) | 240 m/px (polar stereo) | fraction 0–1 | PDS IMG/LBL + GeoTIFF | NASA public domain | Polar regions > ±70°; not global |
| `ice_polar` | LROC PSR Atlas — permanently shadowed regions | LROC / ASU + USGS Astrogeology | https://pds.lroc.asu.edu ; https://astrogeology.usgs.gov | ~240 m/px (from LOLA illumination maps) | binary PSR polygon + area km² | Shapefile / GeoPackage | NASA public domain | South and north polar > ±70° |
| `ice_polar` | LEND neutron suppression (hydrogen proxy) | NASA PDS Geosciences Node / IKI | https://pds-geosciences.wustl.edu/missions/lro/lend.htm | ~10 km/px | H equivalent wt% | PDS IMG/LBL | NASA public domain | Global (south-pole emphasis) |
| `ice_polar` | M³ surface-ice reflectance map (Li et al. 2018) | PDS / ISRO Chandrayaan-1 | https://doi.org/10.1073/pnas.1802345115 (paper); data via PDS M³ archive | ~280 m/px | reflectance anomaly (ice-band index) | PDS / GeoTIFF | NASA/ISRO open data | South pole surface only |
| `geology` | Unified Geologic Map of the Moon v2 (USGS 1:5M) | USGS Astrogeology | https://astrogeology.usgs.gov/search/map/Moon/Geology/Unified_Geologic_Map_of_the_Moon_GIS_v2 | 1:5,000,000 (~1–2 km min feature) | categorical unit code, age | GeoPackage / Shapefile | USGS public domain | Full Moon surface |
| `volcanic_caves` | LROC Lunar Pit Atlas | LROC / ASU | https://data.lroc.im-ldi.com ; fallback: https://pds.lroc.asu.edu | Point catalog (~300+ pits; exact count UNVERIFIED) | lat/lon, diameter m, depth m | CSV / Shapefile | NASA public domain | Global; most pits equatorial–mid-lat |
| `surface_optics` | LROC WAC Global Mosaic — reflectance | LROC / ASU | https://wms.lroc.asu.edu/lroc/view_rdr/WAC_GLD100 ; PDS: https://pds.lroc.asu.edu | 100 m/px | normalized reflectance at 604 nm (0–1) | GeoTIFF (tiles via WMS/HTTP) | NASA public domain | Global + polar stereo |
| `reference_targets` | NASA Artemis Candidate South-Polar Landing Regions | NASA | https://www.nasa.gov/news-release/nasa-identifies-candidate-regions-for-artemis-lunar-landing/ | Press-release map; no official GIS file | — | Press release + map image | NASA public information | 9 regions, all poleward of ~85°S |

### Notes on Moon datasets

- **Common 1 km slope baseline (TEAM DECISION):** LOLA LDEM is the scoring DEM for the Moon; resampled to 1 km before computing slope/roughness/relief. SLDEM2015 and pre-derived LOLA slope products are listed for reference but NOT used for scoring.
- **No EE hosting:** all Moon data must be downloaded from PDS/LROC and processed offline.
- **LOLA illumination sub-product URL:** PDS volume structure for illumination maps not straightforward; confirm Mazarico et al. 2011 PDS4 DOI before preprocessing. UNVERIFIED.
- **No merged ice-detection product:** LEND (10 km/px), Mini-RF, LCROSS, and M³ have never been officially merged. Use LEND hydrogen maps for global screening + M³ surface-ice map for south-pole validation. M³ added as fourth source (not in original `config/characteristics.json` list; added here as supplemental validation source, not scored).
- **WAC reflectance vs. broadband albedo:** LROC WAC mosaic is single-band (604 nm), not broadband. Cross-calibration to MODIS broadband shortwave albedo (0.3–5 µm) is UNVERIFIED. Flag `surface_optics` scoring for Moon as PROXY / Low confidence if no cross-calibration factor is applied; apply percentile/regime comparison as fallback.
- **Diviner resolution:** standard GDR global products are 0.5°/px (~15 km); 128 ppd (~237 m) polar composites exist but PDS volume paths need confirmation.
- **Artemis 9 target coordinates (UNVERIFIED):** official coordinate table not released by NASA. Regions from NASA release 24-136 (Oct 28 2024): Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain. Coordinates in `config/missions/moon-landing.json` are approximate from USGS Gazetteer and release map; must be verified by Ramiro (GIS) before Phase 6.

---

## 3. Mars datasets

All Mars datasets must be downloaded from PDS or Astropedia and preprocessed offline.
No Mars dataset is natively hosted in GEE.

| characteristic | dataset_name | provider | url_or_access | resolution | units | format | license | coverage |
|---|---|---|---|---|---|---|---|---|
| `topography` **(scoring DEM)** | MOLA MEGDR global DEM (1/128°) — resampled to 1 km for scoring | NASA PDS / USGS Astropedia | https://pds-geosciences.wustl.edu/missions/mgs/mola.htm | 463 m/px (1/128°); resampled to 1 km for slope/roughness/relief | m elevation (areoid) | PDS IMG/LBL; Astropedia GeoTIFF | NASA/USGS public domain | Global (90°S–90°N) |
| `topography` **(reference only — not used for scoring)** | MOLA–HRSC Blended DEM (~200 m) | ESA/DLR / USGS Astropedia | https://ode.rsl.wustl.edu/mars/indexproductsearch.aspx | ~200 m/px | m elevation | GeoTIFF | ESA/DLR open science, attribution required | ~90% global (completeness UNVERIFIED) |
| `surface_optics` | TES Bolometric Albedo (Christensen et al. 2001) | NASA PDS Geosciences Node | https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-sddr-v1/ | ~3–8 km (UNVERIFIED — verify from PDS label) | Bond/bolometric albedo 0–1 | PDS IMG/LBL; Astropedia GeoTIFF | NASA public domain | Global; gaps over polar caps |
| `surface_optics` | TES Dust Cover Index (Ruff & Christensen 2002) | NASA PDS Geosciences Node | https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-sddr-v1/ | ~3–8 km | DCI index 0–1 | PDS IMG/LBL | NASA public domain | Global; reduced quality at poles |
| `thermal` | TES Thermal Inertia (Putzig & Mellon 2007) | NASA PDS Geosciences Node | https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-sddr-v1/ | ~3–8 km | J m⁻² K⁻¹ s⁻½ (TIU) | PDS IMG/LBL | NASA public domain | Global; reduced accuracy near poles |
| `thermal` | Mars Climate Database v6.1 (MCD) | LMD / CNRS / ESA | https://www-mars.lmd.jussieu.fr/mars/access.html | 5°×5° standard (~600 km) free; finer by request | K (surface temp); Pa; m/s | NetCDF; Fortran/Python API (pymcd) | Non-commercial / educational license | Global |
| `geology` | USGS Global Geologic Map of Mars (Tanaka et al. 2014) | USGS Astrogeology | https://astropedia.astrogeology.usgs.gov/download/Mars/Geology/Mars_Global_Geologic_Map_Tanaka2014 | 1:20,000,000 (~2 km min mapping unit) | categorical (44 units, age, description) | Shapefile + GeoTIFF | USGS public domain | Full planet |
| `volcanic_caves` | Mars Global Cave Candidate Catalog (MGC³) | USGS / PSI (Wynne et al.) | https://doi.org/10.5066/P9VXZEF5 (ScienceBase) | Point catalog (~1,064 candidates; UNVERIFIED exact count) | lat/lon, diameter m, morphology class, confidence tier | CSV / Shapefile | USGS public domain | Global |
| `ice_polar` | SWIM v3 — Subsurface Water Ice Mapping | PSI / NASA (Bramson, Morgan et al.) | https://swim.psi.edu | ~7 km/px (~8 ppd) | ice depth cm; confidence class 1–5 | GeoTIFF / CSV | NASA-funded open science | Mid-latitudes ~30°–60° N/S; not equatorial |

### Notes on Mars datasets

- **Common 1 km slope baseline (TEAM DECISION):** MOLA MEGDR (463 m) is the scoring DEM for Mars; resampled to 1 km before computing slope/roughness/relief. MOLA–HRSC blended DEM is listed for reference but NOT used for scoring (global completeness unconfirmed).
- **MCD non-commercial license:** suitable for this project (educational/Space Apps). MCD is used at the **target level only** (single reference value per named target site, not a gridded input). The free 5° × 5° download suffices for this purpose.
- **TES product pixel scale UNVERIFIED:** PDS label must be read to confirm exact pixel scale of the distributed mosaics. Resolution is stated as ~3 km in literature (Christensen et al. 2001) but PDS grids may differ.
- **MOLA–HRSC blended DEM (reference only):** not used for scoring. Listed for reference. Global completeness is UNVERIFIED (~90% HRSC coverage).
- **SWIM coverage gap:** equatorial band < 30° latitude has no SWIM ice signal. Mars landing targets at equatorial latitudes (Jezero, Gale, Meridiani) will have no ice_polar score — expected and correct (ice_polar is not in the mars-landing default preset).
- **MGC³ field schema UNVERIFIED:** confirm candidate count and field names by downloading from ScienceBase doi:10.5066/P9VXZEF5 before Phase 3.

---

## 4. Known terrestrial analog site catalogs

Used **only** for exclusion buffering (50 km radius) and blind validation. These are NOT scored.

| catalog_name | provider | doi_or_url | format | approx_site_count | key_fields | notes |
|---|---|---|---|---|---|---|
| USGS Known Terrestrial Analog Sites | USGS / NASA | doi:10.5066/P9J72921 | Shapefile + CSV (ScienceBase) | ~50–60 (UNVERIFIED) | site_name, lat, lon, body, primary_characteristic, reference | Directly cited in AGENTS.md §. Public domain. Priority: download before Phase 3. |
| NASA Astrobiology Field Sites | NASA Astrobiology Program | https://astrobiology.nasa.gov/research/astrobiology-field-sites/ | Web registry; bulk-download format UNVERIFIED | O(100) (UNVERIFIED) | site_name, PI, location, analog_environment_type, associated_mission | If no machine-readable download exists, manually curate a GeoJSON. Flag UNVERIFIED. |
| ESA Catalogue of Planetary Analogues | ESA ESTEC / ILEWG | Bernard et al. 2020, doi:10.1017/S1473550419000491 | PDF + possible CSV; bulk download UNVERIFIED | 53 (Bernard et al. 2020) | site_name, country, coordinates, body_relevance, environment_type, key_parameters | Published as journal supplement. Extract CSV from supplementary table. |
| NASA Planetary Pits and Caves Analog Dataset | NASA / USGS / PSI (Cushing et al.) | Search ScienceBase for "Cushing planetary caves analog" or doi:10.5066 search | CSV / Shapefile (format UNVERIFIED) | O(10–30) (UNVERIFIED) | site_name, lat, lon, cave_type, associated_body, validation_status | Used to validate volcanic_caves proxy. If unavailable at preprocessing: use canonical sites per METHODOLOGY §2.6. **Locate before Phase 3.** |

---

## 5. Gaps and proxies (consolidated)

| characteristic | body | gap | proxy or resolution |
|---|---|---|---|
| `volcanic_caves` | Earth | No global lava-tube catalog | GLiM vb + GVP Holocene distance; HIGH/MEDIUM/LOW categorical; always LOW confidence (PROXY label) |
| `geology` | Earth | GLiM not in EE | Download from PANGAEA (doi:10.1594/PANGAEA.788537); upload as EE asset or process with Rasterio |
| `ice_polar` (permafrost) | Earth | IPA GZI not in EE | Download from PANGAEA (doi:10.1594/PANGAEA.783900); upload as EE asset or process locally |
| `thermal`, `surface_optics` | Earth | MODIS polar-night gaps > ±70° | Flag affected cells as Low confidence |
| `ice_polar` | Moon | No merged ice-detection product | Use LEND hydrogen maps (global, 10 km) + M³ surface-ice map (south-pole, 280 m) separately |
| `surface_optics` | Moon | WAC single-band (604 nm) vs. broadband | Cross-calibration UNVERIFIED; apply percentile/regime fallback if no calibration factor found |
| `illumination` | Moon | Illumination maps only cover poles (> ±70°) | Polar targets: use LOLA illumination fraction. Non-polar: compute analytically from orbital geometry |
| `topography` | Moon | Slope products require derivation | Derive from SLDEM2015 (±60°) and LOLA polar DEMs; USGS pre-derived tiles available |
| `topography` | Mars | MOLA–HRSC blended completeness UNVERIFIED | Fallback: MOLA MEGDR 463 m, confirmed globally complete |
| `thermal` | Mars | TES pixel scale UNVERIFIED | Read PDS label to confirm; use ~8 ppd as working assumption |
| `ice_polar` | Mars | SWIM covers only 30°–60° N/S | Equatorial cells score 0 for ice_polar — correct behavior; not a gap |
| `volcanic_caves` | Mars | MGC³ field schema UNVERIFIED | Download from ScienceBase (doi:10.5066/P9VXZEF5) to confirm count and fields before Phase 3 |
| `aridity` | Moon/Mars | No dataset needed | REQUIREMENT score computed entirely from Earth pr/pet; Moon and Mars always = 1 by definition |
| `illumination` | Mars | No dedicated dataset needed | Computed from orbital parameters and target latitude; low default weight (excluded from mars-landing) |
