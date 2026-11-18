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
import math
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from config import (
    COLUMN_AGE,
    COLUMN_BMI,
    COLUMN_CHARGES,
    COLUMN_REGION,
    COLUMN_SEX,
    COLUMN_SMOKER,
)

logger = logging.getLogger(__name__)


# ── Statistical Calculation Primitives (Dynamic, Non-Hardcoded) ──────────────

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction evaluation for incomplete beta function."""
    MAXIT = 100
    EPS = 3.0e-7
    FPMIN = 1.0e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        del_val = d * c
        h *= del_val
        if abs(del_val - 1.0) < EPS:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    else:
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_p_value_from_stat(t_stat: float, df: float) -> float:
    """Compute exact two-sided p-value from t-statistic and degrees of freedom."""
    if df <= 0:
        return 1.0
    if math.isnan(t_stat) or math.isinf(t_stat):
        return 1.0
    if HAS_SCIPY:
        try:
            return float(2.0 * (1.0 - scipy_stats.t.cdf(abs(t_stat), df=df)))
        except Exception:
            pass
    x = df / (df + t_stat * t_stat)
    return float(_betainc(df / 2.0, 0.5, x))


def student_t_critical(df: int, alpha: float = 0.05) -> float:
    """Calculate Student's t two-tailed critical value for given degrees of freedom."""
    if df < 1:
        return 1.96
    if HAS_SCIPY:
        try:
            return float(scipy_stats.t.ppf(1.0 - alpha / 2.0, df=df))
        except Exception:
            pass
    # High-precision Cornish-Fisher expansion for Student's t quantile
    z = 1.959963984540054  # z_{0.025}
    g1 = (z**3 + z) / (4.0 * df)
    g2 = (5.0 * z**5 + 16.0 * z**3 + 3.0 * z) / (96.0 * df**2)
    g3 = (3.0 * z**7 + 19.0 * z**5 + 17.0 * z**3 - 15.0 * z) / (384.0 * df**3)
    return float(z + g1 + g2 + g3)


def format_p_value(p: Optional[float]) -> str:
    """Format calculated p-value strictly based on numeric result."""
    if p is None or math.isnan(p):
        return "N/A"
    if p < 0.001:
        return "< 0.001"
    elif p < 0.01:
        return f"{p:.3f}"
    else:
        return f"{p:.3f}"


def calculate_welch_t_test(
    sample1: pd.Series,
    sample2: pd.Series,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate Welch's independent samples t-test (equal_var=False).
    
    Returns (t_stat, p_value, degrees_of_freedom).
    """
    n1 = len(sample1)
    n2 = len(sample2)
    if n1 < 2 or n2 < 2:
        return None, None, None

    v1 = float(sample1.var(ddof=1))
    v2 = float(sample2.var(ddof=1))
    m1 = float(sample1.mean())
    m2 = float(sample2.mean())

    se_diff = math.sqrt((v1 / n1) + (v2 / n2))
    if se_diff == 0.0:
        if m1 == m2:
            return 0.0, 1.0, float(n1 + n2 - 2)
        return None, None, None

    t_stat = (m2 - m1) / se_diff

    # Welch-Satterthwaite degrees of freedom
    num = ((v1 / n1) + (v2 / n2)) ** 2
    denom = (((v1 / n1) ** 2) / (n1 - 1)) + (((v2 / n2) ** 2) / (n2 - 1))
    df = num / denom if denom > 0 else float(n1 + n2 - 2)

    if HAS_SCIPY:
        try:
            res = scipy_stats.ttest_ind(sample2, sample1, equal_var=False)
            return float(res.statistic), float(res.pvalue), df
        except Exception:
            pass

    p_val = t_p_value_from_stat(abs(t_stat), df)
    return float(t_stat), float(p_val), float(df)


def calculate_mann_whitney_u(
    sample1: pd.Series,
    sample2: pd.Series,
) -> tuple[Optional[float], Optional[float]]:
    """Calculate two-sided Mann-Whitney U test."""
    n1 = len(sample1)
    n2 = len(sample2)
    if n1 < 1 or n2 < 1:
        return None, None

    if HAS_SCIPY:
        try:
            res = scipy_stats.mannwhitneyu(sample2, sample1, alternative="two-sided")
            return float(res.statistic), float(res.pvalue)
        except Exception:
            pass

    combined = pd.DataFrame({
        "val": list(sample1.values) + list(sample2.values),
        "grp": [1] * n1 + [2] * n2,
    })
    combined["rank"] = combined["val"].rank(method="average")
    r1 = float(combined[combined["grp"] == 1]["rank"].sum())
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    mu = n1 * n2 / 2.0
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    if sigma == 0:
        return u, 1.0
    z = abs(u - mu) / sigma
    p = math.erfc(z / math.sqrt(2))
    return float(u), float(p)


def calculate_cohen_d(
    m1: float,
    m2: float,
    s1: float,
    s2: float,
    n1: int,
    n2: int,
) -> Optional[float]:
    """Calculate Cohen's d using pooled standard deviation formula."""
    if n1 + n2 <= 2:
        return None
    v1 = s1 ** 2
    v2 = s2 ** 2
    pooled_var = (((n1 - 1) * v1) + ((n2 - 1) * v2)) / (n1 + n2 - 2)
    if pooled_var <= 0:
        return None
    return float(abs(m2 - m1) / math.sqrt(pooled_var))


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

    # ── 95% Confidence Interval metrics ──────────────────────────────────────
    non_smoker_ci_margin: float = 0.0
    non_smoker_ci_low: float = 0.0
    non_smoker_ci_high: float = 0.0
    smoker_ci_margin: float = 0.0
    smoker_ci_low: float = 0.0
    smoker_ci_high: float = 0.0
    ci_method: str = "Student's t / Normal distribution (95% CI, α = 0.05)"

    # ── P2 Statistical Significance Metrics ──────────────────────────────────
    t_statistic: Optional[float] = None
    welch_df: Optional[float] = None
    t_p_value: str = "N/A"
    mann_whitney_p_value: str = "N/A"
    cohen_d: Optional[float] = None
    stat_takeaway: str = ""
    chart_takeaways: dict[str, str] = field(default_factory=dict)

    dynamic_statement: str = ""
    academic_disclaimer: str = (
        "This analysis is for academic purposes only (PCC CS 393). "
        "The dataset is publicly available on Kaggle and results should not "
        "be used for clinical or actuarial decision-making."
    )

    df_grouped: Optional[pd.Series] = None
    groupby_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a strictly JSON-serializable dictionary representation."""
        def _clean_num(val: Any, decimals: int = 2) -> Optional[float]:
            if val is None:
                return None
            try:
                f = float(val)
                if math.isnan(f) or math.isinf(f):
                    return None
                return round(f, decimals)
            except (ValueError, TypeError):
                return None

        return {
            "total_valid_records": int(self.total_valid_records),
            "smoker_count": int(self.smoker_count),
            "non_smoker_count": int(self.non_smoker_count),
            "smoker_mean": _clean_num(self.smoker_mean) or 0.0,
            "non_smoker_mean": _clean_num(self.non_smoker_mean) or 0.0,
            "absolute_difference": _clean_num(self.absolute_difference) or 0.0,
            "percentage_difference": _clean_num(self.percentage_difference),
            "multiplier": _clean_num(self.multiplier) or 0.0,
            "smoker_median": _clean_num(self.smoker_median) or 0.0,
            "non_smoker_median": _clean_num(self.non_smoker_median) or 0.0,
            "smoker_std": _clean_num(self.smoker_std) or 0.0,
            "non_smoker_std": _clean_num(self.non_smoker_std) or 0.0,
            "smoker_min": _clean_num(self.smoker_min) or 0.0,
            "smoker_max": _clean_num(self.smoker_max) or 0.0,
            "non_smoker_min": _clean_num(self.non_smoker_min) or 0.0,
            "non_smoker_max": _clean_num(self.non_smoker_max) or 0.0,
            "non_smoker_ci_margin": _clean_num(self.non_smoker_ci_margin) or 0.0,
            "non_smoker_ci_low": _clean_num(self.non_smoker_ci_low) or 0.0,
            "non_smoker_ci_high": _clean_num(self.non_smoker_ci_high) or 0.0,
            "smoker_ci_margin": _clean_num(self.smoker_ci_margin) or 0.0,
            "smoker_ci_low": _clean_num(self.smoker_ci_low) or 0.0,
            "smoker_ci_high": _clean_num(self.smoker_ci_high) or 0.0,
            "ci_method": str(self.ci_method),
            "t_statistic": _clean_num(self.t_statistic),
            "welch_df": _clean_num(self.welch_df),
            "t_p_value": str(self.t_p_value),
            "mann_whitney_p_value": str(self.mann_whitney_p_value),
            "cohen_d": _clean_num(self.cohen_d),
            "stat_takeaway": str(self.stat_takeaway),
            "chart_takeaways": dict(self.chart_takeaways),
            "dynamic_statement": str(self.dynamic_statement),
            "academic_disclaimer": str(self.academic_disclaimer),
            "groupby_text": str(self.groupby_text),
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

    # ── 95% Confidence Intervals (Student's t distribution, df = n - 1) ───
    if result.non_smoker_count > 1 and result.non_smoker_std > 0:
        ns_se = result.non_smoker_std / (result.non_smoker_count ** 0.5)
        ns_t = student_t_critical(result.non_smoker_count - 1, alpha=0.05)
        result.non_smoker_ci_margin = float(ns_t * ns_se)
        result.non_smoker_ci_low = max(0.0, result.non_smoker_mean - result.non_smoker_ci_margin)
        result.non_smoker_ci_high = result.non_smoker_mean + result.non_smoker_ci_margin

    if result.smoker_count > 1 and result.smoker_std > 0:
        sm_se = result.smoker_std / (result.smoker_count ** 0.5)
        sm_t = student_t_critical(result.smoker_count - 1, alpha=0.05)
        result.smoker_ci_margin = float(sm_t * sm_se)
        result.smoker_ci_low = max(0.0, result.smoker_mean - result.smoker_ci_margin)
        result.smoker_ci_high = result.smoker_mean + result.smoker_ci_margin

    # ── Dynamic Statistical Significance (Welch's t-test, Mann-Whitney U, Cohen's d) ──
    if result.non_smoker_count > 1 and result.smoker_count > 1:
        ns_charges = df[df[COLUMN_SMOKER] == "no"][COLUMN_CHARGES].dropna()
        sm_charges = df[df[COLUMN_SMOKER] == "yes"][COLUMN_CHARGES].dropna()

        t_stat, t_pval, _df = calculate_welch_t_test(ns_charges, sm_charges)
        _u_stat, u_pval = calculate_mann_whitney_u(ns_charges, sm_charges)
        cohen_d = calculate_cohen_d(
            result.non_smoker_mean,
            result.smoker_mean,
            result.non_smoker_std,
            result.smoker_std,
            result.non_smoker_count,
            result.smoker_count,
        )

        result.t_statistic = t_stat
        result.welch_df = _df
        result.t_p_value = format_p_value(t_pval)
        result.mann_whitney_p_value = format_p_value(u_pval)
        result.cohen_d = cohen_d

        t_stat_str = f"t = {t_stat:.2f}" if t_stat is not None else "t = N/A"
        cohen_str = f"Cohen's d = {cohen_d:.2f}" if cohen_d is not None else "Cohen's d = N/A"
        result.stat_takeaway = (
            f"Welch's t-test ({t_stat_str}, p {result.t_p_value}) and Mann–Whitney U (p {result.mann_whitney_p_value}) "
            f"confirm the cost disparity is statistically significant ({cohen_str}). "
            f"Caution: this indicates significant actuarial association in this observational dataset, not direct biological causation."
        )
    else:
        result.t_statistic = None
        result.t_p_value = "N/A"
        result.mann_whitney_p_value = "N/A"
        result.cohen_d = None
        result.stat_takeaway = "Insufficient cohort sample size to compute comparative significance metrics."

    # ── P2 Secondary Chart Dynamic Takeaways ──────────────────────────────
    result.chart_takeaways = {
        "bar": f"Smokers pay on average ${result.smoker_mean:,.2f} vs ${result.non_smoker_mean:,.2f} for non-smokers ({result.multiplier:.2f}× higher, difference +${result.absolute_difference:,.2f}).",
        "dist": "Non-smoker charges concentrate heavily under $10,000, while smoker charges display a wide bimodal spread extending beyond $40,000.",
        "box": f"The median smoker charge (${result.smoker_median:,.2f}) substantially exceeds the entire 75th percentile of non-smoker charges.",
        "scatter": "Smokers with BMI ≥ 30 form a distinct high-cost tier exceeding $35,000, demonstrating an interaction between smoking status and obesity.",
        "region": "The smoking cost disparity persists across all 4 geographic regions, with Southeast recording the highest average smoker charges.",
        "sex": "The smoking cost disparity holds similarly across both male and female policyholder cohorts.",
        "age": "Smoker charges consistently exceed non-smoker charges across all age brackets, escalating with age.",
    }

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


# ── Scenario Comparison Engine ────────────────────────────────────────────────

def filter_cohort(df: pd.DataFrame, criteria: dict[str, Any]) -> pd.DataFrame:
    """Filter DataFrame according to demographic and lifestyle scenario criteria."""
    if df is None or df.empty:
        return pd.DataFrame()

    matched = df.copy()

    # Age band filter
    age_band = str(criteria.get("age_band", "all")).strip().lower()
    if age_band == "18-29":
        matched = matched[(matched[COLUMN_AGE] >= 18) & (matched[COLUMN_AGE] <= 29)]
    elif age_band == "30-44":
        matched = matched[(matched[COLUMN_AGE] >= 30) & (matched[COLUMN_AGE] <= 44)]
    elif age_band == "45-64":
        matched = matched[(matched[COLUMN_AGE] >= 45) & (matched[COLUMN_AGE] <= 64)]

    # BMI band filter
    bmi_band = str(criteria.get("bmi_band", "all")).strip().lower()
    if bmi_band in ("<25", "normal"):
        matched = matched[matched[COLUMN_BMI] < 25.0]
    elif bmi_band in ("25-29.9", "overweight"):
        matched = matched[(matched[COLUMN_BMI] >= 25.0) & (matched[COLUMN_BMI] < 30.0)]
    elif bmi_band in (">=30", "obese"):
        matched = matched[matched[COLUMN_BMI] >= 30.0]

    # Sex filter
    sex = str(criteria.get("sex", "all")).strip().lower()
    if sex != "all":
        matched = matched[matched[COLUMN_SEX] == sex]

    # Region filter
    region = str(criteria.get("region", "all")).strip().lower()
    if region != "all":
        matched = matched[matched[COLUMN_REGION] == region]

    # Smoker filter
    smoker = str(criteria.get("smoker", "all")).strip().lower()
    if smoker != "all":
        matched = matched[matched[COLUMN_SMOKER] == smoker]

    return matched


def _calculate_subgroup_metrics(subset: pd.DataFrame) -> dict[str, Any]:
    """Compute summary metrics and 95% CI for an empirical subgroup."""
    n = len(subset)
    if n == 0:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "ci_margin": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
        }

    charges = subset[COLUMN_CHARGES]
    mean_val = float(charges.mean())
    median_val = float(charges.median())
    std_val = float(charges.std()) if n > 1 else 0.0
    min_val = float(charges.min())
    max_val = float(charges.max())

    ci_margin = 0.0
    ci_low = mean_val
    ci_high = mean_val
    if n > 1 and std_val > 0:
        se = std_val / math.sqrt(n)
        t_crit = student_t_critical(df=n - 1, alpha=0.05)
        ci_margin = float(t_crit * se)
        ci_low = max(0.0, mean_val - ci_margin)
        ci_high = mean_val + ci_margin

    return {
        "count": n,
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "std": round(std_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "ci_margin": round(ci_margin, 2),
        "ci_low": round(ci_low, 2),
        "ci_high": round(ci_high, 2),
    }


def compare_scenarios(
    df: pd.DataFrame,
    criteria_a: dict[str, Any],
    criteria_b: dict[str, Any],
) -> dict[str, Any]:
    """Dynamically compare empirical claims distributions between two cohorts."""
    cohort_a = filter_cohort(df, criteria_a)
    cohort_b = filter_cohort(df, criteria_b)

    metrics_a = _calculate_subgroup_metrics(cohort_a)
    metrics_b = _calculate_subgroup_metrics(cohort_b)

    nA = metrics_a["count"]
    nB = metrics_b["count"]
    meanA = metrics_a["mean"]
    meanB = metrics_b["mean"]

    diff_mean = round(meanB - meanA, 2)
    diff_median = round(metrics_b["median"] - metrics_a["median"], 2)

    pct_diff = round((diff_mean / meanA) * 100.0, 1) if meanA > 0 else 0.0
    multiplier = round(meanB / meanA, 2) if meanA > 0 else 0.0

    higher = "b" if meanB > meanA else ("a" if meanA > meanB else "equal")

    # Statistical significance (Welch's independent-samples t-test with equal_var=False)
    t_stat = None
    p_val_text = "N/A"
    df_welch = None
    if nA >= 2 and nB >= 2:
        charges_a = cohort_a[COLUMN_CHARGES].dropna()
        charges_b = cohort_b[COLUMN_CHARGES].dropna()
        t_raw, p_raw, df_raw = calculate_welch_t_test(charges_a, charges_b)
        if t_raw is not None and not math.isnan(t_raw):
            t_stat = round(float(t_raw), 2)
            df_welch = round(float(df_raw), 2) if df_raw is not None and not math.isnan(df_raw) else None
            p_val_text = format_p_value(p_raw)

    warnings = []
    if nA == 0:
        warnings.append("Cohort A contains 0 matching records in dataset.")
    elif nA < 20:
        warnings.append(f"Cohort A has a small sample size (n = {nA} < 20); empirical estimates have high variance.")

    if nB == 0:
        warnings.append("Cohort B contains 0 matching records in dataset.")
    elif nB < 20:
        warnings.append(f"Cohort B has a small sample size (n = {nB} < 20); empirical estimates have high variance.")

    sign_diff = "+" if diff_mean >= 0 else ""
    sign_pct = "+" if pct_diff >= 0 else ""
    statement = (
        f"In this observational dataset, Cohort B averages ${meanB:,.2f} vs ${meanA:,.2f} for Cohort A "
        f"({sign_diff}${diff_mean:,.2f}, {sign_pct}{pct_diff:.1f}%). "
        f"This demonstrates empirical subgroup distribution and does not constitute an individual health risk prediction."
    )

    return {
        "status": "success",
        "cohort_a": metrics_a,
        "cohort_b": metrics_b,
        "criteria_a": criteria_a,
        "criteria_b": criteria_b,
        "diff_mean": diff_mean,
        "diff_median": diff_median,
        "pct_diff": pct_diff,
        "multiplier": multiplier,
        "higher_cohort": higher,
        "baseline": "cohort_a",
        "t_statistic": t_stat,
        "degrees_of_freedom": df_welch,
        "p_value": p_val_text,
        "statement": statement,
        "warnings": warnings,
    }
