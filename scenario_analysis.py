"""
SympSort — Scenario Analysis Engine
===================================
Provides pure-Python & Pandas empirical scenario comparison between two cohorts.
Performs strict validation of incoming scenario criteria and computes genuine
subgroup metrics (count, mean, median, min, max, std).

Academic Disclaimer:
Empirical comparisons represent observational subgroup historical averages
within this dataset and must NEVER be interpreted as personalized insurance
quotes, actuarial premiums, or causal health effects.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Optional

import pandas as pd

import config
from analysis import calculate_welch_t_test, student_t_critical
from config import (
    COLUMN_AGE,
    COLUMN_BMI,
    COLUMN_CHARGES,
    COLUMN_CHILDREN,
    COLUMN_REGION,
    COLUMN_SEX,
    COLUMN_SMOKER,
)

VALID_SMOKER_OPTIONS = {"all", "yes", "no"}
VALID_SEX_OPTIONS = {"all", "male", "female"}
VALID_REGION_OPTIONS = {
    "all",
    "northeast",
    "northwest",
    "southeast",
    "southwest",
}


@dataclass
class ScenarioFilter:
    """Validated filter specification for an empirical scenario cohort."""
    smoker: str = "all"
    sex: str = "all"
    region: str = "all"
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    bmi_min: Optional[float] = None
    bmi_max: Optional[float] = None
    children: Any = "all"  # "all" or non-negative int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_numeric_field(
    val: Any,
    field_name: str,
    min_allowed: float,
    max_allowed: float,
    is_integer: bool = False,
) -> tuple[Optional[float], Optional[str]]:
    """Validate a numeric range boundary (None, number, or valid numeric string)."""
    if val is None or val == "" or str(val).strip().lower() in ("none", "null", "all"):
        return None, None

    if isinstance(val, (int, float)):
        num = float(val)
    elif isinstance(val, str):
        try:
            num = float(val.strip())
        except ValueError:
            return None, f"Field '{field_name}' must be a valid number, got '{val}'."
    else:
        return None, f"Field '{field_name}' must be a number or null, got type {type(val).__name__}."

    if math.isnan(num) or math.isinf(num):
        return None, f"Field '{field_name}' cannot be NaN or Infinity."

    if num < min_allowed or num > max_allowed:
        return None, (
            f"Field '{field_name}' value {num} is outside acceptable range "
            f"[{min_allowed}, {max_allowed}]."
        )

    if is_integer:
        if not num.is_integer():
            return None, f"Field '{field_name}' must be an integer, got {num}."
        return int(num), None

    return round(num, 2), None


def validate_scenario_filter(raw: Any, scenario_label: str = "scenario") -> tuple[Optional[ScenarioFilter], Optional[str]]:
    """Strictly validate scenario input criteria.
    
    Returns (ScenarioFilter, None) on success or (None, error_message) on failure.
    """
    if not isinstance(raw, dict):
        return None, f"'{scenario_label}' must be a JSON object, got {type(raw).__name__}."

    # 1. Smoker filter
    smoker_raw = raw.get("smoker", "all")
    if smoker_raw is None or smoker_raw == "":
        smoker_clean = "all"
    elif isinstance(smoker_raw, str):
        smoker_clean = smoker_raw.strip().lower()
    else:
        return None, f"'{scenario_label}.smoker' must be a string, got {type(smoker_raw).__name__}."

    if smoker_clean not in VALID_SMOKER_OPTIONS:
        return None, (
            f"Invalid value for '{scenario_label}.smoker': '{smoker_raw}'. "
            f"Allowed values are {sorted(list(VALID_SMOKER_OPTIONS))}."
        )

    # 2. Sex filter
    sex_raw = raw.get("sex", "all")
    if sex_raw is None or sex_raw == "":
        sex_clean = "all"
    elif isinstance(sex_raw, str):
        sex_clean = sex_raw.strip().lower()
    else:
        return None, f"'{scenario_label}.sex' must be a string, got {type(sex_raw).__name__}."

    if sex_clean not in VALID_SEX_OPTIONS:
        return None, (
            f"Invalid value for '{scenario_label}.sex': '{sex_raw}'. "
            f"Allowed values are {sorted(list(VALID_SEX_OPTIONS))}."
        )

    # 3. Region filter
    region_raw = raw.get("region", "all")
    if region_raw is None or region_raw == "":
        region_clean = "all"
    elif isinstance(region_raw, str):
        region_clean = region_raw.strip().lower()
    else:
        return None, f"'{scenario_label}.region' must be a string, got {type(region_raw).__name__}."

    if region_clean not in VALID_REGION_OPTIONS:
        return None, (
            f"Invalid value for '{scenario_label}.region': '{region_raw}'. "
            f"Allowed values are {sorted(list(VALID_REGION_OPTIONS))}."
        )

    # 4. Age range
    age_min_val, err = _validate_numeric_field(
        raw.get("age_min"),
        f"{scenario_label}.age_min",
        min_allowed=0,
        max_allowed=120,
        is_integer=True,
    )
    if err:
        return None, err

    age_max_val, err = _validate_numeric_field(
        raw.get("age_max"),
        f"{scenario_label}.age_max",
        min_allowed=0,
        max_allowed=120,
        is_integer=True,
    )
    if err:
        return None, err

    if age_min_val is not None and age_max_val is not None and age_min_val > age_max_val:
        return None, (
            f"'{scenario_label}.age_min' ({age_min_val}) cannot exceed "
            f"'{scenario_label}.age_max' ({age_max_val})."
        )

    # 5. BMI range
    bmi_min_val, err = _validate_numeric_field(
        raw.get("bmi_min"),
        f"{scenario_label}.bmi_min",
        min_allowed=10.0,
        max_allowed=100.0,
        is_integer=False,
    )
    if err:
        return None, err

    bmi_max_val, err = _validate_numeric_field(
        raw.get("bmi_max"),
        f"{scenario_label}.bmi_max",
        min_allowed=10.0,
        max_allowed=100.0,
        is_integer=False,
    )
    if err:
        return None, err

    if bmi_min_val is not None and bmi_max_val is not None and bmi_min_val > bmi_max_val:
        return None, (
            f"'{scenario_label}.bmi_min' ({bmi_min_val}) cannot exceed "
            f"'{scenario_label}.bmi_max' ({bmi_max_val})."
        )

    # 6. Children filter
    children_raw = raw.get("children", "all")
    if children_raw is None or children_raw == "" or str(children_raw).strip().lower() in ("all", "none", "null"):
        children_clean = "all"
    else:
        children_val, err = _validate_numeric_field(
            children_raw,
            f"{scenario_label}.children",
            min_allowed=0,
            max_allowed=20,
            is_integer=True,
        )
        if err:
            return None, err
        children_clean = children_val

    filter_obj = ScenarioFilter(
        smoker=smoker_clean,
        sex=sex_clean,
        region=region_clean,
        age_min=age_min_val,
        age_max=age_max_val,
        bmi_min=bmi_min_val,
        bmi_max=bmi_max_val,
        children=children_clean,
    )
    return filter_obj, None


def filter_cohort_dataframe(df: pd.DataFrame, sf: ScenarioFilter) -> pd.DataFrame:
    """Filter DataFrame according to validated ScenarioFilter criteria."""
    if df is None or df.empty:
        return pd.DataFrame()

    matched = df

    # Smoker
    if sf.smoker != "all" and COLUMN_SMOKER in matched.columns:
        matched = matched[matched[COLUMN_SMOKER] == sf.smoker]

    # Sex
    if sf.sex != "all" and COLUMN_SEX in matched.columns:
        matched = matched[matched[COLUMN_SEX] == sf.sex]

    # Region
    if sf.region != "all" and COLUMN_REGION in matched.columns:
        matched = matched[matched[COLUMN_REGION] == sf.region]

    # Age range
    if COLUMN_AGE in matched.columns:
        if sf.age_min is not None:
            matched = matched[matched[COLUMN_AGE] >= sf.age_min]
        if sf.age_max is not None:
            matched = matched[matched[COLUMN_AGE] <= sf.age_max]

    # BMI range
    if COLUMN_BMI in matched.columns:
        if sf.bmi_min is not None:
            matched = matched[matched[COLUMN_BMI] >= sf.bmi_min]
        if sf.bmi_max is not None:
            matched = matched[matched[COLUMN_BMI] <= sf.bmi_max]

    # Children
    if sf.children != "all" and COLUMN_CHILDREN in matched.columns:
        matched = matched[matched[COLUMN_CHILDREN] == sf.children]

    return matched


def calculate_cohort_metrics(subset: pd.DataFrame, applied_filters: dict[str, Any]) -> dict[str, Any]:
    """Calculate summary statistics for a filtered cohort.
    
    If no records match, returns null (None) for statistical metrics, not 0.
    """
    n = len(subset) if subset is not None else 0

    if n == 0:
        return {
            "matched_records": 0,
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "ci_margin": None,
            "ci_low": None,
            "ci_high": None,
            "has_data": False,
            "applied_filters": applied_filters,
        }

    charges = subset[COLUMN_CHARGES].dropna()
    mean_val = float(charges.mean())
    median_val = float(charges.median())
    min_val = float(charges.min())
    max_val = float(charges.max())
    std_val = float(charges.std(ddof=1)) if n > 1 else None

    ci_margin = None
    ci_low = None
    ci_high = None
    if n > 1 and std_val is not None and std_val > 0:
        se = std_val / math.sqrt(n)
        t_crit = student_t_critical(df=n - 1, alpha=0.05)
        ci_margin = round(float(t_crit * se), 2)
        ci_low = round(max(0.0, mean_val - (t_crit * se)), 2)
        ci_high = round(mean_val + (t_crit * se), 2)

    return {
        "matched_records": n,
        "count": n,
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "std": round(std_val, 2) if std_val is not None else None,
        "ci_margin": ci_margin,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "has_data": True,
        "applied_filters": applied_filters,
    }


def compare_empirical_scenarios(
    df: pd.DataFrame,
    scenario_a_raw: dict[str, Any],
    scenario_b_raw: dict[str, Any],
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Perform a validated two-group empirical scenario comparison.
    
    Returns (result_dict, None) or (None, error_string).
    """
    filter_a, err_a = validate_scenario_filter(scenario_a_raw, "scenario_a")
    if err_a:
        return None, err_a

    filter_b, err_b = validate_scenario_filter(scenario_b_raw, "scenario_b")
    if err_b:
        return None, err_b

    subset_a = filter_cohort_dataframe(df, filter_a)
    subset_b = filter_cohort_dataframe(df, filter_b)

    metrics_a = calculate_cohort_metrics(subset_a, filter_a.to_dict())
    metrics_b = calculate_cohort_metrics(subset_b, filter_b.to_dict())

    nA = metrics_a["count"]
    nB = metrics_b["count"]
    meanA = metrics_a["mean"]
    meanB = metrics_b["mean"]

    warnings = []
    if nA == 0:
        warnings.append("Scenario A matched 0 records in dataset.")
    elif nA < 20:
        warnings.append(f"Scenario A has a small sample size (n = {nA} < 20); empirical estimates have high statistical variance.")

    if nB == 0:
        warnings.append("Scenario B matched 0 records in dataset.")
    elif nB < 20:
        warnings.append(f"Scenario B has a small sample size (n = {nB} < 20); empirical estimates have high statistical variance.")

    # Difference in group means
    diff_mean = None
    pct_diff = None
    multiplier = None
    higher = None

    if meanA is not None and meanB is not None:
        diff_mean = round(meanB - meanA, 2)
        # Percentage difference and multiplier relative to Scenario A as baseline
        if meanA > 0:
            pct_diff = round((diff_mean / meanA) * 100.0, 2)
            multiplier = round(meanB / meanA, 2)
        elif meanA < 0:
            pct_diff = round((diff_mean / abs(meanA)) * 100.0, 2)
            multiplier = round(meanB / meanA, 2)

        if meanB > meanA:
            higher = "scenario_b"
        elif meanA > meanB:
            higher = "scenario_a"
        else:
            higher = "equal"

    # Welch's independent samples t-test between empirical cohorts (equal_var=False)
    t_stat = None
    p_val = None
    df_welch = None
    if nA >= 2 and nB >= 2:
        charges_a = subset_a[COLUMN_CHARGES].dropna()
        charges_b = subset_b[COLUMN_CHARGES].dropna()
        t_raw, p_raw, df_raw = calculate_welch_t_test(charges_a, charges_b)
        if t_raw is not None and not math.isnan(t_raw):
            t_stat = round(float(t_raw), 2)
            p_val = float(p_raw) if p_raw is not None and not math.isnan(p_raw) else None
            df_welch = round(float(df_raw), 2) if df_raw is not None and not math.isnan(df_raw) else None

    disclaimer = (
        "Empirical subgroup comparison based on historical observational records in dataset "
        "(n = 1,338). Results describe historical subgroup cost averages and do not represent "
        "individual health risk predictions, insurance quotes, actuarial premiums, or causal effects."
    )

    result = {
        "status": "success",
        "scenario_a": metrics_a,
        "scenario_b": metrics_b,
        "comparison": {
            "baseline": "scenario_a",
            "difference_mean": diff_mean,
            "percentage_difference": pct_diff,
            "multiplier": multiplier,
            "higher_scenario": higher,
            "t_statistic": t_stat,
            "p_value": p_val,
            "degrees_of_freedom": df_welch,
            "has_data": metrics_a["has_data"] and metrics_b["has_data"],
        },
        "warnings": warnings,
        "disclaimer": disclaimer,
    }

    return result, None
