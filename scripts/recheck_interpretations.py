"""
recheck_interpretations.py — Re-run the deterministic checks on cached AI interpretations.

AI use disclosure: portions generated with AI (Claude); reviewed by the team.

No LLM calls. For every cached file it rebuilds the input from the current export, rewrites
numbers spelled in words with digits ("minus twenty-eight point six" -> "-28.6"), and runs
the schema and number checks again. Files that pass are rewritten; files that fail, or whose
cell is no longer in the export, are deleted so the dashboard never shows an unchecked text.

Usage (repository root): python scripts/recheck_interpretations.py [--dry-run]
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.analyst.analyst import build_result, check, clean  # noqa: E402

DATA = ROOT / "frontend" / "public" / "data"
meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
names = {c["id"]: c["name"] for c in meta["characteristics"]}
DRY = "--dry-run" in sys.argv
kept = removed = 0
for key, preset in meta["presets"].items():
    folder = DATA / "interpretations" / key
    if not folder.exists():
        continue
    feats = {f["properties"]["cell_id"]: f for f in json.loads((DATA / f"{key}.json").read_text(encoding="utf-8"))["features"]}
    targets = {t["id"]: t for t in preset["targets"]}
    cannot = meta.get("cannot_reproduce", {}).get(preset["body"], [])
    for path in sorted(folder.glob("*/*.json")):
        tid, cell = path.parent.name, path.stem
        if tid not in targets or cell not in feats:
            (None if DRY else path.unlink()); removed += 1; print("removed (not in export):", key, tid, cell); continue
        result = build_result(feats[cell], preset, targets[tid], preset["default_characteristics"], preset["default_weights"], cannot, names)
        old = json.loads(path.read_text(encoding="utf-8"))
        new = clean(old, result)
        problems = check(new, result)
        if problems:
            (None if DRY else path.unlink()); removed += 1; print("removed:", key, tid, cell, problems)
        elif not DRY:
            path.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        if not problems:
            kept += 1
print(f"kept {kept}, removed {removed}")
