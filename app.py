"""
SympSort — Flask Web Application
=================================
Application factory and routes for the SympSort desktop web application.
Serves static assets, HTML templates, and REST JSON APIs for data,
statistical summaries, charts, and file downloads.
"""

from __future__ import annotations

import csv
import io
import logging
import math
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
)

import config
from analysis import SmokerAnalysisResult, calculate_smoker_charges
from data_loader import ValidationReport, load_dataset
from visualization import generate_chart_bytes, save_default_chart

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # ── Application-level cache ───────────────────────────────────────────
    _cache: dict[str, Any] = {
        "df_valid": None,
        "df_raw": None,
        "report": None,
        "analysis": None,
    }

    def get_data(
        force_reload: bool = False,
    ) -> tuple[pd.DataFrame, SmokerAnalysisResult, ValidationReport]:
        """Return cached (df, analysis, report), loading on first call."""
        if not force_reload and _cache["df_valid"] is not None:
            return _cache["df_valid"], _cache["analysis"], _cache["report"]

        logger.info("Loading dataset (force_reload=%s)", force_reload)
        df_valid, df_raw, report = load_dataset()

        if report.is_valid and df_valid is not None and not df_valid.empty:
            analysis = calculate_smoker_charges(df_valid)
            try:
                save_default_chart(analysis.df_grouped)
            except Exception as exc:
                logger.warning("Could not pre-save default chart: %s", exc)
        else:
            analysis = SmokerAnalysisResult()
            df_valid = pd.DataFrame()
            df_raw = pd.DataFrame()

        _cache["df_valid"] = df_valid
        _cache["df_raw"] = df_raw
        _cache["report"] = report
        _cache["analysis"] = analysis

        return df_valid, analysis, report

    # ── Page routes ───────────────────────────────────────────────────────

    @app.route("/")
    def index():
        """Serve the single-page application shell."""
        df, analysis, report = get_data()
        return render_template(
            "index.html",
            project_name=config.PROJECT_NAME,
            project_title=config.PROJECT_TITLE,
            course_name=config.COURSE_NAME,
            course_code=config.COURSE_CODE,
            problem_statement=config.PROBLEM_STATEMENT,
            dataset_source_url=config.DATASET_SOURCE_URL,
            dataset_source_name=getattr(config, "DATASET_SOURCE_NAME", "Medical Cost Personal Datasets (Kaggle)"),
            analysis=analysis.to_dict(),
            report={
                "is_valid": report.is_valid,
                "total_raw_rows": report.total_raw_rows,
                "valid_rows": report.valid_rows,
                "excluded_rows": report.excluded_rows,
                "used_sample": report.used_sample,
            },
        )

    # ── API routes ────────────────────────────────────────────────────────

    @app.route("/api/health")
    def api_health():
        """Simple health check endpoint."""
        df, _analysis, _report = get_data()
        return jsonify({"status": "ok", "rows": len(df)})

    @app.route("/api/summary")
    def api_summary():
        """Full analysis summary as JSON."""
        df, analysis, report = get_data()
        payload = analysis.to_dict()
        payload["status"] = "success"
        payload["is_valid"] = report.is_valid
        payload["analysis"] = analysis.to_dict()
        payload["validation"] = {
            "is_valid": report.is_valid,
            "file_path": report.file_path,
            "total_raw_rows": report.total_raw_rows,
            "valid_rows": report.valid_rows,
            "excluded_rows": report.excluded_rows,
            "null_charges_count": report.null_charges_count,
            "invalid_smoker_count": report.invalid_smoker_count,
            "used_sample": report.used_sample,
            "warnings": report.warnings,
        }
        return jsonify(payload)

    @app.route("/api/chart")
    def api_chart():
        """Return chart PNG. ``?theme=dark`` for dark-mode variant."""
        _df, analysis, _report = get_data()
        if analysis.df_grouped is None:
            return jsonify({"error": "No data available"}), 500

        theme = request.args.get("theme", "light").strip().lower()
        dark_mode = theme == "dark"
        png_bytes = generate_chart_bytes(
            analysis.df_grouped, dark_mode=dark_mode, high_res=False
        )
        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            download_name="chart.png",
        )

    @app.route("/api/data")
    def api_data():
        """Paginated, filterable, sortable dataset rows."""
        df, _analysis, _report = get_data()
        filtered = _apply_filters(df, request.args)

        # Sorting
        sort_col = request.args.get("sort", "").strip().lower()
        order = request.args.get("order", "asc").strip().lower()
        if sort_col and sort_col in filtered.columns:
            ascending = order != "desc"
            filtered = filtered.sort_values(by=sort_col, ascending=ascending)

        # Pagination
        try:
            page = max(1, int(request.args.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = min(
                config.MAX_PAGE_SIZE,
                max(1, int(request.args.get("page_size", config.DEFAULT_PAGE_SIZE))),
            )
        except (ValueError, TypeError):
            page_size = config.DEFAULT_PAGE_SIZE

        total_filtered = len(filtered)
        total_pages = max(1, math.ceil(total_filtered / page_size))
        page = min(page, total_pages)

        start = (page - 1) * page_size
        end = start + page_size
        page_df = filtered.iloc[start:end]

        # Convert to list[dict], replacing NaN with None for JSON
        records = _df_to_records(page_df)

        return jsonify({
            "records": records,
            "total_records": len(df),
            "total_unfiltered": len(df),
            "total_filtered": total_filtered,
            "page": page,
            "pages": total_pages,
            "total_pages": total_pages,
            "page_size": page_size,
        })

    @app.route("/api/reload", methods=["POST"])
    def api_reload():
        """Force-reload the dataset from disk."""
        df, _analysis, report = get_data(force_reload=True)
        return jsonify({
            "status": "success",
            "message": f"Reloaded {len(df)} rows",
            "total_rows": len(df),
            "rows": len(df),
            "valid_rows": report.valid_rows,
            "is_valid": report.is_valid,
        })

    @app.route("/api/download/chart")
    def api_download_chart():
        """Download high-resolution (300 DPI) chart."""
        _df, analysis, _report = get_data()
        if analysis.df_grouped is None:
            return jsonify({"error": "No data available"}), 500

        png_bytes = generate_chart_bytes(
            analysis.df_grouped, dark_mode=False, high_res=True
        )
        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name="sympsort_smoker_charges.png",
        )

    @app.route("/api/download/summary")
    def api_download_summary():
        """Download analysis summary as CSV."""
        _df, analysis, _report = get_data()
        summary = analysis.to_dict()

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["metric", "value"])
        for k, v in summary.items():
            if k not in ("academic_disclaimer", "groupby_text"):
                writer.writerow([k, v])

        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=smoker_charges_summary.csv"
            },
        )

    return app


# ── Internal helpers ──────────────────────────────────────────────────────────

def _apply_filters(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Filter DataFrame by search query, smoker status, and region."""
    filtered = df.copy()

    # Smoker filter
    smoker = params.get("smoker", "").strip().lower()
    if smoker in config.VALID_SMOKER_VALUES:
        filtered = filtered[filtered[config.COLUMN_SMOKER] == smoker]

    # Region filter
    region = params.get("region", "").strip().lower()
    if region and region in config.VALID_REGIONS:
        filtered = filtered[filtered[config.COLUMN_REGION] == region]

    # Search filter (across text & numeric columns)
    search = params.get("search", "").strip().lower()
    if search:
        masks = []
        for col in filtered.columns:
            masks.append(
                filtered[col].astype(str).str.lower().str.contains(search, regex=False)
            )
        combined_mask = pd.concat(masks, axis=1).any(axis=1)
        filtered = filtered[combined_mask]

    return filtered


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame rows to JSON-safe dictionaries (NaN -> None)."""
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            elif isinstance(val, (int, float)):
                # Ensure Python native types
                record[col] = int(val) if isinstance(val, int) or val == int(val) else float(val)
            else:
                record[col] = str(val)
        records.append(record)
    return records
