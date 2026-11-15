# Space Apps 2026 — Project submission texts

Ready-to-paste text for each field of the project page. Draft prepared before the final
numbers: replace every `[TO CONFIRM ...]` before submitting, and delete any line that
describes something the final build does not do.

Challenge: Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars.
Team: Space Logistics (Buenos Aires). Members: Adriana Ferrandino, Guillermo Pablo Sardón,
Susana Cardozo.

---

## Project Name

Celestial Analog Finder

Tagline: Discover Earth. Prepare for other worlds.

## High-Level Project Summary

Celestial Analog Finder, by team Space Logistics, is an interactive map that finds and characterizes new places on Earth
where teams can rehearse future Moon and Mars missions. The user picks a body (Moon or
Mars), a mission type (landing site or permanent base) and any combination of eight
characteristics: topography, geology, thermal environment, aridity, ice and polar
conditions, volcanic terrain and caves, surface optics, and illumination. The engine
scores every land cell of the planet at 0.25° against NASA's candidate landing regions and
base sites, ranks the best new candidates, and explains for each one what it reproduces,
what it cannot reproduce (gravity, vacuum, radiation, absolute temperatures) and which
landing or base activities can be tested there. Known analogs such as the Atacama Desert or
Devon Island are excluded from the "new candidates" list but used to check that the engine
finds them. The challenge asks for new, well-characterized analogs for bases and landing
sites; this tool searches the whole planet instead of re-ranking a fixed list, and shows its
reasoning so mission planners can trust or challenge each result.

## Link to Project Demo

[TO CONFIRM: public YouTube link to the 30-second video, or public link to the 7-slide deck]

## Link to Final Project

- Live tool: https://vikingood.github.io/planetary-twin-ai/
- Code: https://github.com/VikinGood/planetary-twin-ai

## Detailed Project Description

**What it does.** Celestial Analog Finder turns the analog search into a mission question: "Where
on Earth can we test this landing or this base before we fly?" The user chooses:

1. the body: Moon or Mars;
2. the mission type: landing site, permanent base, or both side by side;
3. a reference target: one of NASA's nine candidate south-polar landing regions, the
   Shackleton–de Gerlache ridge or the Marius Hills pit for the Moon; Jezero, Gale,
   Meridiani Planum, Arcadia Planitia or an Arsia Mons cave candidate for Mars;
4. one or several characteristics, each with an adjustable weight.

The map shows the ten best new candidates, spread over distinct regions. Each candidate has
a characterization card: score by characteristic, measured values with their source,
environment tags from the challenge (desert, polar, volcanic, arid, cave), the activities it
can support (for example hazard detection and landing pads for a landing site; habitat
construction, water extraction from ground ice, cave shelter and power in extreme light for a
base), and the conditions Earth cannot reproduce.

**How it works.**

- Earth: every land cell of a global 0.25° grid gets slope, roughness and relief computed
  from a digital elevation model resampled to a common 1 km baseline, land surface
  temperature and albedo from NASA MODIS, aridity from TerraClimate, lithology, volcanic
  context, ice and permafrost, and the solar illumination regime computed from orbital
  geometry. Heavy processing runs in Google Earth Engine; the tool only loads small,
  precomputed tables.
- Moon and Mars: reference values for each target are compiled from published NASA
  mission products and peer-reviewed papers (LOLA, Diviner, LROC, MOLA, TES, SWIM and
  others), each with its citation and a coordinate-status flag.
- Scoring: each characteristic follows an explicit rule (absolute comparison, requirement,
  percentile regime or category), documented in `docs/METHODOLOGY.md`. Selected
  characteristics combine with a weighted geometric mean, so a site that fails one
  requirement cannot hide behind good scores elsewhere. Every score breaks down by
  characteristic and carries a confidence level.
- Bare surfaces only: candidates must be at least 50% barren, snow/ice or open shrubland
  (MODIS MCD12Q1), so dark forests are never mistaken for lunar regolith.
- Validation (`docs/VALIDATION_REPORT.md`): we scored all 337,611 land cells and checked where
  12 well-known analog sites fall, without telling the engine about them. For a lunar
  south-pole base, the McMurdo Dry Valleys, Svalbard and Devon Island (Haughton Crater) rank
  in the top 3%, 6% and 8% of all land on Earth; for a Mars landing, Lanzarote ranks in the
  top 5–9% and Rio Tinto in the top 9–19%. Landing and base rankings share no place in their
  top 10, and the top 10 stays stable when any weight changes by ±20%.
- AI interpretation: a language model writes a short, labeled explanation for top
  candidates using only the numbers in the result; a deterministic checker rejects any
  invented number.

**Benefits.** Analog campaigns are expensive and usually return to the same few sites. A
transparent, global search helps mission teams find closer, cheaper or more specific test
sites, compare landing and base needs, and see exactly where each analog falls short.

**Tools.** Python (NumPy, pandas, GeoPandas, Rasterio, FastAPI), Google Earth Engine,
React, MapLibre GL JS, Vite, GitHub Pages. AI-assisted development is described in "Use of
Artificial Intelligence".

## NASA Data

- MODIS MOD11A2 Land Surface Temperature (NASA LP DAAC): day and night temperature,
  annual range and diurnal range for every Earth cell (thermal characteristic).
- MODIS MCD43A3 albedo (NASA LP DAAC): broadband albedo for every Earth cell (surface optics).
- MODIS MCD12Q1 land cover (NASA LP DAAC): land mask, snow and ice cover, and the
  bare-surface filter (barren, snow/ice and open shrubland classes).
- LRO LOLA, LRO Diviner and LROC products (NASA PDS, LROC/ASU): lunar topography,
  temperatures, illumination, permanently shadowed regions and the Lunar Pit Atlas, used for
  the Moon reference targets.
- MGS MOLA and TES products (NASA PDS): Mars topography, albedo, dust cover and thermal
  inertia, used for the Mars reference targets.
- SWIM Subsurface Water Ice Mapping (NASA-funded, PSI): shallow ice context for Arcadia
  Planitia.
- NASA's candidate south-polar landing regions (release 24-136, October 28, 2024): Moon
  landing targets.
- NASA analog field programs (Haughton-Mars Project, ARADS in the Atacama, Desert RATS):
  part of the 12 known analog sites used for validation (`data/reference/known_analogs.csv`).

## Space Agency Partner & Other Data

- Copernicus DEM GLO-30 (ESA / Copernicus programme): Earth topography.
- ESA PANGAEA (Lanzarote) and the Ries crater training sites: known analogs for validation.
- FAO GAUL 2015 administrative boundaries: region names for candidates.
- TerraClimate (University of Idaho): aridity (precipitation over potential evapotranspiration).
- GLiM Global Lithological Map (Hartmann and Moosdorf 2012, PANGAEA): Earth lithology

- Smithsonian Global Volcanism Program, Holocene volcanoes: volcanic recency for the lava-tube
  proxy.
- IPA Global Permafrost Zonation Index (Gruber 2012): permafrost.
- USGS Unified Geologic Map of the Moon, USGS Global Geologic Map of Mars (Tanaka et al.
  2014) and the Mars Global Cave Candidate Catalog (MGC³): geology and cave references.
- Mars Climate Database (LMD/CNRS/ESA): published temperature values cited for the Mars
  reference targets.
- OpenStreetMap (© OpenStreetMap contributors): base map tiles.
- Open-source software: React, MapLibre GL JS, Vite, FastAPI, NumPy, pandas, GeoPandas,
  Rasterio, Earth Engine Python API.
- No copyrighted images are used. All data above is open; licenses are listed in
  `docs/DATASETS.md`.

## Use of Artificial Intelligence

Yes. AI tools were used to speed up planning and coding; every output was reviewed by the
team, and the scoring rules, targets and results were checked against their sources.

- IBM Bob: phased planning, methodology drafts and the first backend code.
- Google Antigravity (Gemini models): implementation and tests of the data pipeline and the
  scoring engine.
- Claude (Anthropic): review of methodology and data, the Explorer dashboard code, and drafts
  of the submission texts.
- [TO CONFIRM: Groq-hosted LLM that writes the per-candidate interpretations, labeled
  "AI interpretation" in the tool.]

AI-generated code carries a header comment saying so, and the README has a "Use of
Artificial Intelligence" section. No AI-generated images or video are used. No NASA logos or mission
insignia appear in the project.

## References

- NASA Space Apps Challenge 2026, challenge "Identify Earth Locations that Analog the
  Permanent Moon Base Locations and Mars".
- NASA, "NASA Provides Update on Artemis III Moon Landing Regions", release 24-136,
  October 28, 2024.
- Hartmann, J. and Moosdorf, N. (2012). The new global lithological map database GLiM.
- Gruber, S. (2012). Derivation and analysis of a high-resolution estimate of global
  permafrost zonation.
- Tanaka, K. L. et al. (2014). Geologic Map of Mars. USGS SIM 3292.
- Mazarico, E. et al. (2011). Illumination conditions of the lunar polar regions using LOLA
  topography.
- Christensen, P. R. et al. (2001). Mars Global Surveyor Thermal Emission Spectrometer
  experiment.
- Putzig, N. E. and Mellon, M. T. (2007). Apparent thermal inertia and the surface
  heterogeneity of Mars.
- Abatzoglou, J. T. et al. (2018). TerraClimate.
- Morgan, G. A. et al. (2021). Availability of subsurface water-ice resources in the northern
  mid-latitudes of Mars (SWIM). Nature Astronomy.
- Copernicus DEM GLO-30, ESA / Airbus (2021, release 2024_1).
- Wan, Z. et al. MODIS MOD11A2 v061; Schaaf, C. and Wang, Z. MCD43A3 v061; Friedl, M. and
  Sulla-Menashe, D. MCD12Q1 v061 (NASA LP DAAC).
- Global Volcanism Program (2024). Volcanoes of the World, Smithsonian Institution.
- Full list with licenses: `docs/DATASETS.md` and `docs/DATA_SOURCES.md` in the repository.

---

## Final checklist (tick before "Submit for Judging")

- [ ] Demo: video of at most 30 seconds with English subtitles, or at most 7 slides in
      English including the title slide.
- [ ] Demo and final project links open in a private browser window, no login.
- [ ] Every field above filled; no `[TO CONFIRM ...]` left.
- [ ] NASA data listed and actually used.
- [ ] AI use disclosed here, in the README and in file headers; any AI image or video
      watermarked.
- [ ] No NASA logos, flags or mission insignia.
- [ ] No names, voices or images of minors.
- [ ] "Terms and Conditions" and "Confirm All Work is Original" boxes checked.
