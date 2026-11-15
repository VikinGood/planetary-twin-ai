"""
cache_interpretations.py — Pre-generate AI interpretations for the dashboard.

AI use disclosure: portions generated with AI (Claude); reviewed by the team.

For each preset (moon_landing, moon_base, mars_landing, mars_base) and each reference target,
ranks the exported cells with the preset's default characteristics (same rules as the
dashboard), takes the top N, and asks the LLM for an interpretation. An answer is written
only if it passes the JSON schema and the number checker (no number that is not in the
input). The demo then never calls the LLM live.

Output: frontend/public/data/interpretations/{preset}/{target_id}/{cell_id}.json

Usage (from the repository root, .venv active, after scripts/export_static.py):
    python scripts/cache_interpretations.py --top 5
    python scripts/cache_interpretations.py --top 3 --presets moon_landing,mars_base

Needs GROQ_API_KEY (and optionally GROQ_MODEL) in .env. Without a key it does nothing.
Groq free-tier limits are small: keep --top low and leave --delay at 2.5 s or more.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from backend.analyst.analyst import build_result, interpret, rank_features  # noqa: E402
from backend.analyst.provider import get_analyst_provider  # noqa: E402
from backend.llm_provider import NoLLMProvider  # noqa: E402

DATA = ROOT / "frontend" / "public" / "data"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5, help="candidates per target (default 5)")
    ap.add_argument("--presets", default="moon_landing,moon_base,mars_landing,mars_base")
    ap.add_argument("--delay", type=float, default=2.5, help="seconds between LLM calls")
    ap.add_argument("--overwrite", action="store_true", help="regenerate existing files")
    args = ap.parse_args()

    provider = get_analyst_provider()
    if isinstance(provider, NoLLMProvider):
        print("GROQ_API_KEY is not set: nothing to do. The dashboard will show 'not available'.")
        return 0

    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    if meta.get("mock"):
        print("WARNING: meta.json is MOCK data. Run scripts/export_static.py first.")
    char_names = {c["id"]: c["name"] for c in meta["characteristics"]}
    written = failed = skipped = 0
    failures = []

    for key in [k.strip() for k in args.presets.split(",") if k.strip()]:
        preset = meta["presets"][key]
        features = json.loads((DATA / f"{key}.json").read_text(encoding="utf-8"))["features"]
        selected = preset["default_characteristics"]
        weights = preset["default_weights"]
        cannot = meta.get("cannot_reproduce", {}).get(preset["body"], [])
        for target in preset["targets"]:
            for total, _cov, _parts, feature in rank_features(features, target["id"], selected, weights, limit=args.top):
                cell = feature["properties"]["cell_id"]
                out = DATA / "interpretations" / key / target["id"] / f"{cell}.json"
                if out.exists() and not args.overwrite:
                    skipped += 1
                    continue
                result = build_result(feature, preset, target, selected, weights, cannot, char_names)
                interp, problems = asyncio.run(interpret(result, provider))
                if interp is None:
                    failed += 1
                    failures.append(f"{key}/{target['id']}/{cell}: {problems}")
                else:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(interp, ensure_ascii=False, indent=1), encoding="utf-8")
                    written += 1
                print(f"{key} {target['id']} {cell} score={total:.3f} -> {'ok' if interp else 'rejected'}")
                time.sleep(args.delay)

    print(f"\nWritten {written}, rejected {failed}, skipped {skipped}.")
    for line in failures[:20]:
        print("  rejected:", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
