# Project state (single source of truth)

Every task reads this file first and updates it last. Keep entries short. English only.

## Phases

| Phase | File | Mode | Status | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 Setup | 00-kickoff-orchestrator.md | Space Apps Orchestrator | approved | Guillermo | |
| 1 Methodology | 01-methodology.md | Plan | approved | | |
| 2 Data and architecture | 02-data-architecture.md | Plan | review | | |
| 3 Backend core | 03-backend.md | Agent | pending | | parallel with 4 and 5 |
| 4 AI analyst | 04-ai-analyst.md | Agent | pending | | parallel with 3 and 5 |
| 5 Explorer dashboard | 05-frontend.md | Agent | pending | | parallel with 3 and 4 |
| 6 Validation | 06-validation.md | Science Reviewer + Agent | pending | | |
| 7 Submission package | 07-submission.md | Agent | pending | | |

Status values: pending, in progress, review, approved, blocked.

## Decisions (append, newest last)

- 2026-11-14: Scope follows the official challenge text in AGENTS.md: Moon and Mars;
  landing site and permanent base; multi-select characteristics; whole-planet Earth search;
  environment-family tags (desert, polar, volcanic, arid, cave). All outputs in English.
  This replaces the earlier "Mars only, rover mobility" scope.
- 2026-11-14: General scoring principle: analog score = similarity to reference target.
  Only REQUIREMENT characteristics (aridity) are exceptions (labeled as such).
  Combination: weighted geometric mean over selected characteristics only (zero score eliminates site).
- 2026-11-14: Topography — landing: slope/roughness similarity + 12° hard cap (NASA HLS threshold).
  Base: adds surrounding relief within 12 km neighborhood radius.
- 2026-11-14: Lava-tube proxy = GLiM vb class + distance to qualifying Smithsonian GVP
  Holocene volcano (shield, lava field, fissure vent, volcanic field); HIGH/MEDIUM/LOW
  categorical output; always LOW confidence; labeled PROXY in data and UI.
- 2026-11-14: Illumination = LOW SUN regime similarity (not "maximize illumination").
  Scored as percentile/regime match on solar elevation statistics.
- 2026-11-14: Mission preset weights defined (summing to 1):
  moon-landing: topography 0.35, illumination 0.25, surface_optics 0.20, thermal 0.20.
  moon-base: ice_polar 0.25, illumination 0.20, volcanic_caves 0.15, thermal 0.15, topography 0.15, geology 0.10.
  mars-landing: topography 0.40, surface_optics 0.25, aridity 0.20, thermal 0.15 (illumination replaced by aridity).
  mars-base: ice_polar 0.25, volcanic_caves 0.20, geology 0.15, thermal 0.15, aridity 0.15, topography 0.10.
- 2026-11-14: mars-landing preset excludes illumination; aridity replaces it.
  AGENTS.md default characteristic list for mars-landing updated accordingly.

## Contracts (files other phases depend on)

- `config/characteristics.json`: ✅ produced in Phase 1.
- `config/missions/*.json` (four presets: moon-landing, moon-base, mars-landing, mars-base): ✅ produced in Phase 1.
- `contracts/similarity_result.sample.json`: ✅ produced in Phase 2.
- `contracts/interpretation.schema.json`: ✅ produced in Phase 2.
- `docs/DATASETS.md`: ✅ produced in Phase 2.
- `docs/ARCHITECTURE.md`: ✅ produced in Phase 2.

## Open questions for the team

- **Moon target coordinates (UNVERIFIED):** nine NASA Artemis south-polar landing regions announced Oct 28 2024 have no official GIS file. Coordinates in moon-landing.json are approximate. Ramiro (GIS) must verify before Phase 6. NASA press release: https://www.nasa.gov/news-release/nasa-identifies-candidate-regions-for-artemis-lunar-landing/
- **Mars target coordinates (UNVERIFIED):** Jezero, Gale, Meridiani are well-known and likely correct; Arcadia Planitia center and Arsia Mons pit coordinates need GIS verification.
- **LOLA illumination sub-product URL:** PDS volume path for Mazarico et al. 2011 illumination maps needs confirmation before Moon preprocessing begins.
- **TES pixel scale:** PDS label must be read to confirm exact resolution of TES bolometric albedo, thermal inertia, and DCI mosaics (stated ~3–8 km in literature).
- **MOLA–HRSC blended DEM completeness:** confirm global seamless coverage from Astropedia label before using as primary Mars DEM.
- **MGC³ field schema:** download from ScienceBase doi:10.5066/P9VXZEF5 to confirm candidate count and field names.
- **NASA Planetary Pits and Caves Analog Dataset URL:** locate exact ScienceBase URL before Phase 3; needed for volcanic_caves proxy validation.
- **NASA Astrobiology Field Sites bulk download:** confirm if machine-readable CSV/GeoJSON export is available; if not, manually curate.
- **WAC broadband cross-calibration:** LROC WAC mosaic is single-band (604 nm); cross-calibration to MODIS broadband shortwave albedo is unconfirmed. Apply percentile/regime fallback if no calibration factor found.

## Accounts the team must create before preprocessing

- Google Earth Engine (all members who run scripts): https://earthengine.google.com — free non-commercial registration.
- PANGAEA (to download GLiM and IPA GZI): https://pangaea.de — free registration.
- Mars Climate Database (for high-res MCD runs, optional): https://www-mars.lmd.jussieu.fr/mars/access.html — free registration.
- NASA Earthdata (for MODIS direct download, optional — not needed if using EE): https://urs.earthdata.nasa.gov

## Known issues

-
