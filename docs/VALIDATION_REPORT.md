# Phase 6 validation report

Data: `frontend/public/data` (mock=False, generated 2026-11-15T04:28:17.063688+00:00).

## 1. Known-analog recall (default characteristics, known analogs not excluded)

| Preset | Target | Known cells | Best known rank | Median percentile | In top 10% |
|---|---|---|---|---|---|
| moon_landing | peak_near_cabeus_b | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | haworth | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | malapert_massif | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | mons_mouton_plateau | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | mons_mouton | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | nobile_rim_1 | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | nobile_rim_2 | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | de_gerlache_rim_2 | 113 | 302 of 755 | 20 | 0/111 |
| moon_landing | slater_plain | 113 | 302 of 755 | 20 | 0/111 |
| moon_base | shackleton_de_gerlache_ridge | 113 | 474 of 1323 | 17 | 0/111 |
| moon_base | marius_hills_pit | 113 | 434 of 1323 | 11 | 0/111 |
| mars_landing | jezero_crater | 113 | 474 of 1074 | 34 | 0/111 |
| mars_landing | gale_crater | 113 | 477 of 1074 | 34 | 0/111 |
| mars_landing | meridiani_planum | 113 | 472 of 1074 | 34 | 0/111 |
| mars_base | arcadia_planitia | 113 | 459 of 1173 | 10 | 0/111 |
| mars_base | arsia_mons_cave_candidate | 113 | 409 of 1173 | 11 | 0/111 |

Known analogs present in the export: 12 of 12: Atacama Desert (Yungay), Craters of the Moon (Idaho), Haughton Crater (Devon Island), Kilauea Volcano, Lanzarote (PANGAEA), Mars Desert Research Station (Utah), Mauna Kea / Mauna Loa (HI-SEAS), McMurdo Dry Valleys, Ries Crater, Rio Tinto, SP Crater / Black Point Lava Flow (AZ), Svalbard (AMASE / Bockfjord).

## 2. Landing vs base contrast (top 10 distinct places, first target of each)

- Moon: shared places 0 of 10; Jaccard 0.00.
- Mars: shared places 0 of 10; Jaccard 0.00.

## 3. Stability: each weight +-20 %, top 10 distinct places

| Preset | Target | Min Jaccard | Mean Jaccard | Most sensitive weight |
|---|---|---|---|---|
| moon_landing | peak_near_cabeus_b | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | haworth | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | malapert_massif | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | mons_mouton_plateau | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | mons_mouton | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | nobile_rim_1 | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | nobile_rim_2 | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | de_gerlache_rim_2 | 0.43 | 0.81 | surface_optics x0.8 |
| moon_landing | slater_plain | 0.43 | 0.81 | surface_optics x0.8 |
| moon_base | shackleton_de_gerlache_ridge | 0.82 | 0.97 | topography x1.2 |
| moon_base | marius_hills_pit | 0.82 | 0.92 | ice_polar x0.8 |
| mars_landing | jezero_crater | 0.82 | 0.95 | surface_optics x0.8 |
| mars_landing | gale_crater | 0.82 | 0.91 | aridity x0.8 |
| mars_landing | meridiani_planum | 0.82 | 0.95 | surface_optics x0.8 |
| mars_base | arcadia_planitia | 0.67 | 0.88 | aridity x1.2 |
| mars_base | arsia_mons_cave_candidate | 0.67 | 0.87 | aridity x1.2 |

## 4. Target discrimination (same preset, top 10 distinct places)

- moon_landing: 9 targets; mean pairwise Jaccard 1.00; 100% of (cell, characteristic) scores are identical across targets.
- moon_base: 2 targets; mean pairwise Jaccard 0.00; 55% of (cell, characteristic) scores are identical across targets.
- mars_landing: 3 targets; mean pairwise Jaccard 0.43; 66% of (cell, characteristic) scores are identical across targets.
- mars_base: 2 targets; mean pairwise Jaccard 0.00; 73% of (cell, characteristic) scores are identical across targets.

## 5. Environment families in the top 50 (default, first target, 1 degree separation)

- moon_landing: {'polar': 45, 'arid': 36, 'ice sheet': 31, 'desert': 18, 'volcanic': 1, 'cave': 1}; 9 countries/areas.
- moon_base: {'polar': 49, 'volcanic': 26, 'ice sheet': 24, 'arid': 10, 'cave': 5, 'desert': 5, 'untagged': 1}; 8 countries/areas.
- mars_landing: {'arid': 50, 'desert': 49, 'polar': 9, 'ice sheet': 8, 'volcanic': 1, 'cave': 1}; 14 countries/areas.
- mars_base: {'polar': 50, 'arid': 24, 'volcanic': 18, 'desert': 12, 'ice sheet': 4, 'cave': 3}; 6 countries/areas.

## 6. Traceability and integrity

- moon_landing: 758 cells; values without units/source 0; scores out of range 0; hard caps 27; null 1%; unnamed region 29.
- moon_base: 1334 cells; values without units/source 0; scores out of range 0; hard caps 22; null 1%; unnamed region 35.
- mars_landing: 1087 cells; values without units/source 0; scores out of range 0; hard caps 39; null 1%; unnamed region 18.
- mars_base: 1182 cells; values without units/source 0; scores out of range 0; hard caps 18; null 1%; unnamed region 45.
## 7. Full-population recall (337,611 land cells, 12 known analog sites)

Percentile = share of all land cells that score lower than the best cell of the site. 90+ means top 10%.

| Preset | Target | Sites in top 10% | Sites in top 25% | Best sites (percentile) |
|---|---|---|---|---|
| moon_landing | peak_near_cabeus_b | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | haworth | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | malapert_massif | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | mons_mouton_plateau | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | mons_mouton | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | nobile_rim_1 | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | nobile_rim_2 | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | de_gerlache_rim_2 | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_landing | slater_plain | 1/12 | 3/12 | Lanzarote (PANGAEA) 95, Ries Crater 83, Rio Tinto 81 |
| moon_base | shackleton_de_gerlache_ridge | 3/12 | 3/12 | McMurdo Dry Valleys 97, Svalbard (AMASE / Bockfjord) 94, Haughton Crater (Devon Island) 92 |
| moon_base | marius_hills_pit | 0/12 | 1/12 | Haughton Crater (Devon Island) 85, McMurdo Dry Valleys 75, Svalbard (AMASE / Bockfjord) 70 |
| mars_landing | jezero_crater | 1/12 | 3/12 | Lanzarote (PANGAEA) 92, Rio Tinto 88, SP Crater / Black Point Lava Flow (AZ) 83 |
| mars_landing | gale_crater | 1/12 | 4/12 | Lanzarote (PANGAEA) 91, Mars Desert Research Station (Utah) 81, Rio Tinto 81 |
| mars_landing | meridiani_planum | 2/12 | 3/12 | Lanzarote (PANGAEA) 95, Rio Tinto 91, SP Crater / Black Point Lava Flow (AZ) 84 |
| mars_base | arcadia_planitia | 0/12 | 2/12 | McMurdo Dry Valleys 85, Haughton Crater (Devon Island) 83, Lanzarote (PANGAEA) 64 |
| mars_base | arsia_mons_cave_candidate | 1/12 | 1/12 | McMurdo Dry Valleys 99, Craters of the Moon (Idaho) 74, Haughton Crater (Devon Island) 74 |

