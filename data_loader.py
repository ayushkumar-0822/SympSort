"""
SympSort — Data Loader
=======================
Reads, validates, and cleans the insurance CSV dataset.

The primary entry-point is :func:`load_dataset`, which returns a cleaned
DataFrame, the raw DataFrame, and a :class:`ValidationReport` summarising
what was kept and what was excluded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

import config
from config import (
    COLUMN_CHARGES,
    COLUMN_SMOKER,
    DEFAULT_DATA_PATH,
    REQUIRED_COLUMNS,
    SAMPLE_DATA_PATH,
    VALID_SMOKER_VALUES,
)

logger = logging.getLogger(__name__)


# ── Validation report ─────────────────────────────────────────────────────────

@dataclass
class ValidationReport:
    """Summary produced after loading and cleaning a dataset."""

    is_valid: bool = False
    file_path: str = ""
    total_raw_rows: int = 0
    total_raw_cols: int = 0
    valid_rows: int = 0
    excluded_rows: int = 0
    missing_required_cols: list[str] = field(default_factory=list)
    null_charges_count: int = 0
    non_numeric_charges_count: int = 0
    negative_charges_count: int = 0
    invalid_smoker_count: int = 0
    unexpected_smoker_values: list[str] = field(default_factory=list)
    demographic_validation: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    warning_messages: list[str] = field(default_factory=list)
    used_sample: bool = False

    @property
    def missing_columns(self) -> list[str]:
        return self.missing_required_cols

    @missing_columns.setter
    def missing_columns(self, val: list[str]) -> None:
        self.missing_required_cols = val

    @property
    def warnings(self) -> list[str]:
        return self.warning_messages

    @warnings.setter
    def warnings(self, val: list[str]) -> None:
        self.warning_messages = val

    @property
    def exclusion_rate(self) -> float:
        """Percentage of raw rows that were excluded."""
        if self.total_raw_rows == 0:
            return 0.0
        return (self.excluded_rows / self.total_raw_rows) * 100


# ── Public API ────────────────────────────────────────────────────────────────

def load_dataset(
    path: Optional[Path] = None,
) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], ValidationReport]:
    """Load and validate the insurance dataset.

    Parameters
    ----------
    path:
        Explicit CSV path. Falls back to ``DEFAULT_DATA_PATH`` and then
        ``SAMPLE_DATA_PATH`` only when *path* is ``None``.

    Returns
    -------
    tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], ValidationReport]
        ``(df_valid, df_raw, report)``
    """
    report = ValidationReport()

    # ── Handle explicit path vs default fallback ──────────────────────────
    if path is not None:
        resolved_path = Path(path)
        if not resolved_path.is_file():
            report.file_path = str(resolved_path)
            report.error_message = f"Dataset file not found: {resolved_path}"
            report.is_valid = False
            logger.error("Dataset file not found: %s", resolved_path)
            return None, None, report
    else:
        # Fallback to default or sample
        resolved_path = None
        if DEFAULT_DATA_PATH.is_file():
            resolved_path = DEFAULT_DATA_PATH
        elif SAMPLE_DATA_PATH.is_file():
            resolved_path = SAMPLE_DATA_PATH
            report.used_sample = True
            report.warning_messages.append("Using sample dataset fallback.")
            logger.warning("Default dataset not found, using sample: %s", SAMPLE_DATA_PATH)
        else:
            report.error_message = "No dataset file found at default or sample paths."
            report.is_valid = False
            return None, None, report

    report.file_path = str(resolved_path)
    logger.info("Loading dataset from %s", resolved_path)

    # ── Read CSV ──────────────────────────────────────────────────────────
    try:
        df_raw = pd.read_csv(resolved_path)
    except Exception as exc:
        logger.error("Failed to read CSV %s: %s", resolved_path, exc)
        report.error_message = f"CSV read error: {exc}"
        report.warning_messages.append(str(exc))
        report.is_valid = False
        return None, None, report

    report.total_raw_rows = len(df_raw)
    report.total_raw_cols = len(df_raw.columns)
    logger.info("Raw rows read: %d, columns: %d", report.total_raw_rows, report.total_raw_cols)

    if report.total_raw_rows == 0:
        report.error_message = "CSV file contains no data rows."
        report.is_valid = False
        return None, df_raw, report

    # ── Normalise column names ────────────────────────────────────────────
    df_raw.columns = df_raw.columns.str.strip().str.lower()

    # ── Check required columns ────────────────────────────────────────────
    missing = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]
    if missing:
        report.missing_required_cols = missing
        report.error_message = f"Missing required columns: {missing}"
        report.warning_messages.append(f"Missing required columns: {missing}")
        logger.error("Missing required columns: %s", missing)
        report.is_valid = False
        return None, df_raw, report

    # ── Clean smoker column ───────────────────────────────────────────────
    df = df_raw.copy()
    raw_smoker = df[COLUMN_SMOKER].astype(str).str.strip().str.lower()
    df["smoker_clean"] = raw_smoker
    df[COLUMN_SMOKER] = raw_smoker

    # Identify invalid / unexpected smoker values
    valid_smoker_mask = raw_smoker.isin(VALID_SMOKER_VALUES)
    unexpected = [
        val for val in raw_smoker[~valid_smoker_mask].unique()
        if str(val) != "nan"
    ]
    report.unexpected_smoker_values = list(unexpected)
    report.invalid_smoker_count = int((~valid_smoker_mask).sum())
    if report.invalid_smoker_count > 0:
        logger.warning(
            "Flagged %d rows with invalid smoker values: %s",
            report.invalid_smoker_count,
            report.unexpected_smoker_values,
        )

    # ── Coerce charges to float64, distinguish null vs non-numeric, reject negatives ──
    raw_charges = df[COLUMN_CHARGES]
    is_missing_mask = raw_charges.isna() | (raw_charges.astype(str).str.strip().str.lower().isin(["", "nan", "none", "null"]))
    converted_charges = pd.to_numeric(raw_charges, errors="coerce")
    is_non_numeric_mask = (~is_missing_mask) & converted_charges.isna()
    is_negative_mask = (~converted_charges.isna()) & (converted_charges < getattr(config, "MIN_CHARGE", 0.0))

    report.null_charges_count = int(is_missing_mask.sum())
    report.non_numeric_charges_count = int(is_non_numeric_mask.sum())
    report.negative_charges_count = int(is_negative_mask.sum())
    df[COLUMN_CHARGES] = converted_charges

    if report.null_charges_count > 0:
        report.warning_messages.append(f"Found {report.null_charges_count} rows with missing charges.")
    if report.non_numeric_charges_count > 0:
        report.warning_messages.append(f"Found {report.non_numeric_charges_count} rows with non-numeric charges.")
    if report.negative_charges_count > 0:
        report.warning_messages.append(f"Rejected {report.negative_charges_count} rows with negative charges (< {getattr(config, 'MIN_CHARGE', 0.0)}).")

    # ── Validate optional demographic columns ─────────────────────────────
    demo_status = {}
    if getattr(config, "COLUMN_AGE", "age") in df.columns:
        converted_age = pd.to_numeric(df[config.COLUMN_AGE], errors="coerce")
        invalid_age = converted_age.isna() | (converted_age < getattr(config, "MIN_AGE", 0)) | (converted_age > getattr(config, "MAX_AGE", 120))
        demo_status[config.COLUMN_AGE] = {"valid": int((~invalid_age).sum()), "invalid": int(invalid_age.sum())}
    if getattr(config, "COLUMN_BMI", "bmi") in df.columns:
        converted_bmi = pd.to_numeric(df[config.COLUMN_BMI], errors="coerce")
        invalid_bmi = converted_bmi.isna() | (converted_bmi < getattr(config, "MIN_BMI", 10.0)) | (converted_bmi > getattr(config, "MAX_BMI", 100.0))
        demo_status[config.COLUMN_BMI] = {"valid": int((~invalid_bmi).sum()), "invalid": int(invalid_bmi.sum())}
    if getattr(config, "COLUMN_SEX", "sex") in df.columns:
        clean_sex = df[config.COLUMN_SEX].astype(str).str.strip().str.lower()
        invalid_sex = ~clean_sex.isin(getattr(config, "VALID_SEXES", {"female", "male"}))
        demo_status[config.COLUMN_SEX] = {"valid": int((~invalid_sex).sum()), "invalid": int(invalid_sex.sum())}
    if getattr(config, "COLUMN_REGION", "region") in df.columns:
        clean_region = df[config.COLUMN_REGION].astype(str).str.strip().str.lower()
        invalid_region = ~clean_region.isin(getattr(config, "VALID_REGIONS", ["northeast", "northwest", "southeast", "southwest"]))
        demo_status[config.COLUMN_REGION] = {"valid": int((~invalid_region).sum()), "invalid": int(invalid_region.sum())}
    if getattr(config, "COLUMN_CHILDREN", "children") in df.columns:
        converted_children = pd.to_numeric(df[config.COLUMN_CHILDREN], errors="coerce")
        invalid_children = converted_children.isna() | (converted_children < getattr(config, "MIN_CHILDREN", 0)) | (converted_children > getattr(config, "MAX_CHILDREN", 20))
        demo_status[config.COLUMN_CHILDREN] = {"valid": int((~invalid_children).sum()), "invalid": int(invalid_children.sum())}
    report.demographic_validation = demo_status

    # ── Filter valid rows ─────────────────────────────────────────────────
    keep_mask = (~converted_charges.isna()) & (~is_negative_mask) & valid_smoker_mask
    df_valid = df.loc[keep_mask].copy()

    # ── Final counts ──────────────────────────────────────────────────────
    report.valid_rows = len(df_valid)
    report.excluded_rows = report.total_raw_rows - report.valid_rows
    report.is_valid = report.valid_rows > 0

    if not report.is_valid:
        report.error_message = "No valid records remained after data cleaning."

    logger.info(
        "Validation complete — valid: %d, excluded: %d (%.1f%%)",
        report.valid_rows,
        report.excluded_rows,
        report.exclusion_rate,
    )

    return df_valid, df_raw, report
