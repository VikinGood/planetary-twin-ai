"""
routers/candidates.py — GET /candidates and GET /candidates/{cell_id}

Main scoring endpoint.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, Request

from backend.scoring import score_all, score_cell

router = APIRouter()

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


@router.get("/candidates")
def get_candidates(
    request: Request,
    body: str = Query(..., description="moon or mars"),
    mission_type: str = Query(..., description="landing or base"),
    target: str | None = Query(None, description="Target ID; omit to use all targets for body+mission"),
    characteristics: str | None = Query(None, description="Comma-separated characteristic IDs"),
    weights: str | None = Query(None, description="JSON string of {char_id: weight}"),
    tags: str | None = Query(None, description="Comma-separated tag filter (AND logic)"),
    exclude_known: bool = Query(True, description="Exclude known analog sites"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
):
    """Score Earth cells against one or more targets and return ranked candidates."""
    earth_df = request.app.state.earth_df
    targets_data = request.app.state.targets

    if earth_df is None:
        raise HTTPException(
            status_code=503,
            detail="Earth data not loaded. Run the preprocessing pipeline first.",
        )

    targets_dict = targets_data.get("targets", {})

    # Resolve targets for this body + mission_type
    if target:
        if target not in targets_dict:
            raise HTTPException(status_code=404, detail=f"Target '{target}' not found.")
        selected_targets = [targets_dict[target]]
    else:
        selected_targets = [
            t for t in targets_dict.values()
            if t.get("body") == body and t.get("mission_type") == mission_type
        ]

    if not selected_targets:
        raise HTTPException(
            status_code=404,
            detail=f"No targets found for body='{body}' mission_type='{mission_type}'.",
        )

    # Resolve characteristics and weights from query or preset defaults
    selected_chars, resolved_weights = _resolve_chars_weights(
        body, mission_type, characteristics, weights, request
    )

    # Score against first matching target (if multiple, use the first; frontend combines)
    # For multi-target requests, we score against each and return the top results
    all_results: list[dict] = []
    seen_cells: set[str] = set()

    for tgt in selected_targets:
        results = score_all(
            earth_df, tgt, selected_chars, resolved_weights, mission_type, exclude_known
        )
        for r in results:
            cid = r["cell_id"]
            if cid not in seen_cells:
                seen_cells.add(cid)
                all_results.append(r)

    # Re-sort the merged list
    all_results.sort(key=lambda r: r["total_score"], reverse=True)
    for rank, r in enumerate(all_results, start=1):
        r["rank"] = rank

    # Tag filter (AND logic — cell must have ALL requested tags)
    if tags:
        required_tags = {t.strip() for t in tags.split(",") if t.strip()}
        all_results = [
            r for r in all_results
            if required_tags.issubset(set(r.get("environment_tags", [])))
        ]

    total_count = len(all_results)
    page = all_results[:limit]

    return {
        "results": page,
        "total_count": total_count,
        "query": {
            "body": body,
            "mission_type": mission_type,
            "target": target,
            "characteristics": selected_chars,
            "weights": resolved_weights,
            "tags": tags,
            "exclude_known": exclude_known,
            "limit": limit,
        },
    }


@router.get("/candidates/{cell_id}")
def get_candidate_detail(
    cell_id: str,
    request: Request,
    body: str = Query(...),
    mission_type: str = Query(...),
    target: str = Query(...),
):
    """Return full SimilarityResult for one Earth cell."""
    earth_df = request.app.state.earth_df
    targets_data = request.app.state.targets

    if earth_df is None:
        raise HTTPException(status_code=503, detail="Earth data not loaded.")

    targets_dict = targets_data.get("targets", {})
    if target not in targets_dict:
        raise HTTPException(status_code=404, detail=f"Target '{target}' not found.")

    tgt = targets_dict[target]

    # Find row
    rows = earth_df[earth_df["cell_id"] == cell_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found.")

    row = rows.iloc[0]

    # Use preset defaults for characteristics/weights
    selected_chars, resolved_weights = _resolve_chars_weights(
        body, mission_type, None, None, request
    )

    result = score_cell(row, tgt, selected_chars, resolved_weights, mission_type)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_chars_weights(
    body: str,
    mission_type: str,
    characteristics: str | None,
    weights: str | None,
    request: Request,
) -> tuple[list[str], dict[str, float]]:
    """Return (selected_chars, weights_dict) from query params or preset defaults."""
    from backend.data_loader import load_missions

    # Load preset for this body+mission
    missions = load_missions()
    preset = next(
        (m for m in missions if m.get("body") == body and m.get("mission_type") == mission_type),
        None,
    )
    default_chars = preset["default_characteristics"] if preset else []
    default_weights = preset["default_weights"] if preset else {}

    if characteristics:
        selected_chars = [c.strip() for c in characteristics.split(",") if c.strip()]
    else:
        selected_chars = default_chars

    if weights:
        try:
            resolved_weights = json.loads(weights)
        except json.JSONDecodeError:
            resolved_weights = default_weights
    else:
        resolved_weights = default_weights

    # Ensure weights only cover selected chars; renormalize
    resolved_weights = {k: v for k, v in resolved_weights.items() if k in selected_chars}
    total_w = sum(resolved_weights.values())
    if total_w > 0:
        resolved_weights = {k: v / total_w for k, v in resolved_weights.items()}
    else:
        # Equal weights fallback
        n = len(selected_chars)
        resolved_weights = {c: 1.0 / n for c in selected_chars} if n else {}

    return selected_chars, resolved_weights
