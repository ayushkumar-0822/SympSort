"""Tests for analysis.py — smoker vs. non-smoker charge calculations."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis import calculate_smoker_charges, SmokerAnalysisResult


# ── 1. Grouped means match expected values on real dataset ───────────────

def test_grouped_means_match_expected(valid_df):
    """Non-smoker ≈ $8,434.27 and smoker ≈ $32,050.23 on the full dataset."""
    result = calculate_smoker_charges(valid_df)

    assert abs(result.non_smoker_mean - 8434.27) < 0.01, (
        f"Non-smoker mean {result.non_smoker_mean} not within ±0.01 of 8434.27"
    )
    assert abs(result.smoker_mean - 32050.23) < 0.01, (
        f"Smoker mean {result.smoker_mean} not within ±0.01 of 32050.23"
    )


# ── 2. Empty DataFrame raises / handles gracefully ──────────────────────

def test_empty_dataframe_raises():
    """Passing an empty DataFrame must raise ValueError."""
    empty_df = pd.DataFrame(columns=["smoker_clean", "charges"])

    with pytest.raises(ValueError, match="empty"):
        calculate_smoker_charges(empty_df)


def test_none_dataframe_raises():
    """Passing None must raise ValueError."""
    with pytest.raises(ValueError):
        calculate_smoker_charges(None)


# ── 3. Missing column raises ValueError ─────────────────────────────────

def test_missing_column_raises():
    """A DataFrame without the required 'charges' column must raise ValueError."""
    df = pd.DataFrame({
        "smoker_clean": ["yes", "no"],
        "age": [25, 30],
    })
    with pytest.raises(ValueError, match="charges"):
        calculate_smoker_charges(df)


# ── 4. Percentage difference ≈ 280.0 ────────────────────────────────────

def test_percentage_difference(valid_df):
    """Percentage difference should be approximately 280.0%."""
    result = calculate_smoker_charges(valid_df)

    assert result.percentage_difference is not None
    assert abs(result.percentage_difference - 280.0) < 0.1, (
        f"Percentage difference {result.percentage_difference} not within ±0.1 of 280.0"
    )


# ── 5. Multiplier ≈ 3.80 ────────────────────────────────────────────────

def test_multiplier_approximately_3_80(valid_df):
    """Smoker mean / non-smoker mean should be ≈ 3.80×."""
    result = calculate_smoker_charges(valid_df)

    multiplier = result.smoker_mean / result.non_smoker_mean
    assert abs(multiplier - 3.80) < 0.01, (
        f"Multiplier {multiplier:.4f} not within ±0.01 of 3.80"
    )


# ── 6. to_dict returns JSON-serializable dict ───────────────────────────

def test_to_dict_is_json_serializable(valid_df):
    """to_dict() must return a dict that json.dumps can handle."""
    import json

    result = calculate_smoker_charges(valid_df)
    d = result.to_dict()

    # Must not raise
    json_str = json.dumps(d)
    assert isinstance(json_str, str)
    assert len(json_str) > 0


# ── 7. Counts add up correctly ───────────────────────────────────────────

def test_counts_add_up(valid_df):
    """smoker_count + non_smoker_count == total_valid_records."""
    result = calculate_smoker_charges(valid_df)

    assert result.smoker_count + result.non_smoker_count == result.total_valid_records


# ── 8. Sample fixture produces expected means ────────────────────────────

def test_sample_df_means(sample_df):
    """Verify analysis works on the small sample fixture with known values."""
    result = calculate_smoker_charges(sample_df)

    expected_non_smoker_mean = (5000.0 + 6000.0 + 7000.0 + 8000.0) / 4  # 6500.0
    expected_smoker_mean = (30000.0 + 40000.0) / 2  # 35000.0

    assert abs(result.non_smoker_mean - expected_non_smoker_mean) < 0.01
    assert abs(result.smoker_mean - expected_smoker_mean) < 0.01
    assert result.smoker_count == 2
    assert result.non_smoker_count == 4


# ── 9. Dynamic p-values & statistical tests genuinely calculated ─────────

def test_dynamic_p_values_and_statistics(valid_df):
    """Welch's t-test and Mann-Whitney U return dynamically calculated values."""
    result = calculate_smoker_charges(valid_df)

    assert result.t_statistic is not None
    assert result.t_statistic > 30.0  # Empirical t-stat on this dataset is ~32.7
    assert result.t_p_value == "< 0.001"
    assert result.mann_whitney_p_value == "< 0.001"
    assert result.cohen_d is not None
    assert result.cohen_d > 2.5  # Documented very large effect size (empirically ~3.16)


def test_students_t_confidence_intervals(valid_df):
    """Verify Student's t confidence intervals use exact critical values."""
    result = calculate_smoker_charges(valid_df)

    # df_ns = 1063 -> t_crit ≈ 1.9622; df_sm = 273 -> t_crit ≈ 1.9687
    assert abs(result.non_smoker_ci_margin - 359.88) < 1.0
    assert abs(result.smoker_ci_margin - 1372.67) < 1.0
    assert result.non_smoker_ci_low < result.non_smoker_mean < result.non_smoker_ci_high
    assert result.smoker_ci_low < result.smoker_mean < result.smoker_ci_high


def test_missing_cohort_handled_gracefully():
    """Dataset with only non-smokers handles missing cohort without crashing."""
    df_ns_only = pd.DataFrame({
        "smoker": ["no", "no", "no"],
        "charges": [1000.0, 2000.0, 3000.0],
    })
    result = calculate_smoker_charges(df_ns_only)

    assert result.non_smoker_count == 3
    assert result.smoker_count == 0
    assert result.smoker_mean == 0.0
    assert result.t_statistic is None
    assert result.t_p_value == "N/A"
    assert result.mann_whitney_p_value == "N/A"
    assert result.cohen_d is None


def test_cohen_d_undefined_on_constant_variance():
    """Cohen's d returns None when variance is zero."""
    from analysis import calculate_cohen_d

    # s1 = 0, s2 = 0
    d = calculate_cohen_d(10.0, 20.0, 0.0, 0.0, 5, 5)
    assert d is None

