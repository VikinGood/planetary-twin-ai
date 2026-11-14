# Planetary Twin AI — Project rules (read before every task)

These rules apply to every mode, task, subtask and subagent. Subagents do not see the
chat history: whoever spawns one must tell it to read this file and `docs/ESTADO.md` first.

## The official challenge (this defines the whole project)
NASA Space Apps Challenge 2026, "Identify Earth Locations that Analog the Permanent Moon
Base Locations and Mars":

> Use open Earth, Moon, and Mars data from NASA and other space agencies to identify and
> characterize new terrestrial analogs for future bases or landing sites, drawing on
> deserts, polar regions, volcanic and arid terrains, caves, and other environments that
> share conditions with the lunar or Martian surface, then present your findings as a map,
> visualization, or other tool.

Every phase must serve these five words: identify, characterize, new, bases, landing sites.

## Context
- Team: Space Logistics (Buenos Aires local event).
- Submission closes Sunday Nov 15, 2026, 23:59 (America/Buenos_Aires). Team target: 21:00.
- Code freeze: Sunday 11:00. After that, only fixes.

## Language
EVERYTHING the project produces is in ENGLISH: code, comments, docs, UI, commit messages,
README, submission texts, slides, subtitles.

## Workflow (non-negotiable)
1. Work in PHASES defined in `docs/prompts/`. Run only the phase the user starts.
2. The single source of truth is `docs/ESTADO.md`, not the chat. Read it at the start of
   every task; update it at the end (status, decisions, open questions, files produced).
3. When a phase is done: update `docs/ESTADO.md`, commit with message `phase N: <summary>`,
   then STOP and report: what was delivered, what is missing, the question for the team.
4. If something is ambiguous, ask. Never expand scope without asking.
5. No placeholder logic presented as real. Mock data is labeled `MOCK` in file names and UI.

## Product scope (MVP)
The user chooses three things, and the tool ranks and characterizes Earth locations:

1. **Planetary body:** Moon or Mars.
2. **Mission type:** Landing site or Permanent base. Both must be simulated, and the UI
   has a "Compare both" view showing how the ranking changes between them.
3. **Characteristics:** one or several at once (multi-select). Only the selected ones enter
   the score; each selected one gets an adjustable weight.

Characteristic catalog (ids are fixed; Phase 1 defines variables and rules for each):

| id | Characteristic | Earth side | Moon / Mars side |
| --- | --- | --- | --- |
| `topography` | Slope, roughness, local relief | Copernicus DEM | LOLA / MOLA |
| `geology` | Lithology and regolith analog | GLiM lithology | Unified geologic maps |
| `thermal` | Temperature extremes and daily range | MODIS LST, TerraClimate | Diviner / TES, Mars Climate Database |
| `aridity` | Aridity and liquid water absence | TerraClimate (pr / pet) | Requirement: as arid as possible |
| `ice_polar` | Ground ice, permafrost, polar light regime | Permafrost and snow/ice cover, latitude | PSRs and ice maps / shallow ice maps |
| `volcanic_caves` | Volcanic terrain, lava tubes, pits | GLiM volcanic classes, Holocene volcanoes | Lunar pit atlas / Mars cave catalog |
| `surface_optics` | Albedo and dust | MODIS albedo | LROC / TES albedo, dust cover |
| `illumination` | Sunlight regime (polar day and night) | Computed from latitude | LOLA illumination / latitude |

Plus `logistics` (travel time, protected areas): a filter and cost, never a similarity.

Mission type presets (defaults, editable in the UI):
- **Landing site:** topography, surface_optics, thermal, illumination selected; slope and
  roughness weigh most. Activities to test: descent imaging, hazard detection, landing pad,
  first mobility.
- **Permanent base:** ice_polar, volcanic_caves, thermal, illumination, geology, topography
  selected; resources (ice) and shelter (caves) weigh most. Activities to test: habitat
  construction, ISRU water extraction, shelter, power in extreme light regimes,
  long-duration crew operations.

Reference targets (defaults, confirm in Phase 1):
- Moon, landing: NASA's nine candidate south-polar landing regions (announced Oct 28, 2024),
  for example Malapert Massif, Mons Mouton, Haworth, Slater Plain.
- Moon, base: Shackleton–de Gerlache connecting ridge (illumination, ice access) and
  Marius Hills pit (lava-tube shelter).
- Mars, landing: Jezero crater, Gale crater, Meridiani Planum.
- Mars, base: Arcadia Planitia (shallow ground ice) and an Arsia Mons cave candidate.

Earth search region: the WHOLE PLANET land surface (global screening at 0.25°, about
28 km; optional refinement only in top regions).

Every candidate gets environment-family tags from the challenge: desert, polar, volcanic,
arid, cave (rules defined in Phase 1).

Known analog sites (USGS Known Terrestrial Analog Sites, NASA astrobiology field sites,
ESA Catalogue of Planetary Analogues, NASA pits and caves analog dataset): excluded from the
"new candidates" list with a buffer, but USED for blind validation.

## Tech stack
- Backend: Python, FastAPI, GeoPandas, Rasterio, NumPy. Always inside `.venv`
  (`python -m venv .venv`), dependencies pinned in `requirements.txt`. Never install globally.
- Heavy global preprocessing runs offline (Google Earth Engine or scripts) and writes
  per-characteristic scores to `data/processed/`. The API and the demo never download live.
- Earth Engine: no API key. Authenticate once with `earthengine authenticate`, then
  initialize with `ee.Initialize(project=os.environ["EE_PROJECT"])`; the project ID lives
  in `.env` (template in `.env.example`).
- Frontend: minimal React + MapLibre GL JS. YARN only (never npm or npx).
  OpenStreetMap tiles with the required attribution. Combines the selected characteristics
  on the client, so any multi-selection re-ranks instantly.
- AI: LLM behind an `LLMProvider` interface. `GroqProvider` reads `GROQ_API_KEY` and
  `GROQ_MODEL` from `.env` (never committed). `NoLLMProvider` fallback.

## Scientific principles
- Traceability: every value keeps source, resolution, units and timestamp.
- Reproducibility: every score can be recomputed from stored inputs and weights.
- Explainability: every score is decomposable per characteristic and per variable.
- Explicit uncertainty: every result carries a confidence level.
- Separation: measured data and AI interpretation are stored and shown separately.
- Never invent measurements, datasets or sources. Mark anything unverified as `UNVERIFIED`.
- State what Earth cannot reproduce (gravity, vacuum or thin atmosphere, radiation,
  absolute lunar or Martian temperatures) instead of hiding it in a score.
- Combine selected characteristics with a weighted geometric mean, so a characteristic
  that scores zero drops the site. Phase 1 may change this only with a written reason.

## Submission rules (Space Apps Project Submission Guide)
- The final project link must be public, no login: static build on GitHub Pages.
- Must use NASA data to be eligible for Global Awards; list it explicitly.
- AI use must be disclosed in descriptive text and metadata (README section + header
  comment in generated files). AI images or videos need a visible watermark. No NASA logos
  or mission insignia in generated content.
- Every external resource (code, data, text, images, even open source) goes in References.
- No personal data, no names, voices or likenesses of minors.
