# Phase 7 — Submission package (Space Apps Project Submission Guide)

Mode: Agent. Runs alone. Suggested owner: Adriana with Guillermo.
Changes only documentation, metadata and deployment. No new features. English only.

## Before you start
Read `AGENTS.md`, `docs/ESTADO.md`, `docs/METHODOLOGY.md`, `docs/DATASETS.md` and
`docs/VALIDATION.md`.

## Deliverables
1. `README.md`: the challenge it answers (quote the official text in one line), what the
   tool does (Moon or Mars, landing site or permanent base, any combination of
   characteristics, whole-planet search), how it works, screenshots, how to run, data
   sources, licenses, validation results, limitations, future work, and a section
   "Use of Artificial Intelligence" listing which tools were used and for what (IBM Bob for
   code generation, a Groq-hosted LLM for interpretations, any other).
2. A header comment in every AI-generated source file: "Portions generated with IBM Bob
   (AI); reviewed by the team."
3. `docs/SUBMISSION.md` with ready-to-paste text for each field of the project page:
   - Project Name
   - High-Level Project Summary (what, how it addresses the challenge, why it matters)
   - Link to Project Demo (placeholder for the YouTube link)
   - Link to Final Project (GitHub Pages URL and repository)
   - Detailed Project Description (what it does, how it works, benefits, goals, tools)
   - NASA Data (each NASA dataset and how it was used)
   - Space Agency Partner & Other Data (all other data, code and tools, with licenses)
   - Use of Artificial Intelligence
   - References (every external resource, including open-source libraries and images)
4. `docs/DEMO.md`:
   - 30-second video script: 0:00 who we are, 0:02 the challenge, 0:05 title and tagline,
     0:10 the dashboard switching Moon/Mars and landing/base with NASA data, 0:20 a new
     analog found and what it can test, plus `docs/demo_subtitles_en.srt` timed to it.
   - Fallback: outline for at most 7 slides including the title slide.
   - 2-minute live demo script for the local jury, showing "Compare both".
5. GitHub Pages deployment working from the static export; test the URL in a private window.
6. A final checklist in `docs/SUBMISSION.md`: video at most 30 s or at most 7 slides,
   English subtitles, public links without login, NASA data listed, AI use disclosed,
   no NASA logos, no minors, every field filled.

## Done when
- Every field in `docs/SUBMISSION.md` is filled except the demo link.
- The public site loads in a private window.

## Close the phase
Update `docs/ESTADO.md`, commit `phase 7: submission package`, STOP and report.
