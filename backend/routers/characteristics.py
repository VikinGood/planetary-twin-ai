"""
routers/characteristics.py — GET /characteristics

Returns the 8 characteristic definitions from config/characteristics.json.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.
"""

from fastapi import APIRouter

from backend.data_loader import load_characteristics

router = APIRouter()

_characteristics_cache: list[dict] | None = None


@router.get("/characteristics")
def get_characteristics() -> list[dict]:
    """Return all 8 characteristic definitions from config/characteristics.json."""
    global _characteristics_cache
    if _characteristics_cache is None:
        _characteristics_cache = load_characteristics()
    return _characteristics_cache
