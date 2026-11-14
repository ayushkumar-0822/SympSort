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
