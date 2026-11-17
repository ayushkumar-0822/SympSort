"""
Tests for Scenario Comparison Engine and POST /api/scenario-compare Endpoint.
============================================================================
Covers all Block 3 requirements:
1. Valid comparison
2. Empty group (0 matched records returns null statistics, not zero)
3. Small sample warning (n < 20 records)
4. Invalid category (smoker, sex, region) returns HTTP 400
5. Invalid age / BMI range (min > max, negative, non-numeric) returns HTTP 400
6. Same filters on both scenarios (difference = 0.0, higher = 'equal')
7. Percentage denominator zero (returns null, no division by zero error)
8. JSON-safe response (dumps cleanly with no NaN / Infinity)
"""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scenario_analysis import (
    ScenarioFilter,
    compare_empirical_scenarios,
    filter_cohort_dataframe,
    validate_scenario_filter,
)


# ── 1. Valid comparison ────────────────────────────────────────────────────────

def test_valid_scenario_comparison(valid_df):
    """Test valid comparison between non-smokers and smokers aged 30–44."""
    scenario_a = {
        "smoker": "no",
        "sex": "all",
        "region": "all",
        "age_min": 30,
        "age_max": 44,
        "bmi_min": None,
        "bmi_max": None,
        "children": "all",
    }
    scenario_b = {
        "smoker": "yes",
        "sex": "all",
        "region": "all",
        "age_min": 30,
        "age_max": 44,
        "bmi_min": None,
        "bmi_max": None,
        "children": "all",
    }

    result, err = compare_empirical_scenarios(valid_df, scenario_a, scenario_b)
    assert err is None
    assert result is not None
    assert result["status"] == "success"

    # Both cohorts should have matching records in this age range
    assert result["scenario_a"]["matched_records"] > 0
    assert result["scenario_b"]["matched_records"] > 0
    assert result["scenario_a"]["mean"] is not None
    assert result["scenario_b"]["mean"] is not None
    assert result["scenario_b"]["mean"] > result["scenario_a"]["mean"]
    assert result["comparison"]["higher_scenario"] == "scenario_b"
    assert result["comparison"]["difference_mean"] > 0
    assert result["comparison"]["percentage_difference"] > 0
    assert "disclaimer" in result
    assert "not represent individual health risk predictions" in result["disclaimer"]


# ── 2. Empty group returns null statistics, not zero ───────────────────────────

def test_empty_group_returns_null_statistics(valid_df):
    """Filter that matches 0 rows returns null (None) for statistics, not zero."""
    scenario_a = {
        "smoker": "no",
        "sex": "all",
        "region": "northeast",
        "age_min": 18,
        "age_max": 19,
        "bmi_min": 50.0,  # Extreme BMI, no 18-19yo in northeast has BMI >= 50
        "bmi_max": 60.0,
        "children": "all",
    }
    scenario_b = {
        "smoker": "yes",
        "sex": "all",
        "region": "all",
        "age_min": 20,
        "age_max": 30,
        "bmi_min": None,
        "bmi_max": None,
        "children": "all",
    }

    result, err = compare_empirical_scenarios(valid_df, scenario_a, scenario_b)
    assert err is None
    assert result["scenario_a"]["matched_records"] == 0
    assert result["scenario_a"]["mean"] is None
    assert result["scenario_a"]["median"] is None
    assert result["scenario_a"]["min"] is None
    assert result["scenario_a"]["max"] is None
    assert result["scenario_a"]["std"] is None
    assert result["scenario_a"]["has_data"] is False

    # Comparison metrics should handle missing cohort gracefully
    assert result["comparison"]["difference_mean"] is None
    assert result["comparison"]["percentage_difference"] is None
    assert any("Scenario A matched 0 records" in w for w in result["warnings"])


# ── 3. Small sample warning (n < 20) ───────────────────────────────────────────

def test_small_sample_warning(valid_df):
    """Cohorts with 1 <= n < 20 generate a statistical variance warning."""
    # Narrow filter: Smokers with 4 or 5 children
    scenario_a = {
        "smoker": "yes",
        "sex": "female",
        "region": "southwest",
        "age_min": 40,
        "age_max": 50,
        "bmi_min": None,
        "bmi_max": None,
        "children": "all",
    }
    scenario_b = {
        "smoker": "no",
        "sex": "all",
        "region": "all",
        "age_min": 40,
        "age_max": 50,
        "bmi_min": None,
        "bmi_max": None,
        "children": "all",
    }

    result, err = compare_empirical_scenarios(valid_df, scenario_a, scenario_b)
    assert err is None
    count_a = result["scenario_a"]["matched_records"]
    assert 0 < count_a < 20
    assert any("small sample size" in w and "Scenario A" in w for w in result["warnings"])


# ── 4. Invalid categories reject with clear error ──────────────────────────────

def test_invalid_categories():
    """Unknown categories for smoker, sex, or region are rejected."""
    # Invalid smoker
    sf, err = validate_scenario_filter({"smoker": "maybe"})
    assert sf is None
    assert "Invalid value for 'scenario.smoker'" in err

    # Invalid sex
    sf, err = validate_scenario_filter({"sex": "unknown"})
    assert sf is None
    assert "Invalid value for 'scenario.sex'" in err

    # Invalid region
    sf, err = validate_scenario_filter({"region": "atlantis"})
    assert sf is None
    assert "Invalid value for 'scenario.region'" in err


# ── 5. Invalid age / BMI range reject with clear error ─────────────────────────

def test_invalid_age_and_bmi_ranges():
    """Inverted, negative, or malformed numeric ranges are rejected."""
    # Inverted age: min > max
    sf, err = validate_scenario_filter({"age_min": 50, "age_max": 30})
    assert sf is None
    assert "cannot exceed" in err

    # Negative age
    sf, err = validate_scenario_filter({"age_min": -5})
    assert sf is None
    assert "outside acceptable range" in err

    # Non-numeric string
    sf, err = validate_scenario_filter({"bmi_min": "not_a_number"})
    assert sf is None
    assert "must be a valid number" in err

    # Inverted BMI: min > max
    sf, err = validate_scenario_filter({"bmi_min": 45.0, "bmi_max": 25.0})
    assert sf is None
    assert "cannot exceed" in err


# ── 6. Same filters on both scenarios ──────────────────────────────────────────

def test_same_filters_on_both_scenarios(valid_df):
    """Identical filters result in 0 difference and 'equal' higher cohort."""
    criteria = {
        "smoker": "all",
        "sex": "male",
        "region": "northwest",
        "age_min": 25,
        "age_max": 55,
        "bmi_min": None,
        "bmi_max": None,
        "children": "all",
    }

    result, err = compare_empirical_scenarios(valid_df, criteria, criteria)
    assert err is None
    assert result["scenario_a"]["matched_records"] == result["scenario_b"]["matched_records"]
    assert result["comparison"]["difference_mean"] == 0.0
    assert result["comparison"]["percentage_difference"] == 0.0
    assert result["comparison"]["higher_scenario"] == "equal"


# ── 7. Percentage denominator zero ─────────────────────────────────────────────

def test_percentage_denominator_zero():
    """When baseline mean is 0 or unavailable, percentage difference is None."""
    import pandas as pd

    # Mock DataFrame where charges are 0
    zero_df = pd.DataFrame({
        "smoker": ["no", "yes"],
        "sex": ["female", "female"],
        "region": ["northwest", "northwest"],
        "age": [30, 30],
        "bmi": [25.0, 25.0],
        "children": [0, 0],
        "charges": [0.0, 5000.0],
    })

    result, err = compare_empirical_scenarios(
        zero_df,
        {"smoker": "no"},
        {"smoker": "yes"},
    )
    assert err is None
    assert result["scenario_a"]["mean"] == 0.0
    assert result["comparison"]["percentage_difference"] is None


# ── 8. JSON-safe response ──────────────────────────────────────────────────────

def test_json_safe_response(valid_df):
    """Result must be completely serializable via json.dumps without NaN/Inf."""
    criteria_a = {"smoker": "no"}
    criteria_b = {"smoker": "yes"}

    result, err = compare_empirical_scenarios(valid_df, criteria_a, criteria_b)
    assert err is None

    # Serialization check
    serialized = json.dumps(result)
    assert isinstance(serialized, str)
    assert "NaN" not in serialized
    assert "Infinity" not in serialized

    # Deserialize back
    loaded = json.loads(serialized)
    assert loaded["status"] == "success"


# ── 9. Flask POST /api/scenario-compare HTTP endpoint ──────────────────────────

def test_post_scenario_compare_endpoint(client):
    """Test POST /api/scenario-compare with valid and invalid JSON payloads."""
    # Valid POST payload
    payload = {
        "scenario_a": {
            "smoker": "no",
            "sex": "all",
            "region": "all",
            "age_min": 30,
            "age_max": 44,
            "bmi_min": None,
            "bmi_max": None,
            "children": "all",
        },
        "scenario_b": {
            "smoker": "yes",
            "sex": "all",
            "region": "all",
            "age_min": 30,
            "age_max": 44,
            "bmi_min": None,
            "bmi_max": None,
            "children": "all",
        },
    }

    res = client.post("/api/scenario-compare", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["scenario_a"]["matched_records"] > 0
    assert data["scenario_b"]["matched_records"] > 0
    assert data["comparison"]["higher_scenario"] == "scenario_b"


def test_post_scenario_compare_400_on_invalid_input(client):
    """Test POST /api/scenario-compare returns 400 with descriptive error message."""
    # Missing scenario_b
    res1 = client.post("/api/scenario-compare", json={"scenario_a": {}})
    assert res1.status_code == 400
    assert "Payload must contain both" in res1.get_json()["message"]

    # Invalid category
    res2 = client.post("/api/scenario-compare", json={
        "scenario_a": {"smoker": "invalid_smoker"},
        "scenario_b": {"smoker": "yes"},
    })
    assert res2.status_code == 400
    assert "Invalid value for 'scenario_a.smoker'" in res2.get_json()["message"]

    # Inverted age range
    res3 = client.post("/api/scenario-compare", json={
        "scenario_a": {"age_min": 60, "age_max": 20},
        "scenario_b": {"smoker": "yes"},
    })
    assert res3.status_code == 400
    assert "age_min" in res3.get_json()["message"]
