"""
routers/interpret.py — POST /interpret

Calls LLMProvider to generate a structured Interpretation for a SimilarityResult.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.
"""

from fastapi import APIRouter

from backend.llm_provider import get_provider

router = APIRouter()


@router.post("/interpret")
async def interpret_result(result: dict) -> dict:
    """Generate an AI interpretation of a SimilarityResult.

    Body: SimilarityResult JSON (from /candidates or /candidates/{cell_id}).
    Returns: Interpretation matching contracts/interpretation.schema.json.

    Uses GroqProvider if GROQ_API_KEY is set in environment; otherwise NoLLMProvider.
    ai_disclosure is always the canonical string from the schema.
    """
    provider = get_provider()
    interpretation = await provider.interpret(result)
    return interpretation
