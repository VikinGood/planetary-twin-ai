# Phase 0 — Kickoff (paste this in the "Space Apps Orchestrator" mode)

You are the orchestrator for this repository. Do not write application code.

1. Read `AGENTS.md` (especially the official challenge text), `docs/ESTADO.md` and list the
   files in `docs/prompts/`.
2. Create a todo list with one item per phase (1 to 7), in the order of `docs/ESTADO.md`.
3. Check the repository: it must have `.gitignore` (with `.venv/`, `node_modules/`, `.env`,
   `data/raw/`), a `LICENSE` (MIT) and a `README.md` stub in English. Create a subtask in
   Agent mode to add whatever is missing, then commit `phase 0: setup`.
4. Mark Phase 0 as approved in `docs/ESTADO.md`.
5. STOP. Tell me the phase order, which phases can run in parallel (3, 4 and 5 after Phase 2
   is approved) and ask me to start Phase 1.

## How to run every later phase

When I say "run Phase N":
1. Read the phase file in `docs/prompts/` that starts with `0N-`. It says which mode to use
   and how to split the work.
2. For each piece of work, create a subtask (or a subagent for read-only research) with a
   self-contained description: the phase file path, "read AGENTS.md and docs/ESTADO.md
   first", the exact files to produce and the acceptance checks.
3. When the pieces return, check them against the phase's "Done when" list.
4. Create a subtask in `science-reviewer` mode to review the phase.
5. Update `docs/ESTADO.md`, commit, and STOP with: delivered, missing, question for me.
