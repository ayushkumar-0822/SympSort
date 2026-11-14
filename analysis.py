"""
SympSort — Statistical Analysis
================================
Core statistical calculations comparing medical insurance charges for smokers
versus non-smokers using Pandas.

The primary computation is:
    df.groupby('smoker')['charges'].mean()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

from config import COLUMN_CHARGES, COLUMN_SMOKER

logger = logging.getLogger(__name__)


# ── Analysis result dataclass ─────────────────────────────────────────────────

@dataclass
class SmokerAnalysisResult:
    """Encapsulates all statistical outputs comparing smoker cohorts."""

    total_valid_records: int = 0
    smoker_count: int = 0
    non_smoker_count: int = 0

    smoker_mean: float = 0.0
    non_smoker_mean: float = 0.0

    absolute_difference: float = 0.0
    percentage_difference: Optional[float] = None
    multiplier: float = 0.0

    smoker_median: float = 0.0
    non_smoker_median: float = 0.0
    smoker_std: float = 0.0
    non_smoker_std: float = 0.0
    smoker_min: float = 0.0
    smoker_max: float = 0.0
    non_smoker_min: float = 0.0
    non_smoker_max: float = 0.0

    dynamic_statement: str = ""
    academic_disclaimer: str = (
        "This analysis is for academic purposes only (PCC CS 393). "
        "The dataset is publicly available on Kaggle and results should not "
        "be used for clinical or actuarial decision-making."
    )

    df_grouped: Optional[pd.Series] = None
    groupby_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "total_valid_records": self.total_valid_records,
            "smoker_count": self.smoker_count,
            "non_smoker_count": self.non_smoker_count,
            "smoker_mean": round(self.smoker_mean, 2),
            "non_smoker_mean": round(self.non_smoker_mean, 2),
            "absolute_difference": round(self.absolute_difference, 2),
            "percentage_difference": (
                round(self.percentage_difference, 2)
                if self.percentage_difference is not None
                else None
            ),
            "multiplier": round(self.multiplier, 2),
            "smoker_median": round(self.smoker_median, 2),
            "non_smoker_median": round(self.non_smoker_median, 2),
            "smoker_std": round(self.smoker_std, 2),
            "non_smoker_std": round(self.non_smoker_std, 2),
            "smoker_min": round(self.smoker_min, 2),
            "smoker_max": round(self.smoker_max, 2),
            "non_smoker_min": round(self.non_smoker_min, 2),
            "non_smoker_max": round(self.non_smoker_max, 2),
            "dynamic_statement": self.dynamic_statement,
            "academic_disclaimer": self.academic_disclaimer,
            "groupby_text": self.groupby_text,
        }


# ── Core analysis function ───────────────────────────────────────────────────

def calculate_smoker_charges(df: pd.DataFrame) -> SmokerAnalysisResult:
    """Analyse smoker vs non-smoker charges.

    The core computation is the literal Pandas groupby::

        df.groupby('smoker')['charges'].mean()

    Parameters
    ----------
    df:
        Cleaned DataFrame with at least ``smoker`` and ``charges`` columns.

    Returns
    -------
    SmokerAnalysisResult
        Populated dataclass with all statistics.
    """
    if df is None:
        raise ValueError("DataFrame cannot be None")

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df)}")

    if len(df) == 0:
        raise ValueError("DataFrame cannot be empty")

    if COLUMN_CHARGES not in df.columns:
        raise ValueError(f"Missing required column '{COLUMN_CHARGES}'")

    if COLUMN_SMOKER not in df.columns:
        if "smoker_clean" in df.columns:
            df = df.copy()
            df[COLUMN_SMOKER] = df["smoker_clean"]
        else:
            raise ValueError(f"Missing required column '{COLUMN_SMOKER}'")

    result = SmokerAnalysisResult()
    result.total_valid_records = len(df)

    # ── Core groupby — the literal assigned Pandas step ───────────────────
    grouped = df.groupby('smoker')['charges'].mean()
    result.df_grouped = grouped
    result.groupby_text = str(grouped)

    logger.info("Groupby result:\n%s", result.groupby_text)

    # ── Counts ────────────────────────────────────────────────────────────
    counts = df[COLUMN_SMOKER].value_counts()
    result.smoker_count = int(counts.get("yes", 0))
    result.non_smoker_count = int(counts.get("no", 0))

    # ── Means ─────────────────────────────────────────────────────────────
    result.smoker_mean = float(grouped.get("yes", 0.0))
    result.non_smoker_mean = float(grouped.get("no", 0.0))
    result.absolute_difference = result.smoker_mean - result.non_smoker_mean

    if result.non_smoker_mean > 0:
        result.percentage_difference = (
            result.absolute_difference / result.non_smoker_mean
        ) * 100.0
        result.multiplier = result.smoker_mean / result.non_smoker_mean
    else:
        result.percentage_difference = 0.0
        result.multiplier = 0.0

    # ── Medians ───────────────────────────────────────────────────────────
    medians = df.groupby(COLUMN_SMOKER)[COLUMN_CHARGES].median()
    result.smoker_median = float(medians.get("yes", 0.0))
    result.non_smoker_median = float(medians.get("no", 0.0))

    # ── Standard deviations ───────────────────────────────────────────────
    stds = df.groupby(COLUMN_SMOKER)[COLUMN_CHARGES].std()
    result.smoker_std = float(stds.get("yes", 0.0))
    result.non_smoker_std = float(stds.get("no", 0.0))

    # ── Min / Max ─────────────────────────────────────────────────────────
    mins = df.groupby(COLUMN_SMOKER)[COLUMN_CHARGES].min()
    maxs = df.groupby(COLUMN_SMOKER)[COLUMN_CHARGES].max()
    result.smoker_min = float(mins.get("yes", 0.0))
    result.smoker_max = float(maxs.get("yes", 0.0))
    result.non_smoker_min = float(mins.get("no", 0.0))
    result.non_smoker_max = float(maxs.get("no", 0.0))

    # ── Headline statement ────────────────────────────────────────────────
    pct_str = f"{result.percentage_difference:.1f}%" if result.percentage_difference else "N/A"
    result.dynamic_statement = (
        f"Smokers pay on average ${result.smoker_mean:,.2f} compared to "
        f"${result.non_smoker_mean:,.2f} for non-smokers — a difference of "
        f"${result.absolute_difference:,.2f} ({pct_str} more, or "
        f"{result.multiplier:.1f}× the non-smoker average)."
    )

    logger.info("Analysis complete: %s", result.dynamic_statement)
    return result
