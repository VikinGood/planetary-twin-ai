# Phase 1 — Scientific methodology (no code)

Mode: Plan. Runs alone. Suggested owner: Adriana, with Ramiro (GIS) reviewing.

## Before you start
Read `AGENTS.md` (the official challenge text and the characteristic catalog) and
`docs/ESTADO.md`.

## Deliverables
1. `docs/METHODOLOGY.md`, at most three pages, covering:
   - For each of the eight characteristics: the variables, units, and the comparison rule,
     chosen among:
     - **Absolute:** same units on both bodies (slope in degrees at a common baseline, since
       LOLA, MOLA and Earth DEMs have different resolutions).
     - **Requirement:** when the Moon or Mars is extreme everywhere (aridity: "as arid as
       possible on Earth").
     - **Percentile or regime:** when absolute values cannot exist on Earth (lunar and
       Martian temperatures; say so explicitly).
     - **Categorical:** lithology classes and environment presence (basaltic volcanic,
       evaporite, permafrost, pits or lava tubes nearby).
   - How each characteristic score in [0, 1] is computed, per body and per target.
   - Combination: weighted geometric mean over the SELECTED characteristics only.
   - The two mission types and why their default selections and weights differ:
     landing site (safe descent and surface access) vs permanent base (resources, shelter,
     thermal and light regime, construction, long-duration operations).
   - Environment-family tag rules: desert, polar, volcanic, arid, cave.
   - Characterization: what each candidate card states (analog for what, not analog for
     what, which activities can be tested there for a landing or a base).
   - Confidence: data resolution, gaps, distance to valid data, rule type used.
   - Known analogs: exclusion buffer for "new candidates" and how blind validation works.
   - What Earth cannot reproduce, per body.
   - Limitations and assumptions.
2. `config/characteristics.json`: id, name, description, variables, units, comparison rule,
   and which bodies support it.
3. Four presets in `config/missions/`: `moon-landing.json`, `moon-base.json`,
   `mars-landing.json`, `mars-base.json`. Each lists reference targets (with coordinates),
   default selected characteristics and default weights (summing to 1 over the selection).

## How to split the work
Optionally spawn one `explore` or `general` subagent per body (Moon, Mars) to draft the
target list with coordinates; you write the final documents.

## Done when
- Every characteristic has a rule, units and a justification for both bodies, or is marked
  as not applicable for one body.
- The four presets differ in a way the document explains.
- The document names what the score does NOT capture.

## Close the phase
Update `docs/ESTADO.md` (decisions), commit `phase 1: methodology`, STOP and report.
