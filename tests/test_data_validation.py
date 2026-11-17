"""Tests for data_loader.py — dataset loading, validation, and cleaning."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_loader import load_dataset, ValidationReport


# ── 1. Missing file returns is_valid=False ────────────────────────────────

def test_missing_file_returns_invalid(tmp_path):
    """Loading a non-existent CSV must yield is_valid=False."""
    missing = tmp_path / "does_not_exist.csv"
    df_valid, df_raw, report = load_dataset(missing)

    assert report.is_valid is False
    assert df_valid is None
    assert "not found" in (report.error_message or "").lower()


# ── 2. Missing 'smoker' column detected ──────────────────────────────────

def test_missing_smoker_column(tmp_path):
    """A CSV without a 'smoker' column must fail validation."""
    csv_path = tmp_path / "no_smoker.csv"
    df = pd.DataFrame({"charges": [100, 200], "age": [25, 30]})
    df.to_csv(csv_path, index=False)

    _, _, report = load_dataset(csv_path)

    assert report.is_valid is False
    assert "smoker" in report.missing_required_cols


# ── 3. Missing 'charges' column detected ─────────────────────────────────

def test_missing_charges_column(tmp_path):
    """A CSV without a 'charges' column must fail validation."""
    csv_path = tmp_path / "no_charges.csv"
    df = pd.DataFrame({"smoker": ["yes", "no"], "age": [25, 30]})
    df.to_csv(csv_path, index=False)

    _, _, report = load_dataset(csv_path)

    assert report.is_valid is False
    assert "charges" in report.missing_required_cols


# ── 4. Non-numeric charges are coerced / excluded ────────────────────────

def test_non_numeric_charges_excluded(tmp_path):
    """Rows with non-numeric charge strings must be excluded from valid data."""
    csv_path = tmp_path / "bad_charges.csv"
    df = pd.DataFrame({
        "smoker": ["yes", "no", "yes", "no"],
        "charges": [1000.0, 2000.0, "not_a_number", 3000.0],
        "age": [25, 30, 35, 40],
        "sex": ["male", "female", "male", "female"],
        "bmi": [22.0, 28.0, 30.0, 25.0],
        "children": [0, 1, 2, 0],
        "region": ["southwest", "southeast", "northwest", "northeast"],
    })
    df.to_csv(csv_path, index=False)

    df_valid, _, report = load_dataset(csv_path)

    assert report.is_valid is True
    assert report.non_numeric_charges_count >= 1
    # The row with "not_a_number" must not appear in valid data
    assert len(df_valid) == 3


# ── 5. Whitespace in smoker values is trimmed correctly ──────────────────

def test_whitespace_smoker_values_trimmed(tmp_path):
    """Leading/trailing whitespace in the smoker column must be stripped."""
    csv_path = tmp_path / "whitespace.csv"
    df = pd.DataFrame({
        "smoker": ["  yes  ", " no", "yes ", "no"],
        "charges": [10000.0, 5000.0, 12000.0, 6000.0],
        "age": [25, 30, 35, 40],
        "sex": ["male", "female", "male", "female"],
        "bmi": [22.0, 28.0, 30.0, 25.0],
        "children": [0, 1, 2, 0],
        "region": ["southwest", "southeast", "northwest", "northeast"],
    })
    df.to_csv(csv_path, index=False)

    df_valid, _, report = load_dataset(csv_path)

    assert report.is_valid is True
    # All 4 rows should survive after trimming
    assert report.valid_rows == 4
    # Verify normalized values
    smoker_vals = set(df_valid["smoker_clean"].unique())
    assert smoker_vals == {"yes", "no"}


# ── 6. Unexpected smoker categories are logged ───────────────────────────

def test_unexpected_smoker_categories_logged(tmp_path):
    """Unrecognized smoker values (e.g., 'maybe') must be flagged and excluded."""
    csv_path = tmp_path / "unexpected.csv"
    df = pd.DataFrame({
        "smoker": ["yes", "no", "maybe", "sometimes", "no"],
        "charges": [10000.0, 5000.0, 8000.0, 9000.0, 6000.0],
        "age": [25, 30, 35, 40, 45],
        "sex": ["male", "female", "male", "female", "male"],
        "bmi": [22.0, 28.0, 30.0, 25.0, 27.0],
        "children": [0, 1, 2, 0, 3],
        "region": ["southwest", "southeast", "northwest", "northeast", "southwest"],
    })
    df.to_csv(csv_path, index=False)

    df_valid, _, report = load_dataset(csv_path)

    assert report.is_valid is True
    assert report.invalid_smoker_count == 2
    assert "maybe" in report.unexpected_smoker_values
    assert "sometimes" in report.unexpected_smoker_values
    # Only 3 valid rows remain (yes, no, no)
    assert report.valid_rows == 3


# ── 7. Empty CSV file handled gracefully ─────────────────────────────────

def test_empty_csv_file(tmp_path):
    """A completely empty CSV file should return is_valid=False."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")

    _, _, report = load_dataset(csv_path)

    assert report.is_valid is False


# ── 8. CSV with only headers and no data rows ────────────────────────────

def test_csv_headers_only(tmp_path):
    """A CSV with headers but no data rows should return is_valid=False."""
    csv_path = tmp_path / "headers_only.csv"
    csv_path.write_text("smoker,charges,age\n")

    _, _, report = load_dataset(csv_path)

    assert report.is_valid is False


# ── 9. Distinguish missing vs. non-numeric charges ───────────────────────

def test_distinguish_null_vs_non_numeric_charges(tmp_path):
    """Validation report cleanly separates null charges from string/malformed charges."""
    csv_path = tmp_path / "mixed_bad_charges.csv"
    csv_content = (
        "smoker,charges,age,sex,bmi,children,region\n"
        "yes,,25,female,22.0,0,southwest\n"            # null charge
        "no,invalid_str,30,male,25.0,1,southeast\n"    # non-numeric charge
        "yes,15000.50,35,female,28.0,0,northwest\n"   # valid
    )
    csv_path.write_text(csv_content)

    df_valid, _, report = load_dataset(csv_path)

    assert report.is_valid is True
    assert report.null_charges_count == 1
    assert report.non_numeric_charges_count == 1
    assert len(df_valid) == 1
    assert abs(df_valid.iloc[0]["charges"] - 15000.50) < 0.01


# ── 10. Reject negative charges ──────────────────────────────────────────

def test_reject_negative_charges(tmp_path):
    """Negative insurance charges must be flagged and excluded from valid records."""
    csv_path = tmp_path / "negative_charges.csv"
    df = pd.DataFrame({
        "smoker": ["yes", "no", "yes"],
        "charges": [12000.0, -500.0, 18000.0],
        "age": [25, 30, 35],
        "sex": ["male", "female", "male"],
        "bmi": [24.0, 26.0, 28.0],
        "children": [0, 1, 2],
        "region": ["southwest", "southeast", "northwest"],
    })
    df.to_csv(csv_path, index=False)

    df_valid, _, report = load_dataset(csv_path)

    assert report.is_valid is True
    assert report.negative_charges_count == 1
    assert len(df_valid) == 2
    assert (df_valid["charges"] >= 0).all()


# ── 11. Demographic column validation ────────────────────────────────────

def test_demographic_validation_report(tmp_path):
    """Demographic ranges (age, bmi, sex, region, children) are validated in report."""
    csv_path = tmp_path / "demographics.csv"
    df = pd.DataFrame({
        "smoker": ["no", "yes"],
        "charges": [5000.0, 25000.0],
        "age": [30, 150],  # 150 exceeds MAX_AGE (120)
        "sex": ["female", "alien"],  # alien invalid sex
        "bmi": [24.5, 150.0],  # 150 exceeds MAX_BMI (100)
        "children": [1, 25],  # 25 exceeds MAX_CHILDREN (20)
        "region": ["northwest", "mars"],  # mars invalid region
    })
    df.to_csv(csv_path, index=False)

    _, _, report = load_dataset(csv_path)

    assert report.demographic_validation is not None
    assert report.demographic_validation["age"]["invalid"] == 1
    assert report.demographic_validation["sex"]["invalid"] == 1
    assert report.demographic_validation["bmi"]["invalid"] == 1
    assert report.demographic_validation["children"]["invalid"] == 1
    assert report.demographic_validation["region"]["invalid"] == 1
