"""AI Scientific Analyst: builds the input for one candidate, calls the LLM provider, and
accepts the answer only if it passes the schema and the number checker.

AI use disclosure: portions generated with AI (Claude); reviewed by the team.

Flow for one candidate:
  1. build_result(): a SimilarityResult-like dict from an exported feature (static export
     format in frontend/README.md) for one target and characteristic selection.
  2. interpret(): provider.interpret(result) -> clean -> schema check -> number check.
     On failure, retry once; if it fails again, return None (the caller writes nothing and
     the dashboard shows "AI interpretation not available").
"""

from __future__ import annotations

import math

from backend.analyst.checker import invented_numbers
from backend.analyst.schema import validate_interpretation
from backend.llm_provider import AI_DISCLOSURE, LLMProvider, NoLLMProvider

DEFAULT_SELECTION_NOTE = "Written for the preset's default characteristic selection."


# ---------------------------------------------------------------------------
# Ranking (same rules as frontend/src/lib/scoring.mjs)
# ---------------------------------------------------------------------------

def normalize_weights(selected: list[str], weights: dict) -> dict:
    raw = [max(0.0, float(weights.get(c, 0) or 0)) for c in selected]
    total = sum(raw)
    return {c: (r / total if total > 0 else 1 / len(selected)) for c, r in zip(selected, raw)}


SCORE_FLOOR = 0.01
HARD_FAIL = -1


def score_feature(props: dict, target_id: str, selected: list[str], weights: dict) -> tuple[float | None, float, dict]:
    """Weighted geometric mean over the selected characteristics that have data.

    Same rules as frontend/src/lib/scoring.mjs: values below SCORE_FLOOR are raised to it
    (penalized, not dropped); -1 marks a failed hard requirement and drops the cell.
    """
    w = normalize_weights(selected, weights)
    scores = props.get("scores", {})
    used, log_sum, zero, parts = 0.0, 0.0, False, {}
    for c in selected:
        v = (scores.get(c) or {}).get(target_id)
        if isinstance(v, (int, float)) and math.isfinite(v):
            parts[c] = 0.0 if v < 0 else round(float(v), 3)
            used += w[c]
            if v < 0:
                zero = True
            else:
                log_sum += w[c] * math.log(min(1.0, max(SCORE_FLOOR, v)))
        else:
            parts[c] = None
    if used == 0:
        return None, 0.0, parts
    return (0.0 if zero else math.exp(log_sum / used)), used, parts


def rank_features(features: list, target_id: str, selected: list[str], weights: dict, limit: int = 10, exclude_known: bool = True, min_sep_deg: float = 3.0) -> list:
    rows = []
    for f in features:
        p = f["properties"]
        if exclude_known and p.get("is_known_analog"):
            continue
        total, coverage, parts = score_feature(p, target_id, selected, weights)
        if total is not None:
            rows.append((total, coverage, parts, f))
    rows.sort(key=lambda r: (-r[0], -r[1]))
    kept = []
    for r in rows:
        if len(kept) >= limit:
            break
        p = r[3]["properties"]
        if any(abs(p["lat_center"] - k[3]["properties"]["lat_center"]) < min_sep_deg and abs(p["lon_center"] - k[3]["properties"]["lon_center"]) < min_sep_deg for k in kept):
            continue
        kept.append(r)
    return kept


# ---------------------------------------------------------------------------
# Input for the LLM
# ---------------------------------------------------------------------------

def build_result(feature: dict, preset: dict, target: dict, selected: list[str], weights: dict, cannot_reproduce: list[str], char_names: dict) -> dict:
    p = feature["properties"]
    total, coverage, parts = score_feature(p, target["id"], selected, weights)
    w = normalize_weights(selected, weights)
    conf = p.get("confidence", {}) or {}
    overall_conf = "low" if any(conf.get(c) == "low" for c in selected) else ("medium" if any(conf.get(c) == "medium" for c in selected) else "high")
    return {
        "cell_id": p["cell_id"],
        "lat_center": p["lat_center"],
        "lon_center": p["lon_center"],
        "region_hint": p.get("region_hint"),
        "body": preset["body"],
        "mission_type": preset["mission_type"],
        "target": {k: target.get(k) for k in ("id", "name", "lat", "lon", "description", "coordinate_status", "value_origin")},
        "selected_characteristics": selected,
        "weights": {c: round(w[c], 3) for c in selected},
        "characteristic_summary_scores": {char_names.get(c, c): v for c, v in parts.items() if v is not None},
        "missing_characteristics": [char_names.get(c, c) for c, v in parts.items() if v is None],
        "total_score": round(total, 3) if total is not None else None,
        "coverage": round(coverage, 3),
        "measured_values": p.get("values", {}),
        "environment_tags": p.get("environment_tags", []),
        "confidence": overall_conf,
        "cannot_reproduce": cannot_reproduce,
    }


# ---------------------------------------------------------------------------
# Interpretation with checks
# ---------------------------------------------------------------------------

def clean(interp: dict, result: dict) -> dict:
    """Keep only schema fields, drop empty optional ones, enforce fixed values."""
    out = {
        "cell_id": result["cell_id"],
        "target_id": result["target"]["id"],
        "body": result["body"],
        "mission_type": result["mission_type"],
        "model": str(interp.get("model", "unknown")),
        "generated_at": str(interp.get("generated_at", "")),
        "analog_summary": str(interp.get("analog_summary", "")).strip(),
        "non_analog_summary": str(interp.get("non_analog_summary", "")).strip(),
        "testable_activities": [str(a).strip() for a in (interp.get("testable_activities") or []) if str(a).strip()][:8],
        "confidence_note": str(interp.get("confidence_note", "")).strip(),
        "ai_disclosure": AI_DISCLOSURE,
    }
    hl = interp.get("characteristic_highlights")
    if isinstance(hl, list):
        hl = [h for h in hl if isinstance(h, dict) and h.get("characteristic_id") and h.get("highlight")]
        if hl:
            out["characteristic_highlights"] = [{"characteristic_id": str(h["characteristic_id"]), "highlight": str(h["highlight"])[:200]} for h in hl]
    note = out["confidence_note"]
    if DEFAULT_SELECTION_NOTE not in note:
        note = (note + " " + DEFAULT_SELECTION_NOTE).strip()
    out["confidence_note"] = note[:400]
    return out


def check(interp: dict, result: dict) -> list[str]:
    problems = validate_interpretation(interp)
    if not interp["analog_summary"] or not interp["non_analog_summary"]:
        problems.append("empty summary")
    bad = invented_numbers(interp, result)
    if bad:
        problems.append(f"numbers not in the input: {bad}")
    return problems


async def interpret(result: dict, provider: LLMProvider, retries: int = 1) -> tuple[dict | None, list[str]]:
    """Return (interpretation, problems). None when no valid AI interpretation was produced."""
    if isinstance(provider, NoLLMProvider):
        return None, ["no LLM configured"]
    problems: list[str] = []
    for _ in range(retries + 1):
        raw = await provider.interpret(result)
        if raw.get("model") == "NoLLMProvider":  # provider fell back after an API error
            problems = [raw.get("confidence_note", "provider error")]
            continue
        interp = clean(raw, result)
        problems = check(interp, result)
        if not problems:
            return interp, []
    return None, problems
