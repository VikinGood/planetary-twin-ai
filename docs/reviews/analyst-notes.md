# Analyst notes (Claude)

Findings from reviewing the repository while Phase 3 runs. Apply when convenient; none of
these blocks the current step.

1. **Lava-tube proxy includes lava domes.** `config/characteristics.json` lists
   "Lava dome(s)" among the qualifying Holocene volcano types. Lava tubes form in fluid,
   low-viscosity basaltic flows (shield volcanoes, fissure vents, volcanic fields); domes are
   built by viscous lava and do not produce tubes. Remove "Lava dome(s)" from the qualifying
   types and from the 06_volcanic_caves.py filter. (Changing `config/` needs the user's
   approval in the chat.)
2. **Moon and Mars target values come from the literature**, not from data extraction. This
   is acceptable for the hackathon only if every value cites its source and the dashboard
   says so (it does: "reference values compiled from the literature"). Keep
   `docs/SUBMISSION.md` consistent with what was actually done.
3. **Submission drafts are ready**: `docs/SUBMISSION.md` (every form field), `docs/DEMO.md`
   (30-second video, 7-slide fallback, 2-minute live demo) and `docs/demo_subtitles_en.srt`.
   Fill the `[TO CONFIRM ...]` items in Phase 7 with the final numbers.
