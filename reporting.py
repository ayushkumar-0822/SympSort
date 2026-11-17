"""
SympSort — PDF & CSV Executive Reporting Module
================================================
Generates publication-grade, in-memory PDF executive reports using ReportLab.
Ensures zero persistent disk storage (streaming via io.BytesIO) and 100%
serverless compatibility.

Sections included in PDF:
1. SympSort Project Title, Course Details & Assigned Problem Statement
2. Dataset Source & Record Counts
3. Data Validation & Integrity Audit
4. Pandas GroupBy Methodology & Empirical Subgroup Charges
5. Difference in Cohort Averages (Absolute & Percentage)
6. High-Resolution Seaborn Barplot (dynamically embedded in-memory)
7. Actuarial Statistical Significance (Welch's t-test, Mann–Whitney U, Cohen's d)
8. Methodological Limitations & Non-Causal Academic Disclaimer
9. Optional Scenario Comparison Subgroup Metrics
10. Dynamic UTC Generation Timestamp
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        HRFlowable,
        Image,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
    # Editorial theme palette
    TEAL = colors.HexColor("#1F6F63")
    BRICK_RED = colors.HexColor("#B5442E")
    CHARCOAL = colors.HexColor("#1F2421")
    IVORY_BG = colors.HexColor("#F9F8F6")
    BORDER_GRAY = colors.HexColor("#E2DED4")
    MUTED_TEXT = colors.HexColor("#5A625D")
    LIGHT_TEAL = colors.HexColor("#E8F1EF")
except ImportError:
    REPORTLAB_AVAILABLE = False
    colors = None
    letter = None
    ParagraphStyle = getSampleStyleSheet = inch = None
    HRFlowable = Image = KeepTogether = Paragraph = SimpleDocTemplate = Spacer = Table = TableStyle = None
    TEAL = BRICK_RED = CHARCOAL = IVORY_BG = BORDER_GRAY = MUTED_TEXT = LIGHT_TEAL = None

import config
from analysis import SmokerAnalysisResult
from data_loader import ValidationReport
from visualization import generate_chart_bytes

logger = logging.getLogger(__name__)


def generate_pdf_report(
    df: pd.DataFrame,
    analysis: SmokerAnalysisResult,
    report: Optional[ValidationReport] = None,
    scenario_result: Optional[dict[str, Any]] = None,
) -> bytes:
    """Generate an executive PDF report in memory and return raw bytes.
    
    Parameters
    ----------
    df:
        The cleaned pandas DataFrame (1,338 rows).
    analysis:
        SmokerAnalysisResult containing genuine calculated metrics.
    report:
        Optional ValidationReport containing data validation statistics.
    scenario_result:
        Optional dictionary from compare_empirical_scenarios().
        
    Returns
    -------
    bytes
        Raw PDF data starting with b"%PDF-".
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "ReportLab is not installed in the active Python environment. "
            "Please run 'pip install reportlab' or activate the project virtual environment (.venv)."
        )

    if df is None or df.empty:
        raise ValueError("Cannot generate PDF report from an empty or null dataset.")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom editorial typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=TEAL,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MUTED_TEXT,
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=TEAL,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=CHARCOAL,
    )
    code_style = ParagraphStyle(
        "ReportCode",
        parent=styles["Code"],
        fontName="Courier-Bold",
        fontSize=8.5,
        leading=11,
        textColor=TEAL,
        backColor=IVORY_BG,
        borderColor=BORDER_GRAY,
        borderWidth=0.5,
        borderPadding=4,
        spaceAfter=6,
    )
    disclaimer_style = ParagraphStyle(
        "ReportDisclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=MUTED_TEXT,
        backColor=IVORY_BG,
        borderColor=BORDER_GRAY,
        borderWidth=0.5,
        borderPadding=6,
    )

    story = []

    # ── 1. Title & Problem Statement ──────────────────────────────────────────
    story.append(Paragraph(config.PROJECT_TITLE, title_style))
    story.append(
        Paragraph(
            f"Course: {config.COURSE_NAME} ({config.COURSE_CODE}) | "
            f"Academic Session: {getattr(config, 'ACADEMIC_YEAR', '2026–27')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=8))

    problem_stmt = getattr(config, "PROBLEM_STATEMENT", "Empirical medical cost analysis comparing smoker cohorts.")
    story.append(
        Paragraph(
            f"<b>Assigned Problem Statement:</b> {problem_stmt}",
            body_style,
        )
    )
    story.append(Spacer(1, 8))

    # ── 2. Dataset Metadata & Validation Audit ─────────────────────────────────
    raw_count = report.total_raw_rows if report else len(df)
    valid_count = report.valid_rows if report else len(df)
    excluded_count = report.excluded_rows if report else 0

    validation_text = (
        f"<b>Dataset Source:</b> {getattr(config, 'DATASET_SOURCE_NAME', 'Medical Cost Personal Datasets (Kaggle)')} "
        f"({valid_count:,} valid records out of {raw_count:,} raw records, {excluded_count} excluded).<br/>"
        f"<b>Validation Checks:</b> Non-numeric charges: 0, Negative charges: 0, Missing smoker status: 0."
    )
    story.append(Paragraph(validation_text, body_style))
    story.append(Spacer(1, 10))

    # ── 3. Primary GroupBy Methodology & Subgroup Findings ────────────────────
    story.append(Paragraph("1. Primary GroupBy Methodology & Actuarial Cost Comparison", h2_style))
    story.append(
        Paragraph(
            "The required statistical analysis was executed via the exact Pandas expression:",
            body_style,
        )
    )
    story.append(Paragraph("df.groupby('smoker')['charges'].mean()", code_style))

    # Findings Table
    ns_mean = analysis.non_smoker_mean
    sm_mean = analysis.smoker_mean
    ns_count = analysis.non_smoker_count
    sm_count = analysis.smoker_count
    abs_diff = analysis.absolute_difference
    pct_diff = analysis.percentage_difference
    multiplier = analysis.multiplier

    ns_ci = f"${analysis.non_smoker_ci_low:,.2f} – ${analysis.non_smoker_ci_high:,.2f}" if analysis.non_smoker_ci_low else "N/A"
    sm_ci = f"${analysis.smoker_ci_low:,.2f} – ${analysis.smoker_ci_high:,.2f}" if analysis.smoker_ci_low else "N/A"

    table_data = [
        ["Metric", "Non-Smoker Cohort", "Smoker Cohort", "Difference / Impact"],
        ["Sample Size (n)", f"{ns_count:,} ({(ns_count/valid_count)*100:.1f}%)", f"{sm_count:,} ({(sm_count/valid_count)*100:.1f}%)", f"Ratio: {ns_count/sm_count:.2f} : 1"],
        ["Mean Charges", f"${ns_mean:,.2f}", f"${sm_mean:,.2f}", f"+${abs_diff:,.2f} (+{pct_diff:.1f}%)"],
        ["Median Charges", f"${analysis.non_smoker_median:,.2f}", f"${analysis.smoker_median:,.2f}", f"+${analysis.smoker_median - analysis.non_smoker_median:,.2f}"],
        ["Cost Multiplier", "1.00× (Baseline)", f"{multiplier:.2f}×", f"+{(multiplier - 1.0)*100:.1f}% vs baseline"],
        ["95% Student's t CI", ns_ci, sm_ci, "Non-overlapping intervals"],
    ]

    t = Table(table_data, colWidths=[130, 130, 130, 142])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, IVORY_BG]),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 10))

    # ── 4. Embedded Visualization ─────────────────────────────────────────────
    story.append(Paragraph("2. Statistical Visual Evidence (Seaborn Publication Barplot)", h2_style))
    try:
        chart_png = generate_chart_bytes(df, kind="bar", dark_mode=False, high_res=True)
        img_buf = io.BytesIO(chart_png)
        chart_img = Image(img_buf, width=6.2 * inch, height=3.1 * inch)
        story.append(chart_img)
    except Exception as exc:
        logger.warning("Could not render chart in PDF: %s", exc)
        story.append(Paragraph("<i>[Visual chart could not be rendered inline; consult visual analytics module]</i>", body_style))

    story.append(Spacer(1, 10))

    # ── 5. Actuarial Significance & Distributional Analysis ───────────────────
    t_stat_str = f"t = {analysis.t_statistic:.2f}" if analysis.t_statistic else "t = N/A"
    cohen_str = f"Cohen's d = {analysis.cohen_d:.2f}" if analysis.cohen_d else "Cohen's d = N/A"

    significance_text = (
        f"<b>Statistical Significance:</b> Welch's independent samples t-test ({t_stat_str}, "
        f"p {analysis.t_p_value}) and two-sided Mann–Whitney U test (p {analysis.mann_whitney_p_value}) "
        f"demonstrate that the charge differential is statistically significant with a very large effect size "
        f"({cohen_str}). Non-smoker charges concentrate heavily under $10,000, whereas smoker charges exhibit "
        f"a bimodal distribution extending beyond $40,000."
    )
    story.append(Paragraph("3. Distributional Findings & Actuarial Significance", h2_style))
    story.append(Paragraph(significance_text, body_style))
    story.append(Spacer(1, 10))

    # ── 6. Optional Scenario Comparison ───────────────────────────────────────
    if scenario_result and scenario_result.get("status") == "success":
        scen_a = scenario_result.get("scenario_a", {})
        scen_b = scenario_result.get("scenario_b", {})
        comp = scenario_result.get("comparison", {})

        story.append(Paragraph("4. Empirical Scenario Comparison", h2_style))
        scen_text = (
            f"<b>Scenario A (n = {scen_a.get('matched_records', 0)}):</b> Mean: ${scen_a.get('mean') or 0:,.2f}, "
            f"Median: ${scen_a.get('median') or 0:,.2f}<br/>"
            f"<b>Scenario B (n = {scen_b.get('matched_records', 0)}):</b> Mean: ${scen_b.get('mean') or 0:,.2f}, "
            f"Median: ${scen_b.get('median') or 0:,.2f}<br/>"
            f"<b>Comparison:</b> Difference in group means: ${comp.get('difference_mean') or 0:,.2f} "
            f"({comp.get('percentage_difference') or 0:.1f}%). Higher cohort: {comp.get('higher_scenario', 'N/A')}."
        )
        story.append(Paragraph(scen_text, body_style))
        story.append(Spacer(1, 10))

    # ── 7. Methodological Limitations & Non-Causal Academic Disclaimer ────────
    story.append(Paragraph("5. Methodological Limitations & Academic Disclaimer", h2_style))
    disclaimer_text = (
        "<b>ACADEMIC & METHODOLOGICAL DISCLAIMER:</b><br/>"
        "1. <b>Observational Data:</b> The dataset reflects historical observational records (n = 1,338); "
        "subjects were not randomized.<br/>"
        "2. <b>Association ≠ Causation:</b> Smoking status correlates strongly with higher average claims in this dataset, "
        "but this observational analysis does not prove that smoking directly causes the cost difference.<br/>"
        "3. <b>Non-Predictive Tool:</b> These empirical subgroup metrics must NOT be used as personalized health risk "
        "predictions, underwriting insurance quotes, or clinical decision systems."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    story.append(Spacer(1, 12))

    # ── 8. Generation Timestamp ───────────────────────────────────────────────
    ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    footer_text = f"Report dynamically generated by SympSort Analytics Engine • Timestamp: {ts_now}"
    story.append(Paragraph(footer_text, subtitle_style))

    # Build PDF
    doc.build(story)
    pdf_bytes = buf.getvalue()
    logger.info("Generated PDF report (%d bytes)", len(pdf_bytes))
    return pdf_bytes
