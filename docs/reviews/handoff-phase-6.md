# Handoff — Phase 6 (Validation)

Run by Claude (analyst role) on commit 3a48975. Full numbers: `docs/VALIDATION_REPORT.md`.
Reproduce: `.venv\Scripts\python scripts/validate_phase6.py` (also writes
`frontend/public/data/validation.json`, used by the dashboard badge).

## Results

| Check | Result | Verdict |
| --- | --- | --- |
| Integrity: values with units and source, scores in (0, 1] or -1 | 0 problems in 4,360 cells | Pass |
| Landing vs base contrast (top 10 distinct places) | 0 shared places, Moon and Mars | Pass: the two missions select different terrain |
| Stability, each weight +-20 % | Mean Jaccard 0.81–0.97; worst 0.43 (Moon landing, surface optics x0.8) | Pass, Moon landing is the most sensitive |
| Known-analog recall, inside the export | 0 in top 10 % | Not meaningful: the export is pre-selected (top 300 per target), and known cells were added on top, so they rank below by construction |
| Known-analog recall, all 337,611 land cells | Moon base (Shackleton): McMurdo top 3 %, Svalbard top 6 %, Haughton top 8 %. Mars landing: Lanzarote top 5–9 %, Rio Tinto top 9–19 %, SP Crater, MDRS top 16–19 %. Mars base (Arsia): McMurdo top 1 % | Pass for bases (polar sites) and Mars landing (desert/volcanic sites); weak for Moon landing |
| Target discrimination | Moon landing: the 9 Artemis III regions have identical scores (same published reference values) | Shown honestly in the dashboard (note under the target selector) |
| Environment families in top 50 | Every preset reaches 3+ families; Mars landing 14 countries/areas | Pass |

Single-characteristic check: Atacama (Yungay) is top 0.5 % for aridity and Haughton top 5 % for
ice and polar, as expected. Atacama ranks lower in the combined presets because its thermal
regime is far from Mars; this is a defensible result and a good demo point.

## Dashboard changes (Claude)

- The badge now reads `validation.json` (full-population percentiles, default weights) instead
  of the in-export top-100 count, which always showed 0.
- A note appears when all targets of a preset produce the same ranking.
- `targetsAreEquivalent()` in `scoring.mjs`, with a test. Frontend tests: 11 pass. Build OK.

## Open items for Antigravity (small)

1. Verify every `source_url` in `data/reference/known_analogs.csv` opens (HTTP 200); replace any
   that do not with the program's real page. Several look guessed.
2. Region names: spot-check `E_+80.625_+46.875` (Franz Josef Land, labeled Nenetskiy Okrug).
   If GAUL nearest-match is used, use point-in-polygon only and fall back to "Unnamed area".
3. In `process_preset` step 1, null scores are floored to 0.01 instead of being skipped as in
   the dashboard (null lowers coverage). Align it so selection and ranking agree.
4. McMurdo Dry Valleys is only at the 57th percentile for aridity: TerraClimate at 4 km likely
   overestimates precipitation there. Note it in LIMITATIONS rather than changing the method.
