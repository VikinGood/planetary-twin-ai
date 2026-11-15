"""
validate_phase6.py - Phase 6 validation of the static export (read-only).

AI use disclosure: portions generated with AI (Claude); reviewed by the team.

Checks, per preset and target, with the preset's default characteristics and the same
scoring rules as the dashboard (weighted geometric mean, 0.01 floor, -1 drops the cell):
  1. Known-analog recall: rank percentile of known analog cells (not excluded).
  2. Landing vs base contrast: overlap of the top 10 distinct places, same body.
  3. Stability: each weight +-20 % (one at a time), Jaccard of the top 10 vs baseline.
  4. Target discrimination: do targets of the same preset produce different rankings?
  5. Environment family coverage in the top 50.
  6. Traceability: every value has units and source; scores in range; region hints.
  7. Full-population recall (needs data/processed/earth_cells_025deg.parquet): percentile of
     each known analog site (best cell within 0.5 deg) among ALL 0.25 deg land cells, so the
     result is not biased by the export selection. Writes frontend/public/data/validation.json
     for the dashboard badge.
Usage: python scripts/validate_phase6.py [data_dir]   -> writes docs/VALIDATION.md
"""
import json, math, sys, statistics
from pathlib import Path

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "frontend/public/data"
FLOOR = 0.01

def norm(sel, w):
    s = sum(max(0, w.get(c, 0)) for c in sel)
    return {c: (max(0, w.get(c, 0)) / s if s else 1 / len(sel)) for c in sel}

def score(p, t, sel, w):
    w = norm(sel, w); used = ls = 0.0
    for c in sel:
        v = (p["scores"].get(c) or {}).get(t)
        if isinstance(v, (int, float)) and math.isfinite(v):
            used += w[c]
            if v < 0: return 0.0, used
            ls += w[c] * math.log(min(1, max(FLOOR, v)))
    return (math.exp(ls / used) if used else None), used

def rank(fs, t, sel, w, sep=3.0, limit=10, exclude_known=True):
    rows = []
    for f in fs:
        p = f["properties"]
        if exclude_known and p["is_known_analog"]: continue
        s, cov = score(p, t, sel, w)
        if s is None or s <= 0: continue
        rows.append((s, cov, p))
    rows.sort(key=lambda r: (-r[0], -r[1]))
    if sep <= 0: return rows[:limit] if limit else rows
    kept = []
    for r in rows:
        if len(kept) >= limit: break
        if all(abs(r[2]["lat_center"] - k[2]["lat_center"]) >= sep or abs(r[2]["lon_center"] - k[2]["lon_center"]) >= sep for k in kept):
            kept.append(r)
    return kept

def places(top):  # 1-degree buckets, so neighbouring cells count as the same place
    return {(round(r[2]["lat_center"]), round(r[2]["lon_center"])) for r in top}

def jac(a, b): return len(a & b) / len(a | b) if a | b else 1.0

meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
data = {k: json.loads((DATA / f"{k}.json").read_text(encoding="utf-8"))["features"] for k in meta["presets"]}
out = []; P = out.append
P(f"# Phase 6 validation report\n\nData: `frontend/public/data` (mock={meta.get('mock')}, generated {meta.get('generated_at')}).\n")

P("## 1. Known-analog recall (default characteristics, known analogs not excluded)\n")
P("| Preset | Target | Known cells | Best known rank | Median percentile | In top 10% |\n|---|---|---|---|---|---|")
recall = {}
for k, pr in meta["presets"].items():
    fs = data[k]; sel, w = pr["default_characteristics"], pr["default_weights"]
    for t in pr["targets"]:
        allr = rank(fs, t["id"], sel, w, sep=0, limit=None, exclude_known=False)
        n = len(allr)
        pos = [i + 1 for i, r in enumerate(allr) if r[2]["is_known_analog"]]
        known = sum(1 for f in fs if f["properties"]["is_known_analog"])
        if not pos:
            P(f"| {k} | {t['id']} | {known} | - | - | - |"); continue
        pct = [100 * (1 - (p - 1) / n) for p in pos]
        top10 = sum(1 for p in pos if p <= 0.1 * n)
        recall[(k, t["id"])] = statistics.median(pct)
        P(f"| {k} | {t['id']} | {known} | {min(pos)} of {n} | {statistics.median(pct):.0f} | {top10}/{len(pos)} |")
names = sorted({f['properties']['known_analog_name'] for fs in data.values() for f in fs if f['properties']['is_known_analog']})
P(f"\nKnown analogs present in the export: {len(names)} of {len(meta.get('known_analogs', []))}: {', '.join(names)}.\n")

P("## 2. Landing vs base contrast (top 10 distinct places, first target of each)\n")
for body in ("moon", "mars"):
    a, b = f"{body}_landing", f"{body}_base"
    ta = rank(data[a], meta["presets"][a]["targets"][0]["id"], meta["presets"][a]["default_characteristics"], meta["presets"][a]["default_weights"])
    tb = rank(data[b], meta["presets"][b]["targets"][0]["id"], meta["presets"][b]["default_characteristics"], meta["presets"][b]["default_weights"])
    P(f"- {body.title()}: shared places {len(places(ta) & places(tb))} of 10; Jaccard {jac(places(ta), places(tb)):.2f}.")
P("")

P("## 3. Stability: each weight +-20 %, top 10 distinct places\n")
P("| Preset | Target | Min Jaccard | Mean Jaccard | Most sensitive weight |\n|---|---|---|---|---|")
for k, pr in meta["presets"].items():
    sel, w = pr["default_characteristics"], pr["default_weights"]
    for t in pr["targets"]:
        base = places(rank(data[k], t["id"], sel, w))
        js = []
        for c in sel:
            for f in (0.8, 1.2):
                w2 = dict(w); w2[c] = w[c] * f
                js.append((jac(base, places(rank(data[k], t["id"], sel, w2))), f"{c} x{f}"))
        mn = min(js)
        P(f"| {k} | {t['id']} | {mn[0]:.2f} | {statistics.mean(j for j, _ in js):.2f} | {mn[1]} |")
P("")

P("## 4. Target discrimination (same preset, top 10 distinct places)\n")
for k, pr in meta["presets"].items():
    sel, w = pr["default_characteristics"], pr["default_weights"]
    tops = {t["id"]: places(rank(data[k], t["id"], sel, w)) for t in pr["targets"]}
    ids = list(tops)
    pairs = [jac(tops[i], tops[j]) for x, i in enumerate(ids) for j in ids[x + 1:]]
    ident = 0; total = 0
    for f in data[k]:
        for c, byt in f["properties"]["scores"].items():
            vals = {v for v in byt.values() if v is not None}
            total += 1; ident += len(vals) <= 1
    P(f"- {k}: {len(ids)} targets; mean pairwise Jaccard {statistics.mean(pairs) if pairs else 1:.2f}; "
      f"{100 * ident / total:.0f}% of (cell, characteristic) scores are identical across targets.")
P("")

P("## 5. Environment families in the top 50 (default, first target, 1 degree separation)\n")
for k, pr in meta["presets"].items():
    top = rank(data[k], pr["targets"][0]["id"], pr["default_characteristics"], pr["default_weights"], sep=1.0, limit=50)
    fam = {}
    for r in top:
        for tg in r[2]["environment_tags"] or ["untagged"]: fam[tg] = fam.get(tg, 0) + 1
    countries = {r[2]["region_hint"].split(", ")[-1] for r in top}
    P(f"- {k}: {dict(sorted(fam.items(), key=lambda x: -x[1]))}; {len(countries)} countries/areas.")
P("")

P("## 6. Traceability and integrity\n")
for k in meta["presets"]:
    fs = data[k]; bad_val = bad_score = hard = nulls = unnamed = 0; cells = 0
    for f in fs:
        p = f["properties"]
        unnamed += p["region_hint"].startswith("Unnamed")
        for v in p["values"].values():
            if v.get("value") is not None and (not v.get("units") or not v.get("source")): bad_val += 1
        for byt in p["scores"].values():
            for v in byt.values():
                cells += 1
                if v is None: nulls += 1
                elif v == -1: hard += 1
                elif not (0 < v <= 1): bad_score += 1
    P(f"- {k}: {len(fs)} cells; values without units/source {bad_val}; scores out of range {bad_score}; "
      f"hard caps {hard}; null {100 * nulls / cells:.0f}%; unnamed region {unnamed}.")

def full_population(P):
    root = Path(__file__).resolve().parents[1]
    pq = root / "data/processed/earth_cells_025deg.parquet"
    if not pq.exists():
        P("## 7. Full-population recall\n\nSkipped: parquet not found.\n"); return None
    import numpy as np, pandas as pd
    sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "scripts"))
    import export_static as E
    df = pd.read_parquet(pq)
    known = pd.read_csv(root / "data/reference/known_analogs.csv")
    tdict = json.loads((root / "data/processed/targets.json").read_text(encoding="utf-8"))["targets"]
    fl = lambda a: np.array([np.nan if x is None else float(x) for x in a], dtype=float)
    site_cells = []
    for _, k in known.iterrows():
        d = np.hypot(df.lat_center.values - k.lat, df.lon_center.values - k.lon)
        site_cells.append((k["name"], d < 0.5))
    result = {"land_cells": int(len(df)), "sites": int(len(known)),
              "method": "Percentile of each known analog site (best 0.25 deg cell within 0.5 deg) among all land cells, preset default characteristics and weights.",
              "presets": {}}
    P(f"## 7. Full-population recall ({len(df):,} land cells, {len(known)} known analog sites)\n")
    P("Percentile = share of all land cells that score lower than the best cell of the site. 90+ means top 10%.\n")
    P("| Preset | Target | Sites in top 10% | Sites in top 25% | Best sites (percentile) |\n|---|---|---|---|---|")
    for key, pr in meta["presets"].items():
        body, mt = key.split("_"); sel = pr["default_characteristics"]; w = norm(sel, pr["default_weights"])
        result["presets"][key] = {}
        for t in pr["targets"]:
            tg = tdict[t["id"]] if t["id"] in tdict else next(v for v in tdict.values() if v["id"] == t["id"])
            arr = {"aridity": df["aridity_score"].values, "ice_polar": df["ice_polar_score"].values,
                   "volcanic_caves": E.score_volcanic_caves_vec(df), "topography": E.score_topography_vec(df, tg, mt),
                   "thermal": E.score_thermal_vec(df, tg), "surface_optics": E.score_surface_optics_vec(df, tg),
                   "illumination": E.score_illumination_vec(df, tg), "geology": E.score_geology_vec(df, tg)}
            ls = np.zeros(len(df)); used = np.zeros(len(df)); hard = np.zeros(len(df), bool)
            for c in sel:
                v = fl(arr[c]); ok = ~np.isnan(v); hard |= ok & (v < 0)
                ls += np.where(ok & (v >= 0), w[c] * np.log(np.clip(np.nan_to_num(v), FLOOR, 1)), 0)
                used += np.where(ok, w[c], 0)
            sc = np.where(hard | (used == 0), 0, np.exp(ls / np.maximum(used, 1e-9)))
            pct = 100 * pd.Series(sc).rank(pct=True).values
            sites = sorted(({"name": n, "percentile": round(float(pct[m].max()), 1)} for n, m in site_cells if m.any()),
                           key=lambda x: -x["percentile"])
            n10 = sum(x["percentile"] >= 90 for x in sites); n25 = sum(x["percentile"] >= 75 for x in sites)
            result["presets"][key][t["id"]] = {"top10": n10, "top25": n25, "sites": sites}
            best = ", ".join(f"{x['name']} {x['percentile']:.0f}" for x in sites[:3])
            P(f"| {key} | {t['id']} | {n10}/{len(sites)} | {n25}/{len(sites)} | {best} |")
    P("")
    return result

val = full_population(P)
root = Path(__file__).resolve().parents[1]
if val is not None:
    (DATA / "validation.json").write_text(json.dumps(val, indent=1), encoding="utf-8")
(root / "docs").mkdir(exist_ok=True)
(root / "docs/VALIDATION_REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[-25:]))
