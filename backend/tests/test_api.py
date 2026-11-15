"""
test_api.py — API integration tests using FastAPI TestClient with mock data.

AI use disclosure: this file was generated with AI assistance and reviewed by the team.

Does NOT require the real earth_cells_025deg.parquet to be present.
Mock data fixtures are built in this file.

Run with:
    cd c:\\dev\\planetary-twin-ai
    .venv\\Scripts\\python -m pytest backend/tests/ -v
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]


def _make_mock_earth_df() -> pd.DataFrame:
    """Return a minimal 10-row Earth cells DataFrame with all required columns."""
    rows = []
    for i in range(10):
        lat = -62.875 + i * 0.25
        lon = -60.625
        rows.append(
            {
                "cell_id": f"E_{lat:+.3f}_{lon:+.3f}",
                "lat_center": lat,
                "lon_center": lon,
                "land_fraction": 1.0,
                "slope": float(i) * 0.5 + 1.0,
                "roughness": float(i) * 2.0 + 10.0,
                "local_relief": float(i) * 50.0 + 200.0,
                "broadband_albedo": 0.08 + i * 0.01,
                "aridity_index": 0.1 + i * 0.08,
                "precipitation": 100.0,
                "pet": 500.0,
                "permafrost_index": max(0.0, 0.9 - i * 0.1),
                "ice_cover_fraction": 0.1,
                "glim_vb": 1 if i < 5 else 0,
                "volcanic_caves_likelihood": "HIGH" if i < 3 else ("MEDIUM" if i < 6 else "LOW"),
                "lithology_class": "vb" if i < 5 else "ss",
                "known_analog_within_km": -1.0,
                # Illumination
                "max_solar_elevation": 90.0 - abs(lat) + 23.44,
                "max_solar_elevation_pct": 0.5 + lat / 200.0,
                "mean_solar_elevation": (90.0 - abs(lat) + 23.44) * 0.4,
                "mean_solar_elevation_pct": 0.4 + lat / 200.0,
                "sun_fraction": 0.5,
                "sun_fraction_pct": 0.5,
                # Thermal
                "lst_annual_mean": -5.0 - i,
                "lst_annual_mean_pct": 0.1 + i * 0.03,
                "lst_annual_range": 35.0 + i * 1.5,
                "lst_annual_range_pct": 0.6 + i * 0.02,
                "lst_diurnal_range": 15.0 + i * 1.0,
                "lst_diurnal_range_pct": 0.5 + i * 0.02,
                "environment_tags": ["polar"] if abs(lat) > 60 else [],
            }
        )
    return pd.DataFrame(rows)


def _make_mock_targets() -> dict:
    """Return a minimal targets dict with one moon landing target."""
    return {
        "schema_version": "1.0",
        "generated_at": "2026-11-14T23:59:58Z",
        "note": "MOCK data for testing",
        "targets": {
            "malapert_massif": {
                "id": "malapert_massif",
                "name": "Malapert Massif",
                "body": "moon",
                "mission_type": "landing",
                "lat": -85.9,
                "lon": -3.5,
                "coordinate_status": "UNVERIFIED",
                "cannot_reproduce": ["Gravity: 1/6 g"],
                "reference_values": {
                    "topography": {
                        "slope": {"value": 2.0, "units": "degrees"},
                        "roughness": {"value": 14.0, "units": "meters"},
                        "local_relief": {"value": 500.0, "units": "meters"},
                    },
                    "thermal": {
                        "temp_annual_mean": {"value": 150.0, "units": "K", "percentile_estimate": 0.03},
                        "temp_annual_range": {"value": 80.0, "units": "K", "percentile_estimate": 0.72},
                        "temp_diurnal_range": {"value": 30.0, "units": "K", "percentile_estimate": 0.45},
                    },
                    "illumination": {
                        "illumination_fraction": {"value": 0.86, "units": "0–1", "percentile_estimate": 0.98},
                        "solar_elevation_range": {"value": 3.0, "units": "degrees", "percentile_estimate": 0.00},
                    },
                    "surface_optics": {
                        "reflectance": {"value": 0.11, "units": "0–1"},
                    },
                    "aridity": {"score": 1.0, "basis": "REQUIREMENT"},
                    "geology": {
                        "geologic_unit": {
                            "class_description": "highland breccia anorthositic",
                            "source": "USGS",
                            "confidence": "low",
                        }
                    },
                    "ice_polar": {
                        "illumination_fraction": {"value": 0.86, "units": "0–1"},
                    },
                    "volcanic_caves": {"likelihood": "LOW"},
                },
            },
            "arcadia_planitia": {
                "id": "arcadia_planitia",
                "name": "Arcadia Planitia",
                "body": "mars",
                "mission_type": "base",
                "lat": 46.7,
                "lon": -172.0,
                "coordinate_status": "UNVERIFIED",
                "cannot_reproduce": ["Gravity: 0.38 g"],
                "reference_values": {
                    "topography": {
                        "slope": {"value": 1.0, "units": "degrees"},
                        "roughness": {"value": 10.0, "units": "meters"},
                        "local_relief": {"value": 300.0, "units": "meters"},
                    },
                    "thermal": {
                        "temp_annual_mean": {"value": 218.0, "units": "K", "percentile_estimate": 0.05},
                        "temp_annual_range": {"value": 110.0, "units": "K", "percentile_estimate": 0.99},
                        "temp_diurnal_range": {"value": 45.0, "units": "K", "percentile_estimate": 0.90},
                    },
                    "aridity": {"score": 1.0, "basis": "REQUIREMENT"},
                    "geology": {
                        "geologic_unit": {
                            "class_description": "volcanic basaltic plains",
                            "source": "USGS Mars map",
                            "confidence": "low",
                        }
                    },
                    "ice_polar": {
                        "illumination_fraction": {"value": 0.5, "units": "0–1"},
                    },
                    "volcanic_caves": {"likelihood": "LOW"},
                    "surface_optics": {
                        "albedo": {"value": 0.25, "units": "0–1"},
                    },
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """TestClient with load_earth_cells and load_targets patched to return mock data."""
    mock_df = _make_mock_earth_df()
    mock_targets = _make_mock_targets()

    with (
        patch("backend.main.load_earth_cells", return_value=mock_df),
        patch("backend.main.load_targets", return_value=mock_targets),
    ):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Tests: GET /characteristics
# ---------------------------------------------------------------------------

class TestGetCharacteristics:
    def test_returns_200(self, client):
        resp = client.get("/characteristics")
        assert resp.status_code == 200

    def test_returns_8_items(self, client):
        resp = client.get("/characteristics")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 8

    def test_all_have_id_field(self, client):
        resp = client.get("/characteristics")
        for item in resp.json():
            assert "id" in item

    def test_known_ids_present(self, client):
        resp = client.get("/characteristics")
        ids = {item["id"] for item in resp.json()}
        expected = {
            "topography", "geology", "thermal", "aridity",
            "ice_polar", "volcanic_caves", "surface_optics", "illumination",
        }
        assert expected == ids


# ---------------------------------------------------------------------------
# Tests: GET /missions
# ---------------------------------------------------------------------------

class TestGetMissions:
    def test_returns_200(self, client):
        resp = client.get("/missions")
        assert resp.status_code == 200

    def test_returns_4_presets(self, client):
        resp = client.get("/missions")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 4

    def test_has_all_body_mission_combos(self, client):
        resp = client.get("/missions")
        combos = {(m["body"], m["mission_type"]) for m in resp.json()}
        assert ("moon", "landing") in combos
        assert ("moon", "base") in combos
        assert ("mars", "landing") in combos
        assert ("mars", "base") in combos

    def test_each_preset_has_weights(self, client):
        resp = client.get("/missions")
        for preset in resp.json():
            assert "default_weights" in preset
            assert len(preset["default_weights"]) > 0


# ---------------------------------------------------------------------------
# Tests: GET /candidates
# ---------------------------------------------------------------------------

class TestGetCandidates:
    def test_returns_200(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "malapert_massif", "limit": 5},
        )
        assert resp.status_code == 200

    def test_returns_at_most_limit_results(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "malapert_massif", "limit": 5},
        )
        data = resp.json()
        assert len(data["results"]) <= 5

    def test_response_has_required_keys(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "malapert_massif", "limit": 3},
        )
        data = resp.json()
        assert "results" in data
        assert "total_count" in data
        assert "query" in data

    def test_each_result_has_total_score(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "malapert_massif", "limit": 5},
        )
        for r in resp.json()["results"]:
            assert "total_score" in r
            assert 0.0 <= r["total_score"] <= 1.0

    def test_results_sorted_descending(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "malapert_massif", "limit": 10},
        )
        scores = [r["total_score"] for r in resp.json()["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_unknown_target_returns_404(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "nonexistent_target"},
        )
        assert resp.status_code == 404

    def test_query_echoed_in_response(self, client):
        resp = client.get(
            "/candidates",
            params={"body": "moon", "mission_type": "landing", "target": "malapert_massif", "limit": 5},
        )
        q = resp.json()["query"]
        assert q["body"] == "moon"
        assert q["mission_type"] == "landing"
        assert q["target"] == "malapert_massif"
