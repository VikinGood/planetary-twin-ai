"""
routers/missions.py — GET /missions

Returns the four mission presets from config/missions/*.json.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.
"""

from fastapi import APIRouter

from backend.data_loader import load_missions

router = APIRouter()

_missions_cache: list[dict] | None = None


@router.get("/missions")
def get_missions() -> list[dict]:
    """Return all four mission presets (moon-landing, moon-base, mars-landing, mars-base)."""
    global _missions_cache
    if _missions_cache is None:
        _missions_cache = load_missions()
    return _missions_cache
