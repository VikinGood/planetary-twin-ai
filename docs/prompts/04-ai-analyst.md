# Phase 4 — AI Scientific Analyst

Mode: Agent. Runs in parallel with Phases 3 and 5. Suggested owner: Guillermo or Susana.
Writes only in `backend/analyst/`, `backend/tests/test_analyst*.py` and
`scripts/cache_interpretations.py`.
Works against `contracts/similarity_result.sample.json` until Phase 3 delivers real data.

## Before you start
Read `AGENTS.md`, `docs/ESTADO.md` and the files in `contracts/`.

## Deliverables
- `LLMProvider` interface, `GroqProvider` (reads `GROQ_API_KEY` and `GROQ_MODEL` from
  `.env`) and `NoLLMProvider` (returns interpretation marked "not available").
- Input: one SimilarityResult (body, mission type, target, selected characteristics).
  Output: JSON valid against `contracts/interpretation.schema.json`, in English, with:
  - why the location is a candidate analog for THIS mission type and body,
  - which characteristics make it a good analog and which do not,
  - what Earth cannot reproduce here,
  - activities that could be tested: for a landing site (descent imaging, hazard
    detection, landing pads, first mobility) or for a permanent base (habitat construction,
    ISRU water, shelter, power in extreme light, long-duration crew operations),
  - missing or low-confidence information.
- A deterministic checker (code, not an LLM) that rejects any output mentioning a number
  that is not in the input. On rejection, retry once, then fall back to `NoLLMProvider`.
- All output labeled "AI interpretation".
- `GET /candidates/{id}/interpretation?body=&mission_type=&target=`.
- `scripts/cache_interpretations.py`: pre-generates interpretations for the exported top
  candidates of the four presets into `frontend/public/data/interpretations/`, so the demo
  never calls the LLM live.
- Tests: schema validation, number checker, fallback without a key.

## Done when
- Tests pass with and without `GROQ_API_KEY`.
- The checker finds zero invented numbers on the sample.

## Close the phase
Update `docs/ESTADO.md`, commit `phase 4: AI analyst`, STOP and report.
