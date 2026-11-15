---
trigger: always_on
---

# Working in Antigravity (adapter for the phase files)

This repository was planned for IBM Bob. The phase files in `docs/prompts/` mention Bob
modes (Space Apps Orchestrator, Science Reviewer, Plan, Agent), subtasks and subagents.
In Antigravity:

- Use Planning mode for every phase. Do the work yourself, sequentially. Ignore
  instructions to spawn subagents, create subtasks or switch modes.
- Roles: you implement and test. An external analyst (Claude) reviews. The
  science-reviewer step is replaced by a handoff: at the end of each phase write
  `docs/reviews/handoff-phase-N.md` with what was built, the commands run, test results,
  the numbers produced (row counts, value ranges, top results) and open doubts. Then
  commit, push and STOP until the user brings the analyst's review.
- Never change `docs/METHODOLOGY.md`, `config/` or `contracts/` without explicit approval
  in the chat. Propose those changes in the handoff instead.
- Python only from `.venv` (Windows: `.venv\Scripts\python`). Frontend: yarn only.
- Earth Engine: read the project from `EE_PROJECT` in `.env`. Never hardcode it and never
  commit `.env`.
- Never present data as real if the script that produces it did not run. After every
  data step, report row counts, null counts and value ranges per column.
- At the end of every phase: update `docs/ESTADO.md`, commit with the phase name, then
  `git push origin main`.
- Everything you write in the repository is in English.
