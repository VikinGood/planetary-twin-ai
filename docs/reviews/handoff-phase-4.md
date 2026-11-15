# Handoff — Phase 4 (AI Scientific Analyst)

Built by Claude (analyst role) in new files only; nothing existing was modified.

## What was built

| File | Purpose |
| --- | --- |
| `backend/analyst/checker.py` | Deterministic number checker. Every number in the input (scores, values, coordinates, numbers inside strings such as "1/6 g") is allowed, also rounded or as a percentage; any other number in the text fields is reported as invented. Ignores dataset codes like MOD11A2. |
| `backend/analyst/schema.py` | Validator for `contracts/interpretation.schema.json` without new dependencies. |
| `backend/analyst/analyst.py` | Ranking identical to the dashboard (weighted geometric mean, null lowers coverage, 3 degree separation), `build_result()` from an exported feature, `clean()` (schema fields only, null highlights dropped, fixed disclosure), `interpret()` with one retry; returns None when no valid answer. |
| `backend/analyst/provider.py` | `AnalystGroqProvider`, extends `GroqProvider` with a stricter prompt: measured values included, candidate activities per mission type, "only use numbers in the data". Default model `openai/gpt-oss-120b` unless `GROQ_MODEL` is set. |
| `scripts/cache_interpretations.py` | For each preset and target: top N with the default characteristics, interpretation, checks, writes `frontend/public/data/interpretations/{preset}/{target_id}/{cell_id}.json`. Writes nothing without `GROQ_API_KEY` or when an answer fails the checks. |
| `backend/tests/test_analyst.py` | 10 tests, no network: checker, schema, geometric mean, ranking, retry then accept, reject after retry, no-LLM path, prompt content. |

## Checks run

- `pytest -q backend/tests/test_analyst.py`: 10 passed.
- Dry run of the cache script on MOCK data with a fake provider that invents a number in
  every third answer: 22 written, invented answers rejected and retried, files pass the
  schema. The dashboard card shows them in the "AI interpretation" block. The fake files
  were deleted and are not committed.

## How to run (after the real export)

```
.venv\Scripts\python -m pytest -q backend/tests/test_analyst.py
.venv\Scripts\python scripts/cache_interpretations.py --top 3
```

`.env` needs `GROQ_API_KEY` (free key at console.groq.com). Groq's free limits are small
(for gpt-oss-120b about 8,000 tokens per minute and 200,000 per day): 16 targets x 3
candidates = 48 calls is a safe first run. Commit the generated JSON files.

## Notes for Antigravity

- Add `httpx` to `backend/requirements.txt` if it is not installed (GroqProvider needs it).
- The existing `POST /interpret` endpoint keeps working; the dashboard uses the cached files.
- Interpretations are written for each preset's default characteristics; the card says so.
