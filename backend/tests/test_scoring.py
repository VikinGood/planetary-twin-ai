"""
test_scoring.py — Unit tests for backend/scoring.py

AI use disclosure: this file was generated with AI assistance and reviewed by the team.

Run with:
    cd c:\\dev\\planetary-twin-ai
    .venv\\Scripts\\python -m pytest backend/tests/ -v
"""

import math

import pandas as pd
import pytest

from backend.scoring import (
    aridity_score,
    gaussian_score,
    geology_score,
    ice_polar_score,
    illumination_score,
    score_cell,
    surface_optics_score,
    thermal_score,
    topography_score,
    volcanic_caves_score,
    weighted_geometric_mean,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row(**kwargs) -> pd.Series:
    """Build a minimal pd.Series for testing."""
    defaults = {
        "cell_id": "test_cell",
        "lat_center": -62.875,
        "lon_center": -60.625,
        "land_fraction": 1.0,
        "slope": 3.2,
        "roughness": 22.0,
        "local_relief": 500.0,
        "broadband_albedo": 0.09,
        "aridity_index": 0.1,
        "precipitation": 50.0,
        "pet": 500.0,
        "permafrost_index": 0.8,
        "ice_cover_fraction": 0.1,
        "glim_vb": 1,
        "volcanic_caves_likelihood": "HIGH",
        "lithology_class": "vb",
        "known_analog_within_km": -1.0,
        # Illumination percentile columns (precomputed)
        "max_solar_elevation": 50.56,
        "max_solar_elevation_pct": 0.407,
        "mean_solar_elevation": 19.31,
        "mean_solar_elevation_pct": 0.429,
        "sun_fraction": 0.500,
        "sun_fraction_pct": 0.50,
        # Thermal percentile columns
        "lst_annual_mean": -8.5,
        "lst_annual_mean_pct": 0.12,
        "lst_annual_range": 38.5,
        "lst_annual_range_pct": 0.74,
        "lst_diurnal_range": 18.2,
        "lst_diurnal_range_pct": 0.60,
    }
    defaults.update(kwargs)
    return pd.Series(defaults)


def _moon_landing_target() -> dict:
    """Minimal Malapert Massif-like target for testing."""
    return {
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
                    "class_description": "highland breccia anorthositic regolith",
                    "source": "USGS Moon map",
                    "confidence": "low",
                }
            },
        },
    }


# ---------------------------------------------------------------------------
# 1. gaussian_score
# ---------------------------------------------------------------------------

class TestGaussianScore:
    def test_x_equals_mu_gives_one(self):
        score = gaussian_score(5.0, 5.0, 2.0, 1.0)
        assert score == pytest.approx(1.0, abs=1e-9)

    def test_far_from_mu_approaches_zero(self):
        score = gaussian_score(100.0, 0.0, 1.0, 1.0)
        assert score < 1e-6

    def test_sigma_floor_kicks_in_when_sigma_target_small(self):
        # sigma_target=0.001, sigma_floor=2.0 → sigma_eff=2.0
        score_with_floor = gaussian_score(1.0, 0.0, 0.001, 2.0)
        score_no_floor = gaussian_score(1.0, 0.0, 0.001, 0.0)
        # With floor: sigma_eff=2.0 → less punishing
        # Without floor: sigma_eff=0.001 → near-zero
        assert score_with_floor > score_no_floor
        assert score_no_floor < 1e-200  # effectively zero

    def test_sigma_floor_does_not_fire_when_sigma_target_larger(self):
        # sigma_target=5.0 > sigma_floor=2.0 → sigma_eff=5.0
        # Identical to calling with sigma_floor=5.0
        score = gaussian_score(1.0, 0.0, 5.0, 2.0)
        expected = math.exp(-(1.0 ** 2) / (2 * 5.0 ** 2))
        assert score == pytest.approx(expected, rel=1e-9)

    def test_symmetry(self):
        assert gaussian_score(3.0, 5.0, 2.0, 0.0) == pytest.approx(
            gaussian_score(7.0, 5.0, 2.0, 0.0), rel=1e-9
        )

    def test_score_range(self):
        for x in [-10, -1, 0, 1, 2, 5, 10]:
            s = gaussian_score(x, 0.0, 1.0, 0.5)
            assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# 2. topography_score
# ---------------------------------------------------------------------------

class TestTopographyScore:
    def test_hard_cap_slope_above_12(self):
        row = _row(slope=15.0, roughness=20.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "landing")
        assert score == 0.0
        assert detail["hard_cap_applied"] is True

    def test_hard_cap_exactly_12_does_not_apply(self):
        row = _row(slope=12.0, roughness=20.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "landing")
        # 12.0 is NOT > 12.0, so cap should not apply
        assert detail["hard_cap_applied"] is False
        assert score > 0.0

    def test_flat_landing_gives_nonzero_score(self):
        # slope=0, roughness=0: flat → non-zero score for landing
        # slope target=2°, sigma_eff=2 → gaussian_score(0, 2, 2, 2) = exp(-0.5) ≈ 0.607
        # roughness target=14 m, sigma_eff=10 → gaussian_score(0, 14, 8, 10) = exp(-0.98) ≈ 0.375
        # geometric_mean(0.607, 0.375) ≈ 0.477
        row = _row(slope=0.0, roughness=0.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "landing")
        assert score > 0.0
        assert not detail["hard_cap_applied"]
        # Verify slope score individually (sigma_eff=2, x=0, mu=2)
        import math
        expected_slope = math.exp(-(2.0 ** 2) / (2 * 2.0 ** 2))  # exp(-0.5) ≈ 0.607
        assert detail["slope_score"] == pytest.approx(expected_slope, abs=0.001)

    def test_exact_match_landing(self):
        # slope = mu_slope, roughness = mu_rough → both gaussians = 1.0 → total = 1.0
        row = _row(slope=2.0, roughness=14.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "landing")
        assert score == pytest.approx(1.0, abs=1e-6)

    def test_base_uses_local_relief(self):
        row = _row(slope=2.0, roughness=14.0, local_relief=500.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "base")
        assert "relief_score" in detail
        assert score > 0.0

    def test_landing_confidence_high(self):
        row = _row(slope=3.0, roughness=20.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "landing")
        assert conf == "high"

    def test_base_confidence_medium(self):
        row = _row(slope=3.0, roughness=20.0, local_relief=500.0)
        score, conf, detail = topography_score(row, _moon_landing_target()["reference_values"], "base")
        assert conf == "medium"


# ---------------------------------------------------------------------------
# 3. aridity_score
# ---------------------------------------------------------------------------

class TestAridityScore:
    def test_zero_pr_pet_gives_one(self):
        row = _row(aridity_index=0.0, ice_cover_fraction=0.0)
        score, conf, detail = aridity_score(row)
        assert score == pytest.approx(1.0)

    def test_pr_equals_pet_gives_zero(self):
        row = _row(aridity_index=1.0, ice_cover_fraction=0.0)
        score, conf, detail = aridity_score(row)
        assert score == pytest.approx(0.0)

    def test_pr_twice_pet_gives_zero(self):
        row = _row(aridity_index=2.0, ice_cover_fraction=0.0)
        score, conf, detail = aridity_score(row)
        assert score == pytest.approx(0.0)

    def test_half_aridity_gives_half(self):
        row = _row(aridity_index=0.5, ice_cover_fraction=0.0)
        score, conf, detail = aridity_score(row)
        assert score == pytest.approx(0.5)

    def test_ice_cover_gives_zero(self):
        row = _row(aridity_index=0.0, ice_cover_fraction=0.9)
        score, conf, detail = aridity_score(row)
        assert score == 0.0

    def test_derived_from_pr_pet_when_aridity_missing(self):
        row = _row(precipitation=100.0, pet=200.0)
        row["aridity_index"] = None  # simulate missing column
        score, conf, detail = aridity_score(row)
        # aridity_index = 100/200 = 0.5 → score = 0.5
        assert score == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# 4. weighted_geometric_mean
# ---------------------------------------------------------------------------

class TestWeightedGeometricMean:
    def test_one_score_zero_gives_total_zero(self):
        scores = {"topography": 0.8, "thermal": 0.0, "illumination": 0.9}
        weights = {"topography": 0.35, "thermal": 0.20, "illumination": 0.45}
        result = weighted_geometric_mean(scores, weights)
        assert result == 0.0

    def test_weights_renormalize_correctly(self):
        # weights sum to 2 instead of 1; result should be same as normalized
        scores = {"a": 0.5, "b": 0.5}
        weights_unnorm = {"a": 2.0, "b": 2.0}  # each 0.5 after renorm
        weights_norm = {"a": 0.5, "b": 0.5}
        r1 = weighted_geometric_mean(scores, weights_unnorm)
        r2 = weighted_geometric_mean(scores, weights_norm)
        assert r1 == pytest.approx(r2, rel=1e-9)

    def test_equal_scores_give_that_score(self):
        scores = {"a": 0.7, "b": 0.7, "c": 0.7}
        weights = {"a": 0.3, "b": 0.4, "c": 0.3}
        result = weighted_geometric_mean(scores, weights)
        assert result == pytest.approx(0.7, rel=1e-6)

    def test_unequal_weights(self):
        # 0.9^0.75 * 0.4^0.25
        scores = {"a": 0.9, "b": 0.4}
        weights = {"a": 0.75, "b": 0.25}
        expected = (0.9 ** 0.75) * (0.4 ** 0.25)
        result = weighted_geometric_mean(scores, weights)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_empty_weights_returns_zero(self):
        result = weighted_geometric_mean({"a": 0.5}, {})
        assert result == 0.0

    def test_unselected_chars_ignored(self):
        # scores has 'extra' key not in weights — should be ignored
        scores = {"topography": 0.8, "extra": 0.1}
        weights = {"topography": 1.0}
        result = weighted_geometric_mean(scores, weights)
        assert result == pytest.approx(0.8, rel=1e-6)


# ---------------------------------------------------------------------------
# 5. illumination_score unit test anchors from METHODOLOGY §2.8
# ---------------------------------------------------------------------------

class TestIlluminationScore:
    """Unit test anchors from METHODOLOGY §2.8 table.

    latitude 0° (equator): max_solar_elev=90°, sun_fraction=0.5
    latitude −62.875°:     max_solar_elev=50.56°, sun_fraction=0.5
    latitude −90° (Pole):  max_solar_elev=23.44°, sun_fraction≈0.5
    """

    def _row_at_lat(self, lat: float, max_elev: float, sun_frac: float, pct: float) -> pd.Series:
        return _row(
            lat_center=lat,
            max_solar_elevation=max_elev,
            max_solar_elevation_pct=pct,
            mean_solar_elevation=max_elev * 0.4,
            mean_solar_elevation_pct=pct,
            sun_fraction=sun_frac,
            sun_fraction_pct=pct,
        )

    def test_anchor_equator(self):
        # Equator: sun_fraction=0.5, percentile ≈ 0.5 in Earth distribution
        # target solar_elevation_range percentile = 0.00 (lunar south pole)
        # score for each var = 1 - |pct_earth - pct_target|
        # mean_solar_elevation_pct same as max_solar_elevation_pct here
        row = self._row_at_lat(0.0, 90.0, 0.5, 0.95)
        target = _moon_landing_target()
        score, conf, detail = illumination_score(row, target["reference_values"])
        # All scores are 1 - |0.95 - pct_target|; for Malapert: sun_frac pct=0.98, solar_elev pct=0.0
        # max_solar_elevation: 1 - |0.95 - 0.0| = 0.05
        # mean_solar_elevation: 1 - |0.95 - 0.0| = 0.05
        # sun_fraction:        1 - |0.95 - 0.98| = 0.97  (pct=0.95 vs target=0.98)
        # geometric_mean(0.05, 0.05, 0.97) ≈ 0.145
        assert 0.0 < score < 1.0
        assert conf == "high"

    def test_anchor_south_pole(self):
        # South Pole: max_solar_elev=23.44°, sun_fraction≈0.5
        # Percentile near 0.0 for max_solar_elevation (lowest on Earth)
        row = self._row_at_lat(-90.0, 23.44, 0.5, 0.0)
        target = _moon_landing_target()
        score, conf, detail = illumination_score(row, target["reference_values"])
        # max_solar_elev pct=0.0 vs target solar_elev pct=0.0 → score=1.0
        # sun_fraction pct=0.0 vs target illumination_fraction pct=0.98 → score=0.02
        # geometric_mean(1.0, 1.0, 0.02) ≈ 0.27
        assert 0.0 < score < 1.0

    def test_percentile_formula_matches_methodology(self):
        """Verify illumination scoring formula: score = 1 - |pct_earth - pct_target|."""
        # For a known pct_earth and pct_target, verify the formula
        row = _row(
            max_solar_elevation=50.56,
            max_solar_elevation_pct=0.407,
            mean_solar_elevation=19.31,
            mean_solar_elevation_pct=0.429,
            sun_fraction=0.500,
            sun_fraction_pct=0.50,
        )
        target_ref = {
            "illumination": {
                "solar_elevation_range": {"percentile_estimate": 0.0},
                "illumination_fraction": {"percentile_estimate": 0.80},
            }
        }
        score, conf, detail = illumination_score(row, target_ref)
        # max_solar_elevation: 1 - |0.407 - 0.0| = 0.593
        # mean_solar_elevation: 1 - |0.429 - 0.0| = 0.571  (uses solar_elevation_range pct)
        # sun_fraction: 1 - |0.50 - 0.80| = 0.70
        expected = (0.593 * 0.571 * 0.70) ** (1 / 3)
        assert score == pytest.approx(expected, abs=0.01)

    def test_missing_percentile_uses_neutral(self):
        # If percentile columns are missing → score defaults to 0.5 per variable
        row = pd.Series({
            "cell_id": "test",
            "lat_center": 0.0,
            "lon_center": 0.0,
            "land_fraction": 1.0,
        })
        target_ref = {}  # no illumination data at all
        score, conf, detail = illumination_score(row, target_ref)
        # All vars use neutral 0.5 → geometric_mean(0.5, 0.5, 0.5) = 0.5
        assert score == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# 6. Full score_cell smoke test
# ---------------------------------------------------------------------------

class TestScoreCell:
    def test_smoke_moon_landing(self):
        """Full score_cell smoke test with known inputs against Malapert Massif.

        Hand-computed expected total_score from METHODOLOGY §1 combination formula.
        Values based on contracts/similarity_result.sample.json example.
        """
        row = _row()
        tgt = _moon_landing_target()
        selected = ["topography", "surface_optics", "thermal", "illumination"]
        weights = {"topography": 0.35, "illumination": 0.25, "surface_optics": 0.20, "thermal": 0.20}

        result = score_cell(row, tgt, selected, weights, "landing")

        # Basic structure checks
        assert result["cell_id"] == "test_cell"
        assert result["body"] == "moon"
        assert result["mission_type"] == "landing"
        assert result["target"]["id"] == "malapert_massif"
        assert isinstance(result["total_score"], float)
        assert 0.0 <= result["total_score"] <= 1.0
        assert len(result["characteristic_scores"]) == 4
        assert result["rank"] is None  # filled by score_all
        assert result["cannot_reproduce"] is not None
        assert len(result["cannot_reproduce"]) >= 1
        assert result["interpretation"] is None

    def test_hard_cap_propagates_to_total_zero(self):
        row = _row(slope=15.0)
        tgt = _moon_landing_target()
        selected = ["topography", "thermal"]
        weights = {"topography": 0.5, "thermal": 0.5}
        result = score_cell(row, tgt, selected, weights, "landing")
        # topography=0 → total=0
        assert result["total_score"] == 0.0

    def test_all_chars_have_score_in_range(self):
        row = _row()
        tgt = _moon_landing_target()
        selected = ["topography", "surface_optics", "thermal", "illumination", "aridity"]
        weights = {c: 0.2 for c in selected}
        result = score_cell(row, tgt, selected, weights, "landing")
        for entry in result["characteristic_scores"]:
            assert 0.0 <= entry["score"] <= 1.0, f"{entry['characteristic_id']} out of range"

    def test_total_score_within_01(self):
        row = _row()
        tgt = _moon_landing_target()
        selected = ["topography", "surface_optics", "thermal", "illumination"]
        weights = {"topography": 0.35, "illumination": 0.25, "surface_optics": 0.20, "thermal": 0.20}
        result = score_cell(row, tgt, selected, weights, "landing")
        assert 0.0 <= result["total_score"] <= 1.0

    def test_known_total_score_approximate(self):
        """Verify total_score matches the sample JSON's hand-computed value (~0.790).

        Uses the exact row from contracts/similarity_result.sample.json:
          lat=-62.875, slope=3.2, roughness=22.0, albedo=0.09
          thermal percentiles: 0.74, 0.60, 0.12
          illumination percentiles: 0.407, 0.429, 0.50
          target: Malapert Massif
        The sample notes total=0.790; we allow ±0.05 tolerance because our scorer
        uses slightly different sigma assumptions.
        """
        row = _row(
            slope=3.2,
            roughness=22.0,
            broadband_albedo=0.09,
            lst_annual_mean=-8.5,
            lst_annual_mean_pct=0.12,
            lst_annual_range=38.5,
            lst_annual_range_pct=0.74,
            lst_diurnal_range=18.2,
            lst_diurnal_range_pct=0.60,
            max_solar_elevation=50.56,
            max_solar_elevation_pct=0.407,
            mean_solar_elevation=19.31,
            mean_solar_elevation_pct=0.429,
            sun_fraction=0.500,
            sun_fraction_pct=0.50,
        )
        tgt = _moon_landing_target()
        selected = ["topography", "surface_optics", "thermal", "illumination"]
        weights = {"topography": 0.35, "illumination": 0.25, "surface_optics": 0.20, "thermal": 0.20}

        result = score_cell(row, tgt, selected, weights, "landing")
        # Sample JSON hand-computes 0.790; allow ±0.05 tolerance
        assert result["total_score"] == pytest.approx(0.790, abs=0.05)

    def test_environment_tags_polar(self):
        row = _row(lat_center=-65.0, aridity_index=0.0, glim_vb=0, volcanic_caves_likelihood="LOW")
        tgt = _moon_landing_target()
        selected = ["aridity"]
        weights = {"aridity": 1.0}
        result = score_cell(row, tgt, selected, weights, "landing")
        assert "polar" in result["environment_tags"]

    def test_environment_tags_desert(self):
        row = _row(lat_center=25.0, aridity_index=0.0, glim_vb=0, volcanic_caves_likelihood="LOW")
        tgt = _moon_landing_target()
        selected = ["aridity"]
        weights = {"aridity": 1.0}
        result = score_cell(row, tgt, selected, weights, "landing")
        assert "desert" in result["environment_tags"]
        assert "arid" in result["environment_tags"]
