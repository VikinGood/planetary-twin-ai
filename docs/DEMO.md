# Demo materials

Three formats: the 30-second video for global judging, the 7-slide fallback, and a
2-minute live demo for the local jury. Everything shown must be the real tool with the real
export (no MOCK banner visible).

## 1. Video: 30 seconds, English subtitles

Follows the structure suggested by the Space Apps submission guide. Screen recording of the
live tool plus voice-over or on-screen text. Subtitles: `docs/demo_subtitles_en.srt`.

| Time | Screen | Voice-over / subtitle |
| --- | --- | --- |
| 0:00–0:02 | Team name over the world map | We are Space Logistics, from Buenos Aires. |
| 0:02–0:05 | Lunar south pole target in the selector | Before we land on the Moon or Mars, we must test everything on Earth. |
| 0:05–0:10 | Title card in the tool header | This is Planetary Twin AI: finding the Moon and Mars on Earth. |
| 0:10–0:15 | Switch Moon to Mars; Landing site to Permanent base | Pick a world and a mission: a landing site or a permanent base. |
| 0:15–0:20 | Toggle characteristics; ranking and map update | Choose what matters. NASA data scores every place on Earth. |
| 0:20–0:25 | Open a new candidate card | It finds new analogs, and says what they test and what Earth cannot reproduce. |
| 0:25–0:30 | "Compare both" view, zoom out | Cheaper, closer test sites for the next steps in space. |

Recording tips: 1920 × 1080, browser zoom 90%, hide bookmarks, cursor visible, no music
with lyrics. Upload to YouTube as Public or Unlisted and test the link logged out.

## 2. Fallback: 7 slides (English, including the title slide)

1. **Title.** Planetary Twin AI — finding the Moon and Mars on Earth. Team Space Logistics:
   Adriana Ferrandino, Guillermo Pablo Sardón, Susana Cardozo. Challenge: Identify Earth
   Locations that Analog the Permanent Moon Base Locations and Mars.
2. **The problem.** Analog campaigns reuse a few famous sites; many terrestrial analogs are
   not well characterized; landing sites and permanent bases need different things.
3. **The tool.** Screenshot: body, mission type, target, characteristic chips, ranked map.
4. **How it works.** Global 0.25° grid; eight characteristics with explicit comparison
   rules; weighted geometric mean; known analogs held out for validation.
5. **Open data.** NASA MODIS, LOLA, Diviner, LROC, MOLA, TES; Copernicus DEM; TerraClimate
   and others (logos not allowed: use names only).
6. **A new candidate.** One characterization card: what it reproduces, what it cannot, which
   activities it supports; landing versus base comparison.
7. **Results and next steps.** Validation: McMurdo, Svalbard and Devon Island in the top 3–8% of all land for a lunar base, found without being told; limits, future work: finer
   grid, field checks with partners, more targets.

## 3. Live demo for the local jury: 2 minutes

1. (15 s) The challenge in one sentence, and why "landing" and "base" are different questions.
2. (30 s) Moon, Landing site, target Malapert Massif: default characteristics, top 10 on the
   map. Open the first candidate card: scores, activities, "what Earth cannot reproduce".
3. (25 s) Add "Ice and Polar" and remove "Surface Optics": the ranking changes live.
4. (25 s) Compare both: landing and base side by side; point at a site that ranks in both.
5. (15 s) Switch to Mars, Permanent base, Arcadia Planitia: different places come up.
6. (10 s) Point at the validation badge: known analog sites (McMurdo, Svalbard, Lanzarote)
   rank in the top few percent of all 337,611 land cells, found without being told.

Backup: if the network fails, run `yarn preview` in `frontend/` on the laptop; the data is
local.
