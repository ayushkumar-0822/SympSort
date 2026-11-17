"""
SympSort — Visualization Module
=================================
Generates publication-quality charts comparing medical insurance costs across
lifestyle factors using Matplotlib / Seaborn.

Supports 7 chart views for analytical depth:
- ``bar``: Primary smoker vs non-smoker barplot with 95% CI error whiskers & dollar labels
- ``dist``: Kernel Density Estimation (KDE) distribution comparing charge profiles
- ``box``: Boxplot showing median, IQR, spread, and high-cost outliers
- ``scatter``: BMI vs Charges scatter showing the BMI ≥ 30 obesity interaction
- ``region``: Regional breakdown across Northeast, Northwest, Southeast, Southwest
- ``sex``: Sex cohort breakdown across female and male policyholders
- ``age``: Age band comparison (18–29, 30–44, 45–64)

Charts are rendered as ``bytes`` (PNG) and cached per kind and theme until data reload.
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
import tempfile
from typing import Optional, Union

# Ensure Matplotlib config directory is writable across all OS & serverless environments
mpl_dir = os.path.join(tempfile.gettempdir(), ".matplotlib")
os.environ.setdefault("MPLCONFIGDIR", mpl_dir)

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must precede pyplot import
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

from config import (
    CHART_AXIS_DARK,
    CHART_AXIS_LIGHT,
    CHART_BG_DARK,
    CHART_BG_LIGHT,
    CHART_DPI_DOWNLOAD,
    CHART_DPI_SCREEN,
    CHART_HEIGHT,
    CHART_TEXT_DARK,
    CHART_TEXT_LIGHT,
    CHART_WIDTH,
    COLUMN_AGE,
    COLUMN_BMI,
    COLUMN_CHARGES,
    COLUMN_REGION,
    COLUMN_SEX,
    COLUMN_SMOKER,
    OUTPUT_DIR,
    PALETTE_DARK,
    PALETTE_LIGHT,
)

logger = logging.getLogger(__name__)

# Configure matplotlib default font family to match UI sans-serif
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Segoe UI",
    "Inter",
    "DejaVu Sans",
    "Arial",
    "sans-serif",
]

# ── In-memory chart cache ─────────────────────────────────────────────────────
_chart_cache: dict[str, bytes] = {}


def _data_fingerprint(data: Union[pd.DataFrame, pd.Series]) -> str:
    """Generate a lightweight data fingerprint for cache keys to prevent stale views."""
    if isinstance(data, pd.DataFrame):
        ch_sum = float(data[COLUMN_CHARGES].sum()) if COLUMN_CHARGES in data.columns else 0.0
        return f"df_{len(data)}_{ch_sum:.1f}"
    elif isinstance(data, pd.Series):
        s_sum = float(data.sum()) if not data.empty else 0.0
        return f"ser_{len(data)}_{s_sum:.1f}"
    return "none"


def clear_chart_cache() -> None:
    """Invalidate all cached chart images (call on data reload)."""
    _chart_cache.clear()
    logger.info("Chart cache cleared.")


def generate_chart_bytes(
    data: Union[pd.DataFrame, pd.Series],
    kind: str = "bar",
    dark_mode: bool = False,
    high_res: bool = False,
) -> bytes:
    """Render a statistical visualization and return PNG bytes.

    Parameters
    ----------
    data:
        Either the cleaned ``pd.DataFrame`` (1,338 rows with relevant columns)
        or a ``pd.Series`` indexed by smoker status (``"no"``, ``"yes"``).
    kind:
        Chart type: ``"bar"``, ``"dist"``, ``"box"``, ``"scatter"``,
        ``"region"``, ``"sex"``, or ``"age"``. Defaults to ``"bar"``.
    dark_mode:
        Use the dark colour scheme.
    high_res:
        Render at 300 DPI (download quality) instead of 150 DPI (screen).

    Returns
    -------
    bytes
        Raw PNG image data.
    """
    valid_kinds = {"bar", "dist", "box", "scatter", "region", "sex", "age"}
    chart_kind = kind.lower().strip() if kind else "bar"
    if chart_kind not in valid_kinds:
        chart_kind = "bar"

    # If data is a Series or missing required columns, multi-variable charts must fallback to "bar"
    if not isinstance(data, pd.DataFrame):
        chart_kind = "bar"

    cache_key = f"{chart_kind}_{'dark' if dark_mode else 'light'}_{'hi' if high_res else 'lo'}_{_data_fingerprint(data)}"

    if cache_key in _chart_cache and not high_res:
        return _chart_cache[cache_key]

    dpi = CHART_DPI_DOWNLOAD if high_res else CHART_DPI_SCREEN

    # ── Theme colours ─────────────────────────────────────────────────────
    palette = PALETTE_DARK if dark_mode else PALETTE_LIGHT
    bg_color = CHART_BG_DARK if dark_mode else CHART_BG_LIGHT
    text_color = CHART_TEXT_DARK if dark_mode else CHART_TEXT_LIGHT
    axis_color = CHART_AXIS_DARK if dark_mode else CHART_AXIS_LIGHT

    fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    # ── Render specific chart kind ────────────────────────────────────────
    if chart_kind == "bar":
        _render_bar_chart(data, ax, palette, text_color, axis_color)
    elif chart_kind == "dist":
        _render_dist_chart(data, ax, palette, text_color, axis_color, bg_color)
    elif chart_kind == "box":
        _render_box_chart(data, ax, palette, text_color, axis_color)
    elif chart_kind == "scatter":
        _render_scatter_chart(data, ax, palette, text_color, axis_color, bg_color)
    elif chart_kind == "region":
        _render_region_chart(data, ax, palette, text_color, axis_color, bg_color)
    elif chart_kind == "sex":
        _render_sex_chart(data, ax, palette, text_color, axis_color, bg_color)
    elif chart_kind == "age":
        _render_age_chart(data, ax, palette, text_color, axis_color, bg_color)

    # Clean spines and grid styling across all charts
    for spine_name, spine in ax.spines.items():
        if spine_name in ("top", "right"):
            spine.set_visible(False)
        else:
            spine.set_color(axis_color)
            spine.set_linewidth(0.8)

    ax.yaxis.grid(True, color=axis_color, linewidth=0.5, alpha=0.6, linestyle="-")
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.tick_params(colors=text_color, labelsize=10.5)

    fig.tight_layout(pad=1.5)

    # ── Export to bytes ───────────────────────────────────────────────────
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=bg_color, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    png_bytes = buf.read()

    # Cache screen-resolution charts only
    if not high_res:
        _chart_cache[cache_key] = png_bytes

    logger.info("Chart generated (%s, %d DPI, %d bytes)", cache_key, dpi, len(png_bytes))
    return png_bytes


# ── Internal chart rendering helpers ──────────────────────────────────────────

def _style_legend(ax: plt.Axes, bg_color: str, axis_color: str, text_color: str) -> None:
    """Format legend labels and styling consistently."""
    leg = ax.get_legend()
    if leg:
        leg.set_title("")
        leg.get_frame().set_facecolor(bg_color)
        leg.get_frame().set_edgecolor(axis_color)
        leg.get_frame().set_linewidth(0.8)
        for text in leg.get_texts():
            text.set_color(text_color)
            text.set_fontsize(10)
            cur = text.get_text().strip()
            if cur in ("no", "0"):
                text.set_text("Non-Smoker")
            elif cur in ("yes", "1"):
                text.set_text("Smoker")


def _render_bar_chart(
    data: Union[pd.DataFrame, pd.Series],
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
) -> None:
    """Render assigned barplot with 95% CI error whiskers & dollar annotations."""
    is_raw_df = isinstance(data, pd.DataFrame) and COLUMN_SMOKER in data.columns and COLUMN_CHARGES in data.columns
    if is_raw_df:
        counts = data[COLUMN_SMOKER].value_counts()
        n_no = int(counts.get("no", 0))
        n_yes = int(counts.get("yes", 0))

        sns.barplot(
            data=data,
            x=COLUMN_SMOKER,
            y=COLUMN_CHARGES,
            order=["no", "yes"],
            hue=COLUMN_SMOKER,
            palette={"no": palette["no"], "yes": palette["yes"]},
            errorbar=("ci", 95),
            capsize=0.15,
            err_kws={"linewidth": 2.2, "color": text_color},
            edgecolor=text_color,
            linewidth=0.8,
            legend=False,
            ax=ax,
        )
    else:
        df_grouped = data if isinstance(data, pd.Series) else pd.Series(data)
        mean_no = float(df_grouped.get("no", 0.0))
        mean_yes = float(df_grouped.get("yes", 0.0))
        n_no = 0
        n_yes = 0

        plot_df = pd.DataFrame({
            "smoker": ["no", "yes"],
            "charges": [mean_no, mean_yes],
        })

        sns.barplot(
            data=plot_df,
            x="smoker",
            y="charges",
            order=["no", "yes"],
            hue="smoker",
            palette={"no": palette["no"], "yes": palette["yes"]},
            edgecolor=text_color,
            linewidth=0.8,
            legend=False,
            ax=ax,
        )

    # Exact dollar labels above bars
    max_bar_val = 0.0
    for bar in ax.patches:
        val = bar.get_height()
        if val > 0:
            if val > max_bar_val:
                max_bar_val = val
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 1100,
                f"${val:,.2f}",
                ha="center",
                va="bottom",
                fontsize=11.5,
                fontweight="bold",
                color=text_color,
            )

    ax.set_xticks([0, 1])
    if is_raw_df and n_no > 0 and n_yes > 0:
        ax.set_xticklabels(
            [f"Non-Smoker (n = {n_no:,})", f"Smoker (n = {n_yes:,})"],
            fontsize=11,
            fontweight="600",
            color=text_color,
        )
    else:
        ax.set_xticklabels(
            ["Non-Smoker", "Smoker"],
            fontsize=11,
            fontweight="600",
            color=text_color,
        )
    ax.set_xlabel("", labelpad=0)
    ax.set_ylabel("Mean Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_ylim(0, max(39500, max_bar_val * 1.15 if max_bar_val > 0 else 39500))


def _render_dist_chart(
    df: pd.DataFrame,
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
    bg_color: str,
) -> None:
    """Render KDE distribution comparison."""
    sns.kdeplot(
        data=df,
        x=COLUMN_CHARGES,
        hue=COLUMN_SMOKER,
        fill=True,
        common_norm=False,
        palette={"no": palette["no"], "yes": palette["yes"]},
        alpha=0.32,
        linewidth=2.2,
        ax=ax,
    )
    ax.set_xlabel("Medical Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.set_ylabel("Density", fontsize=11, color=text_color, labelpad=10)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    _style_legend(ax, bg_color, axis_color, text_color)


def _render_box_chart(
    df: pd.DataFrame,
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
) -> None:
    """Render boxplot showing median, IQR, whiskers, and outliers."""
    counts = df[COLUMN_SMOKER].value_counts()
    n_no = int(counts.get("no", 1064))
    n_yes = int(counts.get("yes", 274))

    sns.boxplot(
        data=df,
        x=COLUMN_SMOKER,
        y=COLUMN_CHARGES,
        order=["no", "yes"],
        hue=COLUMN_SMOKER,
        palette={"no": palette["no"], "yes": palette["yes"]},
        width=0.42,
        linewidth=1.2,
        flierprops={"marker": "o", "markersize": 3.8, "alpha": 0.45, "markeredgecolor": "none"},
        legend=False,
        ax=ax,
    )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(
        [f"Non-Smoker (n = {n_no:,})", f"Smoker (n = {n_yes:,})"],
        fontsize=11,
        fontweight="600",
        color=text_color,
    )
    ax.set_xlabel("", labelpad=0)
    ax.set_ylabel("Medical Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))


def _render_scatter_chart(
    df: pd.DataFrame,
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
    bg_color: str,
) -> None:
    """Render BMI vs Charges scatter with obesity threshold reference line."""
    sns.scatterplot(
        data=df,
        x=COLUMN_BMI,
        y=COLUMN_CHARGES,
        hue=COLUMN_SMOKER,
        palette={"no": palette["no"], "yes": palette["yes"]},
        alpha=0.72,
        s=38,
        edgecolor="none",
        ax=ax,
    )
    # Reference line at BMI = 30
    ax.axvline(30, color=axis_color, linestyle="--", linewidth=1.5, alpha=0.9)
    ax.text(
        30.4,
        ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] > 0 else 55000,
        "Obesity Threshold (BMI ≥ 30)",
        fontsize=9.5,
        color=text_color,
        alpha=0.85,
        fontstyle="italic",
    )
    ax.set_xlabel("Body Mass Index (BMI)", fontsize=11, color=text_color, labelpad=10)
    ax.set_ylabel("Medical Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    _style_legend(ax, bg_color, axis_color, text_color)


def _render_region_chart(
    df: pd.DataFrame,
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
    bg_color: str,
) -> None:
    """Render charges by geographic region split by smoker status."""
    regions = sorted(df[COLUMN_REGION].dropna().unique())
    sns.barplot(
        data=df,
        x=COLUMN_REGION,
        y=COLUMN_CHARGES,
        hue=COLUMN_SMOKER,
        order=regions,
        palette={"no": palette["no"], "yes": palette["yes"]},
        errorbar=None,
        edgecolor=text_color,
        linewidth=0.6,
        ax=ax,
    )
    ax.set_xticks(range(len(regions)))
    ax.set_xticklabels([r.title() for r in regions], fontsize=10.5, color=text_color)
    ax.set_xlabel("Geographic Region", fontsize=11, color=text_color, labelpad=10)
    ax.set_ylabel("Mean Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    _style_legend(ax, bg_color, axis_color, text_color)


def _render_sex_chart(
    df: pd.DataFrame,
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
    bg_color: str,
) -> None:
    """Render charges by sex split by smoker status."""
    sns.barplot(
        data=df,
        x=COLUMN_SEX,
        y=COLUMN_CHARGES,
        hue=COLUMN_SMOKER,
        order=["female", "male"],
        palette={"no": palette["no"], "yes": palette["yes"]},
        errorbar=None,
        edgecolor=text_color,
        linewidth=0.6,
        ax=ax,
    )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Female", "Male"], fontsize=11, color=text_color)
    ax.set_xlabel("Sex Cohort", fontsize=11, color=text_color, labelpad=10)
    ax.set_ylabel("Mean Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    _style_legend(ax, bg_color, axis_color, text_color)


def _render_age_chart(
    df: pd.DataFrame,
    ax: plt.Axes,
    palette: dict[str, str],
    text_color: str,
    axis_color: str,
    bg_color: str,
) -> None:
    """Render charges by age brackets split by smoker status."""
    df_temp = df.copy()
    df_temp["age_band"] = pd.cut(
        df_temp[COLUMN_AGE],
        bins=[17, 29, 44, 65],
        labels=["18–29", "30–44", "45–64"],
    )
    sns.barplot(
        data=df_temp,
        x="age_band",
        y=COLUMN_CHARGES,
        hue=COLUMN_SMOKER,
        palette={"no": palette["no"], "yes": palette["yes"]},
        errorbar=None,
        edgecolor=text_color,
        linewidth=0.6,
        ax=ax,
    )
    ax.set_xlabel("Age Cohort", fontsize=11, color=text_color, labelpad=10)
    ax.set_ylabel("Mean Charges (USD)", fontsize=11, color=text_color, labelpad=10)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    _style_legend(ax, bg_color, axis_color, text_color)


def save_default_chart(data: Union[pd.DataFrame, pd.Series]) -> Optional[Path]:
    """Save a high-resolution 300 DPI chart to the ``outputs/`` directory.

    Returns
    -------
    Path | None
        Path to the saved file, or ``None`` on failure.
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        chart_path = OUTPUT_DIR / "smoker_charges_chart.png"
        comparison_path = OUTPUT_DIR / "smoker_charges_comparison.png"
        png_bytes = generate_chart_bytes(data, kind="bar", dark_mode=False, high_res=True)
        chart_path.write_bytes(png_bytes)
        comparison_path.write_bytes(png_bytes)
        logger.info("Chart saved to %s and %s", chart_path, comparison_path)
        return chart_path
    except Exception as exc:
        logger.error("Failed to save chart: %s", exc)
        return None
