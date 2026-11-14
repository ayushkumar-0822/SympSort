"""
SympSort — Visualization Module
=================================
Generates bar-chart PNGs comparing smoker vs non-smoker mean charges using
Matplotlib / Seaborn.  Charts are returned as ``bytes`` (PNG) and cached
per theme until a data reload.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

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
    COLOR_NON_SMOKER,
    COLOR_SMOKER,
    OUTPUT_DIR,
    PALETTE_DARK,
    PALETTE_LIGHT,
)

logger = logging.getLogger(__name__)

# ── In-memory chart cache ─────────────────────────────────────────────────────
_chart_cache: dict[str, bytes] = {}


def clear_chart_cache() -> None:
    """Invalidate all cached chart images (call on data reload)."""
    _chart_cache.clear()
    logger.info("Chart cache cleared.")


def generate_chart_bytes(
    df_grouped: pd.Series,
    dark_mode: bool = False,
    high_res: bool = False,
) -> bytes:
    """Render a smoker-vs-non-smoker bar chart and return PNG bytes.

    Parameters
    ----------
    df_grouped:
        A ``pd.Series`` indexed by smoker status (``"no"``, ``"yes"``)
        with mean charges as values.
    dark_mode:
        Use the dark colour scheme.
    high_res:
        Render at 300 DPI (download quality) instead of 150 DPI (screen).

    Returns
    -------
    bytes
        Raw PNG image data.
    """
    cache_key = f"{'dark' if dark_mode else 'light'}_{'hi' if high_res else 'lo'}"

    if cache_key in _chart_cache and not high_res:
        return _chart_cache[cache_key]

    dpi = CHART_DPI_DOWNLOAD if high_res else CHART_DPI_SCREEN

    # ── Theme colours ─────────────────────────────────────────────────────
    palette = PALETTE_DARK if dark_mode else PALETTE_LIGHT
    bg_color = CHART_BG_DARK if dark_mode else CHART_BG_LIGHT
    text_color = CHART_TEXT_DARK if dark_mode else CHART_TEXT_LIGHT
    axis_color = CHART_AXIS_DARK if dark_mode else CHART_AXIS_LIGHT

    # ── Build data frame for seaborn ──────────────────────────────────────
    plot_df = pd.DataFrame({
        "Smoker Status": ["Non-Smoker", "Smoker"],
        "Mean Charges ($)": [
            float(df_grouped.get("no", 0)),
            float(df_grouped.get("yes", 0)),
        ],
    })
    bar_colors = [palette["no"], palette["yes"]]

    # ── Create figure ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    sns.barplot(
        data=plot_df,
        x="Smoker Status",
        y="Mean Charges ($)",
        hue="Smoker Status",
        palette={"Non-Smoker": palette["no"], "Smoker": palette["yes"]},
        edgecolor=text_color,
        linewidth=0.8,
        errorbar=("ci", 95),
        legend=False,
        ax=ax,
    )

    # ── Dollar labels on bars ─────────────────────────────────────────────
    for bar, value in zip(ax.patches, plot_df["Mean Charges ($)"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 300,
            f"${value:,.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=text_color,
        )

    # ── Axis styling ──────────────────────────────────────────────────────
    ax.set_title(
        "Average Medical Charges: Smoker vs Non-Smoker",
        fontsize=14,
        fontweight="bold",
        color=text_color,
        pad=14,
    )
    ax.set_xlabel("Smoking Status", fontsize=12, color=text_color, labelpad=8)
    ax.set_ylabel("Mean Charges (USD)", fontsize=12, color=text_color, labelpad=8)

    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.tick_params(colors=text_color, labelsize=10)

    # Thin axis lines, no heavy gridlines
    for spine in ax.spines.values():
        spine.set_color(axis_color)
        spine.set_linewidth(0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.yaxis.grid(True, color=axis_color, linewidth=0.3, alpha=0.5)
    ax.set_axisbelow(True)

    fig.tight_layout()

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


def save_default_chart(df_grouped: pd.Series) -> Optional[Path]:
    """Save a high-resolution chart to the ``outputs/`` directory.

    Returns
    -------
    Path | None
        Path to the saved file, or ``None`` on failure.
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        chart_path = OUTPUT_DIR / "smoker_charges_chart.png"
        png_bytes = generate_chart_bytes(df_grouped, dark_mode=False, high_res=True)
        chart_path.write_bytes(png_bytes)
        logger.info("Chart saved to %s", chart_path)
        return chart_path
    except Exception as exc:
        logger.error("Failed to save chart: %s", exc)
        return None
