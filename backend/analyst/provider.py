"""Groq provider with the analyst prompt (strict: only numbers from the input).

AI use disclosure: portions generated with AI (Claude); reviewed by the team.

Extends backend.llm_provider.GroqProvider: same API call and fallback, different prompt.
Model: GROQ_MODEL from .env, default "openai/gpt-oss-120b" (listed in Groq's rate-limit
docs on 2026-11-14; check your account's limits page).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from backend.llm_provider import AI_DISCLOSURE, GroqProvider, NoLLMProvider

ACTIVITIES = {
    "landing": ["descent imaging and terrain-relative navigation", "hazard detection and avoidance", "landing pads and plume-surface interaction", "first surface mobility"],
    "base": ["habitat construction and site preparation", "ISRU water extraction from ground ice", "shelter in caves or lava tubes", "power systems in extreme light regimes", "long-duration crew operations in extreme cold and dryness"],
}

SYSTEM = (
    "You are a planetary science analyst writing for mission planners. You interpret scored "
    "Earth analog sites. Use only the facts and numbers given in the data. Never write a number "
    "that does not appear in the data. If something is missing or low-confidence, say so. "
    "Answer with one JSON object and nothing else."
)


def build_prompt(result: dict) -> str:
    target = result["target"]
    data = {
        "earth_site": {"cell_id": result["cell_id"], "lat": result["lat_center"], "lon": result["lon_center"], "region": result.get("region_hint")},
        "body": result["body"],
        "mission_type": result["mission_type"],
        "reference_target": {"name": target.get("name"), "description": target.get("description"), "values_from": target.get("value_origin")},
        "total_score_0_to_1": result["total_score"],
        "scores_by_characteristic_0_to_1": result["characteristic_summary_scores"],
        "characteristics_without_data": result["missing_characteristics"],
        "measured_values": result["measured_values"],
        "environment_tags": result["environment_tags"],
        "overall_confidence": result["confidence"],
        "earth_cannot_reproduce": result["cannot_reproduce"],
        "candidate_activities": ACTIVITIES.get(result["mission_type"], []),
    }
    return (
        "Data (JSON):\n" + json.dumps(data, ensure_ascii=False) + "\n\n"
        "Write JSON with exactly these fields, in English:\n"
        '- "analog_summary": at most 80 words. Why this Earth site is a useful analog of the '
        "reference target for this mission type, citing the strongest characteristics.\n"
        '- "non_analog_summary": at most 80 words. What it does not reproduce: the weakest '
        "characteristics and the items in earth_cannot_reproduce.\n"
        '- "testable_activities": 2 to 4 items chosen from candidate_activities that the scores '
        "support (copy them as written).\n"
        '- "characteristic_highlights": one item per characteristic with a notable score, as '
        '{"characteristic_id": "<name>", "highlight": "<one sentence>"}.\n'
        '- "confidence_note": at most 50 words on missing data, proxies and the confidence level.\n'
        "Only use numbers that appear in the data. Prefer words over numbers."
    )


class AnalystGroqProvider(GroqProvider):
    def __init__(self):
        super().__init__()
        self.model = os.environ.get("GROQ_MODEL") or "openai/gpt-oss-120b"

    async def interpret(self, result: dict) -> dict:
        import asyncio
        import httpx

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": build_prompt(result)}],
            "temperature": 0.2,
            "max_tokens": 2500,
            "response_format": {"type": "json_object"},
        }
        for attempt in range(6):
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    r = await client.post(self.api_url, headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
                    if r.status_code == 429:
                        reset_s = 15.0
                        reset_header = r.headers.get("x-ratelimit-reset-tokens") or r.headers.get("retry-after")
                        if reset_header:
                            try:
                                reset_s = float(str(reset_header).rstrip("s")) + 1.0
                            except Exception:
                                reset_s = 15.0
                        await asyncio.sleep(max(5.0, reset_s))
                        continue
                    r.raise_for_status()
                    parsed = json.loads(r.json()["choices"][0]["message"]["content"])
                    break
            except Exception as exc:  # network, rate limit, bad JSON
                if attempt == 5:
                    fallback = await NoLLMProvider().interpret(result)
                    fallback["confidence_note"] = f"Groq API call failed: {exc}"
                    return fallback
                await asyncio.sleep(5.0)
        parsed.update({"model": self.model, "generated_at": datetime.now(timezone.utc).isoformat(), "ai_disclosure": AI_DISCLOSURE})
        return parsed


def get_analyst_provider():
    return AnalystGroqProvider() if os.environ.get("GROQ_API_KEY") else NoLLMProvider()
