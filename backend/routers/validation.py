"""
routers/validation.py — GET /validation

Returns known-analog cells with their scores for blind validation.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from backend.scoring import score_cell

router = APIRouter()


@router.get("/validation")
def get_validation(
    request: Request,
    body: str = Query(..., description="moon or mars"),
    mission_type: str = Query(..., description="landing or base"),
):
    """Return known-analog cells with their scores (blind validation set).

    These are cells where known_analog_within_km <= 50 (i.e., within 50 km of a
    known terrestrial analog site).  The scoring engine runs on these cells using
    the preset defaults for the given body + mission_type combination.

    Returns:
        known_analogs: list of SimilarityResult for known-analog cells
    """
    earth_df = request.app.state.earth_df
    targets_data = request.app.state.targets

    if earth_df is None:
        raise HTTPException(status_code=503, detail="Earth data not loaded.")

    targets_dict = targets_data.get("targets", {})

    # Filter Earth cells that are known analogs
    known_df = earth_df[
        (earth_df.get("known_analog_within_km", -1) >= 0) &
        (earth_df["known_analog_within_km"] <= 50.0)
    ] if "known_analog_within_km" in earth_df.columns else earth_df.iloc[0:0]

    if known_df.empty:
        return {"known_analogs": [], "note": "No known analog cells found (Phase 3c placeholder populates known_analog_within_km)."}

    # Get targets for this body + mission_type
    relevant_targets = [
        t for t in targets_dict.values()
        if t.get("body") == body and t.get("mission_type") == mission_type
    ]
    if not relevant_targets:
        raise HTTPException(
            status_code=404,
            detail=f"No targets found for body='{body}' mission_type='{mission_type}'.",
        )

    from backend.data_loader import load_missions
    missions = load_missions()
    preset = next(
        (m for m in missions if m.get("body") == body and m.get("mission_type") == mission_type),
        None,
    )
    selected_chars = preset["default_characteristics"] if preset else []
    resolved_weights = preset["default_weights"] if preset else {}

    # Use first relevant target for scoring
    tgt = relevant_targets[0]

    results = []
    for _, row in known_df.iterrows():
        result = score_cell(row, tgt, selected_chars, resolved_weights, mission_type)
        result["is_known_analog"] = True
        results.append(result)

    results.sort(key=lambda r: r["total_score"], reverse=True)
    for rank, r in enumerate(results, start=1):
        r["rank"] = rank

    return {"known_analogs": results}
