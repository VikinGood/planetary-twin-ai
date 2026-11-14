# How to use this package with IBM Bob

Based on Gustavo's prompt, split into phases and aligned with the official challenge text.

## Install (5 minutes)

1. Copy everything in this folder to the repository root (including the hidden `.bob/`
   folder) and commit. If the repo has the earlier package, delete the old Spanish phase
   files in `docs/prompts/` first.
2. Open the repository in Bob. Bob loads `AGENTS.md` and the modes in
   `.bob/custom_modes.yaml` on its own.
3. Choose the **🛰️ Space Apps Orchestrator** mode.
   - New start: paste `docs/prompts/00-kickoff-orchestrator.md`.
   - Already started: paste `docs/prompts/UPDATE-2026-11-14-scope.md`.
4. For each later phase, tell the orchestrator: "run Phase N".

If the mode does not appear, check Settings → Modes → Edit Project Modes.

## What the tool does

- The user picks the **body** (Moon or Mars), the **mission type** (landing site or
  permanent base, or "Compare both") and **one or several characteristics**: topography,
  geology, thermal, aridity, ice and polar, volcanic and caves, surface optics, illumination.
- The engine searches the **whole planet** and ranks Earth locations; each candidate gets a
  characterization card and environment tags from the challenge (desert, polar, volcanic,
  arid, cave).
- Known analogs are excluded from "new candidates" but used to validate the engine.

## Why phases instead of one long prompt

- **Rules live in files.** `AGENTS.md` loads in every task, so principles are not lost as
  the conversation grows.
- **State lives in `docs/ESTADO.md`.** Every phase reads it first and updates it last.
  If Bob gets lost, start a new task and it resumes from there.
- **Short phase files** with deliverables, how to split the work, "Done when" and a
  mandatory stop.
- **Subtasks and subagents.** Bob has `explore` (read-only) and `general` (writes files)
  subagents, each with its own context, and subtasks with their own thread. Subagents do
  not see the chat, so every hand-off tells them to read `AGENTS.md` and `ESTADO.md`. Bob
  only uses subagents when asked, and each spawn is approved before it starts.
- **Independent reviewer.** The 🔬 Science Reviewer mode reviews each phase and cannot
  edit code.

## Order and parallelism

1. Phases 0, 1 and 2 in sequence: method, data and contracts.
2. Phases 3, 4 and 5 in parallel: backend, AI analyst and dashboard, each in its own folder,
   against the sample JSON in `contracts/`. Three orchestrator subtasks or three Bob
   sessions, one per person.
3. Phase 6: validation before Sunday 11:00.
4. Phase 7: submission package.

## Accounts the team needs

- Google Earth Engine, registered for non-commercial use (Earth side, global processing).
- NASA Earthdata login, only if downloading MODIS files outside Earth Engine.
- Groq API key, optional (without it the app shows data and scores only).
- Nothing for USGS Astrogeology, PDS, LROC or Copernicus DEM on AWS: open downloads.
