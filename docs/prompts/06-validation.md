# Phase 6 — Integration and validation

Mode: start in `science-reviewer`, fixes in Agent. Runs alone. Suggested owner: Susana.
Must finish before Sunday 11:00 (code freeze).

## Before you start
Read `AGENTS.md`, `docs/ESTADO.md`, `docs/METHODOLOGY.md` and the reviews in `docs/reviews/`.

## How to split the work
1. Review subtask (`science-reviewer`) checks, and writes `docs/reviews/phase-6.md`:
   - **Blind validation**, per preset: with `exclude_known=false`, how many known analogs
     land in the top-N (for example, do Moon presets find Hawaiian or Icelandic volcanic
     fields and Antarctic dry valleys; do Mars presets find Atacama, Devon Island or
     Svalbard). Report the numbers honestly, even if low.
   - **Mission-type contrast:** how many top-10 sites differ between landing and base for
     the same body. If almost none, the presets are not doing their job.
   - **Rank stability:** each weight changed by ±20%; how many top-10 sites stay.
   - **Challenge coverage:** at least one new candidate tagged in each family (desert,
     polar, volcanic, arid, cave) across the four presets, or a stated reason why not.
   - **Traceability:** pick three candidates and trace every displayed number to its source.
   - **End to end:** static site from the real export, with cached interpretations.
2. Fix subtask (Agent): fix only the blocking defects from the review.
3. Write `docs/VALIDATION.md`: method and results, for the README and the pitch.

## Done when
- No blocking defects left.
- `docs/VALIDATION.md` states recall, contrast, stability and family coverage with numbers.

## Close the phase
Update `docs/ESTADO.md`, commit `phase 6: validation`, tag `code-freeze`, STOP and report.
