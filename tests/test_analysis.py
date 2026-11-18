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


# ── 13. Statistical rigor and mathematical validity tests ─────────────────────

def test_welch_t_test_against_scipy():
    """calculate_welch_t_test must match scipy.stats.ttest_ind(equal_var=False) exactly."""
    import scipy.stats as stats
    from analysis import calculate_welch_t_test

    s1 = pd.Series([100.0, 150.0, 120.0, 130.0, 180.0])
    s2 = pd.Series([300.0, 420.0, 390.0, 450.0, 500.0, 480.0])

    t_stat, p_val, df = calculate_welch_t_test(s1, s2)
    expected = stats.ttest_ind(s2, s1, equal_var=False)

    assert t_stat is not None
    assert p_val is not None
    assert abs(t_stat - expected.statistic) < 1e-4
    assert abs(p_val - expected.pvalue) < 1e-4


def test_mann_whitney_u_against_scipy():
    """calculate_mann_whitney_u must match scipy.stats.mannwhitneyu(alternative='two-sided')."""
    import scipy.stats as stats
    from analysis import calculate_mann_whitney_u

    s1 = pd.Series([10.0, 15.0, 12.0, 14.0, 18.0])
    s2 = pd.Series([30.0, 42.0, 39.0, 45.0, 50.0])

    u_stat, p_val = calculate_mann_whitney_u(s1, s2)
    expected = stats.mannwhitneyu(s2, s1, alternative="two-sided")

    assert u_stat is not None
    assert p_val is not None
    assert abs(u_stat - expected.statistic) < 1e-4
    assert abs(p_val - expected.pvalue) < 1e-4


def test_welch_t_test_edge_cases():
    """calculate_welch_t_test handles n < 2, constant values, and zero variance cleanly."""
    from analysis import calculate_welch_t_test

    # Sample size < 2
    t, p, df = calculate_welch_t_test(pd.Series([10.0]), pd.Series([20.0, 30.0]))
    assert t is None and p is None and df is None

    # Both constant with identical means
    t, p, df = calculate_welch_t_test(pd.Series([5.0, 5.0, 5.0]), pd.Series([5.0, 5.0]))
    assert t == 0.0
    assert p == 1.0

    # Both constant with different means (standard error = 0, mathematically undefined)
    t, p, df = calculate_welch_t_test(pd.Series([5.0, 5.0, 5.0]), pd.Series([10.0, 10.0]))
    assert t is None and p is None and df is None


def test_student_t_critical_exact_values():
    """student_t_critical returns exact Student's t quantiles, never a fixed 1.96 for small n."""
    import scipy.stats as stats
    from analysis import student_t_critical

    for df in [1, 2, 5, 10, 29, 30, 100, 1000]:
        val = student_t_critical(df=df, alpha=0.05)
        expected = float(stats.t.ppf(0.975, df=df))
        assert abs(val - expected) < 1e-2, f"Discrepancy at df={df}: got {val}, expected {expected}"

    # For small n (e.g. df=1), value is ≈ 12.71, NOT 1.96!
    assert student_t_critical(df=1, alpha=0.05) > 12.0
    assert student_t_critical(df=2, alpha=0.05) > 4.0


def test_cohen_d_formula_exactness():
    """calculate_cohen_d computes pooled standard deviation correctly."""
    import math
    from analysis import calculate_cohen_d

    m1, m2 = 100.0, 150.0
    s1, s2 = 15.0, 20.0
    n1, n2 = 10, 15

    # Manual pooled variance
    pooled_var = (((n1 - 1) * (s1 ** 2)) + ((n2 - 1) * (s2 ** 2))) / (n1 + n2 - 2)
    expected_d = abs(m2 - m1) / math.sqrt(pooled_var)

    d = calculate_cohen_d(m1, m2, s1, s2, n1, n2)
    assert d is not None
    assert abs(d - expected_d) < 1e-5

    # Edge cases: n1 + n2 <= 2
    assert calculate_cohen_d(m1, m2, s1, s2, 1, 1) is None


