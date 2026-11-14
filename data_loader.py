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
    invalid_smoker_count: int = 0
    unexpected_smoker_values: list[str] = field(default_factory=list)
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

    # ── Coerce charges to float64 ─────────────────────────────────────────
    converted_charges = pd.to_numeric(df[COLUMN_CHARGES], errors="coerce")
    null_charges_mask = converted_charges.isna()
    report.null_charges_count = int(null_charges_mask.sum())
    report.non_numeric_charges_count = report.null_charges_count
    df[COLUMN_CHARGES] = converted_charges

    if report.null_charges_count > 0:
        logger.warning(
            "Dropped %d rows with non-numeric or null charges",
            report.null_charges_count,
        )

    # ── Filter valid rows ─────────────────────────────────────────────────
    keep_mask = (~null_charges_mask) & valid_smoker_mask
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
