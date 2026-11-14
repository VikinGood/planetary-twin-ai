# Project state (single source of truth)

Every task reads this file first and updates it last. Keep entries short. English only.

## Phases

| Phase | File | Mode | Status | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 Setup | 00-kickoff-orchestrator.md | Space Apps Orchestrator | pending | Guillermo | |
| 1 Methodology | 01-methodology.md | Plan | pending | | |
| 2 Data and architecture | 02-data-architecture.md | Plan | pending | | |
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

## Contracts (files other phases depend on)

- `config/characteristics.json`: produced in Phase 1.
- `config/missions/*.json` (four presets: moon-landing, moon-base, mars-landing, mars-base):
  produced in Phase 1.
- `contracts/similarity_result.sample.json`: produced in Phase 2.
- `contracts/interpretation.schema.json`: produced in Phase 2.

## Open questions for the team

-

## Known issues

-
