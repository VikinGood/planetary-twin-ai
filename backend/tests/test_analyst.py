"""Tests for the AI analyst (Phase 4): number checker, schema, retry and fallback.

AI use disclosure: portions generated with AI (Claude); reviewed by the team.
No network: a fake provider stands in for Groq.
"""

import asyncio
import math

from backend.analyst.analyst import build_result, clean, interpret, rank_features, score_feature
from backend.analyst.checker import invented_numbers, numbers_in_text
from backend.analyst.provider import build_prompt
from backend.analyst.schema import validate_interpretation
from backend.llm_provider import AI_DISCLOSURE, LLMProvider, NoLLMProvider

PRESET = {"body": "moon", "mission_type": "landing"}
TARGET = {"id": "malapert_massif", "name": "Malapert Massif", "lat": -85.9, "lon": -2.0, "description": "Peak", "coordinate_status": "UNVERIFIED", "value_origin": "literature"}
NAMES = {"topography": "Topography", "thermal": "Thermal", "geology": "Geology"}


def feature(cell="E_-62.875_-60.625", lat=-62.875, lon=-60.625, topo=0.779, thermal=0.906, geology=None, known=False):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "cell_id": cell, "lat_center": lat, "lon_center": lon, "is_known_analog": known,
            "environment_tags": ["polar", "volcanic"],
            "scores": {"topography": {"malapert_massif": topo}, "thermal": {"malapert_massif": thermal}, "geology": {"malapert_massif": geology}},
            "values": {"slope_mean_deg": {"value": 8.3, "units": "degrees", "source": "Copernicus DEM"}},
            "confidence": {"thermal": "medium"},
        },
    }


def result():
    return build_result(feature(), PRESET, TARGET, ["topography", "thermal", "geology"], {"topography": 0.5, "thermal": 0.3, "geology": 0.2}, ["Gravity: 1/6 g (1.62 m/s²)", "14-day day/night cycle"], NAMES)


def good_answer(**over):
    a = {
        "model": "fake", "generated_at": "2026-11-15T03:00:00+00:00",
        "analog_summary": "Topography scores 0.78 and thermal 0.91, so the site suits hazard detection tests.",
        "non_analog_summary": "It cannot reproduce 1/6 g gravity or the 14-day day/night cycle; geology has no data.",
        "testable_activities": ["hazard detection and avoidance"],
        "characteristic_highlights": None,
        "confidence_note": "Thermal confidence is medium.",
        "ai_disclosure": AI_DISCLOSURE,
    }
    a.update(over)
    return a


class FakeProvider(LLMProvider):
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0

    async def interpret(self, result):
        self.calls += 1
        return self.answers.pop(0)


def test_numbers_in_text_ignores_dataset_codes():
    assert numbers_in_text("MOD11A2 shows 12.5 and −3, plus 1,036 cells") == [12.5, -3.0, 1036.0]


def test_score_matches_geometric_mean_and_skips_missing():
    total, coverage, parts = score_feature(feature()["properties"], "malapert_massif", ["topography", "thermal", "geology"], {"topography": 0.5, "thermal": 0.3, "geology": 0.2})
    expected = math.exp((0.5 * math.log(0.779) + 0.3 * math.log(0.906)) / 0.8)
    assert abs(total - expected) < 1e-9
    assert abs(coverage - 0.8) < 1e-9
    assert parts["geology"] is None


def test_zero_is_floored_and_minus_one_drops():
    sel, w = ["topography", "thermal"], {"topography": 0.5, "thermal": 0.5}
    total, _, _ = score_feature(feature(topo=0.0, thermal=1.0)["properties"], "malapert_massif", sel, w)
    assert abs(total - 0.1) < 1e-9
    total, _, parts = score_feature(feature(topo=-1, thermal=1.0)["properties"], "malapert_massif", sel, w)
    assert total == 0.0 and parts["topography"] == 0.0


def test_rank_excludes_known_and_collapses_neighbours():
    fs = [feature("A", 0, 0, 0.9), feature("B", 0.25, 0, 0.89), feature("C", 20, 0, 0.5), feature("K", 40, 0, 1.0, known=True)]
    ids = [r[3]["properties"]["cell_id"] for r in rank_features(fs, "malapert_massif", ["topography"], {"topography": 1})]
    assert ids == ["A", "C"]


def test_checker_accepts_input_numbers_and_rejects_invented():
    r = result()
    assert invented_numbers(clean(good_answer(), r), r) == []
    bad = clean(good_answer(analog_summary="The site reaches 37.2 C and scores 0.78."), r)
    assert invented_numbers(bad, r) == [37.2]


def test_clean_output_passes_schema():
    r = result()
    out = clean(good_answer(characteristic_highlights=[{"characteristic_id": "Topography", "highlight": "Gentle slopes."}]), r)
    assert validate_interpretation(out) == []
    assert "characteristic_highlights" in out
    assert validate_interpretation(clean(good_answer(), r)) == []  # null highlights dropped


def test_schema_rejects_extra_fields_and_long_text():
    out = clean(good_answer(), result())
    out["extra"] = 1
    out["analog_summary"] = "x" * 700
    errors = validate_interpretation(out)
    assert any("unexpected field" in e for e in errors) and any("longer than" in e for e in errors)


def test_retry_then_accept():
    p = FakeProvider([good_answer(analog_summary="Invented 99.9 percent."), good_answer()])
    interp, problems = asyncio.run(interpret(result(), p))
    assert interp is not None and problems == [] and p.calls == 2


def test_reject_after_retry_returns_none():
    p = FakeProvider([good_answer(analog_summary="Invented 99.9."), good_answer(analog_summary="Invented 88.8.")])
    interp, problems = asyncio.run(interpret(result(), p))
    assert interp is None and "not in the input" in problems[0]


def test_no_llm_writes_nothing():
    interp, problems = asyncio.run(interpret(result(), NoLLMProvider()))
    assert interp is None and problems == ["no LLM configured"]


def test_prompt_contains_rules_and_data():
    prompt = build_prompt(result())
    assert "Only use numbers that appear in the data" in prompt
    assert "Malapert Massif" in prompt and "hazard detection and avoidance" in prompt
