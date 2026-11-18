"""Tests for Scenario Comparison engine and API endpoint."""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis import filter_cohort, compare_scenarios


def test_filter_cohort_smoker(valid_df):
    """filter_cohort properly isolates smokers and non-smokers."""
    smokers = filter_cohort(valid_df, {"smoker": "yes"})
    non_smokers = filter_cohort(valid_df, {"smoker": "no"})
    assert len(smokers) == 274
    assert len(non_smokers) == 1064


def test_filter_cohort_multi_parameter(valid_df):
    """filter_cohort filters by age, bmi, and smoker correctly."""
    subset = filter_cohort(valid_df, {
        "age_band": "18-29",
        "bmi_band": ">=30",
        "smoker": "yes",
    })
    assert len(subset) > 0
    assert (subset["age"] <= 29).all()
    assert (subset["bmi"] >= 30.0).all()
    assert (subset["smoker"] == "yes").all()


def test_compare_scenarios_smoker_vs_nonsmoker(valid_df):
    """compare_scenarios on full dataset reproduces empirical means and Welch's t-test."""
    res = compare_scenarios(valid_df, {"smoker": "no"}, {"smoker": "yes"})
    assert res["status"] == "success"
    assert res["cohort_a"]["count"] == 1064
    assert res["cohort_b"]["count"] == 274
    assert abs(res["cohort_a"]["mean"] - 8434.27) < 0.05
    assert abs(res["cohort_b"]["mean"] - 32050.23) < 0.05
    assert res["diff_mean"] > 23000
    assert res["higher_cohort"] == "b"
    assert res["t_statistic"] is not None
    assert "< 0.001" in res["p_value"]
    # Verify non-causal disclaimer is present
    assert "observational dataset" in res["statement"]
    assert "does not constitute an individual health risk prediction" in res["statement"]


def test_compare_scenarios_empty_subgroup(valid_df):
    """compare_scenarios handles empty subgroups gracefully with warning."""
    # Impossible criteria: age 18-29 with age 60 (filtered via contradictory dummy criteria)
    res = compare_scenarios(
        valid_df,
        {"age_band": "18-29", "region": "nonexistent_region"},
        {"smoker": "yes"},
    )
    assert res["status"] == "success"
    assert res["cohort_a"]["count"] == 0
    assert len(res["warnings"]) > 0
    assert "Cohort A contains 0 matching records" in res["warnings"][0]


def test_api_scenario_compare_endpoint(client):
    """Test the Flask GET /api/scenario-compare endpoint."""
    res = client.get("/api/scenario-compare?a_smoker=no&b_smoker=yes")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["cohort_a"]["count"] == 1064
    assert data["cohort_b"]["count"] == 274
    assert data["higher_cohort"] == "b"
    assert data["multiplier"] >= 3.7
