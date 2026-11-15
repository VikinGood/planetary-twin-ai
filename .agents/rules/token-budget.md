---
trigger: always_on
---

# Token budget (the quota is limited; follow these on every turn)

Heavy data must never pass through the conversation. Scripts process data; you read
only short summaries.

- Never open or print raw data files (`.parquet`, `.tif`, `.nc`, `.csv` over 200 lines,
  large `.json`). Inspect them with a script that prints shape, columns, null counts,
  min/max per column and at most 5 sample rows.
- Run long scripts with output redirected to a log file in `logs/` (gitignored), then
  show only the last 30 lines: `... > logs/<step>.log 2>&1` and `Get-Content -Tail 30`.
- Run tests quietly: `.venv\Scripts\python -m pytest -q`. On failure, show only the
  failing test and its traceback.
- Develop and test on a small fixture first (one region of about 5 x 5 degrees, or a
  sample of 2,000 cells). Run the global job only once the fixture output is correct.
- Earth Engine: do the reductions on the server (`reduceRegions`, exports) and download
  only the final 0.25 degree table. Never pull full-resolution rasters to the machine.
- Do not re-read long documents you already read in this conversation; re-read only the
  section you need.
- Start a new conversation for each phase. Before starting, read `docs/ESTADO.md` and the
  latest `docs/reviews/handoff-phase-*.md` instead of relying on chat history.
- Prefer the faster model for routine edits, running scripts and fixing tests. Use the
  strongest model only for design decisions or hard bugs.
