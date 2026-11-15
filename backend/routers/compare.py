"""
routers/compare.py — GET /compare

Returns landing vs base rankings side by side, plus cells that appear in both top 50.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from backend.scoring import score_all

router = APIRouter()

COMPARE_TOP_N = 50


@router.get("/compare")
def compare_mission_types(
    request: Request,
    body: str = Query(..., description="moon or mars"),
    target: str = Query(..., description="Target ID"),
    characteristics: str | None = Query(None, description="Comma-separated characteristic IDs"),
):
    """Compare landing vs base rankings for the same target.

    Returns:
        landing: top 50 SimilarityResult for landing mission type
        base:    top 50 SimilarityResult for base mission type
        in_both: cell_ids that appear in both top-50 lists
    """
    earth_df = request.app.state.earth_df
    targets_data = request.app.state.targets

    if earth_df is None:
        raise HTTPException(status_code=503, detail="Earth data not loaded.")

    targets_dict = targets_data.get("targets", {})
    if target not in targets_dict:
        raise HTTPException(status_code=404, detail=f"Target '{target}' not found.")

    tgt = targets_dict[target]

    from backend.data_loader import load_missions

    missions = load_missions()

    results_by_type: dict[str, list[dict]] = {}

    for mission_type in ("landing", "base"):
        preset = next(
            (m for m in missions if m.get("body") == body and m.get("mission_type") == mission_type),
            None,
        )
        if preset is None:
            results_by_type[mission_type] = []
            continue

        if characteristics:
            selected_chars = [c.strip() for c in characteristics.split(",") if c.strip()]
            # Use preset weights for the requested chars; equal weight for any not in preset
            preset_weights = preset["default_weights"]
            resolved_weights = {c: preset_weights.get(c, 1.0) for c in selected_chars}
        else:
            selected_chars = preset["default_characteristics"]
            resolved_weights = preset["default_weights"]

        # Renormalize
        total_w = sum(resolved_weights.values())
        if total_w > 0:
            resolved_weights = {k: v / total_w for k, v in resolved_weights.items()}

        results = score_all(earth_df, tgt, selected_chars, resolved_weights, mission_type)
        results_by_type[mission_type] = results[:COMPARE_TOP_N]

    landing_ids = {r["cell_id"] for r in results_by_type.get("landing", [])}
    base_ids = {r["cell_id"] for r in results_by_type.get("base", [])}
    in_both = sorted(landing_ids & base_ids)

    return {
        "landing": results_by_type.get("landing", []),
        "base": results_by_type.get("base", []),
        "in_both": in_both,
    }
